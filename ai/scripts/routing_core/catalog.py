from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat as _stat
import subprocess
import time
import tomllib
from pathlib import Path
from .domain import CatalogSnapshot, RoutingError, StaticRoute, _sorted_strings
# ADR-0042 (022 PKG-1): the single provider registry every provider-keyed table in this file
# derives from. Deliberately a plain top-level import, not a relative `.` one -- the module
# lives OUTSIDE `routing_core` on purpose (see its own docstring and ADR-0042's "Dónde puede
# vivir PROVIDERS" section): it has zero dependencies of its own, so importing it here costs
# nothing this package's other two consumers (`models_config.py`, `set_agents_app.py`) don't
# already pay to import it too.
from provider_registry import PROVIDERS

# ADR-0006 (AM-2): probe cache is a filtering-only optimization. TTL bounds staleness;
# the invalidation key covers uid and the canonical catalog/routing config.
PROBE_CACHE_TTL = 300.0
# ADR-0034 (019 PKG-1, AC-08): bump whenever the cache's CONTENT SHAPE or key semantics
# change -- a stale on-disk document written under an old schema can never be read back
# as if it matched the new one, without waiting for a manual TTL/format migration.
# ADR-0043 (022 PKG-3, AC-09): bumped 2 -> 3 -- `_cache_key`'s KEY SEMANTICS changed
# (six new stat/local-read signatures folded in, AC-07), even though the persisted
# document's own shape (`{"key", "at", "pairs"}`) did not move. A cache document
# written and keyed under schema 2 can never silently read back as valid under 3 --
# see test_adr0043_ac09_cache_schema_version_bump_invalidates_old_cache_documents.
_CACHE_SCHEMA_VERSION = 3

# ADR-0007 (P3-pi-lane, T-301/T-305): pi is invoked through an EXACT pinned version, never
# the bare `pi` on PATH (the managed `~/.local/bin/pi` wrapper only soft-pins by release
# age via PNPM_CONFIG_MINIMUM_RELEASE_AGE) — the probe below and the T-303 spawner share
# this ONE invocation builder, so the audited pair and the executed child are provably the
# same binary. Bump PI_PINNED_VERSION deliberately (code review), never silently.
PI_PACKAGE = "@earendil-works/pi-coding-agent"
PI_PINNED_VERSION = "0.84.0"

# PKG-N02 (repair R1): `set_agents_app.py --doctor --harness pi` already allows 60s
# (DOCTOR_TIMEOUT_SECONDS in set_agents_spawn.py) for a cold `pnpm dlx` resolution on the
# FIRST invocation of the pinned version in a given pnpm store. `probe_inventory`'s own
# default timeout (20s, chosen for the other three runtimes' fast local CLI probes) was
# never raised to match, so a genuinely cold store could silently time out the pi probe
# and produce a false PROVIDER_UNAUTHENTICATED until the store warmed — this floor closes
# that gap for the pi pairs specifically, without slowing down the other (already-fast)
# probes that share the same `timeout` parameter.
PI_PROBE_MIN_TIMEOUT_SECONDS = 60.0


def pi_pinned_argv(*args: str) -> tuple[str, ...]:
    """Exact-version-pinned `pi` invocation shared by the probe (here) and set_agents_spawn.

    Deliberately NO `--` separator before `args`: live QA (2026-07-27) found `pnpm dlx
    --package <pkg> pi -- <args>` forwards that `--` VERBATIM into pi's own argument
    parser instead of stripping it — `pi --version`/`pi --list-models` tolerate the stray
    token (both short-circuit on the first recognized early-exit flag regardless of what
    else is on the line), which silently masked the bug for the probe/doctor calls, but a
    real spawn invocation (`--model ... --print ...`) fails hard with `Unknown option: --`.
    `pnpm dlx --package <pkg> <bin> <args...>` (no separator) is the correct form."""
    return ("pnpm", "dlx", "--package", f"{PI_PACKAGE}@{PI_PINNED_VERSION}", "pi", *args)


# T-305: catalog model id -> Pi canonical model id. openai-codex is IDENTITY (spike-verified
# live, 2026-07-27: catalog `gpt-5.6-luna|sol|terra` == Pi's raw id, zero translation).
# anthropic short catalog names need this curated map (spike-verified against a live
# `pi --list-models`, aligned with the harness's own Claude tiers: auditors=opus-4.8,
# implement=sonnet-5, mechanical=haiku-4.5) — the ONLY translation P3 needs, user-adjustable
# if Pi's catalog names move.
PI_MODEL_MAP = {"anthropic": {"opus": "claude-opus-4-8", "sonnet": "claude-sonnet-5", "haiku": "claude-haiku-4-5"}}

# Repair SEC-001 (panel RP-01, security-auditor, critical, 012 repair): AC-07's
# family-collision guard originally keyed `seen` on the RAW `model` string, so the SAME
# underlying model curated under two DIFFERENT ids for two different providers (not the
# same id under two providers, which AC-07's rule already catches) never collided at all
# — e.g. `anthropic`/`opus` and a future `opencode-zen`/`claude-opus-4-8` row are the
# identical model (proven in-repo by PI_MODEL_MAP above) but two different `model`
# strings, so the old rule's `model in seen` check was always False for that pair.
# CANONICAL_MODEL is a curated `(provider, model) -> canonical id` map, seeded from
# PI_MODEL_MAP (the only other place in this file that already asserts this exact
# identity), so `canonical_model` below resolves both spellings to the same key. Absent
# from this map, a model id is already its own canonical form — this never invents an
# equivalence beyond what is explicitly curated here, same discipline as PROVIDER_BILLING_KIND.
#
# Repair SEC-002 (delta-review round 2, medium): PI_MODEL_MAP is Pi's own CLI-invocation
# name-translation table (a different purpose and lifecycle from a security guarantee —
# see the comment at PI_MODEL_MAP's own definition above), and it does not cover every
# Anthropic id models.toml's `[catalog].claude` allowlist curates: `fable` has no Pi
# route, so PI_MODEL_MAP never needed to translate it, but `[catalog].opencode_zen`
# still curates the SAME underlying model under the alias `claude-fable-5` — seeding
# CANONICAL_MODEL from PI_MODEL_MAP alone left exactly this one pair uncurated, reopening
# the SEC-001 hole for the single Anthropic model PI_MODEL_MAP doesn't translate.
# _ANTHROPIC_CANONICAL_EXTRA is the explicit, hand-curated completion for ids PI_MODEL_MAP
# has no reason to cover — never derived from PI_MODEL_MAP or any other table with a
# different purpose. The coherence test (test_sec002_... in tests/test_routing.py)
# asserts every `[catalog].claude` id resolves, through canonical_model, to a canonical
# id actually present in `[catalog].opencode_zen`, so a future fifth Anthropic id added
# to the allowlist without a curated alias here fails the suite instead of silently
# reopening this same hole again.
_ANTHROPIC_CANONICAL_EXTRA = {"fable": "claude-fable-5"}
_ANTHROPIC_CANONICAL: dict[str, str] = {**PI_MODEL_MAP["anthropic"], **_ANTHROPIC_CANONICAL_EXTRA}
CANONICAL_MODEL: dict[tuple[str, str], str] = {("anthropic", short): canonical
                                               for short, canonical in _ANTHROPIC_CANONICAL.items()}
CANONICAL_MODEL.update({(provider, canonical): canonical
                        for provider in ("opencode-zen", "opencode-go")
                        for canonical in _ANTHROPIC_CANONICAL.values()})


def canonical_model(provider: str, model: str) -> str:
    """Curated cross-provider model-identity normalization (repair SEC-001). Resolves a
    (provider, model) pair to a canonical id ONLY where CANONICAL_MODEL explicitly
    curates the two as the same underlying model; every other pair maps to its own
    `model` string unchanged (identity), so this can never widen equivalence beyond what
    a human curated. Consumed by `_check_family_collisions` below (layer 1) and by
    `service.py`'s REVIEW_MODEL_CONFLICT hard exclusion (layer 2, defense in depth)."""
    return CANONICAL_MODEL.get((provider, model), model)


