from __future__ import annotations

import hashlib
import json
import os
import re
import stat as _stat
import subprocess
import time
import tomllib
from pathlib import Path
from .domain import CatalogSnapshot, RoutingError, StaticRoute, _sorted_strings

# ADR-0006 (AM-2): probe cache is a filtering-only optimization. TTL bounds staleness;
# the invalidation key covers uid and the canonical catalog/routing config.
PROBE_CACHE_TTL = 300.0

# ADR-0007 (P3-pi-lane, T-301/T-305): pi is invoked through an EXACT pinned version, never
# the bare `pi` on PATH (the managed `~/.local/bin/pi` wrapper only soft-pins by release
# age via PNPM_CONFIG_MINIMUM_RELEASE_AGE) — the probe below and the T-303 spawner share
# this ONE invocation builder, so the audited pair and the executed child are provably the
# same binary. Bump PI_PINNED_VERSION deliberately (code review), never silently.
PI_PACKAGE = "@earendil-works/pi-coding-agent"
PI_PINNED_VERSION = "0.81.1"

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


# Catalog provider -> credential display text `_parse_opencode_auth` yields (map 1 of 2,
# 012 AC-02). Used ONLY at the credential-set membership check. For the two pre-existing
# pairs this string happens to coincide with the CLI argument below; for opencode-zen/
# opencode-go it does not ("opencode zen"/"opencode go", two-token display text, vs the
# single-token CLI ids in _OPENCODE_CLI_IDS) — re-measured live against `opencode auth
# list --pure` (docs/specs/012-discovered-inventory/spec.md AC-02).
_OPENCODE_PROVIDER_KEYS = {"openai-codex": "openai", "anthropic": "anthropic",
                           "opencode-zen": "opencode zen", "opencode-go": "opencode go"}
# Catalog provider -> CLI argument for `opencode models <id>` AND the `<id>/<model>` line
# prefix `_parse_opencode_models` strips (map 2 of 2, 012 AC-02). Independently
# addressable from _OPENCODE_PROVIDER_KEYS above: using the CLI-id value at the
# credential-membership check would search the two-token display-name set for a
# single-token string and report the pair absent on every machine (the defect this
# two-map split fixes; PI_MODEL_MAP is explicitly the wrong precedent here — it
# translates a model name within one already-matched provider, a different axis).
_OPENCODE_CLI_IDS = {"openai-codex": "openai", "anthropic": "anthropic",
                     "opencode-zen": "opencode", "opencode-go": "opencode-go"}
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
# Records the fact only; no weighting/selection logic reads this map yet (008-P3's
# territory, out of scope here).
PROVIDER_BILLING_KIND = {"opencode-zen": "metered", "opencode-go": "subscription"}
_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def allowed_probe(runtime: str, provider: str) -> tuple[tuple[str, ...], ...] | None:
    """The closed, exact argv list for a pair; None for any unaudited pair."""
    return _PAIR_COMMANDS.get((runtime, provider))


