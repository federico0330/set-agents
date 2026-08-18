"""ADR-0042 (022 PKG-1): the single audited provider registry.

`PROVIDERS` is the ONE source `routing_core/catalog.py`, `models_config.py`, and
`set_agents_app.py` derive their provider-keyed tables from -- before this module existed,
those three files hand-maintained SIX independently-editable copies of the same four-provider
universe (`_OPENCODE_PROVIDER_KEYS`, `_OPENCODE_CLI_IDS`, `PROVIDER_BILLING_KIND`, the key map
inside `_configured_models`, `DISCOVERABLE_PROVIDERS`, `_MODEL_PREFERENCE_PROVIDERS`), synced
only by human discipline. Adding a provider now means adding one `ProviderSpec` row here.

Deliberately outside the `routing_core` package and importing NEITHER `routing_core` NOR
`models_config`: `routing_core/__init__.py` unconditionally imports `.service`/`.store`
(sqlite3, subprocess, ...) on ANY submodule import, and `models_config.py` documents (at
`detect_subscriptions`/`auto_profile`) that it deliberately avoids a `routing_core` dependency
at module load. A module with zero imports beyond `dataclasses` is importable at module scope
by all three consumers without paying either cost -- see ADR-0042 for the measured alternatives
this rejected.

The dict's INSERTION ORDER is a real contract, not incidental: `set_agents_app.
_MODEL_PREFERENCE_PROVIDERS` derives its ordered tuple from `tuple(PROVIDERS)`, and that order
(`openai-codex, anthropic, opencode-zen, opencode-go`) surfaces in user-facing validation
messages. Never reorder this dict without checking that consumer.
"""

from __future__ import annotations

import dataclasses
import json
import re
import tomllib


@dataclasses.dataclass(frozen=True)
class ProviderSpec:
    """One audited provider's identity across every axis this registry replaces.

    `opencode_auth_key`: the credential display text `opencode auth list --pure` prints for
    this provider (map 1 of 2, 012 AC-02) -- used ONLY at the credential-set membership check.
    `opencode_cli_id`: the CLI argument for `opencode models <id>` AND the `<id>/<model>` line
    prefix `_parse_opencode_models` strips (map 2 of 2) -- independently addressable from
    `opencode_auth_key` (012 AC-02: the two coincide for `openai-codex`/`anthropic` but diverge
    for the OpenCode-lane providers).
    `billing_kind`: `"subscription"` or `"metered"` (012 AC-08 / ADR-0035), curated per
    provider, never a `routes.v1.toml` row field.
    `catalog_key`: the `[catalog]` table key in `models.toml` that curates this provider's
    model allowlist (012 AC-04).
    """

    opencode_auth_key: str
    opencode_cli_id: str
    billing_kind: str
    catalog_key: str


# Order is a contract -- see module docstring. Values are unchanged from the pre-ADR-0042
# literals (PKG-1 AC-02 characterization test pins this).
PROVIDERS: dict[str, ProviderSpec] = {
    "openai-codex": ProviderSpec(
        opencode_auth_key="openai", opencode_cli_id="openai",
        billing_kind="subscription", catalog_key="codex",
    ),
    "anthropic": ProviderSpec(
        opencode_auth_key="anthropic", opencode_cli_id="anthropic",
        billing_kind="subscription", catalog_key="claude",
    ),
    "opencode-zen": ProviderSpec(
        opencode_auth_key="opencode zen", opencode_cli_id="opencode",
        billing_kind="metered", catalog_key="opencode_zen",
    ),
    "opencode-go": ProviderSpec(
        opencode_auth_key="opencode go", opencode_cli_id="opencode-go",
        billing_kind="subscription", catalog_key="opencode_go",
    ),
}


# ================================================================= 022 PKG-4 (AC-11..15)
#
# A SECOND, INDEPENDENT registry in this same neutral module -- NOT the routing-identity
# axis above (`PROVIDERS`, `ollama` never joins it: never probed, never routed, never
# part of `_PAIR_COMMANDS`). This one is the OpenCode `provider.*` JSON-block registry:
# arbitrary local/custom model endpoints a user points OpenCode at directly (today:
# Ollama). Lives on disk at `~/.local/state/set-agentes/providers.toml`, the exact
# atomic-write/private-`STATE_DIR` sibling-file precedent `set_agents_app.
# MODEL_PREFERENCE_PATH` already established (`set_agents_app.py:106`). ADR-0042 is
# extended (not superseded) to name the three origins an entry can carry going forward
# (`harness`, `discovered`, `user`) plus the one-time migration label AC-15 needs
# (`harness-legacy`) for a block this module can prove pre-dates the registry.
PROVIDERS_TOML_NAME = "providers.toml"
PROVIDER_ORIGINS = ("harness", "harness-legacy", "discovered", "user")