# ADR-0042 (022 PKG-1): both maps below DERIVE from the single `PROVIDERS` registry now
# (`provider_registry.py`) -- before this ADR they were two independently hand-edited
# literals, one of six provider-keyed tables that had to move in lockstep by hand across
# this file, `models_config.py`, and `set_agents_app.py`. Values are unchanged from the
# pre-ADR-0042 literals (PKG-1 AC-02 characterization test pins this).
#
# Catalog provider -> credential display text `_parse_opencode_auth` yields (map 1 of 2,
# 012 AC-02). Used ONLY at the credential-set membership check. For the two pre-existing
# pairs this string happens to coincide with the CLI argument below; for opencode-zen/
# opencode-go it does not ("opencode zen"/"opencode go", two-token display text, vs the
# single-token CLI ids in _OPENCODE_CLI_IDS) — re-measured live against `opencode auth
# list --pure` (docs/specs/012-discovered-inventory/spec.md AC-02).
_OPENCODE_PROVIDER_KEYS = {provider: spec.opencode_auth_key for provider, spec in PROVIDERS.items()}
# Catalog provider -> CLI argument for `opencode models <id>` AND the `<id>/<model>` line
# prefix `_parse_opencode_models` strips (map 2 of 2, 012 AC-02). Independently
# addressable from _OPENCODE_PROVIDER_KEYS above: using the CLI-id value at the
# credential-membership check would search the two-token display-name set for a
# single-token string and report the pair absent on every machine (the defect this
# two-map split fixes; PI_MODEL_MAP is explicitly the wrong precedent here — it
# translates a model name within one already-matched provider, a different axis).
_OPENCODE_CLI_IDS = {provider: spec.opencode_cli_id for provider, spec in PROVIDERS.items()}
# ADR-0034 (019 PKG-1) re-measurement, live, 2026-08-10 (opencode 1.18.14): `opencode
# auth list --pure` shows 4 real credentials -- `opencode-go`, `openai`, `github-copilot`,
# `opencode` (auth.json keys). `github-copilot` is authenticated but `opencode models
# github-copilot --pure` (even with `--refresh`) answers `Error: Provider not found:
# github-copilot` -- no CLI id verifies it, so NO pair is added for it here (M-1, fail-
# closed: never hardcode an unverified CLI id, never derive one by a display-name-to-
# CLI-id heuristic like "replace the space with a hyphen" -- that would have produced
# the WRONG id for `opencode-go` itself, "opencode go" -> "opencode-go" only works by
# coincidence for that one pair and fails silently for anything else). The opencode
# `openai` provider (OAuth ChatGPT) is NOT a new provider either -- it is the display/CLI
# name this table ALREADY maps to `openai-codex` (M-2); no duplicate catalog provider is
# added for it. Detection is structural, not a separate code path: `github-copilot`
# never appears in `_PAIR_COMMANDS`, so `_probe_pairs` never even queries it -- the rest
# of the inventory is never at risk of an unverified id leaking in. `--route-doctor`
# (PKG-2, ADR-0035) is the surface that will report "detected, unlistable" to a human;
# nothing here needs to change for that report to be accurate.
# The audited pair table is the single source of runtime/provider compatibility:
# a pair absent here can never authenticate, list models, or appear in identities.
# 012 AC-01: two OpenCode-lane pairs added, `opencode-zen`/`opencode-go` — real,
# currently-authenticated OpenCode providers that were simply outside this table
# (see docs/specs/012-discovered-inventory/spec.md AC-01). No other runtime gains a
# pair; codex/claude-code/pi have no client for either and none is implied here.
# Repair F-05 (012 repair): the opencode-lane argv is DERIVED from _OPENCODE_CLI_IDS
# above, never a second hardcoded copy of the CLI id — a future change to one map with
# the other left stale would otherwise silently leave a pair absent, undetected by any
# test or the live gate (both only ever exercise whichever id `_PAIR_COMMANDS` itself
# carries).
_PAIR_COMMANDS = {
    ("codex", "openai-codex"): (("codex", "login", "status"),),
    ("claude-code", "anthropic"): (("claude", "auth", "status", "--json"),),
    **{("opencode", provider): (("opencode", "auth", "list", "--pure"), ("opencode", "models", cli_id, "--pure"))
       for provider, cli_id in _OPENCODE_CLI_IDS.items()},
    ("pi", "openai-codex"): (pi_pinned_argv("--list-models"),),
    ("pi", "anthropic"): (pi_pinned_argv("--list-models"),),
}
# 012 AC-08: billing-model distinction, curated per provider — NEVER a routes.v1.toml row
# field (the row schema is closed, required_keys/optional_keys below; an extra key raises
# CATALOG_INVALID for every provider, existing two included). OpenCode Go is a monthly
# subscription; OpenCode Zen is metered/API-key (user clarification, logged at
# ai/state/decisions-log.jsonl, slug opencode-zen-go-billing-model-distinto-no-mismo-pool).
# ADR-0035 (019 PKG-2): completed to cover every DISCOVERABLE_PROVIDERS member --
# `openai-codex`/`anthropic` are the curated subscription lanes (Codex CLI login, Claude
# Code OAuth), `opencode-go` stays subscription, `opencode-zen` stays the sole metered
# entry. This is the day `billing_rank` (below) starts reading it -- the previous "no
# weighting/selection logic reads this map yet" note is retired.
# ADR-0042 (022 PKG-1): derives from `PROVIDERS` now, same values as the pre-ADR-0042 literal.
PROVIDER_BILLING_KIND = {provider: spec.billing_kind for provider, spec in PROVIDERS.items()}
# ADR-0035 AC-12: the FREE-model convention is the `-free` suffix -- the exact same
# pattern `inference._FAST_HINTS` already treats as a signal, never a second, competing
# definition of "free" invented here.
_FREE_MODEL_SUFFIX = re.compile(r"-free(\b|$)")


def billing_rank(provider: str, model: str) -> int:
    """ADR-0035 (AC-12): pure order-only signal, `0` (cheap: subscription or a free-suffixed
    model) or `1` (metered, or a provider this map does not even know -- fail-closed toward
    the expensive rank, never toward the cheap one for an unrecognized provider). Consulted
    ONLY by `service.route`'s sort key, strictly between `TIER_ORDER` and `_bias_rank`
    (ADR-0035 d.3) -- it can never affect which candidates reach the sort, only the order
    among candidates that already survived every hard exclusion."""
    if PROVIDER_BILLING_KIND.get(provider) == "subscription":
        return 0
    if isinstance(model, str) and _FREE_MODEL_SUFFIX.search(model):
        return 0
    return 1
_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def allowed_probe(runtime: str, provider: str) -> tuple[tuple[str, ...], ...] | None:
    """The closed, exact argv list for a pair; None for any unaudited pair."""
    return _PAIR_COMMANDS.get((runtime, provider))


# ADR-0042 (022 PKG-1/PKG-2): provider -> `[catalog]` TOML key, derived from `PROVIDERS`
# (same values as the pre-ADR-0042 inline literal `_configured_models` used to carry). Site
# (2) of the five-site lockstep `resolve_ceiling` documents below -- the other four sites
# (the `[catalog]` table itself, `build_snapshot`'s own comprehension, and the two
# `models_config.py` sites) are a DIFFERENT, wider concern (012 AC-04: whether a TOML key
# exists and round-trips through `load_config`/`emit` at all) and are out of this package's
# scope -- only this key map derives from the single provider registry.
_CATALOG_KEYS = {provider: spec.catalog_key for provider, spec in PROVIDERS.items()}


def resolve_ceiling(config: dict, provider: str) -> tuple[str, set[str] | None]:
    """ADR-0042 (022 PKG-2): the tri-state ceiling every one of this file's three
    consumers (`_probe_pairs`, `_read_probe_cache`, `build_snapshot`) reads through now,
    replacing the two-state `_configured_models` this function inlined and removed. That
    function only ever returned a bare `set()`, which collapsed two genuinely different
    TOML shapes into the identical value: "no `[catalog]` key at all for this provider"
    and "curated as an explicit empty allowlist". The FIRST must mean "no ceiling, the
    live probe result is the routable set"; the SECOND must mean "never route this
    provider, no matter what the probe shows" -- conflating them is exactly why
    `_probe_pairs`'s `if not allowed: continue` skipped a provider ENTIRELY the moment its
    `[catalog]` key was absent, which in turn forced editing `models.toml` to add any new
    provider (the defect this whole package exists to remove).

    Three states, a pure reflection of the literal TOML shape under `[catalog].<key>`:
      - key absent from `[catalog]` entirely (or `provider` has no dedicated key at all,
        e.g. a future `PROVIDERS` entry added without one) => `("auto", None)` -- no
        ceiling; whatever the live probe reports for this provider IS the routable set,
        unfiltered by any curated allowlist.
      - key present as `[]` => `("veto", set())` -- curated, explicit "never route this
        provider", regardless of what the live probe would otherwise show.
      - key present as a non-empty list => `("curated", set-of-ids)` -- the audited
        ceiling every model must be a member of (today's only behavior, unchanged).

    Same five-site lockstep `_configured_models` used to document, site (2) of 5: (1)
    `models.toml`'s `[catalog]` table itself; (2) this key map (`_CATALOG_KEYS` above); (3)
    `build_snapshot`'s own `configured_models` comprehension (below); (4)
    `models_config.load_config`'s optional-key validation loop for the same two TOML keys
    (accepts `[]` now, AC-04); (5) `models_config.emit`'s preservation loop for the same
    two keys (round-trips absence AND `[]`, never inventing either).

    Per ADR-0042 (022 PKG-2, decision recorded by Federico 2026-08-12, spec AC-04): in
    PRACTICE only `opencode-zen`/`opencode-go` ever reach the "auto"/"veto" branches --
    `models_config.load_config` dies if `[catalog].claude`/`.codex` are absent or empty, so
    `openai-codex`/`anthropic` are structurally guaranteed "curated" by the time any caller
    here has a validated config. `resolve_ceiling` itself stays provider-agnostic and
    enforces nothing about WHICH providers may reach which state -- that restriction lives
    at the validation layer (`models_config.py`) on purpose, same split ADR-0042 already
    documents for the rest of this registry (billing-kind logic never bleeding into
    provider identity; here, "which providers get tri-state" never bleeding into "what a
    given TOML shape means").
    """
    key = _CATALOG_KEYS.get(provider)
    if key is None or key not in config.get("catalog", {}):
        return ("auto", None)
    models = config["catalog"][key]
    if not isinstance(models, (list, tuple)):
        return ("auto", None)  # defensive only -- load_config already dies on this shape
    cleaned = {item for item in models if isinstance(item, str) and item}
    if not cleaned:
        return ("veto", set())
    return ("curated", cleaned)


def _clean_lines(text: str) -> list[str]:
    return [line.strip() for line in _ANSI.sub("", text).splitlines() if line.strip()]


def _parse_codex_login(stdout: str, stderr: str = "") -> bool:
    """`codex login status` prints a plain-text state line (observed on stderr), never JSON."""
    lines = _clean_lines(stdout) or _clean_lines(stderr)
    return bool(lines) and lines[0].startswith("Logged in")


def _parse_claude_auth(stdout: str) -> bool:
    """`claude auth status --json` is a JSON object; only loggedIn is read and the raw doc is discarded."""
    doc = json.loads(stdout)
    return isinstance(doc, dict) and doc.get("loggedIn") is True