def _configured_models(config: dict, provider: str) -> set[str]:
    # 012 AC-04: same five-site lockstep as the pre-existing two providers (corrected
    # 012 repair F-04: the original comment undercounted "three sites" — this package
    # added two more in models_config.py) — this key map is site (2) of 5 that must move
    # together with: (1) models.toml's [catalog] table itself; (2) this key map; (3)
    # build_snapshot's own `configured_models` comprehension (catalog.py, below); (4)
    # models_config.load_config's optional-key validation loop for the same two TOML
    # keys; (5) models_config.emit's preservation loop for the same two keys (without
    # which a future `./setup-models.sh` write would silently drop the allowlist). Sites
    # (4)/(5) exist because [catalog] has no closed-schema check the way [routing]/
    # [permissions] do — an allowlist key present in the TOML but absent from both
    # models_config.py sites is read here (fine) but never survives a re-emit (data
    # loss). Extending only site (1) leaves the other providers' allowlists unreachable
    # from code; extending only (1)-(3) without (4)/(5) leaves them reachable but
    # silently unpersisted on the next wizard run.
    key = {"openai-codex": "codex", "anthropic": "claude",
           "opencode-zen": "opencode_zen", "opencode-go": "opencode_go"}.get(provider)
    models = config.get("catalog", {}).get(key, ()) if key else ()
    if not isinstance(models, (list, tuple)):
        return set()
    return {item for item in models if isinstance(item, str) and item}


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
    """`opencode auth list --pure` prints decorated credential rows, one provider name per bullet."""
    providers = set()
    for line in _clean_lines(stdout):
        if line.startswith("Error"):
            raise RoutingError("PROVIDER_UNAUTHENTICATED")
        if line.startswith(("●", "○", "*")):
            body = line.lstrip("●○* ").strip()
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
    token values, never logged. Any surprise (missing file, symlink, foreign shape, bad
    JSON) is an empty set, fail-closed — this never raises and the caller never sees a
    credential value, only whether a provider name is present as a key."""
    path = Path.home() / ".pi/agent/auth.json"
    try:
        st = path.lstat()
        if _stat.S_ISLNK(st.st_mode) or not _stat.S_ISREG(st.st_mode):
            return frozenset()
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return frozenset()
    if not isinstance(doc, dict):
        return frozenset()
    return frozenset(key for key in doc if isinstance(key, str))


def _cache_key(config: dict) -> str:
    canon = json.dumps({"catalog": config.get("catalog", {}), "routing": config.get("routing", {})},
                       sort_keys=True, default=str)
    return hashlib.sha256(f"{os.getuid()}\n{canon}".encode("utf-8")).hexdigest()


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
    is re-intersected with the live `_configured_models` catalog on read
    (F09), so a stale-but-key-matching cache can never widen the audited set.
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
            intersected = set(models) & _configured_models(config, provider)
            if intersected:  # empty after intersection ⇒ treated as absent, retried like any negative
                out[(runtime, provider)] = intersected
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


def _probe_pairs(config: dict, pairs, timeout: float, ran=None) -> dict[tuple[str, str], set[str]]:
    """Fresh, uncached, pair-scoped subprocess observation for exactly `pairs`.

    Any surprise — missing binary, timeout, nonzero exit, unexpected shape,
    error text — makes only that pair unavailable (never raises). A pair
    without any resulting model is simply absent from the returned dict:
    negative results are never a first-class cached value (F06).
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
        allowed = _configured_models(config, provider)
        if not allowed:
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
                models = allowed & _parse_opencode_models(models_result.stdout, cli_id)
            except (RoutingError, ValueError, KeyError, IndexError, TypeError):
                continue
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
                    models = allowed if _parse_codex_login(completed[0].stdout, completed[0].stderr) else set()
                elif runtime == "claude-code":
                    models = allowed if _parse_claude_auth(completed[0].stdout) else set()
                else:  # pi
                    # Belt-and-suspenders (T-305, spike Q2): the auth.json key-set is a cheap,
                    # non-subprocess signal alongside the naturally fail-closed column-parse
                    # below (an unauthenticated provider simply has no rows in --list-models).
                    if provider not in pi_auth_provider_keys():
                        continue
                    models = allowed & _parse_pi_models(completed[0].stdout, provider)
            except (RoutingError, ValueError, KeyError, IndexError, TypeError):
                continue
        if models:
            result[pair] = models
    return result


def probe_inventory(config: dict, timeout: float = 20.0, cache_root=None, fresh: bool = False,
                    pairs=None, now=None, cache_write: bool = True) -> dict[tuple[str, str], set[str]]:
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
    """
    now = time.time() if now is None else now
    if pairs is not None:
        selected = [pair for pair in pairs if pair in _PAIR_COMMANDS]
        return _probe_pairs(config, selected, timeout)
    all_pairs = list(_PAIR_COMMANDS)
    use_cache = cache_root is not None and _validate_cache_dir(Path(cache_root))
    key = _cache_key(config) if use_cache else None
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
    # 012 AC-04, site 3 of 5 (corrected 012 repair F-04 — see _configured_models's own
    # comment above for the full five-site enumeration; moves in lockstep with
    # models.toml's [catalog] table and _configured_models's key map at minimum):
    # opencode-zen/opencode-go are listed here too, even though no routes.v1.toml row
    # references them yet — this contract's non-goals paragraph states "no curated
    # routes.v1.toml rows for the new models" (docs/specs/012-discovered-inventory/
    # spec.md, "Non-goals of P2"; corrected 012 repair F-07 — this is NOT AC-11, which is
    # the cache/decision-trail AC and says nothing about routes.v1.toml rows) — an absent
    # provider's allowlist would otherwise be silently unreachable the moment a row for it
    # is curated later.
    configured_models = {provider: _configured_models(config, provider)
                         for provider in ("openai-codex", "anthropic", "opencode-zen", "opencode-go")}
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
            if (provider not in enabled or model not in configured_models.get(provider, set())
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

def discovered_models(config: dict, provider: str, inventory: dict) -> set[str]:
    """Every model the probe actually observed for `provider`, across runtimes.

    Unlike `_configured_models` (curated ceiling, intersection semantics), this is
    the raw observed pool — the [catalog] allowlist already shaped what the probe
    could return for the two OpenCode-lane providers, and the synthesized-route
    layer applies its own exclusions on top.
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
    models.toml) veto individual discovered ids; providers outside the audited
    `_PAIR_COMMANDS` set are never synthesized, no matter what the config says.
    """
    from .inference import synthesize_route_row
    base = build_snapshot(catalog_path, roster, config, digest)
    providers = (config.get("routing") or {}).get("discovered_providers") or []
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
        if provider not in audited:
            continue
        for model in sorted(discovered_models(config, provider, inventory)):
            if (provider, canonical_model(provider, model)) in curated_ids:
                continue
            if (provider, model) in exclusions:
                continue
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