# The one block the harness itself used to hardcode straight into
# `Global/_shared/opencode.json` (AC-13: no longer hardcoded there -- this dict is now
# its only home). Used ONLY for two things: (a) seeding a brand-new machine's registry
# on first bootstrap (no live `opencode.json` to read at all), so a fresh install keeps
# today's default behaviour until the user explicitly removes it; and (b) as the
# comparison VALUE `seed_or_migrate` uses to tell a live block that is still
# byte-identical to what the harness always sent (`origin=harness-legacy`) apart from one
# the user has since edited, or added under an id the harness never shipped
# (`origin=user`) -- structural VALUE equality, never an id/name heuristic (022 context
# pack, P4: "escribí la comparación, no una heurística por nombre").
HARNESS_PROVIDER_SEED: dict[str, dict] = {
    "ollama": {
        "npm": "@ai-sdk/openai-compatible",
        "name": "Ollama (local)",
        "options": {"baseURL": "http://localhost:11434/v1"},
        "models": {
            "qwen2.5-coder:7b-instruct-q5_K_M": {"name": "Qwen2.5 Coder 7B Q5 (local, code)"},
            "qwen2.5-coder:7b": {"name": "Qwen2.5 Coder 7B Q4 (local, code)"},
            "llama3.1:8b": {"name": "Llama 3.1 8B (local, general)"},
        },
    },
}


@dataclasses.dataclass(frozen=True)
class ProviderEntry:
    """One `providers.toml` row: `origin` (one of `PROVIDER_ORIGINS`) plus `spec`, the
    exact JSON object that lands verbatim at `opencode.json["provider"][provider_id]`
    (AC-13: install.py renders this dict, never re-derives or reshapes it)."""

    origin: str
    spec: dict


class ProvidersRegistryError(ValueError):
    """Fail-closed: a malformed `providers.toml` never degrades to a silently-empty
    registry -- same discipline `set_agents_app.ModelPreferenceError` already applies to
    the sibling `model-preference.toml` file."""


def _die(path, message):
    raise ProvidersRegistryError(f"{path}: {message}")


_BARE_TOML_KEY = re.compile(r"[A-Za-z0-9_-]+")


def _toml_string(value: str) -> str:
    """A TOML basic string is, character for character, a JSON string for every value
    this module ever writes: `json.dumps` and TOML's basic-string grammar agree on the
    exact same escape set (`\\", \\\\, \\n, \\t, \\r, \\b, \\f, \\uXXXX`) and `json.dumps`
    (ensure_ascii=True, the default) never emits a raw non-ASCII byte or a literal control
    character outside that set. So `json.dumps` doubles as this module's ENTIRE
    TOML-string-escaping routine -- not a general nested-TOML writer, the same
    closed-schema discipline `set_agents_app._serialize_model_preference` already
    documents for its own sibling file (ADR-0018 R2-F-04)."""
    return json.dumps(value)


def _toml_key(key: str) -> str:
    # Bare TOML keys allow only [A-Za-z0-9_-]; every id observed in the wild so far
    # already matches, but a future user-chosen id might not (spaces, dots, colons) --
    # quote it like any other TOML basic string instead of assuming.
    return key if _BARE_TOML_KEY.fullmatch(key) else _toml_string(key)


def parse_providers_toml(path) -> dict[str, ProviderEntry]:
    """Fail-closed parse. An absent file is the unbiased empty default (same shape
    `_read_model_preference_raw` uses for its own sibling file) -- callers that need to
    bootstrap on absence do so explicitly via `seed_or_migrate`, never here."""
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except OSError as exc:
        _die(path, str(exc))
    try:
        doc = tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        _die(path, f"invalid TOML ({exc})")
    entries = {}
    for provider_id, table in doc.items():
        if not isinstance(table, dict) or set(table) != {"origin", "spec"}:
            _die(path, f"[{provider_id}] must have exactly 'origin' and 'spec'")
        origin = table["origin"]
        if origin not in PROVIDER_ORIGINS:
            _die(path, f"[{provider_id}].origin unknown: {origin!r}")
        spec_raw = table["spec"]
        if not isinstance(spec_raw, str):
            _die(path, f"[{provider_id}].spec must be a string")
        try:
            spec = json.loads(spec_raw)
        except json.JSONDecodeError as exc:
            _die(path, f"[{provider_id}].spec is not valid JSON ({exc})")
        if not isinstance(spec, dict):
            _die(path, f"[{provider_id}].spec must decode to a JSON object")
        entries[provider_id] = ProviderEntry(origin=origin, spec=spec)
    return entries