def _parse_opencode_auth(stdout: str) -> set[str]:
    """`opencode auth list --pure` prints decorated credential rows, one provider name per
    bullet. ADR-0034 (AC-07): only `●`/`*` mark a REAL, usable credential; `○` is opencode's
    own "pending/incomplete" marker (e.g. an invitation not yet accepted, a session that
    needs re-auth) and must never count as authenticated -- treating it as live would widen
    the audited set past what is actually usable, the opposite of fail-closed. Live-measured
    2026-08-10 (opencode 1.18.14): every row on this machine is `●`, so this fix has no
    observable effect on today's real inventory -- it closes the defect regardless."""
    providers = set()
    for line in _clean_lines(stdout):
        if line.startswith("Error"):
            raise RoutingError("PROVIDER_UNAUTHENTICATED")
        if line.startswith(("●", "*")):
            body = line.lstrip("●* ").strip()
            if body:
                # The trailing word is the credential method (api/oauth); the rest is the provider name.
                name = body.rsplit(None, 1)[0] if len(body.split()) > 1 else body
                providers.add(name.strip().lower())
    return providers


def _parse_opencode_models(stdout: str, provider_key: str) -> set[str]:
    """`opencode models <provider> --pure` prints `<provider>/<model>` lines; errors exit 0, so text is authoritative."""
    models = set()
    for line in _clean_lines(stdout):
        if line.startswith("Error"):
            raise RoutingError("PROVIDER_UNAUTHENTICATED")
        prefix = provider_key + "/"
        if not line.startswith(prefix):
            raise RoutingError("PROVIDER_UNAUTHENTICATED")
        model = line[len(prefix):].strip()
        if model:
            models.add(model)
    return models


def _parse_pi_models(stdout: str, provider: str) -> set[str]:
    """`pi --list-models` prints a `provider  model  ...` column table (header row first,
    columns whitespace-separated); only rows whose first column matches `provider` are
    read. openai-codex ids are catalog-IDENTITY (returned verbatim, spike-verified);
    anthropic raw ids are translated through PI_MODEL_MAP so callers intersect against the
    SAME short-name vocabulary every other pair uses — a raw Pi id never leaks through
    untranslated. An unrecognized header shape fails closed (PROVIDER_UNAUTHENTICATED),
    same discipline as the opencode parsers above."""
    lines = _clean_lines(stdout)
    if not lines or lines[0].split()[:2] != ["provider", "model"]:
        raise RoutingError("PROVIDER_UNAUTHENTICATED")
    raw = {parts[1] for line in lines[1:] if len(parts := line.split()) >= 2 and parts[0] == provider}
    if provider == "openai-codex":
        return raw
    return {short for short, canonical in PI_MODEL_MAP.get(provider, {}).items() if canonical in raw}


def pi_auth_provider_keys() -> frozenset[str]:
    """Read-only key-SET of `~/.pi/agent/auth.json` (spike Q2): provider NAMES only, never
    token values, never logged. Any surprise (missing file, symlink, foreign-owned file,
    foreign shape, bad JSON) is an empty set, fail-closed — this never raises and the
    caller never sees a credential value, only whether a provider name is present as a
    key. P3-SEC-002 repair (022 PKG-3): the uid check was missing here even though
    `_read_credential_json` (below) has always had it -- a file owned by another uid on
    the same box could be read and its keys folded into a routing decision (the real
    gate at `_probe_pairs`, `provider not in pi_auth_provider_keys()`) as if it were this
    user's own credential state. Same discipline as `_read_credential_json` now: `lstat`,
    never a symlink, a regular file, owned by THIS uid.

    P3-F03 repair (022 PKG-3 repair round 2): a top-level key is kept ONLY when it is
    both (a) a provider `_PAIR_COMMANDS` actually audits for the `pi` runtime
    (`openai-codex`/`anthropic` today -- exactly the two providers the sole call site,
    `_probe_pairs`'s `provider not in pi_auth_provider_keys()` gate at catalog.py:803,
    can ever ask about) and (b) mapped to a JSON OBJECT, never any other value shape.
    Before this fix the docstring above already promised "provider NAMES only" but the
    implementation kept every top-level string key verbatim -- an unaudited key
    (`{"proveedor-inventado": {...}}`) or an audited key holding a non-object value
    (`{"openai-codex": []}`) both survived into the returned set, silently widening the
    routing gate past what this file actually audits. Filtering to the SAME set
    `resolve_discovered_providers` already treats as the pi-runtime audited universe
    means a legitimate `{"openai-codex": {...}, "anthropic": {...}}` file is completely
    unaffected -- see test_pi_auth_provider_keys_rejects_unaudited_and_non_object_entries."""
    path = Path.home() / ".pi/agent/auth.json"
    try:
        st = path.lstat()
        if _stat.S_ISLNK(st.st_mode) or not _stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid():
            return frozenset()
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return frozenset()
    if not isinstance(doc, dict):
        return frozenset()
    audited = {provider for runtime, provider in _PAIR_COMMANDS if runtime == "pi"}
    return frozenset(key for key, value in doc.items()
                      if isinstance(key, str) and key in audited and isinstance(value, dict))


def _binary_signature(name: str) -> str:
    """ADR-0034 (AC-08), generalized by ADR-0043 (022 PKG-3, AC-07): path + mtime of
    `name`'s resolved binary on PATH right now -- swapping the binary (upgrade,
    reinstall, a different shim) invalidates every existing cache entry without a
    manual version bump. Originally scoped to `opencode` alone; AC-07 extends the same
    argument to `codex` and `claude` too -- any of the three CLI binaries can change how
    it reads/writes its OWN credential store on a swap, so each binary's signature is
    folded into `_cache_key` alongside its runtime's credential-file signature (below).
    No subprocess here, just a PATH lookup and a stat -- safe to call from a pure
    hashing function. Unresolvable is a fixed per-name sentinel that simply never
    equals a real signature, so the cache is skipped (fail-closed), never fabricated as
    a match."""
    path = shutil.which(name)
    if not path:
        return f"{name}:absent"
    try:
        mtime_ns = os.stat(path).st_mtime_ns
    except OSError:
        return f"{name}:absent"
    return f"{name}:{path}:{mtime_ns}"


# ------------------------------------------------------------------ ADR-0043 (022 PKG-3)
# Per-runtime credential signatures, AC-07: closes "de-auth invisible for up to
# PROBE_CACHE_TTL (300s) in 3 of 4 runtimes" -- `_cache_key` used to fold in ONLY
# opencode's live subprocess-based auth signature (`_live_opencode_auth_signature`
# above). Every signature below is `stat`/local-read only -- ZERO new subprocesses
# (the one subprocess this whole cache-key computation ever pays stays
# `_live_opencode_auth_signature`, called by the CALLER and passed in, never invoked
# from here -- see `test_adr0043_ac07_cache_key_never_spawns_a_subprocess_for_the_new_
# signatures` in tests/test_routing.py and evidence/P3-implementer.md's proof). Same
# security discipline as `pi_auth_provider_keys` throughout (AC-09): `lstat` (never a
# symlink), a regular file, this uid, ONLY named fields ever read -- never a whole-file
# hash or mtime, because `~/.claude/.credentials.json` also holds an unrelated
# `mcpOAuth` block (today a Vercel token, live-measured) that rotates on ITS OWN MCP
# refresh cycle with zero relation to the Claude Code provider credential; hashing the
# file or its mtime would rotate this signature on every MCP token refresh, defeating
# the cache for a reason that has nothing to do with what this signature exists to
# track. Every value is hashed before being folded into `_cache_key` -- never logged,
# never placed in an envelope, never a raw credential value.


def _read_credential_json(path: Path) -> dict | None:
    """Shared fail-closed read for a local per-runtime credential file: `lstat` (never
    a symlink), a regular file, owned by this uid, valid JSON, a dict -- ANY surprise is
    `None`, never raised, same discipline as `pi_auth_provider_keys` above. The caller
    reads only specific NAMED fields from the result; this function itself never
    inspects field values, so widening what a signature reads is always a one-line,
    auditable change at the call site, never here."""
    try:
        st = path.lstat()
        if _stat.S_ISLNK(st.st_mode) or not _stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid():
            return None
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


def _codex_auth_signature() -> str:
    """AC-07/AC-09: codex's per-runtime signature -- `~/.codex/auth.json`, ONLY
    `tokens.account_id` (real account identity; codex is the one runtime of the three
    whose credential file carries one, ADR-0043) and whether `OPENAI_API_KEY` is
    present (a boolean, never the key's own value). NEVER `tokens.access_token`/
    `tokens.refresh_token`/`tokens.id_token`/`last_refresh` -- token material and its
    timestamp, which rotate on every refresh (AC-08 property 1: a signature built from
    a rotating field would miss the cache on every routine OAuth renewal). File absent,
    foreign-owned, a symlink, or unreadable -- fail-closed to the empty string, which
    never equals a real signature, so the cache is simply skipped (a fresh probe runs),
    never fabricated as a match (AC-08 property 2: this is what makes a real logout/
    delete visible immediately).

    P3-SEC-001 repair (022 PKG-3, AC-09): a VALID JSON object that is missing `tokens`
    or whose `tokens.account_id` isn't a string (corrupt file, foreign shape, a `{}`
    written mid-write) must fail closed too, exactly like a missing/foreign-owned/
    unreadable file already does via `_read_credential_json` -- shape and type of every
    field this signature actually reads are validated BEFORE hashing, never after. Before
    this fix, a missing/mistyped `tokens.account_id` silently defaulted to `""` and STILL
    got folded into a hash (`account_id=|api_key_present=...`), producing a fixed
    non-empty signature instead of the required empty one -- fail-open, because that
    non-empty value looked exactly like a real (if account-id-less) signature to
    `_cache_key`, so a corrupt-shaped file could still warm/serve a cache entry."""
    doc = _read_credential_json(Path.home() / ".codex/auth.json")
    if doc is None:
        return ""
    tokens = doc.get("tokens")
    if not isinstance(tokens, dict):
        return ""
    account_id = tokens.get("account_id")
    if not isinstance(account_id, str):
        return ""
    has_api_key = isinstance(doc.get("OPENAI_API_KEY"), str)
    material = f"account_id={account_id}|api_key_present={has_api_key}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _claude_code_auth_signature() -> str:
    """AC-07/AC-09: claude-code's per-runtime signature -- `~/.claude/.credentials.json`,
    ONLY the three `claudeAiOauth` fields measured NON-rotating across a refresh
    (`scopes`, `subscriptionType`, `rateLimitTier` -- attributes of the OAuth grant/plan
    itself, not of the token instance; evidence/P3-implementer.md). NEVER
    `accessToken`/`refreshToken`/`expiresAt`/`refreshTokenExpiresAt` (token material,
    AC-09: "hashear el refreshToken no se hace"), and NEVER the file's OTHER top-level
    key `mcpOAuth` (the trap this module's own section docstring names).
    ADR-0043's declared limit: `claudeAiOauth` carries NO account-identity field (unlike
    codex's `tokens.account_id`) -- this signature therefore detects PRESENCE/ABSENCE
    (logout, deletion, file absent) but never a same-plan account swap without an
    intervening logout. Closing that gap would mean hashing `refreshToken`, which this
    package explicitly does not do.

    P3-SEC-001 repair (022 PKG-3, AC-09): `claudeAiOauth` being present as a dict is not
    enough -- shape and type of the three fields this signature actually reads are
    validated BEFORE hashing (`scopes` a list, `subscriptionType`/`rateLimitTier` a
    string each); any absence or wrong type fails closed to the empty string. Before this
    fix, `{"claudeAiOauth": {}}` (or any object missing one of the three fields) still
    produced a fixed non-empty hash of the literal string `"None"` in place of each
    missing field, indistinguishable from a real signature to `_cache_key` -- fail-open
    on a corrupt/foreign-shaped file."""
    doc = _read_credential_json(Path.home() / ".claude/.credentials.json")
    if doc is None:
        return ""
    oauth = doc.get("claudeAiOauth")
    if not isinstance(oauth, dict):
        return ""
    scopes, subscription_type, rate_limit_tier = (oauth.get(f) for f in
                                                   ("scopes", "subscriptionType", "rateLimitTier"))
    if not isinstance(scopes, list) or not isinstance(subscription_type, str) \
            or not isinstance(rate_limit_tier, str):
        return ""
    parts = [str(scopes), subscription_type, rate_limit_tier]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _pi_auth_signature() -> str:
    """AC-07: pi's per-runtime signature folds `pi_auth_provider_keys()` (already
    stat/local-read only, zero subprocess, spike Q2 discipline -- untouched by this
    package beyond the uid check, P3-SEC-002) with `PI_PINNED_VERSION` (the EXACT pi
    release the probe invokes, above) -- a version bump is itself credential-relevant: a
    different pinned pi release could read/write a differently-shaped auth.json. Provider
    NAMES only (never a token value), hashed before folding into `_cache_key`.

    P3-SEC-002 repair (022 PKG-3, AC-09): an EMPTY key-set (file absent, symlink,
    foreign-owned, corrupt/foreign-shaped JSON -- anything `pi_auth_provider_keys()`
    itself already fails closed on) must fail closed HERE too, to the empty string, same
    as `_codex_auth_signature`/`_claude_code_auth_signature` above. Before this fix, an
    empty key-set was folded into a hash alongside `PI_PINNED_VERSION` regardless,
    producing a fixed non-empty signature for "pi has no credentials" -- fail-OPEN,
    because a non-empty signature is indistinguishable, at the `_cache_key` level, from a
    real credential state. This is safe to change: `_pi_auth_signature`'s only consumer
    is `_cache_key` (cache freshness), never the real per-pair authentication gate
    (`_probe_pairs` calls `pi_auth_provider_keys()` directly, catalog.py:753) -- an empty
    signature can only ever cost a cache miss (a fresh, correctly-gated probe runs next),
    never fabricate or suppress which pairs are actually authenticated."""
    keys = pi_auth_provider_keys()
    if not keys:
        return ""
    names = ",".join(sorted(keys))
    return hashlib.sha256(f"{names}|{PI_PINNED_VERSION}".encode("utf-8")).hexdigest()


def _live_opencode_auth_signature(timeout: float) -> str:
    """ADR-0034 (AC-08): a cheap, ALWAYS-fresh (never itself cached) read of `opencode
    auth list --pure` -- credential NAMES only, never a model listing, never persisted
    to disk on its own -- folded into the cache key so the authenticated-provider set is
    genuinely re-checked on every composition that consults the cache, instead of trusted
    from whatever it was when the cache was last written. Any surprise (missing binary,
    timeout, non-zero exit, parse failure) is the empty signature, fail-closed: an
    unreadable auth state simply differs from a real one, so the cache is missed and a
    full fresh probe runs -- it can never fabricate a match."""
    probe_env = dict(os.environ, CI="1", NO_COLOR="1", TERM="dumb")
    try:
        completed = subprocess.run(("opencode", "auth", "list", "--pure"), stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   timeout=timeout, check=False, env=probe_env)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if completed.returncode != 0:
        return ""
    try:
        return ",".join(sorted(_parse_opencode_auth(completed.stdout)))
    except RoutingError:
        return ""


def _cache_key(config: dict, auth_signature: str = "") -> str:
    """ADR-0006 base key (uid + canonical catalog/routing config), the cache schema
    version, always; extended by ADR-0034 AC-08 with the resolved `opencode` binary's
    path+mtime, and by ADR-0043 (022 PKG-3, AC-07) with EVERY runtime's own
    stat/local-read-only credential signature (`_codex_auth_signature`,
    `_claude_code_auth_signature`, `_pi_auth_signature`) plus the `codex`/`claude`
    binary signatures (`_binary_signature`, generalized from the opencode-only one) --
    none of these six calls does any I/O beyond a stat/local read, so this function
    stays pure/no-subprocess for every existing direct caller (proven by
    `test_adr0043_ac07_cache_key_never_spawns_a_subprocess_for_the_new_signatures`,
    tests/test_routing.py). `auth_signature` -- the caller-supplied, freshly-read,
    normalized opencode-authenticated-provider set, the ONE genuinely subprocess-backed
    signal in this whole key -- is folded in only when the caller actually has one.
    `probe_inventory` is the only production caller that supplies a non-empty
    `auth_signature` (see `_live_opencode_auth_signature` above); every pre-existing
    direct caller (including tests) keeps calling this with the same two-argument shape
    it always had and is unaffected. The ENTIRE key changes when ANY one runtime's
    credential state changes -- the probe-cache document covers every runtime's pairs
    at once, so a credential change in one runtime correctly forces a fresh probe of
    ALL pairs on the next decision, never a partial/stale mix."""
    canon = json.dumps({"catalog": config.get("catalog", {}), "routing": config.get("routing", {})},
                       sort_keys=True, default=str)
    parts = "\n".join((str(os.getuid()), canon, str(_CACHE_SCHEMA_VERSION),
                       _binary_signature("opencode"), _binary_signature("codex"), _binary_signature("claude"),
                       _codex_auth_signature(), _claude_code_auth_signature(), _pi_auth_signature(),
                       auth_signature))
    return hashlib.sha256(parts.encode("utf-8")).hexdigest()


def _validate_cache_dir(root: Path) -> bool:
    """Same private-directory discipline as the store: no symlink, this uid's 0700 dir.

    Never creates or chmods anything; an unvalidated root just means the cache
    is skipped (read AND write) and every pair is probed fresh (SEC-A03/F06).
    """
    try:
        st = root.lstat()
    except OSError:
        return False
    return (_stat.S_ISDIR(st.st_mode) and not _stat.S_ISLNK(st.st_mode)
            and st.st_uid == os.getuid() and _stat.S_IMODE(st.st_mode) == 0o700)


def _read_probe_cache(cache_root, key: str, now: float, config: dict):
    """Valid cache or None; anything unexpected is ignored fail-closed (fresh probes run).

    Only PAIRS PRESENT are ever positive (F06: negatives are never persisted,
    so a transient failure costs one retry, never the full TTL). Every entry
    is re-checked against the live `resolve_ceiling` state on read (F09), so a
    stale-but-key-matching cache can never widen the audited set. ADR-0042 (022 PKG-2):
    the three tri-states matter here as much as at `_probe_pairs` -- a "veto" provider
    is dropped outright (never served from cache, however it got written); a "curated"
    provider is re-intersected exactly like before; an "auto" provider has NO ceiling to
    intersect against, so the cached models are kept as-is. Naively re-intersecting
    against `set()` in "auto" mode (the pre-tri-state behavior applied blindly) would
    leave every auto-mode pair's cached entry EMPTY on every read, defeating the cache
    entirely -- the caller would re-probe on every single decision (up to
    `PI_PROBE_MIN_TIMEOUT_SECONDS` for pi). See `test_read_probe_cache_auto_mode_is_not_
    always_empty` in tests/test_routing.py, which exists specifically to catch that
    regression.
    """
    root = Path(cache_root)
    if not _validate_cache_dir(root):
        return None
    try:
        path = root / "probe-cache.json"
        st = path.lstat()
        if _stat.S_ISLNK(st.st_mode) or not _stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or _stat.S_IMODE(st.st_mode) != 0o600:
            return None
        doc = json.loads(path.read_text(encoding="utf-8"))
        if (not isinstance(doc, dict) or doc.get("key") != key
                or not isinstance(doc.get("at"), (int, float)) or isinstance(doc.get("at"), bool)
                or doc["at"] > now or now - doc["at"] > PROBE_CACHE_TTL
                or not isinstance(doc.get("pairs"), dict)):
            return None
        out: dict[tuple[str, str], set[str]] = {}
        for name, models in doc["pairs"].items():
            runtime, _, provider = str(name).partition("|")
            if (runtime, provider) not in _PAIR_COMMANDS or not isinstance(models, list) or not all(isinstance(m, str) for m in models):
                return None
            state, ceiling = resolve_ceiling(config, provider)
            if state == "veto":
                continue  # never served from cache, no matter what is on disk (AC-05 layer 2)
            # "auto": no ceiling exists to re-intersect against -- keeping `set()` here
            # (the naive port of the pre-tri-state one-liner) would empty every auto-mode
            # entry on every single read, defeating the cache (see docstring above).
            kept = set(models) if state == "auto" else (set(models) & ceiling)
            if kept:  # empty after filtering ⇒ treated as absent, retried like any negative
                out[(runtime, provider)] = kept
        return out
    except (OSError, ValueError):
        return None