def serialize_providers_toml(entries: dict[str, ProviderEntry]) -> str:
    """The small, purpose-built, fixed-shape emitter this schema's own closure makes
    safe -- exactly two keys per table, `origin` a closed-vocabulary string and `spec` an
    opaque JSON-encoded string (see `_toml_string`). Sorted by id for a stable,
    diffable file, same as `_serialize_model_preference` sorts its own tables."""
    lines = []
    for provider_id in sorted(entries):
        entry = entries[provider_id]
        lines.append(f"[{_toml_key(provider_id)}]")
        lines.append(f"origin = {_toml_string(entry.origin)}")
        lines.append(f"spec = {_toml_string(json.dumps(entry.spec, sort_keys=True))}")
        lines.append("")
    return ("\n".join(lines).rstrip("\n") + "\n") if entries else ""


def _normalize_spec(spec: dict) -> dict:
    """Round-trips `spec` through the exact same `sort_keys=True` JSON encoding
    `serialize_providers_toml` uses for storage, so a freshly bootstrapped entry (this
    call) and one read back later via `parse_providers_toml` (which necessarily gets
    the STORED, sort_keys=True key order back) render byte-for-byte identical JSON into
    `opencode.json`. Without this, the very next `install.py --preview` after a fresh
    bootstrap reports the provider block as 'changed' purely from key-order churn
    (`dict` equality ignores order, `json.dumps` does not) -- caught live by `check-
    drift.sh`/`tests/test_harness.py::test_check_drift_detects_stale_and_clean_install`
    during this package's own gate run, not invented after the fact."""
    return json.loads(json.dumps(spec, sort_keys=True))


def seed_or_migrate(live_provider_block: dict) -> dict[str, ProviderEntry]:
    """AC-15: the ONE-TIME bootstrap content for a machine with no `providers.toml` yet
    (callers only invoke this when the file is confirmed absent -- an existing file,
    even an empty one, is authoritative forever after and is never reseeded; that is
    what makes `--provider-remove` stick across future installs).

    `live_provider_block` is the CURRENT on-disk `provider` object under the live
    `opencode.json` (or `{}`/absent on a brand-new machine with no prior install).

    - Non-empty: every id present is registered -- 'a nadie le desaparece nada' -- each
      tagged `harness-legacy` when its value is STRUCTURALLY EQUAL to the matching
      `HARNESS_PROVIDER_SEED` entry (the harness's own past content, byte-for-byte) or
      `user` otherwise (an id the harness never shipped, OR one it did ship but whose
      live value has since diverged -- the user edited it by hand). Never an id/name
      heuristic: `ollama` with a value the user changed is `user`, not `harness-legacy`.
      The comparison itself runs on the ORIGINAL (pre-normalization) values -- dict
      equality already ignores key order, so `_normalize_spec` below changes nothing
      about which entries are found equal, only the key order later written to disk.
    - Empty (nothing to migrate): every `HARNESS_PROVIDER_SEED` entry is registered
      fresh as `origin=harness`, so a brand-new machine keeps today's default behaviour
      (Ollama pre-declared) until the user explicitly runs `--provider-remove`.
    """
    if not live_provider_block:
        return {provider_id: ProviderEntry(origin="harness", spec=_normalize_spec(spec))
                for provider_id, spec in HARNESS_PROVIDER_SEED.items()}
    entries = {}
    for provider_id, spec in live_provider_block.items():
        seed = HARNESS_PROVIDER_SEED.get(provider_id)
        origin = "harness-legacy" if seed is not None and spec == seed else "user"
        entries[provider_id] = ProviderEntry(origin=origin, spec=_normalize_spec(spec))
    return entries


def load_or_bootstrap(path, live_provider_block: dict) -> tuple[dict[str, ProviderEntry], str | None]:
    """The one entry point both `install.py` and `set_agents_app.py` share to resolve
    the CURRENT registry content. Returns `(entries, bootstrap_text)`:
    - `path` already exists: `(parse_providers_toml(path), None)` -- nothing new to
      persist, `bootstrap_text` is `None` so a caller never mistakes "already there" for
      "must write".
    - `path` absent: `(seed_or_migrate(live_provider_block), <serialized text>)` --
      freshly computed, not yet persisted. `install.py` defers the actual write until
      after its own smoke checks pass (same discipline as its `MANIFEST` write); a
      direct CLI caller with no transaction to protect may write it immediately.
    """
    if path.exists():
        return parse_providers_toml(path), None
    entries = seed_or_migrate(live_provider_block)
    return entries, serialize_providers_toml(entries)