def _write_probe_cache(cache_root, key: str, result: dict, now: float) -> None:
    """Atomic 0600 tmp+rename under the managed root; content is redacted pair->models only."""
    root = Path(cache_root)
    if not _validate_cache_dir(root):
        return  # the store owns root creation; never create or chmod it from here
    tmp = root / f".probe-cache.{os.getpid()}.tmp"
    doc = {"key": key, "at": now,
           "pairs": {f"{runtime}|{provider}": sorted(models) for (runtime, provider), models in result.items()}}
    old = os.umask(0o077)
    try:
        tmp.write_text(json.dumps(doc, sort_keys=True), encoding="utf-8")
        os.chmod(tmp, 0o600)
        os.replace(tmp, root / "probe-cache.json")
    except OSError:
        try: tmp.unlink()
        except OSError: pass
    finally:
        os.umask(old)


def prune_legacy_probe_cache(legacy_root) -> bool:
    """AC-10 (022 PKG-3): a single probe cache lives at the store's cache root now
    (`RoutingStore.ensure_cache_root()`, `~/.local/state/set-agentes/routing-v2`) --
    this removes the STALE SIBLING file at the old, divergent location
    (`STATE_DIR/probe-cache.json`, what `--route-doctor`/`--doctor-all`/the 'Estado
    general' panel used to read while the decision path already read/wrote the
    routing-v2 one -- two caches confirmed diverging live, ADR-0043).

    Same security discipline as `_write_probe_cache`, mirrored exactly: the directory
    must pass `_validate_cache_dir` (0700, this uid, no symlink) and the file itself
    must independently be a regular, this-uid file (never following a symlink) before
    it is ever unlinked -- any surprise leaves it untouched (fail-closed: an
    unrecognized foreign object is never deleted). `STATE_DIR` also holds
    `config.toml`/`model-preference.toml` and other real state -- this function NEVER
    touches the directory itself or any other file in it, only this one legacy
    `probe-cache.json`. Returns True only when a file was actually removed (for the
    caller's own best-effort bookkeeping); False for "nothing to prune" and every
    fail-closed branch alike -- the caller never needs to distinguish them, pruning is
    always best-effort."""
    root = Path(legacy_root)
    if not _validate_cache_dir(root):
        return False
    path = root / "probe-cache.json"
    try:
        st = path.lstat()
    except OSError:
        return False
    if _stat.S_ISLNK(st.st_mode) or not _stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid():
        return False
    try:
        path.unlink()
    except OSError:
        return False
    return True


def _run_cached(ran, argv, timeout, env):
    """Subprocess run for `argv`, memoized in the caller's `ran` dict (shared across pairs
    in one probe call, e.g. the single `opencode auth list --pure` all opencode pairs
    reuse). Returns the CompletedProcess, or None on any OSError/timeout — never raises."""
    if argv not in ran:
        try:
            ran[argv] = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True, timeout=timeout, check=False, env=env)
        except (OSError, subprocess.TimeoutExpired):
            ran[argv] = None
    return ran[argv]


def _probe_pairs(config: dict, pairs, timeout: float, ran=None,
                 listed_out: dict[tuple[str, str], set[str]] | None = None) -> dict[tuple[str, str], set[str]]:
    """Fresh, uncached, pair-scoped subprocess observation for exactly `pairs`.

    Any surprise — missing binary, timeout, nonzero exit, unexpected shape,
    error text — makes only that pair unavailable (never raises). A pair
    without any resulting model is simply absent from the returned dict:
    negative results are never a first-class cached value (F06).

    AC-19 (022 PKG-5): `listed_out`, when a caller passes a dict, is populated as a SIDE
    CHANNEL with the RAW opencode-lane listing (`parsed`, pre-ceiling) for every opencode
    pair this call reaches, regardless of whether the ceiling then empties `models` for
    the function's own (unchanged) return value -- the split this AC exists to expose:
    `listed_out[pair]` is "what the provider says it has", the return value stays "what
    survives the curated ceiling and is therefore actually routable". `None` (the
    default) costs nothing extra and changes no existing caller's behavior at all.
    """
    result: dict[tuple[str, str], set[str]] = {}
    # Identical argvs across pairs (e.g. `opencode auth list` for both opencode pairs) run once.
    ran = {} if ran is None else ran
    # Non-interactive probe environment: opencode's TUI writer blocks forever on a
    # non-TTY stdout unless CI/TERM signal a dumb terminal (observed 2026-07-26).
    probe_env = dict(os.environ, CI="1", NO_COLOR="1", TERM="dumb")
    for pair in pairs:
        runtime, provider = pair
        commands = _PAIR_COMMANDS[pair]
        # ADR-0042 (022 PKG-2, AC-04): "veto" is dropped before any subprocess runs at
        # all -- same early-exit position the pre-tri-state `if not allowed: continue`
        # had, so a curated-empty provider still costs nothing to probe. "auto" (no
        # `[catalog]` key for this provider) used to fall into that SAME branch (an empty
        # `set()` is falsy too) and get skipped just the same -- exactly the defect this
        # package removes: `allowed` being `None` below is deliberately NOT treated as
        # falsy-skip; only genuine credential/parse failure further down drops the pair.
        state, allowed = resolve_ceiling(config, provider)
        if state == "veto":
            continue
        # PKG-N02: only the pi pairs get the cold-pnpm floor; every other pair keeps the
        # caller's own timeout unchanged.
        pair_timeout = max(timeout, PI_PROBE_MIN_TIMEOUT_SECONDS) if runtime == "pi" else timeout
        if runtime == "opencode":
            # 012 AC-02: the credential-set check (map 1) and the models-listing CLI
            # id/prefix (map 2) are two independently addressable lookups, never one.
            # Repair F-06 (012 repair, medium, +69%/+10.5s measured without this fix):
            # map 1's membership check runs BEFORE the second, more expensive `opencode
            # models <id>` call, not after both commands already ran — a machine missing
            # a given OpenCode-lane subscription now never pays that pair's models-call
            # latency at all, instead of always paying it only to discard the result.
            auth_result = _run_cached(ran, commands[0], pair_timeout, probe_env)
            if auth_result is None or auth_result.returncode != 0:
                continue
            try:
                provider_key = _OPENCODE_PROVIDER_KEYS[provider]
                credentials = _parse_opencode_auth(auth_result.stdout)
            except (RoutingError, ValueError, KeyError, IndexError, TypeError):
                continue
            if provider_key not in credentials:
                continue
            models_result = _run_cached(ran, commands[1], pair_timeout, probe_env)
            if models_result is None or models_result.returncode != 0:
                continue
            try:
                cli_id = _OPENCODE_CLI_IDS[provider]
                parsed = _parse_opencode_models(models_result.stdout, cli_id)
            except (RoutingError, ValueError, KeyError, IndexError, TypeError):
                continue
            if listed_out is not None:
                listed_out[pair] = set(parsed)
            # AC-05 layer 3 is unaffected by "auto": billing_rank's fail-closed-to-
            # expensive default already applies to any provider PROVIDER_BILLING_KIND
            # does not classify as "subscription" -- ceiling state never enters that map.
            models = parsed if state == "auto" else (allowed & parsed)
        else:
            completed, failed = [], False
            for argv in commands:
                completed_item = _run_cached(ran, argv, pair_timeout, probe_env)
                if completed_item is None:
                    failed = True; break
                completed.append(completed_item)
            if failed or any(item.returncode != 0 for item in completed):
                continue
            try:
                if runtime == "codex":
                    # ADR-0042 AC-04: codex/claude-code never see state == "auto" here --
                    # `models_config.load_config` dies if [catalog].codex/.claude are
                    # absent or empty, so `allowed` is always the curated set by the time
                    # a validated config reaches this function (see resolve_ceiling's
                    # own docstring). Neither runtime has a models-LISTING command to
                    # fall back on if it ever were "auto" (only a login-status boolean).
                    models = allowed if _parse_codex_login(completed[0].stdout, completed[0].stderr) else set()
                elif runtime == "claude-code":
                    models = allowed if _parse_claude_auth(completed[0].stdout) else set()
                else:  # pi
                    # Belt-and-suspenders (T-305, spike Q2): the auth.json key-set is a cheap,
                    # non-subprocess signal alongside the naturally fail-closed column-parse
                    # below (an unauthenticated provider simply has no rows in --list-models).
                    if provider not in pi_auth_provider_keys():
                        continue
                    # Same guarantee as codex/claude-code above: pi's two pairs are both
                    # openai-codex/anthropic, always curated by validation.
                    models = allowed & _parse_pi_models(completed[0].stdout, provider)
            except (RoutingError, ValueError, KeyError, IndexError, TypeError):
                continue
        if models:
            result[pair] = models
    return result


def probe_inventory(config: dict, timeout: float = 20.0, cache_root=None, fresh: bool = False,
                    pairs=None, now=None, cache_write: bool = True,
                    listed_out: dict[tuple[str, str], set[str]] | None = None) -> dict[tuple[str, str], set[str]]:
    """Fresh exact pair-scoped observation with per-pair parsers.

    Any surprise — missing binary, timeout, nonzero exit, unexpected shape,
    error text — makes only that pair unavailable. Model names are always the
    intersection with the canonical models.toml catalog for the provider, so a
    runtime can never widen the audited model set. Raw provider output
    (including account identifiers) is parsed and discarded, never returned.

    `pairs` restricts probing to those exact pairs, always fresh and never
    cached (the AM-2 fresh-selected path). Otherwise, with `cache_root`, a
    valid unexpired cache (ADR-0006 key) filters candidates; pairs ABSENT
    from that cache (never-seen or previously negative, F06) are always
    re-probed fresh regardless of TTL, so a transient failure only ever
    costs one retry, never the whole cache window. `cache_write=False`
    (SEC-A03: the simulate/explain lane) reads a warm cache but never
    persists one, preserving explain's no-mutation contract.

    ADR-0034 (AC-08): whenever a cache is even consulted, the authenticated-opencode-
    provider set is re-read fresh (`_live_opencode_auth_signature`, one cheap credential-
    only call, never itself cached) and folded into the lookup/write key -- a credential
    change is caught immediately, never only after the TTL window; the cache on disk
    still holds model LISTINGS only, never the raw signature.

    AC-19 (022 PKG-5): `listed_out` (see `_probe_pairs`) is forwarded ONLY on the
    `pairs=` explicit path, the one branch that is ALWAYS fresh/uncached regardless of
    `cache_root` -- the cached path's persisted document never carried a pre-ceiling
    listing (`_write_probe_cache`'s doc is `{"key","at","pairs"}`, ceiling-applied only),
    so there is nothing honest to report there; a caller wanting `listed_out` from the
    cached path would silently get a value that is sometimes fresh and sometimes not,
    which is exactly the kind of unmarked guess ADR-0026 forbids. Every caller that needs
    a reliable `listed_out` uses the explicit-`pairs=` path, same discipline `route_doctor`
    already established for its own (always-fresh) opencode-lane listing.
    """
    now = time.time() if now is None else now
    if pairs is not None:
        selected = [pair for pair in pairs if pair in _PAIR_COMMANDS]
        return _probe_pairs(config, selected, timeout, listed_out=listed_out)
    all_pairs = list(_PAIR_COMMANDS)
    use_cache = cache_root is not None and _validate_cache_dir(Path(cache_root))
    auth_signature = _live_opencode_auth_signature(timeout) if use_cache else ""
    key = _cache_key(config, auth_signature) if use_cache else None
    cached = _read_probe_cache(cache_root, key, now, config) if (use_cache and not fresh) else None
    if cached is not None:
        missing = [pair for pair in all_pairs if pair not in cached]
        if not missing:
            return cached
        merged = dict(cached)
        merged.update(_probe_pairs(config, missing, timeout))
    else:
        merged = _probe_pairs(config, all_pairs, timeout)
    if use_cache and cache_write:
        _write_probe_cache(cache_root, key, merged, now)
    return merged


def _check_family_collisions(rows) -> None:
    """012 AC-07: `family` stays fully curated, never vendor-captured — but for any model
    id curated under more than one provider, every curated row for that id must share the
    identical (curator-normalized) `family` value, so REVIEW_FAMILY_CONFLICT/
    REVIEW_PROVIDER_CONFLICT (service.py) can never be satisfied independently by the same
    underlying model reviewing itself under two different provider names (measured live:
    `minimax-m2.7` reports two DIFFERENT vendor `family` strings under `opencode` vs
    `opencode-go` — a literal vendor copy would fabricate false reviewer independence for
    that id; see docs/specs/012-discovered-inventory/spec.md AC-07).

    Repair SEC-001 (panel RP-01, critical): the row key is `canonical_model(provider,
    model)`, never the raw `model` string. A raw-string key only ever catches the SAME id
    curated under two providers; it is blind to the SAME underlying model curated under
    two DIFFERENT ids (e.g. `anthropic`/`opus` and `opencode-zen`/`claude-opus-4-8`,
    proven identical in-repo by PI_MODEL_MAP) — exactly the gap the panel's PoC exploited.
    `row.get("provider")` falls back to the model id itself when a row carries no
    `provider` key (kept for the pre-existing pure-function unit tests that call this
    directly with `{"model": ..., "family": ...}` fixtures only), so canonicalization is
    strictly additive and never changes behavior for a provider-less caller.

    Pure function over any row sequence exposing `model`/`family` (plain dicts, including
    synthetic fixtures, or the same row shape build_snapshot already validates) — needs no
    probe, no `--verbose`, and no curated routes.v1.toml rows for the new providers to be
    unit-tested today. Raises RoutingError("CATALOG_FAMILY_COLLISION") on the first
    collision found (repair F-12: differentiated from the generic "CATALOG_INVALID" every
    other build_snapshot failure raises, same style already used to tell CATALOG_COLLISION
    apart from CATALOG_INVALID below) — never silently accepts one.
    """
    seen: dict[str, str] = {}
    for row in rows:
        model, family = row["model"], row["family"]
        key = canonical_model(row["provider"], model) if row.get("provider") is not None else model
        if key in seen and seen[key] != family:
            raise RoutingError("CATALOG_FAMILY_COLLISION")
        seen[key] = family


def build_snapshot(catalog_path: Path, roster: list[dict], config: dict, digest=None) -> CatalogSnapshot:
    from .domain import TIER_ORDER
    try:
        source = tomllib.loads(catalog_path.read_text(encoding="utf-8"))
        if set(source) != {"catalog_version", "routes"} or source["catalog_version"] != 2 or not isinstance(source["routes"], list): raise ValueError
        rows = source["routes"]
        enabled = set(config["routing"]["enabled_providers"])
        codex_efforts = set(config["catalog"].get("codex_effort", ()))
        xhigh_ok = bool(config.get("routing", {}).get("xhigh_benchmarked", False))
    except (OSError, tomllib.TOMLDecodeError, KeyError, TypeError, ValueError) as exc: raise RoutingError("CATALOG_INVALID") from exc
    roster_names = {row["role"] for row in roster}; routes=[]; canonical_seen=set(); ids={}; route_runtimes={}
    # 012 AC-04, site 3 of 5 (corrected 012 repair F-04 — see resolve_ceiling's own
    # comment above for the full five-site enumeration; moves in lockstep with
    # models.toml's [catalog] table and _CATALOG_KEYS at minimum):
    # opencode-zen/opencode-go are listed here too, even though no routes.v1.toml row
    # references them yet — this contract's non-goals paragraph states "no curated
    # routes.v1.toml rows for the new models" (docs/specs/012-discovered-inventory/
    # spec.md, "Non-goals of P2"; corrected 012 repair F-07 — this is NOT AC-11, which is
    # the cache/decision-trail AC and says nothing about routes.v1.toml rows) — an absent
    # provider's allowlist would otherwise be silently unreachable the moment a row for it
    # is curated later. ADR-0042 (022 PKG-2): derived from `PROVIDERS` (the registry)
    # instead of a hardcoded four-provider literal tuple, so a future provider added to
    # the registry alone is already covered here without a second edit to this file.
    configured_models = {provider: resolve_ceiling(config, provider) for provider in PROVIDERS}
    # Closed row schema: required keys plus the allowlisted-optional `runtimes` (contract 004 AC-12:
    # never part of the canonical static-ID tuple; rows differing only in runtimes stay duplicates).
    required_keys = {"provider", "model", "family", "effort", "tier", "roles", "tools", "curated_priority"}
    optional_keys = {"runtimes"}
    audited: dict[str, set[str]] = {}
    for runtime, provider in _PAIR_COMMANDS:
        audited.setdefault(provider, set()).add(runtime)
    for row in rows:
        try:
            if not required_keys <= set(row) or set(row) - required_keys - optional_keys: raise ValueError
            provider, model, family, effort, tier = (row[key] for key in ("provider", "model", "family", "effort", "tier"))
            roles, tools = (_sorted_strings(row[key]) for key in ("roles", "tools"))
            priority = row["curated_priority"]
            # AC-06: a curated row pointing at a provider whose ceiling resolves to
            # "auto"/"veto" (never possible for openai-codex/anthropic per AC-04's
            # validated-config guarantee -- see resolve_ceiling) fails NAMED, not with the
            # generic CATALOG_INVALID every other shape mismatch below raises. Same
            # precedent as CATALOG_FAMILY_COLLISION (below): a specific, actionable code
            # for a specific, diagnosable cause. Checked for EVERY provider known to
            # `configured_models` regardless of `enabled_providers` membership -- "there
            # is no ceiling to curate against" is the more specific, more useful diagnosis
            # than "this provider is not enabled" whenever both would otherwise be true.
            ceiling = configured_models.get(provider)
            if ceiling is not None and ceiling[0] != "curated":
                raise RoutingError("CATALOG_CEILING_REQUIRED")
            allowed_models = ceiling[1] if ceiling is not None else set()
            if (provider not in enabled or model not in allowed_models
                    or not isinstance(tier, str) or tier not in TIER_ORDER
                    or not isinstance(priority, int) or priority < 0 or not set(roles) <= roster_names): raise ValueError
            if provider == "openai-codex" and (effort not in codex_efforts or (effort == "xhigh" and not xhigh_ok)): raise ValueError
            if provider == "anthropic" and effort != "medium": raise ValueError
            runtimes = None
            if "runtimes" in row:
                runtimes = _sorted_strings(row["runtimes"])
                if not set(runtimes) <= audited.get(provider, set()): raise ValueError
            rid = StaticRoute.identifier(2, provider, model, family, effort, (tier,), roles, tools, priority, digest or __import__("hashlib").sha256)
            canon=(2, provider, model, family, effort, (tier,), roles, tools, priority)
            if canon in canonical_seen: raise RoutingError("CATALOG_INVALID")
            if rid in ids and ids[rid] != canon: raise RoutingError("CATALOG_COLLISION")
            canonical_seen.add(canon); ids[rid]=canon
            route = StaticRoute(2, provider, model, family, effort, tier, roles, tools, priority, rid)
            routes.append(route); route_runtimes[rid] = set(runtimes) if runtimes else None
        except RoutingError:
            # ADR-0042 (022 PKG-2, AC-06 repair): `RoutingError` is a `ValueError`
            # subclass (routing_core/domain.py), so the broad `except (..., ValueError)`
            # below used to catch a NAMED RoutingError raised inside this very try block
            # (CATALOG_CEILING_REQUIRED above, and CATALOG_COLLISION a few lines up,
            # never exercised by any test before this fix) and silently downgrade it to
            # the generic CATALOG_INVALID -- exactly the "differentiated from the
            # generic" AC-06 asks for, defeated by the broader except that runs after it.
            # A named RoutingError always propagates as itself; only a genuine shape
            # failure (KeyError/TypeError/plain ValueError) becomes CATALOG_INVALID.
            raise
        except (KeyError, TypeError, ValueError): raise RoutingError("CATALOG_INVALID")
    # 012 AC-07: runs before any shared-id row set is accepted — trivially satisfied by
    # today's six real rows (no shared model id across openai-codex/anthropic), meaningful
    # once curated rows for the new OpenCode-lane providers share an id with them. `provider`
    # is passed (repair SEC-001) so the check normalizes through canonical_model, not just
    # the raw curated `model` string — catches the same underlying model curated under two
    # DIFFERENT ids across providers, not only the same id repeated.
    _check_family_collisions([{"provider": route.provider, "model": route.model, "family": route.family} for route in routes])
    if not routes or set().union(*(set(route.roles) for route in routes)) != roster_names: raise RoutingError("CATALOG_INVALID")
    # Runtime compatibility derives from the audited probe table, optionally narrowed per route.
    identities=frozenset((r.route_id, runtime, r.provider, r.model, r.family, r.effort)
                         for r in routes
                         for runtime in (route_runtimes[r.route_id] or audited.get(r.provider, set())))
    return CatalogSnapshot(tuple(routes), identities)


# --------------------------------------------------------------------------- ADR-0029
# 017 PKG-B1: the ADDITIVE discovered-routes path. `build_snapshot` above is the
# audited, curated snapshot and does not change (its immutable-test contract:
# "a runtime can never widen the audited model set" holds — this wrapper is a
# DIFFERENT entry point that a caller opts into via [routing].discovered_providers,
# absent by default, and the curated allowlist path never flows through it).

def resolve_discovered_providers(config: dict, inventory: dict) -> tuple[str, ...]:
    """ADR-0034 (AC-01/AC-02): the ONE function that turns `[routing].discovered_providers`
    into the concrete provider tuple `build_effective_snapshot` synthesizes routes for.
    `service.py`'s initial composition AND its `recheck` lambda (re-probed on a fresh
    inventory at authorization time) both call this SAME pure function -- deriving the
    universe two different ways would let a candidate authorized against one derivation
    fail `AUTHORIZATION_INVALID` against the other purely from derivation drift, never a
    real auth change.

    `"auto"` derives from the PROBED inventory (never a static list) intersected with the
    audited `_PAIR_COMMANDS` provider set -- copilot and any other never-audited provider
    can never appear here no matter what a probe observes (M-1). An explicit list is used
    as-is (already validated against `DISCOVERABLE_PROVIDERS` at models_config load time);
    anything else (missing key, malformed value from a caller that skipped validation) is
    the empty tuple, fail-closed.
    """
    raw = (config.get("routing") or {}).get("discovered_providers") if isinstance(config, dict) else None
    if raw == "auto":
        audited_providers = {provider for _, provider in _PAIR_COMMANDS}
        # `inventory` never stores an empty-model pair (`_probe_pairs`'s own `if models:`
        # guard), so key presence alone already means "live" -- no extra truthiness check.
        live_providers = {provider for (_, provider) in inventory}
        return tuple(sorted(live_providers & audited_providers))
    if isinstance(raw, (list, tuple)):
        return tuple(raw)
    return ()


def _unlistable_candidate_id(display: str) -> str:
    """AC-16 (022 PKG-5): the ONE candidate `route_doctor` ever tries for a
    `detected_unlistable` credential -- an EXACT, deterministic transform of the
    credential's own display name (`opencode auth list --pure`'s row text, already
    lower-cased by `_parse_opencode_auth`), space -> hyphen, nothing else. Never a table
    lookup, never a second candidate, never widened by any other rule.

    ADR-0034 already measured, live, that this exact rule is a trap if trusted on its
    own: it "would have produced the WRONG id for `opencode-go` itself -- `opencode go`
    -> `opencode-go` only works by coincidence", and `opencode-zen`'s real CLI id is
    `opencode`, not `opencode-zen` (its display text is `opencode zen`). That is exactly
    why this function's return value is a CANDIDATE, never trusted by itself --
    `_verify_unlistable_credential` (below) accepts it ONLY when the CLI's own live
    answer confirms it. Measurement, not a heuristic that guesses."""
    return display.replace(" ", "-")


def _verify_unlistable_credential(display: str, timeout: float) -> tuple[str, set[str]] | None:
    """AC-16: the empirical verification itself. One subprocess, one candidate
    (`_unlistable_candidate_id`), fail-closed to `None` on ANY surprise -- missing
    binary, timeout, nonzero exit, an `Error` line, a listing that does not start with
    the exact `<candidate>/` prefix (`_parse_opencode_models` already raises
    `RoutingError` for all of these), or a well-formed but EMPTY listing. Never a
    partial credit, never a second guess: the id is accepted only if the CLI answered
    with a well-formed `<id>/<model>` listing, exactly AC-16's own words.

    AC-17: this function's result is diagnostic memory ONLY -- `route_doctor` is the
    ONLY caller, it is NEVER wired into `_PAIR_COMMANDS`, `_probe_pairs`, or any other
    structure `resolve_discovered_providers`/`service.route()` reads, so a confirmed
    candidate here can never grant routing eligibility by itself (unchanged:
    test_adr0034_m1_github_copilot_never_gets_an_audited_pair_even_authenticated in
    tests/test_routing.py, which this function does not touch). Because `route_doctor`
    re-runs this check fresh on every single call (nothing here is cached or persisted),
    a credential that stops confirming its candidate is reported unlistable again on the
    very next call, automatically and symmetrically to how it was confirmed -- AC-17's
    "la baja es simétrica y automática" needs no separate code path."""
    candidate = _unlistable_candidate_id(display)
    probe_env = dict(os.environ, CI="1", NO_COLOR="1", TERM="dumb")
    try:
        completed = subprocess.run(("opencode", "models", candidate, "--pure"), stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   timeout=timeout, check=False, env=probe_env)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    try:
        models = _parse_opencode_models(completed.stdout, candidate)
    except RoutingError:
        return None
    return (candidate, models) if models else None


def route_doctor(config: dict, cache_root=None, timeout: float = 20.0, now=None) -> dict:
    """ADR-0035 (AC-15): read-only diagnostic snapshot for `set-agents --route-doctor`.

    Never opens a routing run, never authorizes anything, and never WRITES the probe
    cache (only inspects it, when `cache_root` is given) -- every subprocess call here
    is either a fresh auth-only read or `probe_inventory(..., pairs=...)`, which
    `probe_inventory` itself always runs fresh/uncached for an explicit `pairs` list
    (see its own docstring), so this function can never leave a mutated cache file
    behind and never races the composition path's own cache.

    Reports, for every audited OpenCode-lane pair: authenticated (fresh
    `opencode auth list --pure` read), `listed_by_provider` (AC-19: the RAW live count
    the CLI reports, pre-ceiling) and `usable_after_ceiling` (AC-19: what survives the
    curated allowlist and is therefore actually routable -- the OLD, misleadingly-named
    `models_listable`), and its billing kind. Additionally -- this is what makes M-1
    (ADR-0034) diagnosable without reading code -- any OTHER authenticated OpenCode
    credential this table does NOT map to a CLI id (today exactly `github-copilot`) is
    reported `detected_unlistable=True`, never added to any pair table; AC-16 attempts
    ONE empirical verification for it (`_verify_unlistable_credential`) and reports
    `verified_cli_id`/`listed_by_provider` from that attempt -- `usable_after_ceiling`
    stays 0 for these entries always: there is no audited pair and no curated ceiling
    for them to ever be routable against (AC-17: memory of a CLI id is never an
    authorization).
    """
    now = time.time() if now is None else now
    probe_env = dict(os.environ, CI="1", NO_COLOR="1", TERM="dumb")
    try:
        auth_result = subprocess.run(("opencode", "auth", "list", "--pure"), stdin=subprocess.DEVNULL,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                     timeout=timeout, check=False, env=probe_env)
        raw_auth = _parse_opencode_auth(auth_result.stdout) if auth_result.returncode == 0 else set()
    except (OSError, subprocess.TimeoutExpired, RoutingError):
        raw_auth = set()
    opencode_pairs = [pair for pair in _PAIR_COMMANDS if pair[0] == "opencode"]
    # Always fresh, never cached, never written -- `pairs=` bypasses the cache entirely
    # in `probe_inventory` itself (its `if pairs is not None:` branch). `listed_raw`
    # captures AC-19's pre-ceiling count as a side channel (see `_probe_pairs`).
    listed_raw: dict[tuple[str, str], set[str]] = {}
    fresh_inventory = probe_inventory(config, timeout=timeout, pairs=opencode_pairs, listed_out=listed_raw)
    providers = []
    for provider, cli_id in sorted(_OPENCODE_CLI_IDS.items()):
        display = _OPENCODE_PROVIDER_KEYS[provider]
        models = fresh_inventory.get(("opencode", provider), set())
        listed_models = listed_raw.get(("opencode", provider), set())
        providers.append({
            "provider": provider, "runtime": "opencode",
            "authenticated": display in raw_auth,
            "listed_by_provider": len(listed_models),
            "usable_after_ceiling": len(models),
            "billing": PROVIDER_BILLING_KIND.get(provider, "unknown"),
            "detected_unlistable": False,
            "verified_cli_id": cli_id,
        })
    known_display = set(_OPENCODE_PROVIDER_KEYS.values())
    for display in sorted(raw_auth - known_display):
        # M-1: authenticated but no audited CLI id maps to it -- never a pair, never
        # added to any pair table. AC-16: ONE empirical verification attempt against a
        # candidate derived only from `display`'s own name; accepted only if the CLI
        # confirms it (never a guess). `usable_after_ceiling` is always 0 here: even a
        # confirmed candidate is diagnostic memory only, never routing eligibility
        # (AC-17).
        verified = _verify_unlistable_credential(display, timeout)
        candidate, models_found = verified if verified is not None else (None, set())
        providers.append({
            "provider": display, "runtime": "opencode",
            "authenticated": True,
            "listed_by_provider": len(models_found),
            "usable_after_ceiling": 0,
            "billing": "unknown", "detected_unlistable": True,
            "verified_cli_id": candidate,
        })
    cache = {"used": False, "reason": "CACHE_ROOT_ABSENT"}
    if cache_root is not None:
        root = Path(cache_root)
        if not _validate_cache_dir(root):
            cache = {"used": False, "reason": "CACHE_DIR_INVALID"}
        else:
            auth_signature = _live_opencode_auth_signature(timeout)
            key = _cache_key(config, auth_signature)
            path = root / "probe-cache.json"
            try:
                st = path.lstat()
                if _stat.S_ISLNK(st.st_mode) or not _stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or _stat.S_IMODE(st.st_mode) != 0o600:
                    cache = {"used": False, "reason": "CACHE_FILE_UNSAFE"}
                else:
                    doc = json.loads(path.read_text(encoding="utf-8"))
                    at = doc.get("at") if isinstance(doc, dict) else None
                    key_current = isinstance(doc, dict) and doc.get("key") == key
                    age = (now - at) if isinstance(at, (int, float)) and not isinstance(at, bool) else None
                    expired = age is None or age < 0 or age > PROBE_CACHE_TTL
                    cache = {
                        "used": bool(key_current and not expired),
                        "key_current": bool(key_current),
                        "age_seconds": age,
                        "reason": "OK" if (key_current and not expired) else
                                  ("KEY_MISMATCH" if not key_current else "EXPIRED"),
                    }
            except (OSError, ValueError):
                cache = {"used": False, "reason": "CACHE_ABSENT_OR_UNREADABLE"}
    return {"providers": providers, "cache": cache}


def probe_listed_and_usable(config: dict, cache_root=None,
                            timeout: float = 20.0) -> tuple[dict[tuple[str, str], set[str]],
                                                            dict[tuple[str, str], set[str]]]:
    """AC-19: the same `listed_by_provider` / `usable_after_ceiling` split `route_doctor`
    reports, shaped for `cmd_doctor_all` and `_estado_general_lines` (`set_agents_app.py`)
    -- the two OTHER "vidriera" surfaces this AC names, which (unlike `route_doctor`) use
    `probe_inventory`'s CACHED path for performance/consistency with the real decision
    path. Returns `(listed, usable)`, two `{(runtime, provider): set[str]}` maps sharing
    `probe_inventory`'s own key-presence convention (a pair with an empty set is simply
    absent, never a zero-length entry).

    `usable` is exactly `probe_inventory(config, cache_root=cache_root)` -- unchanged
    cost and freshness characteristics, whatever the caller's `cache_root` already buys.

    `listed` starts as a copy of `usable` and is overwritten, ONLY for the OpenCode-lane
    pairs, with a small, ALWAYS-FRESH re-probe (`pairs=`, the same always-uncached branch
    `route_doctor` already relies on for its own listing) that captures the raw pre-
    ceiling count via `listed_out`. Deliberately NOT a full fresh re-probe of every
    runtime: codex/claude-code/pi only ever report a login-status boolean in
    `_PAIR_COMMANDS` (no live per-model listing distinct from their curated ceiling), so
    for those three runtimes `listed` is `usable` by construction -- and `pi` alone
    floors at `PI_PROBE_MIN_TIMEOUT_SECONDS` (60s cold), so re-probing it here on every
    menu render would make `_estado_general_lines` (the first-item-of-the-menu surface
    this AC exists to fix) newly, badly slow. `cache_root` is passed to BOTH internal
    `probe_inventory` calls -- inert on the `pairs=` one (that branch never even reads
    it), kept only so a caller mocking `probe_inventory` wholesale sees one consistent
    `cache_root` value across both calls (see
    test_adr0043_ac10_cmd_doctor_all_uses_the_single_root_and_prunes_the_legacy_file)."""
    usable = probe_inventory(config, timeout=timeout, cache_root=cache_root)
    listed = dict(usable)
    opencode_pairs = [pair for pair in _PAIR_COMMANDS if pair[0] == "opencode"]
    raw_opencode: dict[tuple[str, str], set[str]] = {}
    probe_inventory(config, timeout=timeout, cache_root=cache_root, pairs=opencode_pairs, listed_out=raw_opencode)
    for pair in opencode_pairs:
        if raw_opencode.get(pair):
            listed[pair] = raw_opencode[pair]
        else:
            listed.pop(pair, None)
    return listed, usable


# AC-05 layer 4 (022 PKG-2): deterministic upper bound on how many NEWLY-synthesized
# routes a single discovered provider ever contributes to one snapshot, regardless of
# ceiling state (curated OR auto). Live-measured 2026-08-12: opencode-zen alone lists
# 58-61 models (`opencode models opencode --pure`), already comfortably under this cap
# today (curated at 60) -- the cap exists for what today's curated allowlist happens to
# bound "by accident": an "auto" provider (no `[catalog]` key at all) has NO curated
# ceiling to keep the raw live-probe count in check, so a provider whose upstream
# catalog grows past this constant in the future (or is auto from day one) still gets a
# hard, predictable stop, not silent unbounded growth of the synthesized-route pool that
# feeds `service.route`'s candidate sort. Alphabetical truncation (`sorted()`, never
# probe/dict iteration order) keeps which models survive the cut IDENTICAL across runs
# for the same inputs -- "deterministic" is about repeatability, not about the cut being
# the "best" N by any other measure. Applied to the post-filter (curated/excluded ids
# already dropped) candidate list per provider, so the cap bounds actual pool growth,
# not merely how many raw ids were considered.
_DISCOVERED_ROUTE_CAP_PER_PROVIDER = 80


def discovered_models(config: dict, provider: str, inventory: dict) -> set[str]:
    """Every model the probe actually observed for `provider`, across runtimes.

    Unlike `resolve_ceiling` (curated ceiling, tri-state), this is the raw observed
    pool — the [catalog] allowlist already shaped what the probe could return for a
    "curated" provider (never for "auto", by definition), and the synthesized-route
    layer applies its own exclusions and cap on top.
    """
    pool: set[str] = set()
    for (_, prov), models in inventory.items():
        if prov == provider:
            pool |= {m for m in models if isinstance(m, str) and m}
    return pool


def build_effective_snapshot(catalog_path: Path, roster: list[dict], config: dict,
                             inventory: dict, digest=None):
    """Curated snapshot ∪ synthesized routes for discovered, uncurated models.

    Returns `(CatalogSnapshot, frozenset[str])` — the second element is the set of
    route_ids whose tier/family are INFERRED (routing_core/inference.py), so the
    decision layer can mark them `MODEL_METADATA_INFERRED` and apply the
    inference-only-removes-independence rule. Precedence rules (ADR-0029 d.2):
    a curated row with the same (provider, canonical_model) wins — no synthesized
    twin is ever added; `[catalog].exclude` entries (`"provider:model"` strings in
    models.toml) veto individual discovered ids, and (ADR-0042, 022 PKG-2, AC-05 layer
    4) a `"provider:*"` entry vetoes the ENTIRE provider from this synthesized path in
    one line, without touching `[routing].discovered_providers` or `resolve_ceiling`'s
    own veto (a different axis: this is "never synthesize", not "never probe"); providers
    outside the audited `_PAIR_COMMANDS` set are never synthesized, no matter what the
    config says; and `_DISCOVERED_ROUTE_CAP_PER_PROVIDER` bounds how many NEW routes one
    provider ever contributes (AC-05 layer 4's other half).

    ADR-0034: `providers` comes from `resolve_discovered_providers` -- the single
    function that also drives `service.py`'s recheck lambda, so `"auto"` derives from
    the SAME live-inventory-intersect-audited rule both places (AC-02).
    """
    from .inference import synthesize_route_row
    base = build_snapshot(catalog_path, roster, config, digest)
    providers = resolve_discovered_providers(config, inventory)
    if not providers:
        return base, frozenset()
    roster_names = tuple(sorted({row["role"] for row in roster}))
    curated_ids = {(r.provider, canonical_model(r.provider, r.model)) for r in base.routes}
    exclusions = set()
    for item in (config.get("catalog") or {}).get("exclude") or []:
        if isinstance(item, str) and ":" in item:
            exclusions.add(tuple(item.split(":", 1)))
    audited: dict[str, set[str]] = {}
    for runtime, prov in _PAIR_COMMANDS:
        audited.setdefault(prov, set()).add(runtime)
    routes = list(base.routes)
    identities = set(base.identities)
    inferred: set[str] = set()
    for provider in providers:
        if provider not in audited or (provider, "*") in exclusions:
            continue
        candidates = [model for model in sorted(discovered_models(config, provider, inventory))
                     if (provider, canonical_model(provider, model)) not in curated_ids
                     and (provider, model) not in exclusions]
        for model in candidates[:_DISCOVERED_ROUTE_CAP_PER_PROVIDER]:
            row = synthesize_route_row(provider, model, roster_names)
            roles = tuple(sorted(row["roles"]))
            tools = tuple(sorted(row["tools"]))
            rid = StaticRoute.identifier(2, provider, model, row["family"], row["effort"],
                                         (row["tier"],), roles, tools, row["curated_priority"])
            route = StaticRoute(2, provider, model, row["family"], row["effort"], row["tier"],
                                roles, tools, row["curated_priority"], rid)
            routes.append(route)
            inferred.add(rid)
            for runtime in audited[provider]:
                if model in inventory.get((runtime, provider), set()):
                    identities.add((rid, runtime, provider, model, row["family"], row["effort"]))
    return CatalogSnapshot(tuple(routes), frozenset(identities)), frozenset(inferred)
