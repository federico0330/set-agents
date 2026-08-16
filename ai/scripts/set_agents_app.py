#!/usr/bin/env python3
"""set-agents: unified console app for the SET-AGENTS harness (gentle-ai style).

A TTY menu plus a scriptable CLI over the same primitives: install/repair
(install.sh), self-update (git pull --ff-only + managed reinstall), model
routing (setup-models.sh), and — in later sections — the optional tools
catalog, MCP servers, and Claude Code plugins.
"""

import argparse
import hashlib
import json
import os
import pwd
import re
import secrets
import shlex
import shutil
import subprocess
import sys
import tempfile
import tomllib
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
# When this file runs as a script, extracted helpers lazily importing `set_agents_app`
# must resolve this live module rather than execute a second copy with PROJECT_ROOT=None.
# Importing normally already has this key, so setdefault is behavior-preserving there.
sys.modules.setdefault("set_agents_app", sys.modules[__name__])
import coord_policy
import models_config
import provider_registry
import routing
import set_agents_spawn
import tui
from routing_core.domain import classify_pi_terminal_error

# SET_AGENTS_ROOT/SET_AGENTS_STATE/SET_AGENTS_ROUTING_TEST_ROOT are test seams; real runs
# never set them. routing_core itself never reads any of them (ADR-0006: the routing store's
# production root is fixed, derived from the account database, never from the environment) —
# this indirection lives entirely here, in the CLI composition layer (F07).
ROOT = Path(os.environ.get("SET_AGENTS_ROOT") or Path(__file__).resolve().parents[2])
STATE_DIR = Path(os.environ.get("SET_AGENTS_STATE") or Path.home() / ".local/state/set-agentes")
ROUTING_TEST_ROOT = os.environ.get("SET_AGENTS_ROUTING_TEST_ROOT")
APP_CONFIG = STATE_DIR / "config.toml"
MANAGED_MCP = models_config.MANAGED_MCP
HARNESS_CLIS = ("opencode", "claude", "codex")
PROJECT_ROOT: Path | None = None
PROJECT_KEY: str | None = None
ROUTING_WARNINGS: tuple[str, ...] = ()
_PROJECT_KEY_RE = re.compile(r"^proj1_[0-9a-f]{32}$")
_MAX_FEATURE_BYTES = 1024 * 1024
_MAX_FEATURE_FILES = 256

# project_identity.py: project-root discovery and stable identity. It carries its own
# (identical-value) copies of `_PROJECT_KEY_RE`/`_MAX_FEATURE_BYTES` rather than importing
# them back from here, to avoid a genuine circular import (see its own module docstring).
from project_identity import (  # noqa: E402
    _real_directory, _has_project_marker, find_project_root, resolve_project_root,
    _casefold_project_path, _safe_read, ProjectIdentityError, project_key_for,
)


def _routing_store():
    """F07: the one seam a hermetic CLI test uses to drive decide/dispatched/terminal/abandoned
    against a temp root. Never set by real runs (see the module-level seam note above)."""
    key = PROJECT_KEY
    return (routing.RoutingStore._for_tests(Path(ROUTING_TEST_ROOT), project_key=key)
            if ROUTING_TEST_ROOT else routing.RoutingStore(project_key=key))


def _probe_cache_root() -> Path:
    """ADR-0043 (022 PKG-3, AC-10): the ONE probe-cache root every reader in this file
    resolves to now -- the same root `RoutingService`'s own composition creates/
    validates via `RoutingStore.ensure_cache_root()` (routing_core/service.py:112-115),
    never `STATE_DIR` directly (the legacy, divergent root `--route-doctor`/
    `--doctor-all`/the 'Estado general' panel used to read while the decision path
    already read/wrote `routing-v2/probe-cache.json` -- two caches confirmed diverging
    live). `RoutingStore.root` is a PURE attribute (no I/O at construction, same
    laziness `STATE_DIR` itself always had, respects the `ROUTING_TEST_ROOT` seam via
    `_routing_store()` above) -- this function never creates or validates anything
    itself; that stays exactly where it always lived, inside
    `probe_inventory`/`_validate_cache_dir` (which never creates either, only
    validates)."""
    return _routing_store().root


def _project_root_or_harness() -> Path:
    # Direct helper calls in legacy unit tests have no CLI resolution; production
    # routes always set PROJECT_ROOT in main before accessing project data.
    return PROJECT_ROOT or ROOT


# --------------------------------------------------- 014-model-preference-policy (AC-02)
#
# One real, per-harness-install sibling config file next to `APP_CONFIG` (the same
# private `STATE_DIR`, `write_app_config`'s own directory) -- NEVER routed through
# `write_app_config` (its flat `key = value` serializer, `:XXX` below, corrupts a nested
# preference table) or `app_config()` (its silent parse-failure-as-`{}` swallow). This
# file gets its OWN dedicated, atomic, fail-closed round-trip: `atomic_write` (already
# established for the Claude settings JSON writer above) for the temp-file+`os.replace`
# discipline, and a small, purpose-built two-table TOML serializer for a schema this
# contract fully owns and closes (`[preference]`, `[role_override]`) -- not a
# general-purpose nested-TOML writer (round-2 finding R2-F-04).
MODEL_PREFERENCE_PATH = STATE_DIR / "model-preference.toml"

# The closed, four-provider universe `_PAIR_COMMANDS` already probes
# (`routing_core/catalog.py:165-172`). ADR-0042 (022 PKG-1) supersedes this table's own
# ORIGINAL "defined independently here, never importing" framing -- that framing was wider
# than the reason it named: the AC-06 non-goal it cites (014-model-preference-policy,
# test_ac06_no_provider_billing_kind_reference_in_new_code) is specifically about never
# letting the catalog module's own billing-kind classification table decide provider
# membership here, and that narrower non-goal still holds -- this tuple's derivation below
# never reads that table (nor even names it -- see the test above, unchanged by this
# package). What changed is provider IDENTITY: this tuple now derives from the single
# `provider_registry.PROVIDERS` registry every provider-keyed table in the harness shares,
# instead of being a second hand-maintained copy of the same four provider ids. Order is a
# real contract (surfaces in pin/preference validation errors) --
# `tuple(provider_registry.PROVIDERS)`, never `tuple(models_config.DISCOVERABLE_PROVIDERS)`,
# because that sibling table is an unordered `set`.
_MODEL_PREFERENCE_PROVIDERS = tuple(provider_registry.PROVIDERS)
_MODEL_PREFERENCE_CLASSES = ("decision", "grunt", "build")
# AC-02's inertness note: the six roles with real, live effect today (`### Honest scope`,
# spec) -- every other in-scope role, and the whole `decision` class, is genuinely inert.
_MODEL_PREFERENCE_LIVE_ROLES = frozenset({
    "delta-reviewer", "finding-verifier", "package-reviewer", "security-auditor",
    "implementer", "debugger",
})


class ModelPreferenceError(ValueError):
    """AC-02: fail-closed error for the sibling `model-preference.toml` file/CLI -- a
    malformed value never degrades to a silent default (round-1 F-07, round-3 R3-F-04)."""


def _model_preference_die(message):
    raise ModelPreferenceError(message)


def _effective_preference_providers():
    """ADR-0034 (AC-09): the base audited set (`_MODEL_PREFERENCE_PROVIDERS`, unchanged
    -- same VALUES as `models_config.DISCOVERABLE_PROVIDERS`, both derived from the single
    `provider_registry.PROVIDERS` registry since ADR-0042; the two differ in TYPE on
    purpose, ordered tuple vs. unordered set, never in membership) UNION whatever the
    CURRENT effective snapshot reports as routable, when that snapshot is cheaply
    resolvable -- a live probe, never network/credential material. Deliberately never
    called from `load_model_preference`/`load_model_pin` (the boot path, `_read_model_
    preference_raw`'s callers): probing there would make a plain `models.toml` read
    depend on a live opencode probe, which the spec explicitly forbids. Only the WRITE
    CLI paths below (`cmd_model_preference_set`, `cmd_model_pin_set`, ...) -- explicit,
    interactive user actions where the probe's cost is acceptable -- use this. ANY
    failure (missing routing_core state, a broken probe, an unreadable models.toml)
    degrades silently to the base set alone, never a crash: a wider live set is a
    convenience, never a requirement for pins/preferences to keep working.

    F-05 (P1 repair): the union only ever has an observable effect on a day
    `resolve_discovered_providers` can return a provider OUTSIDE the base set --
    which today it structurally cannot: every provider it can produce comes from
    `routing_core.catalog._PAIR_COMMANDS`'s own audited provider set, and that set is
    pinned equal to `models_config.DISCOVERABLE_PROVIDERS` (== `_MODEL_PREFERENCE_
    PROVIDERS`, guarded for real since ADR-0042 -- both are derived from
    `provider_registry.PROVIDERS`, and `test_adr0042_ac01b_...` in tests/test_routing.py
    compares this tuple against `_PAIR_COMMANDS`'s own provider set directly, never a
    second hardcoded literal). So the probe below is skipped whenever the
    base set already covers `DISCOVERABLE_PROVIDERS` -- a cheap, exact short-circuit
    that avoids paying a subprocess probe (each `_PAIR_COMMANDS` entry can block up to
    20s) on every `--model-pin-set`/`--model-preference-set` call for a union that
    cannot widen anything yet. The probe only actually runs again once
    `_PAIR_COMMANDS`'s audited set genuinely grows past the base set (e.g. a future
    ADR widens discovery beyond today's four providers)."""
    if set(models_config.DISCOVERABLE_PROVIDERS) <= set(_MODEL_PREFERENCE_PROVIDERS):
        return _MODEL_PREFERENCE_PROVIDERS
    try:
        from routing_core.catalog import probe_inventory, resolve_discovered_providers
        config = models_config.load_config()
        # ADR-0043 (022 PKG-3, AC-10): the single store root, not the legacy STATE_DIR.
        inventory = probe_inventory(config, cache_root=_probe_cache_root())
        live = resolve_discovered_providers(config, inventory)
    except Exception:
        return _MODEL_PREFERENCE_PROVIDERS
    return tuple(dict.fromkeys((*_MODEL_PREFERENCE_PROVIDERS, *live)))


def _validate_preference_providers(class_name, providers, valid_providers=_MODEL_PREFERENCE_PROVIDERS):
    """AC-02 resolution states 1/2/4d: shared by the config-load path and the CLI write
    path (`load_model_preference`/`cmd_model_preference_set` below) -- a malformed value
    can never even be WRITTEN by the CLI to begin with; a hand-edited file is the only way
    to reach this same check at load time. `valid_providers` (ADR-0034 AC-09) defaults to
    the static base set (the boot-path callers below never pass anything else, so the
    arranque stays network-free); the write-CLI passes `_effective_preference_providers()`."""
    if not isinstance(providers, (list, tuple)) or not providers:
        _model_preference_die(f"model-preference.toml: [preference].{class_name} must be a non-empty list of providers")
    validated = []
    for token in providers:
        if not isinstance(token, str) or token not in valid_providers:
            _model_preference_die(f"model-preference.toml: [preference].{class_name} contains unknown provider {token!r}")
        validated.append(token)
    if len(validated) != len(set(validated)):
        _model_preference_die(f"model-preference.toml: [preference].{class_name} contains a duplicate provider")
    return tuple(validated)


def _validate_role_override_entry(role, class_name, roster_roles):
    """AC-02 resolution states 3/4: reuses the exact `models_config.load_roles` unknown-
    role precedent shape (per-role-named `die()`, `models_config.py:274-276`), and rejects
    `"unscoped"` (a resolution OUTCOME, never a legal override target)."""
    if role not in roster_roles:
        _model_preference_die(f"model-preference.toml: [role_override].{role} does not match any role in roles.tsv")
    if not isinstance(class_name, str) or class_name not in _MODEL_PREFERENCE_CLASSES:
        _model_preference_die(f"model-preference.toml: [role_override].{role} names unknown class {class_name!r}")
    return class_name


def _read_model_preference_raw():
    """Fail-closed parse only -- never `app_config()`'s silent `except: return {}}` swallow
    (round-3 R3-F-04(a)); a malformed file loudly fails every caller, load or write alike."""
    try:
        raw = MODEL_PREFERENCE_PATH.read_text()
    except FileNotFoundError:
        return {}
    except OSError as exc:
        _model_preference_die(f"model-preference.toml: {exc}")
    try:
        doc = tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        _model_preference_die(f"model-preference.toml: {exc}")
    if not isinstance(doc, dict) or set(doc) - {"preference", "role_override", "model_pin"}:
        _model_preference_die("model-preference.toml: unknown top-level key")
    return doc


def load_model_preference(roster_roles=None):
    """AC-02/AC-03: the config-load path. Returns
    `{"preference": {class: (providers...)}, "role_override": {role: class}}` --
    absent file is the unbiased default (both tables empty), never a crash. `roster_roles`
    is an optional pre-loaded `{role, ...}` set (the CLI's own composition already has
    one); when omitted, the roster is loaded fresh from `roles.tsv`."""
    doc = _read_model_preference_raw()
    preference_table = doc.get("preference", {})
    if not isinstance(preference_table, dict):
        _model_preference_die("model-preference.toml: [preference] must be a table")
    preference = {}
    for class_name, providers in preference_table.items():
        if class_name not in _MODEL_PREFERENCE_CLASSES:
            _model_preference_die(f"model-preference.toml: [preference] has unknown class {class_name!r}")
        preference[class_name] = _validate_preference_providers(class_name, providers)
    override_table = doc.get("role_override", {})
    if not isinstance(override_table, dict):
        _model_preference_die("model-preference.toml: [role_override] must be a table")
    roles = roster_roles if roster_roles is not None else {row["role"] for row in models_config.load_roster(ROOT / "roles.tsv")}
    role_override = {}
    for role, class_name in override_table.items():
        role_override[role] = _validate_role_override_entry(role, class_name, roles)
    return {"preference": preference, "role_override": role_override}


# ---------------------------------------------------------------- ADR-0032: model pin
#
# `[model_pin]` is the third table in the SAME sibling file (never a new mechanism —
# ADR-0018's infra reused per ADR-0032): `role = "provider/model"`, plus the literal
# key `"*"` as the global pin every role without its own entry inherits. The pin is a
# USER OVERRIDE the router respects as a soft, sort-level preference: it never bypasses
# a hard exclusion (auth, independence, tier floor) — when the pinned identity is not
# eligible the decision degrades to dynamic with an additive MODEL_PIN_UNAVAILABLE code,
# never a fabricated authorization. `load_model_preference`'s public two-key return
# shape is a frozen contract (tests/test_routing.py:4004) — pins load through this
# SEPARATE sibling loader, same file, same fail-closed discipline.
_MODEL_PIN_MODEL_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")


def _validate_model_pin_entry(role, value, roster_roles, valid_providers=_MODEL_PREFERENCE_PROVIDERS):
    """`valid_providers` (ADR-0034 AC-09): defaults to the static base set, so every
    boot-path caller (`load_model_pin`) stays network-free; the write-CLI
    (`cmd_model_pin_set`) passes `_effective_preference_providers()`."""
    if role != "*" and role not in roster_roles:
        _model_preference_die(f"model-preference.toml: [model_pin].{role} does not match any role in roles.tsv")
    if not isinstance(value, str) or value.count("/") != 1:
        _model_preference_die(f"model-preference.toml: [model_pin].{role} must be \"provider/model\"")
    provider, model = value.split("/", 1)
    if provider not in valid_providers:
        _model_preference_die(f"model-preference.toml: [model_pin].{role} names unknown provider {provider!r}")
    if not _MODEL_PIN_MODEL_RE.fullmatch(model):
        _model_preference_die(f"model-preference.toml: [model_pin].{role} has an invalid model token")
    return provider, model


def _validate_model_request(value, valid_providers=_MODEL_PREFERENCE_PROVIDERS):
    """AC-04 (026-orquestador-elige-modelo P2): validates `--route-decide`'s descriptor
    `model_request` value -- the SAME "provider/model" shape and closed, network-free
    provider vocabulary `_validate_model_pin_entry` already enforces for the PERSISTENT
    `[model_pin]` table (reused here as a bare value: no role key, no file, nothing
    written -- AC-07's ephemerality lives entirely in the caller never calling
    `atomic_write`/`MODEL_PREFERENCE_PATH` for this value, not in this function).
    Raises plain `ValueError` (never `ModelPreferenceError`, which is the sibling
    FILE's own exception type) -- `cmd_route_decide`'s existing `except (OSError,
    ValueError)` clause turns it into `ROUTING_INPUT_INVALID`/rc=2, the same PARSE-time
    fail-closed discipline as `risk`/`selected_runtime`'s enum checks (F01): a malformed
    model_request never reaches the service to degrade silently into a different
    reason code. Returns `(provider, model)`."""
    if not isinstance(value, str) or value.count("/") != 1:
        raise ValueError
    provider, model = value.split("/", 1)
    if provider not in valid_providers or not _MODEL_PIN_MODEL_RE.fullmatch(model):
        raise ValueError
    return provider, model


def load_model_pin(roster_roles=None):
    """ADR-0032: `{role_or_star: (provider, model)}` — absent file/table is the unpinned
    default (empty dict), never a crash; a malformed entry fails closed like every other
    table in this file."""
    doc = _read_model_preference_raw()
    pin_table = doc.get("model_pin", {})
    if not isinstance(pin_table, dict):
        _model_preference_die("model-preference.toml: [model_pin] must be a table")
    roles = roster_roles if roster_roles is not None else {row["role"] for row in models_config.load_roster(ROOT / "roles.tsv")}
    return {role: _validate_model_pin_entry(role, value, roles) for role, value in pin_table.items()}


def _config_with_model_preference(config, roster):
    """AC-04: the one channel available to feed AC-02's resolved preference tables into
    `RoutingService` without touching `routing.py`'s read-only `compose()` signature --
    injected under an internal-marker key `RoutingService.__init__` reads and strips,
    the same underscore-prefixed convention `models_config.py` already uses for
    `config["_source_schema"]` (never itself re-serialized to models.toml). A malformed
    sibling file fails closed exactly like a malformed `models.toml` already does --
    `ModelPreferenceError` bubbles to the caller's own existing except clause."""
    roster_roles = {row["role"] for row in roster}
    preference = dict(load_model_preference(roster_roles))
    # ADR-0032: pins ride the same internal-marker channel; the service treats an
    # absent/empty table as the unpinned default.
    preference["model_pin"] = load_model_pin(roster_roles)
    config["_model_preference"] = preference
    return config


def _serialize_model_preference(doc):
    """The small, purpose-built, fixed-shape emitter this schema's own closure makes safe
    -- exactly two tables, each a flat mapping to a closed-vocabulary list/string. NOT a
    general nested-TOML writer (R2-F-04); every value is `json.dumps`-quoted, which is
    valid TOML string syntax for these ASCII, punctuation-free tokens."""
    lines = []
    preference = doc.get("preference") or {}
    if preference:
        lines.append("[preference]")
        for class_name in sorted(preference):
            rendered = ", ".join(json.dumps(token) for token in preference[class_name])
            lines.append(f"{class_name} = [{rendered}]")
        lines.append("")
    role_override = doc.get("role_override") or {}
    if role_override:
        lines.append("[role_override]")
        for role in sorted(role_override):
            lines.append(f"{role} = {json.dumps(role_override[role])}")
        lines.append("")
    model_pin = doc.get("model_pin") or {}
    if model_pin:
        lines.append("[model_pin]")
        for role in sorted(model_pin):
            lines.append(f'"{role}" = {json.dumps(model_pin[role])}' if role == "*" else f"{role} = {json.dumps(model_pin[role])}")
        lines.append("")
    return ("\n".join(lines).rstrip("\n") + "\n") if (preference or role_override or model_pin) else ""


def _model_preference_class_inert(class_name):
    """AC-02: re-baselined round 4 (F-01) -- only `decision` is inert as a WHOLE class
    today; `grunt`/`build` each have at least one live tiered role, so a class-scoped
    write to either never fires the note even though some of that class's own non-tiered
    members individually would (checked per-role by `_model_preference_role_inert`)."""
    return class_name == "decision"


def _model_preference_role_inert(role):
    """AC-02: true for every role except the six with real, live effect today."""
    return role not in _MODEL_PREFERENCE_LIVE_ROLES


_MODEL_PREFERENCE_NOTE_SUFFIX = "(see docs/specs/014-model-preference-policy/spec.md ### Honest scope)"


def cmd_model_preference_set(class_name, providers):
    """AC-02: `--model-preference-set CLASS --provider NAME [--provider NAME ...]` --
    writes/replaces `[preference].<CLASS>`, leaving every other key untouched (the
    round-trip regression test proves this isolation)."""
    # ADR-0034 (AC-09): the explicit write CLI validates against the LIVE effective set
    # (base union whatever the current snapshot reports routable), never just the
    # static 4-provider constant -- this is a user action, not the boot path, so the
    # probe's cost is acceptable here.
    validated = _validate_preference_providers(class_name, providers, _effective_preference_providers())
    # RF14-06: the ENTIRE existing document -- not just the class/role this write
    # touches -- must validate via `load_model_preference`'s own validators before any
    # merge/re-serialize; a pre-existing invalid entry (e.g. a hand-edited non-list
    # value) must `die()` here rather than reach `_serialize_model_preference`, whose
    # `", ".join(... for token in preference[class_name])` would silently iterate a
    # string value character by character and corrupt the file.
    load_model_preference()
    load_model_pin()  # ADR-0032: [model_pin] is part of the same whole-document check
    doc = _read_model_preference_raw()
    preference = dict(doc.get("preference") or {})
    preference[class_name] = list(validated)
    doc = {**doc, "preference": preference}
    atomic_write(MODEL_PREFERENCE_PATH, _serialize_model_preference(doc))
    if _model_preference_class_inert(class_name):
        print(f"MODEL_PREFERENCE_NOTE class={class_name} has no observable effect on the primary lane today {_MODEL_PREFERENCE_NOTE_SUFFIX}", file=sys.stderr)
    print(f"MODEL_PREFERENCE_SET class={class_name} providers=" + ",".join(validated))
    return 0


def cmd_model_preference_role_override(role, class_name):
    """AC-02: `--model-preference-role-override ROLE CLASS` -- writes/replaces
    `[role_override].<ROLE>`, moving that one role into a different class than AC-01's
    default resolution."""
    roster_roles = {row["role"] for row in models_config.load_roster(ROOT / "roles.tsv")}
    validated_class = _validate_role_override_entry(role, class_name, roster_roles)
    # RF14-06: same fail-closed whole-document validation as cmd_model_preference_set above.
    load_model_preference(roster_roles)
    load_model_pin(roster_roles)  # ADR-0032
    doc = _read_model_preference_raw()
    role_override = dict(doc.get("role_override") or {})
    role_override[role] = validated_class
    doc = {**doc, "role_override": role_override}
    atomic_write(MODEL_PREFERENCE_PATH, _serialize_model_preference(doc))
    if _model_preference_role_inert(role):
        print(f"MODEL_PREFERENCE_NOTE role={role} has no observable effect on the primary lane today {_MODEL_PREFERENCE_NOTE_SUFFIX}", file=sys.stderr)
    print(f"MODEL_PREFERENCE_ROLE_OVERRIDE role={role} class={validated_class}")
    return 0


def cmd_model_preference_show():
    """AC-02 resolution state (e): read-only, prints the sibling file's current, fully-
    resolved `[preference]`/`[role_override]`/`[model_pin]` contents, or a clear
    no-preferences line."""
    data = load_model_preference()
    pins = load_model_pin()
    if not data["preference"] and not data["role_override"] and not pins:
        print("MODEL_PREFERENCE_NONE")
        return 0
    for class_name in sorted(data["preference"]):
        print(f"MODEL_PREFERENCE preference.{class_name}=" + ",".join(data["preference"][class_name]))
    for role in sorted(data["role_override"]):
        print(f"MODEL_PREFERENCE role_override.{role}=" + data["role_override"][role])
    for role in sorted(pins):
        provider, model = pins[role]
        print(f"MODEL_PREFERENCE model_pin.{role}={provider}/{model}")
    return 0


def cmd_model_pin_set(role, target):
    """ADR-0032: `--model-pin-set ROLE PROVIDER/MODEL` — pins ROLE (or the literal `*`
    for the global default) to one catalog identity; the router honors it as a soft
    override (pin > dynamic > curated fallback) and reports MODEL_PINNED /
    MODEL_PIN_UNAVAILABLE in the decision's reason codes."""
    roster_roles = {row["role"] for row in models_config.load_roster(ROOT / "roles.tsv")}
    # ADR-0034 (AC-09): same live-effective-set validation as cmd_model_preference_set.
    provider, model = _validate_model_pin_entry(role, target, roster_roles, _effective_preference_providers())
    # RF14-06: whole-document validation before any merge/re-serialize.
    load_model_preference(roster_roles)
    load_model_pin(roster_roles)
    doc = _read_model_preference_raw()
    model_pin = dict(doc.get("model_pin") or {})
    model_pin[role] = f"{provider}/{model}"
    doc = {**doc, "model_pin": model_pin}
    atomic_write(MODEL_PREFERENCE_PATH, _serialize_model_preference(doc))
    print(f"MODEL_PIN_SET role={role} model={provider}/{model}")
    return 0


def cmd_model_pin_clear(role):
    """ADR-0032: `--model-pin-clear ROLE` — removes ROLE's pin (or `*`'s); an absent pin
    is reported, never an error."""
    roster_roles = {row["role"] for row in models_config.load_roster(ROOT / "roles.tsv")}
    load_model_preference(roster_roles)
    load_model_pin(roster_roles)
    doc = _read_model_preference_raw()
    model_pin = dict(doc.get("model_pin") or {})
    if role not in model_pin:
        print(f"MODEL_PIN_ABSENT role={role}")
        return 0
    del model_pin[role]
    doc = {**doc, "model_pin": model_pin}
    atomic_write(MODEL_PREFERENCE_PATH, _serialize_model_preference(doc))
    print(f"MODEL_PIN_CLEARED role={role}")
    return 0


def routing_catalog(simulation=False):
    """Compose trusted v2 inputs; callers never supply a catalog or route ID."""
    config = models_config.load_config(ROOT / "models.toml")
    roster = models_config.load_roster(ROOT / "roles.tsv")
    config = _config_with_model_preference(config, roster)
    # No optimistic defaults: each real invocation gets a fresh exact probe.
    return routing.compose(config, roster, simulate=simulation, store=None if simulation else _routing_store()), config


def _human_render_value(value, limit=6):
    """D1-F02: render one payload value for the human (non-`--json`) routing channel.
    `print(f"{key}: {value}")`'s plain f-string was `repr()`-ing nested dicts/tuples
    verbatim -- a single `exclusions` entry measured 5763 characters on one line. This
    collapses collections instead of dumping them: booleans read `sí`/`no`, `None` reads
    `-`, and lists/tuples/dicts render as a short comma-joined summary, truncated at
    `limit` items with a `(+N más)` tail rather than printed in full. Recursive so a list
    of dicts (like `exclusions`) renders each dict the same way, not as Python's repr."""
    if isinstance(value, bool):
        return "sí" if value else "no"
    if value is None:
        return "-"
    if isinstance(value, dict):
        if not value:
            return "(vacío)"
        return ", ".join(f"{k}={_human_render_value(v, limit=limit)}" for k, v in value.items())
    if isinstance(value, (list, tuple)):
        if not value:
            return "(vacío)"
        shown = [_human_render_value(item, limit=limit) for item in value[:limit]]
        extra = len(value) - limit
        return ", ".join(shown) + (f", … (+{extra} más)" if extra > 0 else "")
    return str(value)


def _routing_output(payload, human):
    if ROUTING_WARNINGS:
        payload = dict(payload)
        payload["warnings"] = list(dict.fromkeys((*payload.get("warnings", ()), *ROUTING_WARNINGS)))
    if not human:
        print(json.dumps(payload, sort_keys=True))
        return
    # D1-F02: real human text, not repr() dumped through an f-string -- and reason_codes
    # is skipped inside `data` (whenever the underlying dataclass carries its own copy,
    # e.g. RouteDecision.reason_codes surfacing through `to_dict()`) because it is always
    # printed once below from the envelope's own top-level `reason_codes` field, which
    # carries the exact same value every caller passes into `data` (verified: every
    # `cli_envelope(..., data, ..., reason_codes)` call site in this file passes the SAME
    # tuple both places when `data` happens to carry the key). Every line is clamped to
    # the live terminal width (`_term_width()`/`_clip()`, same discipline as the menu
    # panels) so a long collection truncates instead of ever producing a 5763-char line.
    width = _term_width()
    print(_clip(f"{payload['command']}: {'OK' if payload['ok'] else 'NO DISPONIBLE'}", width), file=sys.stderr)
    for key, value in payload["data"].items() if isinstance(payload["data"], dict) else []:
        if key == "reason_codes":
            continue
        print(_clip(f"{key}: {_human_render_value(value)}", width), file=sys.stderr)
    if payload["reason_codes"]:
        print(_clip("reason_codes: " + ", ".join(payload["reason_codes"]), width), file=sys.stderr)


def cmd_route_explain(task_class, human=False):
    if task_class not in routing.TASK_CLASSES:
        _routing_output(routing.cli_envelope(False, "route-explain", {}, (), ("TASK_CLASS_INVALID",)), human); return 2
    try:
        service, _config = routing_catalog(simulation=True)
        role = "architect" if task_class in routing.CRITICAL else ("debugger" if task_class == "incident" else "product-analyst")
        runtime = "codex" if task_class in routing.CRITICAL else "claude-code"
        request = routing.TaskRequest(role=role, operation="inspection" if task_class == "inspection" else "change", task_class=task_class, selected_runtime=runtime)
        facts = service._observe_for_invocation(role=role, operation=request.operation, task_class=task_class,
            read_write="read" if task_class == "inspection" else "write", write_started=False,
            risk="high" if task_class in routing.CRITICAL else "low", criticality=task_class if task_class in routing.CRITICAL else "",
            affected_surfaces=(), required_tools=("read",), context_required=True, context_present=True,
            critical_coverage=True, selected_runtime=runtime)
        decision = service.route(request, facts)
        # Explain is a successful simulation even when execution would be unavailable.
        _routing_output(routing.cli_envelope(True, "route-explain", decision.to_dict(), (), decision.reason_codes), human)
        return 0
    except models_config.ModelsError:
        _routing_output(routing.cli_envelope(False, "route-explain", {}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    except ModelPreferenceError as exc:
        _routing_output(routing.cli_envelope(False, "route-explain", {"message": str(exc)}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    except (routing.RoutingError, OSError):
        _routing_output(routing.cli_envelope(False, "route-explain", {}, (), ("ROUTING_UNAVAILABLE",)), human); return 1


def cmd_routing_report(human=False):
    try:
        report = _routing_store().report()
    except (OSError, routing.RoutingError):
        report = {"retained_events": 0, "p50_ms": None, "p90_ms": None, "reason_codes": ["ROUTING_UNAVAILABLE"]}
    reasons = tuple(report.get("reason_codes", ()))
    warnings = routing.legacy_warnings(STATE_DIR)
    _routing_output(routing.cli_envelope(not reasons, "routing-report", report, warnings, reasons), human)
    return 1 if reasons else 0


def cmd_route_doctor(human=False):
    """ADR-0035 (AC-15): read-only diagnostic -- same one-line envelope discipline as
    `--routing-report`/`--route-decide`, never opens a run, never writes the store or the
    probe cache. Precedent: `cmd_routing_report` above.

    ADR-0043 (022 PKG-3, AC-10): reports on the SAME cache root `--route-decide`
    actually reads/writes now (`_probe_cache_root()`), not the legacy `STATE_DIR` one
    -- this is the surface that used to inspect a file the decider never touched.
    Best-effort prunes the stale legacy sibling on the way (same security discipline
    as `_write_probe_cache`, `prune_legacy_probe_cache`); a failed prune never blocks
    the diagnostic itself."""
    try:
        from routing_core.catalog import prune_legacy_probe_cache, route_doctor
        config = models_config.load_config(ROOT / "models.toml")
        prune_legacy_probe_cache(STATE_DIR)
        report = route_doctor(config, cache_root=_probe_cache_root())
        _routing_output(routing.cli_envelope(True, "route-doctor", report, (), ()), human)
        return 0
    except models_config.ModelsError:
        _routing_output(routing.cli_envelope(False, "route-doctor", {}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    except (routing.RoutingError, OSError):
        _routing_output(routing.cli_envelope(False, "route-doctor", {}, (), ("ROUTING_UNAVAILABLE",)), human); return 1


_RUN_ID = re.compile(r"^run1_[0-9a-f]{32}$")

# routing_cli.py: routing helpers with no dependency on `_routing_store`/`_routing_output`
# (both stay in this file -- see routing_cli.py's own module docstring for why).
from routing_cli import (  # noqa: E402
    _role_class_of, _DECIDE_OK_NON_EXECUTABLE_REASONS, _decide_status, _SAFE_STATE_ID,
    _TERMINAL_FEATURE_PHASES, _TERMINAL_PACKAGE_STATUS, _load_feature_doc, _safe_state_id,
    _validate_context_pack_path, _package_context_ok, _resolve_context_pack,
    _MAX_USAGE_TEXT_LEN, parse_usage,
)

# --------------------------------------------------------------- ADR-0031: decisions log
#
# Every --route-decide (simulate included) appends one JSONL line here, so the 22
# non-writer roles' decisions stop evaporating with the CLI envelope. This is CLI-layer
# observability, NOT the store: it authorizes nothing, the store never touches it, and
# routing.db's frozen schema stays at its pinned version. Best-effort by contract — a
# logging failure can never break the one-JSON-line envelope or the exit code.
# The name deliberately avoids `routing-decisions.json` (legacy set in routing.py).
DECISION_LOG_NAME = "decisions-v1.jsonl"
DECISION_LOG_CAP = 1_000_000  # bytes; single-generation rotation past this


def _decision_log_path() -> Path:
    if ROUTING_TEST_ROOT:
        return Path(ROUTING_TEST_ROOT) / DECISION_LOG_NAME
    # Same fixed production root as RoutingStore (account database, not $HOME), so the
    # sidecar always sits next to routing.db regardless of environment overrides.
    home = Path(pwd.getpwuid(os.getuid()).pw_dir) if os.name == "posix" else Path.home()
    return home / ".local/state/set-agentes/routing-v2" / DECISION_LOG_NAME


def _append_decision_log(entry: dict) -> None:
    try:
        path = _decision_log_path()
        if ROUTING_TEST_ROOT:
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # F-02 (ADR-0032 review repair): NEVER a raw mkdir on the store's root — the
            # store's `_safe_dir` validates leaf 0700 and refuses to adopt a foreign
            # directory, so a umask-permissioned mkdir here would permanently poison
            # every later store open with ROUTING_UNAVAILABLE. `ensure_cache_root()` is
            # the one sanctioned creator (same discipline as the spawn CLIs'
            # `_persist_audit_binding`); best-effort stays best-effort via the except.
            routing.RoutingStore().ensure_cache_root()
        if path.exists() and path.stat().st_size > DECISION_LOG_CAP:
            path.replace(path.with_name(path.name + ".1"))
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
        os.chmod(path, 0o600)  # F-02: same explicit 0600 the store's own files carry
    except (OSError, routing.RoutingError):
        pass


def cmd_route_decide(source, human=False, fresh=False):
    # AC-04 (026-orquestador-elige-modelo P2): `model_request` is the ONE new key -- the
    # closed set stays closed, an unrecognized key stays ROUTING_INPUT_INVALID/rc=2
    # exactly as before (see the `set(doc) - allowed` check below, untouched shape).
    allowed = {"role", "task_class", "risk", "review_of_run_id", "selected_runtime", "feature_id",
               "package_id", "model_request"}
    try:
        raw = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
        doc = json.loads(raw)
        if not isinstance(doc, dict) or set(doc) - allowed: raise ValueError
        role, task_class = doc.get("role"), doc.get("task_class")
        if not isinstance(role, str) or task_class not in routing.TASK_CLASSES: raise ValueError
        req_risk = doc.get("risk", "low"); runtime = doc.get("selected_runtime", "opencode")
        review_of = doc.get("review_of_run_id")
        feature_id = doc.get("feature_id"); package_id = doc.get("package_id")
        for value in (req_risk, runtime) + tuple(v for v in (review_of, feature_id, package_id) if v is not None):
            if not isinstance(value, str) or not value: raise ValueError
        # F01: a descriptor risk/runtime outside the closed enum is a PARSE failure (exit 2
        # ROUTING_INPUT_INVALID) — it never reaches the service to degrade into FACTS_INCOMPLETE.
        if req_risk not in routing.RISK_ORDER or runtime not in routing.SELECTED_RUNTIMES: raise ValueError
        # AC-04: absent key -> `None` (no preference, byte-identical to every pre-AC-04
        # decision); present -> validated "provider/model" -> `(provider, model)`, or this
        # same PARSE-failure/rc=2 path as every other malformed descriptor field above.
        model_request_raw = doc.get("model_request")
        model_request = _validate_model_request(model_request_raw) if model_request_raw is not None else None
    except (OSError, ValueError):
        _routing_output(routing.cli_envelope(False, "route-decide", {}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    try:
        config = models_config.load_config(ROOT / "models.toml")
        roster = models_config.load_roster(ROOT / "roles.tsv")
        row = next((item for item in roster if item["role"] == role), None)
        if row is None:
            _routing_output(routing.cli_envelope(False, "route-decide", {}, (), ("FACTS_INCOMPLETE",)), human); return 1
        role_class = _role_class_of(row)
        # AM-1 (ADR-0006): capability decides write access and tools; task_class decides criticality
        # and the base risk; the descriptor risk can only RAISE (combined in the service); context
        # flags derive from the active package's context pack.
        writer = role_class == "writer"
        criticality = task_class if task_class in routing.CRITICAL else ""
        base_risk = "high" if (criticality or task_class == "incident") else "low"
        needs_context = bool(criticality) or base_risk == "high" or req_risk == "high"
        context_ok, resolved_feature, resolved_package = _resolve_context_pack(feature_id, package_id)
        if needs_context and context_ok is None:
            # F03d: the harness itself could not narrow the default resolution to exactly one
            # actively-executing package — distinct from NO_ELIGIBLE_ROUTE (a real catalog
            # exclusion), and distinct from a resolved-but-missing pack (plain CONTEXT_MISSING).
            data = {"feature_id": resolved_feature, "package_id": resolved_package, "context_ok": None}
            _routing_output(routing.cli_envelope(False, "route-decide", data, (), ("CONTEXT_UNRESOLVED",)), human)
            return 1
        context_flag = bool(context_ok)
        unverified_review = role_class == "review" and not review_of
        simulate = not writer and not (role_class == "review" and review_of)
        config = _config_with_model_preference(config, roster)
        service = routing.compose(config, roster, simulate=simulate, fresh_probes=fresh,
                                  store=None if simulate else _routing_store())
        request = routing.TaskRequest(role=role, operation="inspection" if task_class == "inspection" else "change",
                                      task_class=task_class, risk=req_risk, selected_runtime=runtime)
        facts = service._observe_for_invocation(role=role, operation=request.operation, task_class=task_class,
            read_write="write" if writer else "read", write_started=False,
            risk=base_risk, criticality=criticality, affected_surfaces=(),
            required_tools=("read", "shell", "write") if writer else ("read",),
            context_required=needs_context,
            context_present=context_flag, critical_coverage=context_flag, selected_runtime=runtime)
        decision = service.route(request, facts, review_of, unverified_review=unverified_review,
                                 model_request=model_request)
        tier = next((r.tier for r in service.snapshot.routes if r.route_id == decision.route_id), None)
        data = decision.to_dict(); data["tier"] = tier; data["role_class"] = role_class
        # F03: the effective (feature_id, package_id, context_ok) is always in the envelope,
        # even when context wasn't needed, for audit.
        data["feature_id"] = resolved_feature; data["package_id"] = resolved_package; data["context_ok"] = context_flag
        # ADR-0031: mint a per-decision id (parallel to run1_/proj1_) and append the whole
        # decision to the sidecar log — simulate included, which is exactly the class of
        # decision that previously left no durable trace (store=None above stays as-is).
        decision_id = "dec1_" + secrets.token_hex(16)
        data["decision_id"] = decision_id
        # ADR-0032: which of the selection paths produced this identity — "pin" (a user
        # [model_pin] override was selected) or "dynamic" (the router's own pick; a
        # configured-but-ineligible pin shows up as MODEL_PIN_UNAVAILABLE in
        # reason_codes and still counts as dynamic). The THIRD path, the curated static
        # fallback, only exists at materialization time and is recorded on the spawn
        # record as MODEL_STATIC_FALLBACK (ADR-0030), never here.
        selection_path = ("pin" if any(code.startswith("MODEL_PINNED") for code in decision.reason_codes)
                          else "dynamic")
        data["selection_path"] = selection_path
        ok, exit_code = _decide_status(decision)
        _append_decision_log({
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "decision_id": decision_id, "run_id": data.get("run_id"),
            "project_key": PROJECT_KEY, "role": role, "task_class": task_class,
            "risk": req_risk, "role_class": role_class, "simulate": simulate,
            "route_id": data.get("route_id"), "runtime": data.get("runtime"),
            "provider": data.get("provider"), "model": data.get("model"),
            "family": data.get("family"), "effort": data.get("effort"), "tier": tier,
            "feature_id": resolved_feature, "package_id": resolved_package,
            "reason_codes": list(decision.reason_codes),
            "execution_enabled": bool(data.get("execution_enabled")),
            "selection_path": selection_path,
        })
        _routing_output(routing.cli_envelope(ok, "route-decide", data, (), decision.reason_codes), human)
        return exit_code
    except models_config.ModelsError:
        _routing_output(routing.cli_envelope(False, "route-decide", {}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    except ModelPreferenceError as exc:
        _routing_output(routing.cli_envelope(False, "route-decide", {"message": str(exc)}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    # SEC-A02: any unvalidated internal edge (a malformed feature-state.json field, an
    # out-of-range value reaching the store) degrades to ROUTING_UNAVAILABLE — never an
    # uncaught traceback breaking the schema-2 envelope / one-JSON-line contract.
    except (routing.RoutingError, OSError, TypeError, ValueError, OverflowError):
        _routing_output(routing.cli_envelope(False, "route-decide", {}, (), ("ROUTING_UNAVAILABLE",)), human); return 1


def _lifecycle_command(name, run_id, action, human):
    if not isinstance(run_id, str) or not _RUN_ID.fullmatch(run_id):
        _routing_output(routing.cli_envelope(False, name, {}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    try:
        result = action(_routing_store())
        _routing_output(routing.cli_envelope(True, name, result, (), ()), human); return 0
    except routing.RoutingError as exc:
        _routing_output(routing.cli_envelope(False, name, {}, (), (str(exc),)), human); return 1
    except (OSError, TypeError, ValueError, OverflowError):
        _routing_output(routing.cli_envelope(False, name, {}, (), ("ROUTING_UNAVAILABLE",)), human); return 1


def cmd_route_dispatched(run_id, human=False):
    def action(store):
        store.mark_dispatched(run_id); return {"run_id": run_id, "state": "dispatched"}
    return _lifecycle_command("route-dispatched", run_id, action, human)


def cmd_route_quota_exhausted(run_id, quota_error_text, latency_ms, usage_text=None, human=False):
    try:
        error = parse_usage(quota_error_text)
        usage = parse_usage(usage_text) if usage_text is not None else None
    except ValueError:
        _routing_output(routing.cli_envelope(False, "route-quota-exhausted", {}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    if classify_pi_terminal_error(error) != "quota_exhausted":
        _routing_output(routing.cli_envelope(False, "route-quota-exhausted", {}, (), ("AUTHORIZATION_INVALID",)), human); return 1
    def action(store):
        replacement = store.close_exhausted_and_authorize_replacement(run_id, "quota_exhausted", usage, latency_ms)
        return {"run_id": run_id, "state": "terminal_failure", "outcome": "quota_exhausted",
                "replacement_run_id": replacement["run_id"], "replacement_existing": replacement["existing"],
                "replacement_provider": replacement.get("provider"), "replacement_model": replacement.get("model")}
    return _lifecycle_command("route-quota-exhausted", run_id, action, human)


def cmd_quota_failover_e2e():
    """AC-06's deliberately separate live-provider gate.

    This harness never manufactures an exhausted subscription, credentials, or provider
    inventory.  Until an operator supplies and independently verifies that controlled
    environment, the only honest outcome is blocked; in particular this command must not
    become a green mock/simulation shortcut for the real failure path.
    """
    print(json.dumps({"status": "BLOCKED", "reason": "HUMAN_DECISION_REQUIRED",
                      "gate": "AC-06", "detail": "controlled exhausted subscription not verified"},
                     sort_keys=True))
    return 3


_LATENCY_MAX = 2**31 - 1


def cmd_route_terminal(run_id, outcome, latency_ms, usage_text=None, human=False):
    if outcome not in {"success", "failure"}:
        _routing_output(routing.cli_envelope(False, "route-terminal", {}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    # SEC-A02: bound --latency-ms at the CLI, before it ever reaches the store — an
    # out-of-range value (overflow) or a negative one (would decrement rollup sums) is a
    # PARSE failure, not a runtime one.
    if latency_ms is not None and (isinstance(latency_ms, bool) or not isinstance(latency_ms, int)
                                   or not (0 <= latency_ms <= _LATENCY_MAX)):
        _routing_output(routing.cli_envelope(False, "route-terminal", {}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    # AC-11: malformed (unparseable) --usage is a PARSE failure at the CLI, same edge as
    # --latency-ms above. Anything parseable but untrustworthy is the STORE's edge
    # (close_run/_usage_row), never rejected here. "There is nothing to protect" was this
    # comment's claim before N-01 (delta review): a dict always serializes to valid JSON,
    # so malformed input is unreachable from route_and_spawn's production wiring either
    # way -- but a legitimate, merely-large usage object is reachable from it, and that
    # case is not "nothing to protect" (see parse_usage's docstring and ADR-0010 D3).
    usage = None
    if usage_text is not None:
        try:
            usage = parse_usage(usage_text)
        except ValueError:
            _routing_output(routing.cli_envelope(False, "route-terminal", {}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    def action(store):
        # F02: ONE transaction reads the state and transitions to exactly the right
        # destination (dispatched->terminal, authorized+failure->abandoned, anything else a
        # single rejected/STATE_CONFLICT) — never a try-terminal-then-except-abandon pair of
        # independent transactions, which left a spurious rejected row behind a successful
        # abandon and wrote two rejected rows for an unclosable run.
        state = store.close_run(run_id, outcome, latency_ms, usage=usage)
        return {"run_id": run_id, "state": state}
    return _lifecycle_command("route-terminal", run_id, action, human)


def cmd_routing_open_runs(human=False):
    try:
        data = {"open_runs": _routing_store().open_runs()}
        _routing_output(routing.cli_envelope(True, "routing-open-runs", data, (), ()), human); return 0
    except (routing.RoutingError, OSError):
        _routing_output(routing.cli_envelope(False, "routing-open-runs", {}, (), ("ROUTING_UNAVAILABLE",)), human); return 1


def cmd_routing_recent_writers(human=False):
    try:
        data = {"recent_writers": _routing_store().recent_writers()}
        _routing_output(routing.cli_envelope(True, "routing-recent-writers", data, (), ()), human); return 0
    except (routing.RoutingError, OSError):
        _routing_output(routing.cli_envelope(False, "routing-recent-writers", {}, (), ("ROUTING_UNAVAILABLE",)), human); return 1


def cmd_routing_decisions(limit=50, human=False):
    """ADR-0031: read-only tail of the per-decision sidecar log, filtered to this
    project. Missing/empty log is a legitimate zero, never an error; malformed lines
    (a torn write in a best-effort append-only file) are skipped, not fatal."""
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        _routing_output(routing.cli_envelope(False, "routing-decisions", {}, (), ("ROUTING_INPUT_INVALID",)), human); return 2
    try:
        decisions = []
        path = _decision_log_path()
        if path.exists():
            for raw in path.read_text(encoding="utf-8").splitlines():
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    entry = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(entry, dict) and entry.get("project_key") == PROJECT_KEY:
                    decisions.append(entry)
        data = {"decisions": decisions[-limit:]}
        _routing_output(routing.cli_envelope(True, "routing-decisions", data, (), ()), human); return 0
    except OSError:
        _routing_output(routing.cli_envelope(False, "routing-decisions", {}, (), ("ROUTING_UNAVAILABLE",)), human); return 1


def cmd_doctor(harness, human=False):
    """AC-09: `--doctor --harness pi` — a redacted schema-2 envelope (pinned version,
    auth.json KEY-SET, `pi --list-models` OK/FAIL). Never prints credential contents.
    Only `--harness pi` is specified by this package; any other/absent harness is a
    parse-time input error, not a routing decision."""
    if harness != "pi":
        _routing_output(routing.cli_envelope(False, "doctor", {}, (), ("DOCTOR_HARNESS_UNSUPPORTED",)), human); return 2
    report = set_agents_spawn.doctor()
    ok = bool(report.get("doctor_green"))
    _routing_output(routing.cli_envelope(ok, "doctor", report, (), () if ok else ("PI_DOCTOR_NOT_GREEN",)), human)
    return 0 if ok else 1


def _pi_lane_state():
    """pi has no global binary by design: it resolves via `pnpm dlx` against the
    pin in routing_core/catalog.py, so pnpm present == lane installable. A bare
    which("pi") was a structural false negative on every fresh machine."""
    if shutil.which("pi"):
        return "yes"
    if shutil.which("pnpm"):
        return "via-pnpm-dlx"
    return "no"


def _install_scope():
    scope_path = STATE_DIR / "install-targets.json"
    if not scope_path.exists():
        return None
    try:
        return sorted(t for t in json.loads(scope_path.read_text()) if isinstance(t, str))
    except (OSError, json.JSONDecodeError):
        return "unreadable"


def cmd_doctor_all():
    """017/AC-02: qué tiene esta máquina y qué va a usar el harness — harnesses
    instalados, scope de instalación, CLIs del catálogo, y proveedores/modelos
    realmente autenticados (probe con cache; nunca imprime credenciales).

    ADR-0043 (022 PKG-3, AC-10): probes against the SAME cache root `--route-decide`
    uses (`_probe_cache_root()`), never the legacy `STATE_DIR` one, and best-effort
    prunes the stale legacy sibling on the way (same discipline as
    `_write_probe_cache`).

    AC-19 (022 PKG-5): `listed_by_provider` (raw, pre-ceiling) is reported alongside
    `usable_after_ceiling` (post-ceiling, actually routable) -- the OLD `models=<N>` line
    printed the ceiling-applied count under a name that read as "what the provider
    exposes"; a provider that lists models the curated ceiling drops entirely used to be
    invisible here (`if models:` on the ceiling-applied set alone), which is exactly the
    "listado != usable" defect this AC exists to surface, not hide."""
    from routing_core.catalog import prune_legacy_probe_cache, probe_listed_and_usable
    for harness, cli in (("claude-code", "claude"), ("opencode", "opencode"), ("codex", "codex")):
        print(f"HARNESS {harness} installed={'yes' if shutil.which(cli) else 'no'}")
    print(f"HARNESS pi installed={_pi_lane_state()}")
    scope = _install_scope()
    if scope is None:
        print("INSTALL_SCOPE all (sin registro: instalación previa a 017 o nunca instalado)")
    elif scope == "unreadable":
        print("INSTALL_SCOPE unreadable")
    else:
        print("INSTALL_SCOPE " + (",".join(scope) or "none"))
    for name, installed in _tools_data():
        print(f"TOOL {name} installed={'yes' if installed else 'no'}")
    try:
        config = models_config.load_config()
    except SystemExit:
        print("PROVIDERS_UNKNOWN models.toml inválido — corré ./build.sh --check")
        return 1
    prune_legacy_probe_cache(STATE_DIR)
    listed, usable = probe_listed_and_usable(config, cache_root=_probe_cache_root())
    all_pairs = sorted(set(listed) | set(usable))
    if not all_pairs:
        print("PROVIDERS_NONE no se detectó ninguna suscripción activa (claude/codex/opencode/pi) — "
              "logueate en al menos una herramienta y volvé a correr set-agents --doctor-all")
    for (runtime, provider) in all_pairs:
        listed_n = len(listed.get((runtime, provider), set()))
        usable_n = len(usable.get((runtime, provider), set()))
        print(f"PROVIDER {provider} runtime={runtime} listed_by_provider={listed_n} usable_after_ceiling={usable_n}")
    return 0


def use_color():
    return sys.stdout.isatty() and not os.environ.get("NO_COLOR") and os.environ.get("TERM") != "dumb"


def color(text, code):
    return f"\033[{code}m{text}\033[0m" if use_color() else text


def bold(text):
    return color(text, "1")


def dim(text):
    return color(text, "2")


# --------------------------------------------------------------------- banner

# Two-row half-block wordmark; per-character truecolor gradient cyan -> violet.
WORDMARK = (
    "█▀▀ █▀▀ ▀█▀ ▄▄ ▄▀▄ █▀▀ █▀▀ █▄ █ ▀█▀ █▀▀",
    "▄▄█ █▄▄  █     █▀█ █▄█ █▄▄ █ ▀█  █  ▄▄█",
)
GRADIENT = ((0, 229, 255), (167, 80, 255))
# The app's motif: three agent nodes (one per harness) wired into one system.
NODES = (("opencode", "38;2;77;208;225"), ("claude", "38;2;217;119;87"), ("codex", "38;2;120;220;120"))


def _lerp(t):
    (r1, g1, b1), (r2, g2, b2) = GRADIENT
    return (round(r1 + (r2 - r1) * t), round(g1 + (g2 - g1) * t), round(b1 + (b2 - b1) * t))


def _gradient_row(row, offset):
    width = max(1, len(row) - 1)
    out = []
    for index, char in enumerate(row):
        if char == " ":
            out.append(char)
            continue
        r, g, b = _lerp(min(1.0, (index + offset) / width))
        out.append(f"\033[38;2;{r};{g};{b}m{char}")
    return "".join(out) + "\033[0m"


def banner():
    if not use_color():
        print("SET-AGENTS — opencode · claude · codex")
        return
    node_rows = [
        f"  \033[{code}m●\033[0m \033[2m{name:<8}\033[0m" for name, code in NODES
    ]
    wire = ["─┐", "─┤", "─┘"]
    rows = [
        f"{node_rows[0]}\033[2m{wire[0]}\033[0m   {_gradient_row(WORDMARK[0], 0)}",
        f"{node_rows[1]}\033[2m{wire[1]}\033[0m   {_gradient_row(WORDMARK[1], 6)}",
        f"{node_rows[2]}\033[2m{wire[2]}\033[0m   " + dim("un comando · tres agentes · cero drift"),
    ]
    print("\n".join(rows))


def platform_label():
    if sys.platform == "darwin":
        return "macOS"
    try:
        if "microsoft" in Path("/proc/version").read_text().lower():
            return "WSL"
    except OSError:
        pass
    return "Linux"


def first_run():
    return not APP_CONFIG.exists()


# ---------------------------------------------------------------- app config

def app_config():
    try:
        return tomllib.loads(APP_CONFIG.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def auto_update_enabled():
    return app_config().get("auto_update", True)


def write_app_config(**updates):
    """Read-merge-write over app_config() — the ONE writer every config mutation goes through
    (AC-15). A raw `APP_CONFIG.write_text(...)` anywhere else would silently clobber whatever
    this call didn't know about (e.g. a `vault` key persisted by a prior, unrelated run)."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    config = {**app_config(), **updates}
    lines = [
        f"{key} = {'true' if value else 'false'}" if isinstance(value, bool) else f"{key} = {json.dumps(value)}"
        for key, value in sorted(config.items())
    ]
    APP_CONFIG.write_text("\n".join(lines) + "\n")
    return config


def set_auto_update(enabled):
    write_app_config(auto_update=enabled)
    print(f"AUTO_UPDATE={'on' if enabled else 'off'}")


# ----------------------------------------------------------------------- git

def git(*args, timeout=None):
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True, text=True, timeout=timeout, check=False,
        # Never let git throw an interactive credential prompt at a captured TTY.
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


# AC-12 (024/C4): a GitHub fork's `origin` is the fork's OWN copy, not the project this harness
# ships from -- comparing against a hardcoded "origin/main" then measures "commits behind my own
# fork", not "commits behind the real upstream". Re-pointable via SET_AGENTS_UPSTREAM (e.g.
# "upstream/main" after `git remote add upstream https://github.com/federico0330/set-agents.git`);
# DEFAULT_UPSTREAM is the fallback, so a direct clone (this repo's own README instructions, where
# `origin` already IS upstream) keeps behaving exactly as before.
DEFAULT_UPSTREAM = "origin/main"


def upstream_ref():
    return os.environ.get("SET_AGENTS_UPSTREAM") or DEFAULT_UPSTREAM


def _upstream_remote_and_branch():
    remote, _, branch = upstream_ref().partition("/")
    return remote, branch or "main"


def fetch(timeout=10):
    remote, _branch = _upstream_remote_and_branch()
    try:
        return git("fetch", "--quiet", remote, timeout=timeout).returncode == 0
    except subprocess.TimeoutExpired:
        return False


def short_sha():
    result = git("rev-parse", "--short", "HEAD")
    return result.stdout.strip() if result.returncode == 0 else "?"


def rev_count(spec):
    result = git("rev-list", "--count", spec)
    return int(result.stdout.strip()) if result.returncode == 0 else None


def tree_clean():
    return git("status", "--porcelain").stdout.strip() == ""


# -------------------------------------------------------------------- status

def drift_state():
    script = ROOT / "ai/scripts/check-drift.sh"
    if not script.is_file():
        return "unknown"
    result = subprocess.run([str(script), "--quiet"], capture_output=True, text=True, check=False)
    return {0: "ok", 1: "stale"}.get(result.returncode, "unknown")


# F-04: both remote CLI probes get an explicit timeout -- without one, a scripted
# `set-agents --status` (or the menu's status branch) can hang indefinitely on a wedged
# `opencode auth list`/`codex login status` instead of degrading to "needed" like `version_of`
# already does for a wedged `--version`.
AUTH_STATE_TIMEOUT_SECONDS = 15


def auth_state(cli):
    if not shutil.which(cli):
        return "missing"
    if cli == "opencode":
        try:
            result = subprocess.run(
                ["opencode", "auth", "list"], capture_output=True, text=True,
                timeout=AUTH_STATE_TIMEOUT_SECONDS, check=False,
            )
        except subprocess.TimeoutExpired:
            return "needed"
        return "ok" if result.returncode == 0 and result.stdout.strip() else "needed"
    if cli == "codex":
        try:
            result = subprocess.run(
                ["codex", "login", "status"], capture_output=True,
                timeout=AUTH_STATE_TIMEOUT_SECONDS, check=False,
            )
        except subprocess.TimeoutExpired:
            return "needed"
        return "ok" if result.returncode == 0 else "needed"
    # claude: no stable status command; same heuristic install.sh uses.
    credentials = Path.home() / ".claude/.credentials.json"
    return "ok" if credentials.exists() and credentials.stat().st_size > 0 else "needed"


def version_of(cli):
    try:
        out = subprocess.run([cli, "--version"], capture_output=True, text=True, timeout=15, check=False).stdout
        return out.strip().splitlines()[0] if out.strip() else "?"
    except (OSError, subprocess.TimeoutExpired):
        return "?"


def _status_data(*, rows=True):
    """AC-28: the data cmd_status() prints from -- both the one-line machine summary and the
    human table rows, so a caller (the menu, a future non-print consumer) never has to re-derive
    what cmd_status() already computed.

    F-04: `rows` is lazy on purpose -- the per-CLI table (`version_of`/`auth_state`, up to 6
    subprocess probes) is ONLY needed for the human-readable render. `cmd_status(human=False)`
    (the scripted/piped `set-agents --status` path) must stay as cheap as it was before the
    data/print split -- it never calls this with `rows=True`.
    """
    data = {
        "sha": short_sha(), "drift": drift_state(), "behind": rev_count(f"HEAD..{upstream_ref()}"),
        "auto_update": auto_update_enabled(), "rows": [],
    }
    if rows:
        for cli in HARNESS_CLIS:
            installed = shutil.which(cli)
            version = version_of(cli) if installed else "FALTA"
            data["rows"].append((cli, version, auth_state(cli) if installed else "-"))
    return data


def _status_machine_line(data):
    return (
        f"APP_STATUS sha={data['sha']} drift={data['drift']} "
        f"update={data['behind'] if data['behind'] is not None else '?'} "  # cached; --check-update fetches
        f"auto_update={'on' if data['auto_update'] else 'off'}"
    )


def _status_table_lines(data):
    """AC-28/F-03: the human table's lines, shared between `cmd_status(human=True)`'s own print
    and `menu()`'s status branch, which ALSO needs this exact text as the toggle picker's
    `header=` (F-03) so it survives the alternate-screen switch instead of being erased."""
    lines = [f"{'CLI':<10} {'VERSIÓN':<28} AUTH"]
    for cli, version, auth in data["rows"]:
        lines.append(f"{cli:<10} {version:<28} {auth}")
    if data["drift"] == "stale":
        # F-09: "Instalar / Reparar" is the actual menu item label now (arrow-key selector,
        # no numbered grid) -- "opción [1]" stopped meaning anything the day the grid did.
        lines.append("")
        lines.append("drift: la instalación quedó atrás del repo → Instalar / Reparar o ./build.sh --install")
    return lines


def cmd_status(human=False):
    data = _status_data(rows=human)
    print(_status_machine_line(data))
    if not human:
        return 0
    print()
    for line in _status_table_lines(data):
        print(line)
    return 0


# -------------------------------------------------------------------- update

def cmd_check_update():
    online = fetch()
    behind = rev_count(f"HEAD..{upstream_ref()}")
    suffix = "" if online else " (sin red: valor cacheado)"
    print(f"UPDATE_AVAILABLE={behind if behind is not None else '?'}{suffix}")
    return 0 if behind is not None else 2


def cmd_update(yes=False, no_install=False, assume_fetched=False):
    if not tree_clean():
        print("UPDATE_BLOCKED: hay cambios locales sin commitear — resolvelos y reintentá.")
        return 1
    if not assume_fetched:
        fetch()
    ref = upstream_ref()
    behind = rev_count(f"HEAD..{ref}")
    ahead = rev_count(f"{ref}..HEAD")
    if behind is None:
        print("UPDATE_BLOCKED: no pude determinar el estado remoto.")
        return 2
    if behind == 0:
        print("UPDATE_AVAILABLE=0")
        return 0
    if ahead:
        print(f"UPDATE_BLOCKED: historia divergida ({ahead} commits locales) — resolvé a mano.")
        return 1
    old = short_sha()
    print(f"Novedades ({behind} commits):")
    print(git("log", "--oneline", f"HEAD..{ref}").stdout.rstrip())
    remote, branch = _upstream_remote_and_branch()
    try:
        pull = git("pull", "--ff-only", remote, branch, timeout=180)
    except subprocess.TimeoutExpired:
        print("UPDATE_BLOCKED: git pull colgado (¿red o credenciales? probá `gh auth status`).")
        return 1
    if pull.returncode != 0:
        print(f"UPDATE_BLOCKED: git pull falló:\n{pull.stderr.strip()}")
        return 1
    print(f"UPDATE_APPLIED {old}..{short_sha()}")
    if no_install:
        return 0
    install = [str(ROOT / "build.sh"), "--install"]
    if yes:
        install.append("--yes")
    # No capture: build.sh shows the managed diff and asks on the caller's TTY (AC-26).
    with tui.suspend_terminal():
        return subprocess.run(install, check=False).returncode


def launch_update_check():
    """Menu-open behavior: auto-update with notice, or just a badge."""
    online = fetch(timeout=6)
    ref = upstream_ref()
    behind = rev_count(f"HEAD..{ref}")
    if not online and behind is None:
        return "sin red o sin acceso (probá `gh auth status`)"
    if not behind:
        return "al día"
    if not auto_update_enabled():
        # F-09: "Actualizar" is the actual menu item label -- "opción [2]" is a numbered-grid
        # reference that stopped being true the day the grid was replaced by the arrow selector.
        return f"{behind} commits nuevos (auto-update off → Actualizar)"
    if not tree_clean() or rev_count(f"{ref}..HEAD"):
        return f"{behind} commits nuevos (repo local con cambios → Actualizar)"
    print(bold(f"Actualización disponible ({behind} commits) — aplicando automáticamente…"))
    cmd_update(yes=True, assume_fetched=True)
    return "al día (recién actualizado)"


# --------------------------------------------------------------------- tools

def _load_local_catalog():
    """ADR-0038: `tools.local.toml` is the untracked, optional overlay `--tools-approve`
    writes to. Its absence can never fail (same never-fails contract as `notes_root`,
    `render_notes.py:37`) -- a repo without it is just "curated catalog only", and a file
    that fails to parse degrades the same way rather than crashing every `--tools` call.

    F-04 repair: "degrades" no longer means SILENTLY -- a parse error used to disappear
    into a bare `except: return {}`, so a two-line `--why` that corrupted this exact file
    (see `_toml_str`'s docstring) made every previously-approved tool vanish from `--tools`
    with `rc=0` and no trace at all. A warning to stderr is cheap and turns "the catalog
    is mysteriously empty" into "here is the file and the exact reason it didn't parse".

    F-06 repair: the never-fails contract was false for input that PARSES fine but is
    shaped wrong -- a stray top-level scalar (`oops = 1`) or a section entry that isn't
    itself a table used to reach `load_catalog`/`_tools_header`/`tools_menu`/the state
    panel as a bare `AttributeError` (`int`/`str` has no `.items()`/`.get()`), not a
    graceful degrade. Every level this function indexes into is shape-checked; anything
    that doesn't look like `{kind: {name: {...}}}` is dropped, never crashed on.

    F-06 repair, round 2 (REABIERTO): being a well-formed TABLE (round 1's check) isn't
    enough -- an entry missing `detect`/`install`, or carrying either with the wrong
    type, is still a dict and used to sail straight through into `_tools_data`
    (`entry["detect"]`) and `cmd_tools_install` (`entry["detect"]` then
    `entry["install"]`) as a bare `KeyError`, which propagates to every caller of
    `_tools_data` too (`tools_menu`, the state panel). Every kind `--tools-approve`
    writes uses the SAME uniform schema (ADR-0038 §7, `_dump_toml_catalog`'s own
    docstring: detect + install, never the curated mcp-native type/command/url) -- this
    is safe to enforce for every kind in THIS file, not just `cli`, and any entry that
    doesn't match is dropped with a warning instead of crashing something downstream."""
    path = ROOT / "tools.local.toml"
    if not path.is_file():
        return {}
    try:
        raw = tomllib.loads(path.read_text())
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        print(f"WARNING: {path} no se pudo leer ({exc}) -- el catálogo local se ignora "
              f"hasta que se corrija o se borre el archivo", file=sys.stderr)
        return {}
    if not isinstance(raw, dict):
        return {}
    catalog = {}
    for kind, entries in raw.items():
        if kind not in _TOOL_KINDS or not isinstance(entries, dict):
            continue
        section = {}
        for name, entry in entries.items():
            if not isinstance(entry, dict):
                continue
            if not _valid_local_entry_shape(entry):
                print(f"WARNING: {path} [{kind}.{name}] ignorada -- falta 'detect' o "
                      f"'install' (o no tienen el tipo esperado); corregí o borrá esa "
                      f"entrada", file=sys.stderr)
                continue
            section[name] = entry
        if section:
            catalog[kind] = section
    return catalog


def _valid_local_entry_shape(entry):
    """F-06 repair, round 2: `detect` must be a non-empty string and `install` a
    non-empty dict of string -> string -- the exact shape `cmd_tools_approve` always
    writes (see `_load_local_catalog`'s own docstring on why this applies to every
    kind, not just cli). Anything else is a well-formed TOML table that is still the
    wrong shape for what `_tools_data`/`cmd_tools_install`/`_tools_header` index into."""
    if not isinstance(entry.get("detect"), str) or not entry["detect"].strip():
        return False
    install = entry.get("install")
    if not isinstance(install, dict) or not install:
        return False
    return all(isinstance(method, str) and isinstance(cmd, str) for method, cmd in install.items())


def load_catalog():
    """AC-31/ADR-0038 §6: merges the curated `tools.toml` with the optional local overlay.
    On a name collision the CURATED entry always wins (silently, here) -- a local catalog
    must never be able to shadow e.g. `vercel`. This is defense in depth for a hand-edited
    `tools.local.toml`; the normal path (`cmd_tools_approve`) refuses the collision outright
    at write time instead of ever producing an entry this merge would just hide."""
    curated = tomllib.loads((ROOT / "tools.toml").read_text())
    for section, entries in _load_local_catalog().items():
        merged = dict(curated.get(section, {}))
        for name, entry in entries.items():
            merged.setdefault(name, entry)
        curated[section] = merged
    return curated


def _is_local_only_entry(kind, name):
    """NEW-01 repair (delta review round 2, high): tells apart a catalog entry that comes
    from the CURATED, reviewed, git-tracked `tools.toml` from one that only exists because
    of the untracked `tools.local.toml` overlay (.gitignore'd -- no gate or review ever
    sees it, and a hand edit to it never passes through `_validate_proposal`/
    `_validate_install_command`, unlike the normal `--tools-approve` write path). Mirrors
    `load_catalog()`'s own curated-wins collision rule byte for byte: a name present in
    BOTH is curated for every purpose, including this one -- never treated as local just
    because a local block with that name also exists."""
    curated = tomllib.loads((ROOT / "tools.toml").read_text())
    if name in curated.get(kind, {}):
        return False
    return name in _load_local_catalog().get(kind, {})


# ---------------------------------------------------- tools discovery (ADR-0038, AC-30/31)

_TOOL_KINDS = ("cli", "mcp", "skill")
# Mirrors pick_method()/tools.toml's real vocabulary -- the closed set of installer
# methods a proposed `--install-<method>` may name.
_INSTALL_METHODS = ("pacman", "apt", "dnf", "zypper", "brew", "winget", "choco", "npm", "curl")

# ADR-0038 §3 (F-03 repair): privilege-escalation binaries rejected by BASENAME of every
# shlex token, never a whitespace-boundary regex on the raw string -- `/usr/bin/sudo` has
# no whitespace before "sudo" (preceded by "/"), so a `(?:^|\s)sudo(?:\s|$)` regex (the
# old `_SUDO_RE`) never saw it, and neither did `doas`/`pkexec`/`su -c`/`runas`. Shared by
# _validate_install_command (propose/approve, rejects outright) AND cmd_tools_install's
# own sudo-detection (:~1544, ownership exception approved for F-03 -- see
# ai/state/decisions-log.jsonl slug p5-repair-excepciones-y-diseno): that branch keeps
# showing the exact command and asking, even under --yes, for every name here, not just
# a literal `sudo ` prefix.
# OBS-3 (delta review round 2, low, fixed): `sudoedit`/`run0`/`please` were missing --
# all three escalate privileges the same way the original five do.
_PRIVILEGE_ESCALATORS = frozenset(
    {"sudo", "sudoedit", "doas", "pkexec", "su", "runas", "run0", "please"})


def _cmd_privilege_escalator(cmd):
    """Returns the escalator binary name (e.g. "sudo") found anywhere in `cmd`'s tokens,
    or None. Tokenizes with shlex (so a quoted argument that merely CONTAINS the word
    "sudo" inside a longer string doesn't false-positive) and compares each token's
    basename -- not the raw token -- against `_PRIVILEGE_ESCALATORS`, which is what
    catches a path-qualified `/usr/bin/sudo` a bare-word check misses. Checked in EVERY
    token position (`env sudo ...` too), not only the first, matching what the old
    whitespace-boundary regex already did for the plain-word case.

    OBS-2 (delta review round 2, low, fixed): the basename comparison is case-INsensitive
    (`.lower()`) -- irrelevant on a case-sensitive filesystem (the real `sudo` binary is
    always lowercase on Linux) but relevant on a case-insensitive one (macOS default
    APFS/HFS+, Windows), where `SUDO apt install evil` would otherwise resolve to the
    same file and slip past an exact-case check. `_PRIVILEGE_ESCALATORS` itself stays
    all-lowercase; only the comparison is case-folded, so the set never needs every
    case variant enumerated."""
    try:
        tokens = shlex.split(cmd)
    except ValueError:
        # Unbalanced quotes etc. -- _ALLOWED_CMD_CHARS_RE below already excludes quote
        # characters entirely for _validate_install_command's caller, so this path is
        # unreachable there; kept defensive since cmd_tools_install's caller is the
        # already-catalogued tools.toml/tools.local.toml, not fresh untrusted input.
        return None
    for token in tokens:
        basename = os.path.basename(token)
        if basename.lower() in _PRIVILEGE_ESCALATORS:
            return basename
    return None


# ADR-0038 §3 (F-01 repair): an ALLOWLIST of characters, never a denylist of remembered
# shell metacharacters. The old denylist (`_SHELL_METACHAR_RE`/`_REDIRECT_RE`) enumerated
# `;`, `&&`, `||`, backtick, `$(`, `>`, `<` -- and never a bare `&`, which is a full
# statement separator in `bash -c` exactly like `;` is. A denylist only ever rejects what
# someone thought to type; an allowlist rejects everything it doesn't recognize. This set
# is exactly what this repo's own curated `tools.toml` install commands use: letters,
# digits, a literal space, and the narrow punctuation real package-manager/curl/npm
# invocations need (path separators, flags, versions, npm `@scope/pkg`, URLs). Every shell
# control character a `bash -c` string could use to compose a second command is excluded
# by construction: `;`, `&`, backtick, `$`, `(`, `)`, `<`, `>`, `!`, `*`, `?`, `[`, `]`,
# `{`, `}`, `\`, `%`, `#`, quotes, and every ASCII control character (newline included).
# `|` stays IN this set only because the dedicated pipe-shape check right below
# re-validates it strictly (curl|wget ... | bash|sh, one pipe, nothing else) -- every
# other still-dangerous character never reaches that far.
# OBS-1 (delta review round 2, low, fixed): checked with `.fullmatch()`, not `.match()`
# -- `$` matches at the end of the string OR just before a single trailing newline, so
# `.match()` accepted a command with exactly one bare `\n` appended. Not independently
# exploitable (anything meaningful appended after that newline would itself break the
# match, and `_toml_str` escapes any newline that does reach the TOML writer), but
# `fullmatch` closes it for free -- Python's own docs recommend `fullmatch` over a
# `match()` + `$` combination for exactly this reason.
_ALLOWED_CMD_CHARS_RE = re.compile(r"^[A-Za-z0-9 @+,\-./:=_~|]+$")
# F-04 repair: `--why`/`--detect` are free text (unlike `<cmd>`, which has its own
# narrower allowlist above), but they still end up as TOML string VALUES via
# `_toml_str`/`_dump_toml_catalog` -- reject any ASCII control character (newline
# included) at the source instead of relying solely on `_toml_str`'s escaping. Fail
# fast with a clear error beats silently turning a two-line reason into an escaped,
# ugly-but-technically-valid TOML string.
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")
# The ONE legitimate pipe shape this repo's own curated catalog already uses
# (tools.toml [cli.gcloud.install] curl = "curl -sSL ... | bash") -- a single trailing
# pipe from a known fetch tool into a plain shell interpreter, nothing else.
# OBS-4 (delta review round 2, low, fixed): `\b` is a WORD boundary, not a "real binary
# name" boundary -- "curl.evil -x | bash" has a `.` right after "curl", which IS a word
# boundary (word char "l" -> non-word char "."), so the old regex accepted any binary
# whose name merely STARTS WITH "curl"/"wget". Require actual whitespace right after the
# fetch tool's name instead (every real invocation in this catalog looks like
# "curl <flags/url>...", never "curl<anything>") -- `curlish`/`curl.evil` no longer
# match, `curl -sSL ...`/`wget -qO- ...` (the real, tested shapes) still do.
_LEGIT_PIPE_RE = re.compile(r"^(?:curl|wget)(?=\s)[^|]*\|\s*(?:bash|sh)\s*$")
_CANONICAL_TARGET_RE = re.compile(r"Global/_canonical", re.IGNORECASE)


def _validate_install_command(cmd):
    """ADR-0038 §3/§7: fail-closed validation for a PROPOSED install command, shared by
    cmd_tools_propose (first check) and cmd_tools_approve (re-check via _validate_proposal,
    defense in depth against a hand-edited tools.proposals.json). Returns a human-readable
    rejection reason, or None if `cmd` is acceptable to catalog. Privilege escalation
    (sudo/doas/pkexec/su/runas, see `_cmd_privilege_escalator`) is rejected outright here,
    a layer earlier than (and in addition to) cmd_tools_install's own escalation prompt
    (unchanged posture: shows the exact command and asks, even under --yes) -- a
    "catalogued" entry that always re-prompts anyway would be a confusing thing to have
    approved in the first place."""
    if not cmd or not cmd.strip():
        return "el comando no puede estar vacío"
    escalator = _cmd_privilege_escalator(cmd)
    if escalator:
        return (f"'{escalator}' no está permitido en un comando propuesto — la escalación de "
                f"privilegios siempre queda manual")
    if not _ALLOWED_CMD_CHARS_RE.fullmatch(cmd):
        return ("comando con caracteres no permitidos — solo se aceptan letras, números, espacios "
                "y - . / : = _ ~ @ + , | (allowlist, ADR-0038 §3)")
    if "|" in cmd and not _LEGIT_PIPE_RE.match(cmd.strip()):
        return "pipe no reconocido — el único pipe permitido es 'curl|wget ... | bash|sh' (ver tools.toml gcloud)"
    if _CANONICAL_TARGET_RE.search(cmd):
        return "un comando propuesto no puede instalar dentro de Global/_canonical (ADR-0038 §7)"
    return None


def _read_tools_proposals():
    """F-06 repair: never-fails the same way `_load_local_catalog` does -- a parse error
    degrades to `{}` (staging is throwaway by nature, no warning needed the way the
    curated-adjacent `tools.local.toml` gets one), and so does a shape mismatch: a
    `tools.proposals.json` that parses but isn't a JSON object (e.g. a bare list) used to
    reach `cmd_tools_approve`'s `.get(name)` as an `AttributeError`; any individual
    proposal entry that isn't itself an object is dropped the same way."""
    path = ROOT / "tools.proposals.json"
    try:
        raw = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {name: value for name, value in raw.items() if isinstance(value, dict)}


def _write_tools_proposal(name, proposal):
    """ADR-0038 §5: the one artifact `--tools-propose` persists -- a staging entry so a
    later, independent `--tools-approve NAME` (bare name, per AC-31's own grammar) can
    reproduce byte-for-byte what the human already reviewed. Never the catalog itself,
    never an install. Re-proposing the same name overwrites its pending entry."""
    proposals = _read_tools_proposals()
    proposals[name] = proposal
    _save_tools_proposals(proposals)


# F-04 repair: TOML basic-string escapes for the characters the spec requires escaped
# (backslash/quote plus the named short escapes) -- the old `_toml_str` only handled
# `\\` and `"`, so `_toml_str("a\nb")` produced `"a\nb"` with a LITERAL, unescaped
# newline: an unterminated basic string that broke every subsequent parse of the whole
# file (`_load_local_catalog` then silently degraded to `{}`, wiping every previously
# approved tool -- see that function's own docstring). `--why`/`--detect` are rejected
# outright if they contain a control character (`cmd_tools_propose`/`_validate_proposal`,
# fail-closed at the source) -- this escaping is defense in depth for whatever reaches
# here anyway (e.g. a hand-edited tools.proposals.json `cmd_tools_approve` re-validates
# but a caller of `_dump_toml_catalog` should never be able to emit a broken file).
_TOML_STR_ESCAPES = {"\\": "\\\\", '"': '\\"', "\b": "\\b", "\t": "\\t",
                     "\n": "\\n", "\f": "\\f", "\r": "\\r"}


def _toml_str(value):
    out = []
    for ch in str(value):
        if ch in _TOML_STR_ESCAPES:
            out.append(_TOML_STR_ESCAPES[ch])
        elif ord(ch) < 0x20 or ord(ch) == 0x7f:
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def _dump_toml_catalog(data):
    """Minimal, schema-specific TOML writer for tools.local.toml's exact shape only --
    `[<kind>.<name>]` with `detect`/`note` plus one `[<kind>.<name>.install]` subtable
    (ADR-0038: same uniform schema for every kind, no mcp-native type/command/url). Never
    a general-purpose TOML serializer -- tomllib is read-only in the stdlib, and every
    string written here already passed `_validate_install_command`'s fail-closed checks."""
    lines = [
        "# tools.local.toml -- generated by `set-agents --tools-approve` (ADR-0038).",
        "# Untracked (see .gitignore). Hand edits survive, but the next --tools-approve",
        "# for the same name overwrites its block, and a name colliding with tools.toml",
        "# is always shadowed by the curated entry (docs/adr/0038-*.md).",
        "",
    ]
    for kind in sorted(data):
        for name in sorted(data[kind]):
            entry = data[kind][name]
            lines.append(f"[{kind}.{name}]")
            if entry.get("detect"):
                lines.append(f"detect = {_toml_str(entry['detect'])}")
            if entry.get("note"):
                lines.append(f"note = {_toml_str(entry['note'])}")
            install = entry.get("install") or {}
            if install:
                lines.append(f"[{kind}.{name}.install]")
                for method in sorted(install):
                    lines.append(f"{method} = {_toml_str(install[method])}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def cmd_tools_propose(name, kind, detect, method, cmd, why):
    """AC-30: validate + print the consolidated question. Never installs, never writes
    tools.toml/tools.local.toml -- the single artifact it can produce is a staged
    proposal (see `_write_tools_proposal`'s docstring for why that still counts as "no
    muta nada" in the sense ADR-0038 §5 argues). F-05 repair: validation goes through
    `_validate_proposal`, the SAME check `cmd_tools_approve` re-runs against the staged
    copy later -- the two paths can never validate differently."""
    why = (why or "").strip()
    detect = (detect or "").strip()
    reason = _validate_proposal(name, kind, detect, method, cmd, why)
    if reason:
        print(f"TOOLS_PROPOSE_REJECTED {name} — {reason}")
        return 2
    proposal = {
        "kind": kind, "detect": detect, "method": method, "cmd": cmd, "why": why,
        "proposed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    _write_tools_proposal(name, proposal)
    print(f"TOOLS_PROPOSE_OK {name}")
    print(f"  kind={kind}")
    print(f"  detect={detect}")
    print(f"  install.{method}={cmd}")
    print(f"  why={why}")
    print(f"¿Aprobás agregar '{name}' al catálogo de herramientas? Esto NO instala nada todavía.")
    # F-07 repair: the old wording ("un agente no puede correr esto") was a technical
    # claim that's only true for coord_policy-gated channels (ADR-0038 §2) -- a writer
    # role (implementer, on any lane) has broad, undifferentiated bash access and is NOT
    # technically blocked from typing this command. The real invariant is doctrinal
    # ("never yours to run, no matter your role"), not universally enforced.
    print("Requiere una persona -- el approve nunca es tuyo para correr, sea cual sea tu rol")
    print("(ADR-0038 §2). Para aprobar:")
    print(f"  python3 ai/scripts/set_agents_app.py --tools-approve {name}")
    return 0


def _validate_proposal(name, kind, detect, method, cmd, why):
    """F-05 repair: the SAME validation `cmd_tools_propose` runs against fresh CLI input,
    run again here so propose and approve can never diverge. Before this existed,
    `cmd_tools_approve` only re-checked `cmd` (via `_validate_install_command`) and
    `kind` -- `name`/`method`/`detect` came straight from the staged
    `tools.proposals.json` and were written into `tools.local.toml` UNQUOTED and
    unvalidated (a TOML-structure-injection vector via a hand-edited staging file,
    which is exactly the file this defense-in-depth re-check exists for -- ADR-0038 §5).
    Returns a human-readable rejection reason, or None if every field is acceptable."""
    if not coord_policy._CATALOG_NAME.fullmatch(name or ""):
        return f"nombre inválido (usá {coord_policy._CATALOG_NAME.pattern})"
    if kind not in _TOOL_KINDS:
        return f"--kind inválido: {kind} (usá {'|'.join(_TOOL_KINDS)})"
    if method not in _INSTALL_METHODS:
        return f"método de instalación desconocido: {method} (usá {'|'.join(_INSTALL_METHODS)})"
    reason = _validate_install_command(cmd or "")
    if reason:
        return reason
    detect = (detect or "").strip()
    if not detect:
        return "falta --detect"
    if _CONTROL_CHAR_RE.search(detect):
        return "--detect no puede contener caracteres de control (saltos de línea, tabs, etc.)"
    why = (why or "").strip()
    if not why:
        return "falta --why (motivo)"
    if _CONTROL_CHAR_RE.search(why):
        return "--why no puede contener caracteres de control (saltos de línea, tabs, etc.) — usá un motivo de una sola línea"
    return None


def _log_tool_decision(name, kind, why):
    """AC-31: `log-decision` on approve (qué herramienta, por qué, quién la pidió).

    Deliberately a subprocess to `feature-state.py log-decision` -- the repo's one
    sanctioned mutation channel for this log (`coord_policy.SAFE` already allowlists
    `python3 ai/scripts/feature-state.py \\S+`) -- and NOT a direct import of
    `feature_state_lib.cli_reporting.cmd_log_decision`. Verified live (round-trip
    evidence, P5-implementer.md): that function reads `model.render_notes`, which only
    exists because `feature-state.py`'s OWN top-level script monkeypatches
    `model.render_notes = render_notes` at import time (see that file's own comment on
    why `render_notes` physically lives there instead of in `feature_state_lib/`) --
    calling `cmd_log_decision` from a process that never ran `feature-state.py` as
    `__main__` raises `AttributeError: module 'feature_state_lib.model' has no
    attribute 'render_notes'`.

    F-11 repair: passes `cwd=ROOT` explicitly -- the catalog this decision documents
    (`tools.local.toml`/`tools.proposals.json`) always lives at ROOT (the harness clone
    root, never per-project -- see ADR-0038 §2 and .gitignore's corrected comment), so
    the decision record must land in that SAME place, not wherever the calling process's
    CWD happened to be (before this fix, `set-agents --tools-approve x` run from `~`
    created `~/ai/state/decisions-log.jsonl`, inconsistent with the harness-global
    catalog).

    F-12 repair: bounded `timeout`, `capture_output` (the subprocess used to inherit
    stdout, so `feature-state.py`'s own raw JSON leaked into `--tools-approve`'s output),
    and a non-zero/timeout outcome is reported as a WARNING, never a failure -- the
    catalog write already happened by the time this runs, so a broken/slow log-decision
    must not make `--tools-approve` itself look like it failed."""
    script = Path(__file__).resolve().parent / "feature-state.py"
    argv = [sys.executable, str(script), "log-decision",
            "--title", f"Herramienta de catálogo aprobada: {name}",
            "--context", f"--tools-approve {name} (kind={kind}) -- flujo ADR-0038 "
                          f"propose -> aprobación humana -> approve.",
            "--decision", f"Se aprobó agregar '{name}' (kind={kind}) a tools.local.toml. Motivo: {why}",
            "--consequences", "Disponible vía --tools/--tools-install tras el approve; sudo sigue siempre manual.",
            "--actor", "tools-approve"]
    try:
        result = subprocess.run(argv, check=False, cwd=str(ROOT), timeout=30,
                                 capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        print("WARNING: log-decision (ADR-0038 --tools-approve) superó el timeout de 30s -- "
              "el catálogo ya quedó escrito, pero la decisión puede no haberse registrado.",
              file=sys.stderr)
        return 1
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()[:500]
        print(f"WARNING: log-decision (ADR-0038 --tools-approve) terminó con rc={result.returncode} -- "
              f"el catálogo ya quedó escrito. Salida: {detail}", file=sys.stderr)
    return result.returncode


def _save_tools_proposals(proposals):
    """F-15 repair: single writer for tools.proposals.json -- the exact same
    `atomic_write`+`json.dumps` shape used to be duplicated inline in
    `_write_tools_proposal` (stage a new one) and `cmd_tools_approve` (consume/delete
    one)."""
    atomic_write(ROOT / "tools.proposals.json", json.dumps(proposals, indent=2, sort_keys=True) + "\n")


def cmd_tools_approve(name):
    """AC-31: writes the staged proposal into tools.local.toml + log-decision. The
    actual installation still goes through cmd_tools_install unchanged (sudo posture,
    TTY/--yes gating, MCP-disabled-by-default -- none of that lives here).

    F-02 repair (critical, variant chosen by the orchestrator -- ai/state/decisions-log
    .jsonl slug p5-repair-excepciones-y-diseno): the approval used to be tied to the bare
    NAME alone -- it printed only `TOOLS_APPROVE_OK {name} kind={kind}` and never
    re-showed what it was about to catalog, while the payload lived in
    `tools.proposals.json` (untracked, writable by any agent between propose and
    approve). This now re-prints the FULL staged block and requires an interactive
    confirmation, reusing the exact pattern `cmd_tools_install` already uses for sudo
    (shows the command, asks, refuses outright without a TTY -- never runs/writes
    anything silently). AC-31's bare-name grammar for the CLI invocation is unchanged;
    only what happens once that name resolves to a proposal changed."""
    proposals = _read_tools_proposals()
    proposal = proposals.get(name)
    if proposal is None:
        print(f"TOOLS_APPROVE_UNKNOWN {name} — no hay propuesta pendiente, corré --tools-propose primero")
        return 2
    kind = proposal.get("kind")
    detect = proposal.get("detect")
    method = proposal.get("method")
    cmd = proposal.get("cmd")
    why = proposal.get("why") or ""
    reason = _validate_proposal(name, kind, detect, method, cmd, why)
    if reason:
        print(f"TOOLS_APPROVE_REJECTED {name} — {reason}")
        return 2
    curated = tomllib.loads((ROOT / "tools.toml").read_text())
    if any(name in curated.get(section, {}) for section in _TOOL_KINDS):
        print(f"TOOLS_APPROVE_REJECTED {name} — colisiona con el catálogo curado (tools.toml); "
              f"el curado siempre gana, elegí otro nombre")
        return 2
    print(f"Vas a aprobar '{name}' para el catálogo de herramientas:")
    print(f"  kind={kind}")
    print(f"  detect={detect}")
    print(f"  install.{method}={cmd}")
    print(f"  why={why}")
    print("Esto agrega la entrada a tools.local.toml. NO instala nada todavía.")
    if not sys.stdin.isatty():
        print(f"TOOLS_APPROVE_MANUAL {name}: sin TTY — no se puede confirmar interactivamente, "
              f"corré este --tools-approve desde una terminal")
        return 1
    with tui.suspend_terminal():
        answer = _safe_input(f"¿Confirmás que esto es lo que aprobás para '{name}'? [y/N] ")
    if answer.strip().lower() not in {"y", "yes", "s", "si"}:
        return 1
    local = _load_local_catalog()
    section = dict(local.get(kind, {}))
    section[name] = {
        "detect": detect,
        "install": {method: cmd},
        "note": f"agregado por --tools-approve: {why}",
    }
    local[kind] = section
    atomic_write(ROOT / "tools.local.toml", _dump_toml_catalog(local))
    del proposals[name]
    _save_tools_proposals(proposals)
    _log_tool_decision(name, kind, why)
    print(f"TOOLS_APPROVE_OK {name} kind={kind}")
    if kind == "cli":
        print(f"Para instalar: python3 ai/scripts/set_agents_app.py --tools-install {name}")
    elif kind == "mcp":
        # F-10 repair + NEW-02 repair (delta review round 3): kind=mcp entries are
        # catalogued with the uniform detect/install schema (ADR-0038 "Rejected
        # alternatives" -- deliberate, no native type/command/url modeled here), which
        # is NOT what _mcp_json_entry/_codex_section index (spec["type"]). --tools-install
        # already didn't wire kind=mcp (F-10); this NOTA now says the same for
        # --mcp-add/--mcp-on too, so a human finds out here instead of hitting
        # MCP_UNSUPPORTED (_mcp_spec) later.
        print(f"NOTA: kind=mcp queda catalogado en tools.local.toml pero todavía no tiene "
              f"instalación automática (ADR-0038 §7/Rejected alternatives) — instalalo a mano "
              f"con install.{method} de arriba; ni --tools-install ni --mcp-add/--mcp-on lo van "
              f"a encontrar (falta el esquema type/command/url nativo que esos comandos esperan).")
    else:
        # F-10 repair: kind=skill entries are catalogued but NOT wired into
        # cmd_tools_install/_tools_data (ADR-0038 "Rejected alternatives" -- deliberate,
        # only kind=cli connects end-to-end). Suggesting --tools-install here used to
        # print a command that always fails with TOOL_UNKNOWN; now it says so up front.
        print(f"NOTA: kind={kind} queda catalogado en tools.local.toml pero todavía no tiene "
              f"instalación automática (ADR-0038 §7/Rejected alternatives) — instalalo a mano "
              f"con install.{method} de arriba; --tools-install no lo va a encontrar.")
    return 0


def _parse_tools_propose_argv(rest):
    """Manual walker for --tools-propose's grammar (argparse cannot declare a dynamic
    --install-<method> flag name, so this subcommand is intercepted in main() before the
    main parser ever runs -- see _dispatch_tools_discovery). Purely SYNTACTIC: extracts
    name/kind/detect/method/cmd/why without judging whether any of them is actually
    valid -- cmd_tools_propose does every semantic check (name grammar, kind enum,
    command safety), same division of labor coord_policy's own walkers keep with this
    module's re-checks."""
    if not rest or rest[0].startswith("--"):
        raise ValueError("falta <name>")
    name, rest = rest[0], rest[1:]
    values = {"kind": None, "detect": None, "why": None}
    method = cmd = None
    i = 0
    while i < len(rest):
        token = rest[i]
        if token in ("--kind", "--detect", "--why"):
            key = token[2:]
            if i + 1 >= len(rest):
                raise ValueError(f"falta valor para {token}")
            if values[key] is not None:
                raise ValueError(f"{token} repetido")
            values[key] = rest[i + 1]
            i += 2
            continue
        if token.startswith("--install-") and len(token) > len("--install-"):
            if i + 1 >= len(rest):
                raise ValueError(f"falta valor para {token}")
            if method is not None:
                raise ValueError("--install-<method> repetido")
            method, cmd = token[len("--install-"):], rest[i + 1]
            i += 2
            continue
        raise ValueError(f"flag no reconocida: {token}")
    missing = [f"--{k}" for k, v in values.items() if v is None]
    if method is None:
        missing.append("--install-<method>")
    if missing:
        raise ValueError(f"faltan flags: {', '.join(missing)}")
    return name, values["kind"], values["detect"], method, cmd, values["why"]


def _parse_tools_approve_argv(rest):
    """--tools-approve's grammar is deliberately just the bare name (AC-31/ADR-0038 §5)."""
    if len(rest) != 1 or rest[0].startswith("--"):
        raise ValueError("uso: --tools-approve <name>")
    return rest[0]


def _dispatch_tools_discovery(verb, rest):
    """Entry point called from main() BEFORE the main argparse parser runs -- see the
    comment at that call site for why these two verbs cannot go through the declarative
    parser at all."""
    if verb == "--tools-propose":
        try:
            name, kind, detect, method, cmd, why = _parse_tools_propose_argv(rest)
        except ValueError as exc:
            print(f"TOOLS_PROPOSE_REJECTED — {exc}")
            return 2
        return cmd_tools_propose(name, kind, detect, method, cmd, why)
    try:
        name = _parse_tools_approve_argv(rest)
    except ValueError as exc:
        print(f"TOOLS_APPROVE_REJECTED — {exc}")
        return 2
    return cmd_tools_approve(name)


def platform_pm():
    if sys.platform == "darwin":
        return "brew" if shutil.which("brew") else None
    if sys.platform == "win32":
        for pm, binary in (("winget", "winget"), ("choco", "choco")):
            if shutil.which(binary):
                return pm
        return None
    for pm, binary in (("pacman", "pacman"), ("apt", "apt-get"), ("dnf", "dnf"), ("zypper", "zypper")):
        if shutil.which(binary):
            return pm
    return None


def pick_method(install):
    """First applicable method: platform pm -> npm -> curl. None -> manual."""
    order = [platform_pm()]
    if shutil.which("npm") or shutil.which("pnpm"):
        order.append("npm")
    order.append("curl")
    for method in order:
        if method and method in install:
            return method
    return None


def _safe_input(prompt):
    """`input()` that exits cleanly instead of a traceback on EOFError/KeyboardInterrupt
    (AC-29) — every remaining raw `input()` call in this module goes through this, since a
    prompt reached from the picker runs in COOKED mode (via `tui.suspend_terminal()`, where
    Ctrl-C generates a real SIGINT again, unlike inside the raw-mode picker loop itself, which
    reads Ctrl-C as a plain byte and never raises at all)."""
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def _tools_data():
    """AC-28: the data cmd_tools()/tools_menu() both render, in catalog order."""
    return [
        (name, bool(shutil.which(entry["detect"])))
        for name, entry in load_catalog().get("cli", {}).items()
    ]


def cmd_tools():
    for name, installed in _tools_data():
        print(f"TOOL {name} installed={'yes' if installed else 'no'}")
    return 0


def cmd_tools_install(name, dry=False, yes=False):
    entry = load_catalog().get("cli", {}).get(name)
    if entry is None:
        # AC-32: no longer a dead end -- the token stays TOOL_UNKNOWN (pinned by
        # tests/test_harness.py), only the tail changes to the ADR-0038 propose flow.
        print(f"TOOL_UNKNOWN {name} — no está en el catálogo curado; proponelo (ADR-0038): "
              f'--tools-propose {name} --kind cli --detect <bin> --install-<method> "<cmd>" --why "<motivo>"')
        return 2
    if _is_local_only_entry("cli", name):
        # NEW-01 repair (ADR-0038 §3/§8, delta review round 2, high): `tools.local.toml`
        # is the untracked overlay `--tools-approve` writes to -- a HAND edit to that file
        # used to reach `subprocess.run(["bash", "-c", command])` below completely
        # unvalidated, even under `--yes` (which skips the confirmation prompt entirely,
        # see the `elif not yes:` branch further down). The read path (this function) is
        # the ONLY one of the two paths into that file that never ran
        # `_validate_install_command` -- the write path (`cmd_tools_approve`) always has,
        # via `_validate_proposal`. Re-run that SAME fail-closed check here, against every
        # install command this entry actually carries (not just the one method
        # `pick_method` happens to choose on this platform), before touching
        # `shutil.which`/`pick_method` at all. Curated `tools.toml` entries are exempt --
        # reviewed, tracked in git, and some legitimately use sudo, which this would
        # reject outright instead of the guarded show-and-ask prompt curated sudo entries
        # keep further down (`_cmd_privilege_escalator`, unchanged).
        for method, cmd in entry.get("install", {}).items():
            if method == "doc":
                continue
            reason = _validate_install_command(cmd)
            if reason:
                print(f"TOOL_REJECTED {name} — la entrada de tools.local.toml no pasa la "
                      f"validación de instalación (ADR-0038 §3): {reason}. Una entrada "
                      f"legítima solo llega ahí vía --tools-approve, que ya la valida; "
                      f"revisá o borrá tools.local.toml.")
                return 2
    if shutil.which(entry["detect"]):
        print(f"TOOL_SKIP {name} ({version_of(entry['detect'])})")
        return 0
    method = pick_method(entry["install"])
    if method is None:
        print(f"TOOL_MANUAL {name}: sin método automático acá — {entry['install'].get('doc', '')}")
        return 1
    command = entry["install"][method]
    if command.startswith("npm ") and not shutil.which("npm"):
        command = "p" + command  # pnpm fallback, same verbs
    if dry:
        print(f"TOOL_PLAN {name} method={method}")
        return 0
    if _cmd_privilege_escalator(command):
        # F-03 repair (ownership exception approved, ai/state/decisions-log.jsonl slug
        # p5-repair-excepciones-y-diseno): a plain `command.startswith("sudo ")` missed
        # `/usr/bin/sudo`/doas/pkexec/su/runas -- an escalator with a resolved path took
        # this whole branch by surprise and, with --yes (already allowed for agents),
        # reached subprocess.run with no prompt at all. Same basename-of-every-token
        # check `_validate_install_command` uses; this HARDENS the existing contract
        # (never silent, same as install.sh) -- it never relaxes it, even under --yes.
        if not sys.stdin.isatty():
            print(f"TOOL_MANUAL {name}: necesita privilegios elevados — corré: {command}")
            return 1
        print(f"Se necesita privilegio de administrador para:\n    {command}")
        # AC-26: reached from the picker (tools_menu -> here), the terminal must be in cooked
        # mode for this to echo at all -- a no-op when there is no active session (the bare
        # --tools-install CLI path), so the behavior above is unchanged either way.
        with tui.suspend_terminal():
            answer = _safe_input("¿Ejecutar ese comando? [y/N] ")
        if answer.strip().lower() not in {"y", "yes", "s", "si"}:
            return 1
    elif not yes:
        # No TTY and no --yes -> never run anything silently.
        if not sys.stdin.isatty():
            print(f"TOOL_MANUAL {name}: sin TTY y sin --yes — corré: {command}")
            return 1
        with tui.suspend_terminal():
            answer = _safe_input(f"¿Ejecutar '{command}'? [y/N] ")
        if answer.strip().lower() not in {"y", "yes", "s", "si"}:
            return 1
    with tui.suspend_terminal():  # the command itself may prompt too (e.g. a sudo password)
        result = subprocess.run(["bash", "-c", command], check=False)
    if result.returncode == 0:
        print(f"TOOL_OK {name}")
        if entry.get("note"):
            print(f"NOTA: {entry['note']}")
        return 0
    print(f"TOOL_FAIL {name} rc={result.returncode} — {entry['install'].get('doc', '')}")
    return 1


def _tools_header():
    """Herramientas panel: per-tool install method + short note, rendered with
    the shared width-aware table (no hardcoded widths). Header-only on purpose:
    the row format and Enter→install behavior of the picker items below are a
    pinned contract of the immutable suite."""
    catalog = load_catalog().get("cli", {})
    rows = []
    for name, entry in catalog.items():
        installed = bool(shutil.which(entry.get("detect", name)))
        method = pick_method(entry.get("install", {})) or "manual (ver doc)"
        note = str(entry.get("note", ""))
        rows.append((name, "✓" if installed else "·", method, note))
    lines = ["Herramientas del catálogo (Enter instala la elegida; sudo siempre pregunta)"]
    lines += table_lines(rows)
    return "\n".join(lines)


def tools_menu():
    data = _tools_data()
    if not data:
        print("(sin herramientas en el catálogo)")
        return
    items = [
        f"{name:<10} {color('instalado', '32') if installed else 'falta'}"
        for name, installed in data
    ]
    choice = tui.run_picker(items, style={"color": color, "bold": bold, "dim": dim},
                            header=_tools_header())
    if isinstance(choice, tui.Selected):
        cmd_tools_install(data[choice.index][0])


_TOOLS_PROPOSE_INTRO = ("Proponer una herramienta nueva para el catálogo "
                         "(no instala nada -- requiere aprobación humana aparte, ADR-0038)")


def tools_propose_menu():
    """AC-35 console entry point for ADR-0038's propose flow: chained free-text/picker
    prompts (vault_menu's pattern) feeding the SAME cmd_tools_propose() the CLI flags
    call, so console and CLI share one validation path. Deliberately never offers
    approve here -- approve is the human's own separate action (ADR-0038 §2); folding it
    into this same picker would blur the exact boundary the ADR draws."""
    style = {"color": color, "bold": bold, "dim": dim}
    with tui.TerminalSession():
        name_result = tui.run_picker((), freetext_allowed=True, style=style,
                                      header=_TOOLS_PROPOSE_INTRO, prompt="Nombre (a-z0-9_-, Esc cancela):")
        name = name_result.value.strip() if isinstance(name_result, tui.FreeText) else ""
        if not name:
            return
        kind_choice = tui.run_picker(_TOOL_KINDS, style=style, header=_TOOLS_PROPOSE_INTRO, prompt="Tipo:")
        if not isinstance(kind_choice, tui.Selected):
            return
        kind = _TOOL_KINDS[kind_choice.index]
        detect_result = tui.run_picker(
            (), freetext_allowed=True, style=style, header=_TOOLS_PROPOSE_INTRO,
            prompt="Binario/archivo para detectar que ya está instalada:")
        detect = detect_result.value.strip() if isinstance(detect_result, tui.FreeText) else ""
        if not detect:
            return
        method_choice = tui.run_picker(_INSTALL_METHODS, style=style, header=_TOOLS_PROPOSE_INTRO,
                                        prompt="Método de instalación:")
        if not isinstance(method_choice, tui.Selected):
            return
        method = _INSTALL_METHODS[method_choice.index]
        cmd_result = tui.run_picker(
            (), freetext_allowed=True, style=style, header=_TOOLS_PROPOSE_INTRO,
            prompt=f"Comando completo para instalar con {method}:")
        cmd = cmd_result.value.strip() if isinstance(cmd_result, tui.FreeText) else ""
        if not cmd:
            return
        why_result = tui.run_picker((), freetext_allowed=True, style=style,
                                     header=_TOOLS_PROPOSE_INTRO, prompt="Motivo (por qué la necesitás):")
        why = why_result.value.strip() if isinstance(why_result, tui.FreeText) else ""
        if not why:
            return
    with tui.suspend_terminal():
        cmd_tools_propose(name, kind, detect, method, cmd, why)


# ----------------------------------------------------------------------- mcp

_BACKED_UP = set()


def atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path not in _BACKED_UP:
        shutil.copy2(path, str(path) + ".bak")
        _BACKED_UP.add(path)
    fd, temp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(content)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def read_json_for_write(path):
    """Like read_json, but NEVER treats an existing-but-corrupt file as empty:
    rewriting it would silently destroy the user's config."""
    path = Path(path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"MCP_ABORT {path} existe pero no parsea como JSON ({exc}); arreglalo antes de tocarlo")


def mcp_targets():
    """Detected harnesses that can host MCP servers, adapter config per target."""
    home = Path.home()
    table = {
        "opencode": {"detect": shutil.which("opencode"), "path": home / ".config/opencode/opencode.json"},
        "claude": {"detect": shutil.which("claude"), "path": home / ".claude.json"},
        "codex": {"detect": shutil.which("codex"), "path": home / ".codex/config.toml"},
        "cursor": {"detect": (home / ".cursor").is_dir(), "path": home / ".cursor/mcp.json"},
        "gemini": {"detect": shutil.which("gemini"), "path": home / ".gemini/settings.json"},
    }
    return {name: entry for name, entry in table.items() if entry["detect"]}


def _servers_key(harness):
    return "mcp" if harness == "opencode" else "mcpServers"


def _mcp_json_entry(harness, spec):
    if harness == "opencode":
        entry = {"type": spec["type"]}
        if spec["type"] == "local":
            entry["command"] = spec["command"]
        else:
            entry["url"] = spec["url"]
        entry["enabled"] = False  # repo policy: added disabled, toggled on demand
        return entry
    if spec["type"] == "local":
        return {"command": spec["command"][0], "args": spec["command"][1:]}
    return {"type": "http", "url": spec["url"]}


def _codex_section(name, spec):
    lines = [f"[mcp_servers.{name}]"]
    if spec["type"] == "local":
        lines.append(f"command = {json.dumps(spec['command'][0])}")
        lines.append(f"args = {json.dumps(spec['command'][1:])}")
    else:
        lines.append(f"url = {json.dumps(spec['url'])}")
    lines.append("enabled = false")
    return lines


def _codex_span(lines, name):
    header = f"[mcp_servers.{name}]"
    try:
        start = lines.index(header)
    except ValueError:
        return None
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("[") and lines[i].endswith("]")),
        len(lines),
    )
    return start, end


def mcp_state(harness, target, name):
    path = target["path"]
    if harness == "codex":
        try:
            section = tomllib.loads(path.read_text()).get("mcp_servers", {}).get(name)
        except (OSError, tomllib.TOMLDecodeError):
            section = None
        if section is None:
            return "absent"
        return "on" if section.get("enabled", True) else "off"
    entry = read_json(path).get(_servers_key(harness), {}).get(name)
    if entry is None:
        return "absent"
    if harness == "opencode":
        return "on" if entry.get("enabled") else "off"
    return "on"  # claude/cursor/gemini: present == active


def mcp_write(harness, target, name, spec=None, enabled=None, remove=False):
    """Add (spec), toggle (enabled) or remove a server in the target's native format."""
    path = target["path"]
    if harness == "codex":
        lines = path.read_text().splitlines() if path.exists() else []
        span = _codex_span(lines, name)
        if remove and span:
            del lines[span[0]:span[1]]
        elif enabled is not None and span:
            start, end = span
            pattern = [i for i in range(start + 1, end) if lines[i].split("=")[0].strip() == "enabled"]
            value = f"enabled = {'true' if enabled else 'false'}"
            if pattern:
                lines[pattern[0]] = value
            else:
                lines.insert(start + 1, value)
        elif spec is not None and not span:
            if lines and lines[-1] != "":
                lines.append("")
            lines.extend(_codex_section(name, spec))
        if not lines:
            return  # nothing to write; never create an empty config.toml
        atomic_write(path, "\n".join(lines).rstrip() + "\n")
        return
    data = read_json_for_write(path)
    servers = data.setdefault(_servers_key(harness), {})
    if remove:
        servers.pop(name, None)
    elif enabled is not None and harness == "opencode" and name in servers:
        servers[name]["enabled"] = enabled
    elif spec is not None and name not in servers:
        servers[name] = _mcp_json_entry(harness, spec)
    atomic_write(path, json.dumps(data, indent=2) + "\n")


def _mcp_spec_supported(spec):
    """NEW-02 repair (delta review round 3) validated only that `type` was PRESENT, not
    that the rest of the native shape was. That left a gap NEW-03 (round 4) found: a
    hand-edited `tools.local.toml` that has valid `detect`/`install` (so it clears
    `_valid_local_entry_shape`, F-06 round 2) AND adds a bare `type` key sails through
    the old check and reaches `_mcp_json_entry`/`mcp_write` (`mcp_write` -> `_mcp_json_entry`,
    `:2031-2042`) or `_codex_section` (`:2045-2053`), both of which index every one of these
    WITHOUT `.get()`:
      - `spec["type"]`             (`_mcp_json_entry` opencode branch `:2033`; the
                                     `spec["type"] == "local"` comparisons at `:2034`/`:2040`
                                     and `_codex_section`'s `:2047` don't KeyError on a
                                     missing key, but do on `spec` not being a mapping)
      - `spec["command"]`          (`_mcp_json_entry` opencode-local `:2035`, assigned
                                     as-is into the native config -- a non-list here writes
                                     a shape opencode itself doesn't accept, not just a
                                     Python crash)
      - `spec["command"][0]`       (`_mcp_json_entry` claude/cursor/gemini-local `:2041`,
                                     `_codex_section` `:2048`)
      - `spec["command"][1:]`      (same two sites, `:2041`/`:2049`)
      - `spec["url"]`              (`_mcp_json_entry` opencode-remote `:2037`,
                                     claude/cursor/gemini-remote `:2042`, `_codex_section`
                                     `:2051`)
    Live-reproduced (sandboxed HOME/ROOT, see P5-repair-4.md): missing `command` ->
    `KeyError: 'command'`; `command=[]` -> `IndexError`; `command` a STRING (the worst
    case) -> no crash at all, `command[0]`/`command[1:]` silently slice the string
    character-by-character and `MCP_ADDED`/`rc=0` writes a corrupt entry into the user's
    real `~/.claude.json`; `command` a list with a non-string element -> no crash, writes
    a non-string arg into the native config; `type` outside `{local, remote}` ->
    `KeyError: 'url'` (falls into the `else` branch of both `_mcp_json_entry` and
    `_codex_section`, which assumes "not local" means "remote, so `url` exists"); missing
    or empty `url` -> `KeyError: 'url'` / a silently-written empty URL.

    The fix enforces the NATIVE shape completely, not just the presence of one key: a
    curated `tools.toml` `[mcp.*]` entry always has this shape by construction (it is
    hand-authored and reviewed to match exactly what `_mcp_json_entry`/`_codex_section`
    expect); a `tools.local.toml` overlay entry -- whether it lacks `type` entirely (the
    common, honest case: `--tools-approve --kind mcp` never writes it, ADR-0038 §7) or
    was hand-edited to add a `type`-shaped but malformed native block -- fails this check
    the same way and gets degraded by every caller instead of indexed into and crashed
    (or worse, silently written corrupt) on."""
    if not isinstance(spec, dict):
        return False
    kind = spec.get("type")
    if kind not in ("local", "remote"):
        return False
    if kind == "local":
        command = spec.get("command")
        return (
            isinstance(command, list) and bool(command)
            and all(isinstance(part, str) for part in command)
        )
    url = spec.get("url")
    return isinstance(url, str) and bool(url)


def _mcp_spec(name):
    spec = load_catalog().get("mcp", {}).get(name)
    if spec is None:
        print(f"MCP_UNKNOWN {name} — agregalo en tools.toml")
        return None
    if not _mcp_spec_supported(spec):
        print(f"MCP_UNSUPPORTED {name} — entrada local de tools.local.toml sin esquema "
              f"MCP nativo; instalala a mano con install.<method> (ADR-0038)")
        return None
    return spec


def _mcp_selected(harness):
    targets = mcp_targets()
    if harness:
        if harness not in targets:
            print(f"MCP_NO_HARNESS {harness} (no detectado en esta máquina)")
            return {}
        return {harness: targets[harness]}
    return targets


def _mcp_data():
    """AC-28: the data cmd_mcp()/mcp_menu() both render -- [(server, [(harness, state), ...]), ...]."""
    targets = mcp_targets()
    return [
        (name, [(harness, mcp_state(harness, target, name)) for harness, target in targets.items()])
        for name in load_catalog().get("mcp", {})
    ]


def cmd_mcp():
    for name, states in _mcp_data():
        for harness, state in states:
            print(f"MCP {name} harness={harness} state={state}")
    return 0


def cmd_mcp_add(name, harness=None):
    spec = _mcp_spec(name)
    if spec is None:
        return 2
    for h, target in _mcp_selected(harness).items():
        if h == "opencode" and name in MANAGED_MCP:
            print(f"MCP_MANAGED {name} harness=opencode — ya lo gestiona el repo (toggle con --mcp-on/--mcp-off)")
            continue
        if mcp_state(h, target, name) != "absent":
            print(f"MCP_SKIP {name} harness={h} (ya existe)")
            continue
        mcp_write(h, target, name, spec=spec)
        print(f"MCP_ADDED {name} harness={h} state={mcp_state(h, target, name)}")
    if spec.get("note"):
        print(f"NOTA: {spec['note']}")
    return 0


def cmd_mcp_toggle(name, harness, enabled):
    # opencode/codex toggle an existing entry in place, so managed servers
    # (engram/brave-cdp) work here even without a tools.toml spec; the
    # add-on-enable formats (claude/cursor/gemini) do need the catalog.
    spec = load_catalog().get("mcp", {}).get(name)
    for h, target in _mcp_selected(harness).items():
        state = mcp_state(h, target, name)
        if h in ("opencode", "codex"):
            if state == "absent":
                print(f"MCP_ABSENT {name} harness={h} (primero --mcp-add)")
                continue
            mcp_write(h, target, name, enabled=enabled)
        else:
            # No disable flag in these formats: on == present, off == removed.
            if enabled and state == "absent":
                if spec is None:
                    print(f"MCP_UNKNOWN {name} harness={h} — agregalo en tools.toml para poder encenderlo acá")
                    continue
                if not _mcp_spec_supported(spec):
                    # NEW-02 repair (delta review round 3): this call site resolves the
                    # spec straight off load_catalog() (not via _mcp_spec) so opencode/
                    # codex can toggle a managed server without needing a tools.toml
                    # entry at all -- but that means it must run the SAME type-present
                    # check _mcp_spec does before ever forwarding spec to mcp_write, or a
                    # local-overlay entry (detect/install, no type -- F-06 round 2's
                    # shape guarantee, never a native type/command/url) reaches
                    # _mcp_json_entry's spec["type"] as a bare KeyError.
                    print(f"MCP_UNSUPPORTED {name} harness={h} — entrada local de "
                          f"tools.local.toml sin esquema MCP nativo; instalala a mano con "
                          f"install.<method> (ADR-0038)")
                    continue
                mcp_write(h, target, name, spec=spec)
            elif not enabled and state != "absent":
                mcp_write(h, target, name, remove=True)
        print(f"MCP_SET {name} harness={h} state={mcp_state(h, target, name)}")
    return 0


def cmd_mcp_remove(name, harness=None):
    targets = _mcp_selected(harness)
    known = name in load_catalog().get("mcp", {}) or any(
        mcp_state(h, target, name) != "absent" for h, target in targets.items()
    )
    if not known:
        # A typo must never delete a user's own unrelated server.
        print(f"MCP_UNKNOWN {name} — no está en el catálogo ni configurado en ningún harness")
        return 2
    for h, target in targets.items():
        if h == "opencode" and name in MANAGED_MCP:
            print(f"MCP_MANAGED {name} harness=opencode — no se remueve un server gestionado")
            continue
        mcp_write(h, target, name, remove=True)
        print(f"MCP_REMOVED {name} harness={h}")
    return 0


# ----------------------------------------------------------- 022 PKG-4: providers (AC-11..14)
#
# `~/.local/state/set-agentes/providers.toml` (AC-11): the OpenCode `provider.*` JSON-block
# registry, same private-STATE_DIR/atomic-write precedent as MODEL_PREFERENCE_PATH above,
# same fail-closed discipline (`provider_registry.ProvidersRegistryError`, never a silent
# empty-registry swallow). NOT the routing-identity `provider_registry.PROVIDERS` table:
# these commands never write to it and never read it as a source of ids -- they only
# CHECK a new id against it, to stop a user from shadowing a routed provider's own id
# with an unrelated local/custom OpenCode block (AC-12).
#
# AC-13's render step lives in `install.py`, not here: these commands only ever touch
# `providers.toml` (never `opencode.json` directly -- "sin tocar JSON a mano" is a promise
# about the USER, not a ban on install.py's own render/prune step doing it on their
# behalf at install time). A change here needs `./build.sh --install` (the same "Instalar
# / Reparar" drift-repair entry point `cmd_status`/the menu already point at) to reach the
# live file -- every command below says so explicitly, so "I removed it but opencode still
# shows it" is never a silent surprise.
PROVIDERS_TOML_PATH = STATE_DIR / provider_registry.PROVIDERS_TOML_NAME
_PROVIDER_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
_PROVIDER_MODEL_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
_INSTALL_HINT = "corré './build.sh --install' para que se refleje en opencode.json"


def _load_providers_registry():
    """Fail-closed load shared by every `--provider-*` command below -- a malformed
    `providers.toml` (hand-edited, corrupted) never degrades to 'nothing registered'."""
    try:
        return provider_registry.parse_providers_toml(PROVIDERS_TOML_PATH)
    except provider_registry.ProvidersRegistryError as exc:
        print(f"providers.toml: {exc}", file=sys.stderr)
        raise SystemExit(2)


def _provider_spec_summary(spec):
    """`--provider-list`/`--provider-verify`'s one-line rendering of an arbitrary
    provider spec dict -- tolerant of a spec that doesn't have the expected shape
    (`?` per missing field), never a crash on a hand-migrated oddity."""
    npm = spec.get("npm") if isinstance(spec, dict) else None
    options = spec.get("options") if isinstance(spec, dict) else None
    base_url = options.get("baseURL") if isinstance(options, dict) else None
    models = spec.get("models") if isinstance(spec, dict) else None
    model_count = len(models) if isinstance(models, dict) else "?"
    return f"npm={npm or '?'} base_url={base_url or '?'} models={model_count}"


def cmd_provider_list():
    """AC-12 (read-only): every registered provider id, its origin, and a one-line
    summary of its declared spec."""
    entries = _load_providers_registry()
    if not entries:
        print("PROVIDER_NONE — nada registrado todavía (corré --provider-add, o instalá con "
              "./build.sh --install para sembrar el registro desde lo que ya haya en opencode.json)")
        return 0
    for provider_id in sorted(entries):
        entry = entries[provider_id]
        print(f"PROVIDER {provider_id} origin={entry.origin} {_provider_spec_summary(entry.spec)}")
    return 0


def _provider_spec_shape_issues(spec):
    """AC-12's `--provider-verify`: ONLY the declared surface (never liveness -- no HTTP
    call, that's AC-18/P5's `GET {baseURL}/models`). Checks the minimal shape OpenCode's
    own `provider.<id>` schema needs to be usable at all: a non-empty `npm` package, a
    non-empty `options.baseURL`, and at least one declared model."""
    issues = []
    if not isinstance(spec, dict):
        return ["spec is not an object"]
    if not isinstance(spec.get("npm"), str) or not spec["npm"]:
        issues.append("npm")
    options = spec.get("options")
    if not isinstance(options, dict) or not isinstance(options.get("baseURL"), str) or not options.get("baseURL"):
        issues.append("options.baseURL")
    models = spec.get("models")
    if not isinstance(models, dict) or not models:
        issues.append("models")
    return issues


_LIVENESS_TIMEOUT_SECONDS = 2.0
# AC-18 (022 PKG-5): the literal spec text is "sólo providers user" -- the DEFAULT here
# never widens past that, not re-litigable. `harness-legacy` is the P4 interaction named
# explicitly in the context pack (ollama, after P4, is `origin=harness-legacy`, not
# `user`): resolved with an EXPLICIT opt-in argument (`--include-legacy`), never
# silently folded into the default set. A plain `--provider-verify` run therefore never
# liveness-checks the real machine's dead Ollama block by design -- `--include-legacy`
# is the documented path to it, not a second `--provider-remove`/`--provider-add`
# round-trip.
_LIVENESS_DEFAULT_ORIGINS = frozenset({"user"})
_LIVENESS_WITH_LEGACY_ORIGINS = frozenset({"user", "harness-legacy"})


def _provider_liveness(base_url, timeout: float = _LIVENESS_TIMEOUT_SECONDS) -> str:
    """AC-18: `GET {base_url}/models`, timeout 2s. Three outcomes, never conflated
    ("nunca 'no existe' cuando fue 'no contestó'"):

    - `alive`: the server answered with SOME HTTP status, 2xx or not -- even a 401/404
      still proves something is listening and speaking HTTP on that port.
    - `dead`: the TCP connection was actively REFUSED -- nothing is listening at all,
      the measured Ollama case (`curl` reports `000` for exactly this: the process is
      not running, the port is closed).
    - `unreachable`: a timeout, a DNS failure, or any other network-level surprise --
      genuinely undetermined, NEVER reported as `dead`. A transient network hiccup must
      never read as "this provider does not exist".
    """
    if not isinstance(base_url, str) or not base_url:
        return "unreachable"
    url = base_url.rstrip("/") + "/models"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=timeout):
            return "alive"
    except urllib.error.HTTPError:
        return "alive"  # the server answered (even an error status): it is listening
    except urllib.error.URLError as exc:
        return "dead" if isinstance(exc.reason, ConnectionRefusedError) else "unreachable"
    except (OSError, TimeoutError):
        return "unreachable"


def cmd_provider_verify(provider_id=None, include_legacy=False, prune_dead=False):
    """AC-12 (declared-surface shape, unchanged) + AC-18/P5 (liveness): for every entry
    that PASSES the shape check and whose origin is in scope (`user` by default, plus
    `harness-legacy` with `include_legacy` -- see `_LIVENESS_DEFAULT_ORIGINS` above), a
    real `GET {baseURL}/models` is now attempted (`_provider_liveness`) and reported as
    `liveness=alive|dead|unreachable` with the measurement's own timestamp
    (`at=<ISO-8601 UTC>`). A shape-invalid entry is never liveness-checked (no baseURL to
    trust) -- same `continue` as before this package, no network call added there.

    `prune_dead=True` (`--prune-dead`) removes every entry THIS RUN measured `dead` --
    never `unreachable` (no evidence of absence) and never a shape-invalid entry (no
    liveness was ever attempted for it) -- from `providers.toml`. Same
    `_INSTALL_HINT`-gated, non-silent discipline as `--provider-remove`: takes effect at
    the next `./build.sh --install`, and offering it is opt-in, never automatic on a
    plain `--provider-verify`."""
    full_registry = _load_providers_registry()  # AC-18: --prune-dead must never drop an
    # entry this run did not even examine -- a single-`provider_id` verify narrows
    # `entries` below for REPORTING only; pruning always writes back against the FULL
    # registry with just the measured-dead ids removed, never the narrowed view.
    entries = full_registry
    if provider_id:
        if provider_id not in entries:
            print(f"PROVIDER_UNKNOWN {provider_id}")
            return 2
        entries = {provider_id: entries[provider_id]}
    elif not entries:
        print("PROVIDER_NONE")
        return 0
    liveness_origins = _LIVENESS_WITH_LEGACY_ORIGINS if include_legacy else _LIVENESS_DEFAULT_ORIGINS
    ok = True
    dead_ids = []
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    for pid in sorted(entries):
        entry = entries[pid]
        issues = _provider_spec_shape_issues(entry.spec)
        if issues:
            ok = False
            print(f"PROVIDER_VERIFY {pid} origin={entry.origin} shape=invalid missing=" + ",".join(issues))
            continue
        line = f"PROVIDER_VERIFY {pid} origin={entry.origin} shape=ok"
        if entry.origin in liveness_origins:
            options = entry.spec.get("options") if isinstance(entry.spec, dict) else None
            base_url = options.get("baseURL") if isinstance(options, dict) else None
            state = _provider_liveness(base_url)
            line += f" liveness={state} at={now}"
            if state != "alive":
                ok = False
            if state == "dead":
                dead_ids.append(pid)
        print(line)
    if prune_dead:
        if not dead_ids:
            print("PROVIDER_PRUNE_NONE — ningún provider midió dead en esta corrida")
        else:
            remaining = {pid: entry for pid, entry in full_registry.items() if pid not in dead_ids}
            atomic_write(PROVIDERS_TOML_PATH, provider_registry.serialize_providers_toml(remaining))
            print(f"PROVIDER_PRUNED ids={','.join(sorted(dead_ids))} — {_INSTALL_HINT}")
    return 0 if ok else 1


def cmd_provider_add(provider_id, base_url, npm=None, label=None, models=()):
    """AC-12: builds an OpenCode-compatible `provider.<id>` block from structured flags
    (never raw JSON typed anywhere) and upserts it into `providers.toml` as
    `origin=user` -- re-adding an id that already exists (including a harness one the
    user removed and wants back with their own settings) is an explicit user action,
    so it always claims `user` origin going forward, superseding whatever origin the
    entry had before."""
    if not _PROVIDER_ID_RE.fullmatch(provider_id):
        print(f"PROVIDER_INVALID id={provider_id!r} — usá letras/números/guiones, hasta 64 caracteres")
        return 2
    if provider_id in provider_registry.PROVIDERS:
        print(f"PROVIDER_RESERVED {provider_id} — es un id de ruteo (provider_registry.PROVIDERS); "
              f"elegí otro id para este provider local")
        return 2
    if not base_url or not (base_url.startswith("http://") or base_url.startswith("https://")):
        print("PROVIDER_INVALID --base-url debe ser una URL http(s)")
        return 2
    if not models:
        print("PROVIDER_INVALID --provider-add requiere al menos un --model ID[:nombre]")
        return 2
    model_specs = {}
    for token in models:
        model_id, _, display = token.partition(":")
        if not _PROVIDER_MODEL_RE.fullmatch(model_id):
            print(f"PROVIDER_INVALID --model {token!r} — el id de modelo es inválido")
            return 2
        model_specs[model_id] = {"name": display or model_id}
    spec = {
        "npm": npm or "@ai-sdk/openai-compatible",
        "name": label or provider_id,
        "options": {"baseURL": base_url},
        "models": model_specs,
    }
    entries = dict(_load_providers_registry())
    previous = entries.get(provider_id)
    entries[provider_id] = provider_registry.ProviderEntry(origin="user", spec=spec)
    atomic_write(PROVIDERS_TOML_PATH, provider_registry.serialize_providers_toml(entries))
    verb = "PROVIDER_REPLACED" if previous is not None else "PROVIDER_ADDED"
    prior_note = f" origin_previo={previous.origin}" if previous is not None else ""
    print(f"{verb} id={provider_id} origin=user models={len(model_specs)}{prior_note} — {_INSTALL_HINT}")
    return 0


def cmd_provider_remove(provider_id):
    """AC-12/AC-14: removes ONE row from the registry. `providers.toml` itself never
    auto-removes anything ('a nadie le desaparece nada') -- this command IS the explicit
    user action the registry's own no-goal defers to. Takes effect in the live
    `opencode.json` only at the next `./build.sh --install` (AC-14's manifest-diff prune
    step in `install.py`) -- this command never edits that file itself."""
    entries = dict(_load_providers_registry())
    if provider_id not in entries:
        print(f"PROVIDER_UNKNOWN {provider_id}")
        return 2
    removed = entries.pop(provider_id)
    atomic_write(PROVIDERS_TOML_PATH, provider_registry.serialize_providers_toml(entries))
    print(f"PROVIDER_REMOVED id={provider_id} origin={removed.origin} — {_INSTALL_HINT}")
    return 0


# --------------------------------------------------------------------- vault
# Company-level Obsidian vault: one graph per company/client. Default mode:
# project notes live INSIDE each repo (docs/notas/, versioned, auto-rendered
# by feature-state.py) and join the vault through a symlink under Proyectos/.
# Private mode inverts that: notes live INSIDE the vault (so syncing the vault
# folder between machines carries them) and the repo holds a git-excluded
# symlink — nothing note-related ever reaches the project's remote.

# vault_ops.py: registry read/write, seed text, migration planning/repair, doctor reporting.
# `find_vault`/`_resolve_vault`/`cmd_vault_init`/`cmd_vault_link`/`apply_vault_migration`/
# `cmd_vault_doctor`/`vault_menu` stay here (see vault_ops.py's own module docstring for why:
# they need `app_config`/`write_app_config`/`STATE_DIR`, which must stay in this file).
from vault_ops import (  # noqa: E402
    VAULT_HUB, VAULT_REGISTRY, vault_registry_path, read_vault_registry, write_vault_registry_entry,
    vault_seed_hub, vault_seed_case_template, project_notes_seed, _git_rev_parse, _git_exclude_path,
    _notes_currently_excluded, exclude_notes_from_git, vault_link_private, VaultMigrationError,
    vault_migration_plan, _vault_project_dir_for, _vault_side_for_doctor, vault_doctor_report,
    _plan_fingerprint, _read_vault_doctor_marker as _vault_ops_read_vault_doctor_marker,
)


# AC-14: fixed core-plugin set, no community plugin manager. Ids verified against a real,
# already-configured Obsidian vault on this machine (~/iey/obsidian/.obsidian/core-plugins.json),
# not guessed — "backlink"/"tag-pane"/"global-search" are the real ids, not the spec's colloquial
# "backlinks"/"tags"/"search". app.json/appearance.json start empty, same as every vault Obsidian
# itself creates; Obsidian fills them in as the user configures the app, never overwritten here
# after first creation.
OBSIDIAN_CORE_PLUGINS = {"graph": True, "backlink": True, "outline": True, "global-search": True, "tag-pane": True}


def cmd_vault_init(target, company=None):
    target = Path(target).expanduser()
    company = company or target.resolve().name.upper()
    vault = target / "obsidian"
    seeds = {
        vault / VAULT_HUB: vault_seed_hub(company),
        vault / company / "contexto.md": (
            f"# {company} — contexto\n\n_TODO: contexto general de la empresa/cliente que "
            "cualquier agente debería conocer antes de trabajar en sus proyectos._\n"
        ),
        vault / "Casos" / "00 - Plantilla Caso.md": vault_seed_case_template(),
        vault / ".obsidian" / "app.json": "{}\n",
        vault / ".obsidian" / "appearance.json": "{}\n",
        vault / ".obsidian" / "core-plugins.json": json.dumps(OBSIDIAN_CORE_PLUGINS, indent=2) + "\n",
    }
    created = False
    for path, content in seeds.items():
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            print(f"VAULT_CREATED {path.relative_to(target)}")
            created = True
    projects = vault / "Proyectos"
    if not projects.exists():
        projects.mkdir(parents=True)
        created = True
    write_app_config(vault=str(vault.resolve()))  # AC-15: known-vault fallback for find_vault()
    print(f"{'VAULT_INIT_OK' if created else 'VAULT_INIT_SKIP'} dir={vault}")
    return 0


def find_vault(project, explicit=None):
    if explicit:
        vault = Path(explicit).expanduser()
        return vault if (vault / VAULT_HUB).exists() else None
    for ancestor in Path(project).resolve().parents:
        candidate = ancestor / "obsidian"
        if (candidate / VAULT_HUB).exists():
            return candidate
    configured = app_config().get("vault")
    if configured and (Path(configured).expanduser() / VAULT_HUB).exists():
        return Path(configured).expanduser()
    return None


def project_notes_seed(project_name):
    # feature-state.py regenerates the auto block; this seed adds the manual frame.
    return (
        f"# {project_name} — notas\n\n"
        "<!-- notas:auto -->\n_Se completa solo con la primera mutación de estado "
        "(o corré `python3 ai/scripts/feature-state.py sync-notes`)._\n<!-- /notas:auto -->\n\n"
        "## Notas propias\n\n_Qué es este proyecto, contexto, links útiles — esto no se pisa._\n"
    )


def _git_rev_parse(project, *args):
    """`git -C project rev-parse <args>`, hardened the same way as `git()` above:
    a purged env (a `GIT_DIR`/`GIT_WORK_TREE`/`GIT_COMMON_DIR`/`GIT_INDEX_FILE` inherited
    from the caller's shell would redirect git at a repo `project` never named -- verified
    live: with a stray `GIT_DIR` set, `rev-parse --git-common-dir` happily answers about an
    unrelated repo even for a `project` that isn't inside any repo at all), a timeout (never
    hang the CLI on git), and a caught missing binary. Returns None on any failure.
    """
    env = {
        key: value for key, value in os.environ.items()
        if key not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE")
    }
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        result = subprocess.run(
            ["git", "-C", str(project), "rev-parse", *args],
            capture_output=True, text=True, timeout=10, check=False, env=env,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _git_exclude_path(project):
    """The real `info/exclude` for `project`, resolved via `git rev-parse
    --git-common-dir` rather than assuming `.git` is a directory -- a linked git
    worktree's `.git` is a FILE (a `gitdir:` pointer), and `info/exclude` is not
    per-worktree: it lives in the common dir all worktrees of a repo share. Returns
    None when `project` isn't inside a git repo at all, OR when it's a subdirectory of
    someone else's repo rather than a repo root itself (`--show-toplevel` walks UP past
    `project`, so a project with no `.git` of its own but sitting inside e.g. `~/iey`'s own
    repo would otherwise silently write into -- and report notes_excluded=true against --
    a repo the caller never named, and whose root-anchored `docs/notas` pattern would not
    even match the nested path).
    """
    toplevel = _git_rev_parse(project, "--show-toplevel")
    if toplevel is None or Path(toplevel) != Path(project).resolve():
        return None
    common = _git_rev_parse(project, "--git-common-dir")
    if common is None:
        return None
    common_dir = Path(common) if Path(common).is_absolute() else project / common
    return common_dir / "info" / "exclude"


def _notes_currently_excluded(project):
    exclude = _git_exclude_path(project)
    return exclude is not None and exclude.exists() and "docs/notas" in exclude.read_text().splitlines()


def exclude_notes_from_git(project):
    """Hide docs/notas from the project's git locally (.git/info/exclude, never pushed)."""
    exclude = _git_exclude_path(project)
    if exclude is None:
        return False
    exclude.parent.mkdir(parents=True, exist_ok=True)
    lines = exclude.read_text().splitlines() if exclude.exists() else []
    if "docs/notas" in lines:
        return False
    exclude.write_text("\n".join(lines + ["docs/notas"]) + "\n")
    return True


def vault_link_private(project, target_vault, notes, notes_home):
    """Private mode: notes live in the vault; the repo gets an excluded symlink."""
    if notes.is_symlink():
        if notes.resolve() == notes_home.resolve():
            if exclude_notes_from_git(project):
                print("VAULT_PRIVATE_EXCLUDED docs/notas (.git/info/exclude)")
            write_vault_registry_entry(
                target_vault, project, topology="private", vault_path=notes_home,
                notes_excluded=_notes_currently_excluded(project),
            )
            print(f"VAULT_LINK_SKIP project={project.name} vault={target_vault} mode=private")
            return 0
        print(f"VAULT_LINK_CONFLICT {notes} ya apunta a {notes.resolve()} — resolvelo a mano")
        return 1
    if notes_home.is_symlink():
        # Old outward link (vault -> repo) from default mode: replace with the real home.
        notes_home.unlink()
    if notes_home.exists() and not notes_home.is_dir():
        print(f"VAULT_LINK_CONFLICT {notes_home} existe y no es un directorio — resolvelo a mano")
        return 1
    notes_home.mkdir(parents=True, exist_ok=True)
    if notes.is_dir():
        # Migrate repo-resident notes into the vault: never clobber a differing file.
        files = [path for path in sorted(notes.rglob("*")) if path.is_file()]
        conflicts = [
            path.relative_to(notes) for path in files
            if (notes_home / path.relative_to(notes)).exists()
            and (notes_home / path.relative_to(notes)).read_bytes() != path.read_bytes()
        ]
        if conflicts:
            listed = ", ".join(str(item) for item in conflicts[:5])
            print(f"VAULT_LINK_CONFLICT notas difieren entre repo y vault ({listed}) — resolvelo a mano")
            return 1
        for path in files:
            destination = notes_home / path.relative_to(notes)
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(destination))
        shutil.rmtree(notes)
    seed = notes_home / "00 - Proyecto.md"
    if not seed.exists():
        seed.write_text(project_notes_seed(project.name))
        print(f"VAULT_CREATED {seed}")
    notes.parent.mkdir(parents=True, exist_ok=True)
    try:
        notes.symlink_to(os.path.relpath(notes_home, notes.parent))
    except OSError as exc:
        print(f"VAULT_LINK_CONFLICT no pude crear el symlink: {exc}")
        return 1
    if exclude_notes_from_git(project):
        print("VAULT_PRIVATE_EXCLUDED docs/notas (.git/info/exclude)")
    write_vault_registry_entry(
        target_vault, project, topology="private", vault_path=notes_home,
        notes_excluded=_notes_currently_excluded(project),
    )
    print(f"VAULT_LINK_OK project={project.name} vault={target_vault} mode=private")
    return 0


def cmd_vault_link(project, vault=None, private=False):
    project = Path(project).expanduser().resolve()
    if not project.is_dir():
        print(f"VAULT_NOT_FOUND proyecto inexistente: {project}")
        return 2
    target_vault = find_vault(project, vault)
    if target_vault is None:
        print("VAULT_NOT_FOUND: no hay obsidian/00 - INICIO.md en los ancestros; corré --vault-init o pasá --vault")
        return 2
    write_app_config(vault=str(target_vault.resolve()))  # AC-15: known-vault fallback for find_vault()
    notes = project / "docs" / "notas"
    if private:
        return vault_link_private(project, target_vault, notes, target_vault / "Proyectos" / project.name)
    seed = notes / "00 - Proyecto.md"
    if not seed.exists():
        notes.mkdir(parents=True, exist_ok=True)
        seed.write_text(project_notes_seed(project.name))
        print(f"VAULT_CREATED {seed}")
    link = target_vault / "Proyectos" / project.name
    if link.is_symlink():
        if link.resolve() == notes.resolve():
            write_vault_registry_entry(target_vault, project, topology="hybrid", vault_path=link, notes_excluded=_notes_currently_excluded(project))
            print(f"VAULT_LINK_SKIP project={project.name} vault={target_vault}")
            return 0
        print(f"VAULT_LINK_CONFLICT {link} ya apunta a {link.resolve()} — resolvelo a mano")
        return 1
    if link.exists():
        print(f"VAULT_LINK_CONFLICT {link} existe y no es symlink — resolvelo a mano")
        return 1
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        relative = os.path.relpath(notes, link.parent)
        link.symlink_to(relative)
    except OSError as exc:
        print(f"VAULT_LINK_CONFLICT no pude crear el symlink: {exc}")
        return 1
    write_vault_registry_entry(target_vault, project, topology="hybrid", vault_path=link, notes_excluded=_notes_currently_excluded(project))
    print(f"VAULT_LINK_OK project={project.name} vault={target_vault}")
    return 0


def apply_vault_migration(project, target_vault, vault_project_dir, plan, *, exclude_notes=True):
    """Executes a `pure-move`/`merge` plan. Copy-verify-then-delete PER FILE (never a bare
    `shutil.move`, never a batch delete after a batch copy): an interrupted run leaves both
    copies present for whatever it hadn't reached yet, and a re-run is idempotent because
    `vault_migration_plan` skips files already copied and byte-identical. Reuses
    `cmd_vault_link`'s own hybrid-linking code for the final symlink instead of duplicating it.
    """
    if plan["action"] not in ("pure-move", "merge"):
        raise VaultMigrationError(f"cannot apply a plan with action={plan['action']!r}")
    project = Path(project)
    vault_project_dir = Path(vault_project_dir)
    notes = project / "docs" / "notas"
    notes.mkdir(parents=True, exist_ok=True)
    for rel in plan["files"]:
        src = vault_project_dir / rel
        dest = notes / rel
        # SEC-003: containment on both ends, re-checked here rather than trusted from the
        # plan -- plan and apply can run far apart, and a symlink planted at `dest` (e.g. a
        # dangling link into a repo outside the tree) is invisible to `dest.exists()` but
        # `shutil.copy2` still writes straight through it. Demonstrated arbitrary write.
        if _resolve_within(src, vault_project_dir) is None:
            raise VaultMigrationError(f"VAULT_MIGRATION_UNSAFE_SOURCE {rel}: source escapes the vault project dir")
        if dest.is_symlink() or _resolve_within(dest, notes) is None:
            raise VaultMigrationError(f"VAULT_MIGRATION_UNSAFE_DEST {rel}: destination is a symlink or escapes docs/notas")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        if dest.stat().st_size != src.stat().st_size or dest.read_bytes() != src.read_bytes():
            raise VaultMigrationError(f"VAULT_MIGRATION_VERIFY_FAILED {rel}: copy did not match source")
        src.unlink()
    for rel in plan.get("already_present", []):
        # Byte-identical (re-verified, never trusted from a stale plan): safe to drop the
        # vault-side original without copying anything new.
        src, dest = vault_project_dir / rel, notes / rel
        if _resolve_within(src, vault_project_dir) is None or _resolve_within(dest, notes) is None:
            raise VaultMigrationError(f"VAULT_MIGRATION_UNSAFE_PATH {rel}: source or destination escapes its tree")
        if src.read_bytes() != dest.read_bytes():
            raise VaultMigrationError(f"VAULT_MIGRATION_VERIFY_FAILED {rel}: no longer byte-identical since planning")
        src.unlink()
    # Drop now-empty subdirectories left behind on the vault side, deepest first; never rmtree
    # (a directory that still holds something -- e.g. a sibling file this plan didn't touch --
    # simply fails to rmdir and is left alone).
    all_rel = plan["files"] + plan.get("already_present", [])
    emptied = sorted({(vault_project_dir / rel).parent for rel in all_rel}, key=lambda p: -len(p.parts))
    for directory in emptied:
        try:
            directory.rmdir()
        except OSError:
            pass
    if exclude_notes:
        exclude_notes_from_git(project)
    try:
        vault_project_dir.rmdir()
    except OSError:
        pass  # not empty or already gone -- cmd_vault_link below still succeeds either way
    return cmd_vault_link(project, vault=str(target_vault), private=False)


# ---------------------------------------------------------------- vault doctor (AC-17)

def _resolve_vault(explicit=None):
    """Same tail as find_vault(), for the no-project report pass: explicit path, else the
    configured fallback. Never walks ancestors — there is no project to walk from."""
    if explicit:
        vault = Path(explicit).expanduser()
        return vault if (vault / VAULT_HUB).exists() else None
    configured = app_config().get("vault")
    if configured and (Path(configured).expanduser() / VAULT_HUB).exists():
        return Path(configured).expanduser()
    return None


def _vault_doctor_marker_path(project):
    key = hashlib.sha256(str(Path(project).resolve()).encode()).hexdigest()[:16]
    return STATE_DIR / "vault-doctor-pending" / f"{key}.json"


# SEC-008: a --dry-run marker with no expiry stayed valid forever -- a marker backdated (or
# simply forgotten) by hours was still accepted for --repair. 15 minutes covers the real
# workflow (dry-run, read the plan, confirm, repair) without turning into a standing grant.
VAULT_DOCTOR_MARKER_TTL_SECONDS = 900


def _read_vault_doctor_marker(marker):
    """Consume the marker (single-use, atomically-enough for a single-operator CLI) and
    return its parsed content, or None if it's absent/corrupt/expired/stale. SEC-008: a
    corrupt marker used to raise `json.JSONDecodeError` straight through the CLI, and an
    expired one had no TTL at all -- see `vault_ops._read_vault_doctor_marker` (the
    read/unlink/parse step, moved out) for the single-use-consumption details; the TTL check
    itself stays here because it needs `VAULT_DOCTOR_MARKER_TTL_SECONDS`, kept alongside
    `cmd_vault_doctor` for the same STATE_DIR-monkeypatch reasons documented on vault_ops.py.
    """
    recorded = _vault_ops_read_vault_doctor_marker(marker)
    if recorded is None:
        return None
    try:
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(recorded["at"].replace("Z", "+00:00"))).total_seconds()
    except (KeyError, ValueError):
        return None
    if age > VAULT_DOCTOR_MARKER_TTL_SECONDS:
        return None
    return recorded


def cmd_vault_doctor(project=None, vault=None, dry_run=False, repair=False, exclude_notes=True):
    # AC-21: missing Obsidian is a steady WARNING, never a blocking exit -- the file vault
    # (docs/notas/, plain git-tracked markdown) works with or without a GUI to browse it in.
    if not shutil.which("obsidian"):
        print("VAULT_DOCTOR_WARNING obsidian no está instalado — el vault de archivos sigue funcionando igual; instalalo con --tools-install obsidian si querés navegarlo con la app")
    if project is None:
        if repair:
            print("VAULT_DOCTOR_REPAIR_REFUSED reason=no-project — --repair exige --project, nunca headless/generico")
            return 1
        resolved_vault = _resolve_vault(vault)
        if resolved_vault is None:
            print("VAULT_NOT_FOUND: no hay vault configurado — corré --vault-init o pasá --vault")
            return 2
        for row in vault_doctor_report(resolved_vault):
            if row["project"] is not None:
                print(f"VAULT_DOCTOR project={row['project']} topology={row['topology']} health={row['health']}")
            else:
                print(f"VAULT_DOCTOR_UNREGISTERED vault_path={row['vault_path']} health=unregistered")
        return 0

    project_path = Path(project).expanduser().resolve()
    resolved_vault = find_vault(project_path, vault)
    if resolved_vault is None:
        print("VAULT_NOT_FOUND: no hay obsidian/00 - INICIO.md en los ancestros; corré --vault-init o pasá --vault")
        return 2
    vault_side, refusal = _vault_side_for_doctor(resolved_vault, project_path)
    if vault_side is None:
        print(f"VAULT_DOCTOR_REPAIR_REFUSED reason={refusal}")
        return 1
    plan = vault_migration_plan(project_path, vault_side)
    marker = _vault_doctor_marker_path(project_path)

    if repair:
        if plan["action"] not in ("pure-move", "merge"):
            print(f"VAULT_DOCTOR_REPAIR_REFUSED action={plan['action']} — nada para reparar de forma segura; corré --dry-run para ver el detalle")
            return 1
        if not marker.exists():
            print("VAULT_DOCTOR_REPAIR_REFUSED reason=no-dry-run — corré --vault-doctor --project ... --dry-run primero")
            return 1
        # SEC-008: consumes (unlinks) the marker before trusting its content -- single-use
        # either way, and a corrupt/expired/absent marker degrades to a clean refusal instead
        # of an uncaught JSONDecodeError.
        recorded = _read_vault_doctor_marker(marker)
        if recorded is None:
            print("VAULT_DOCTOR_REPAIR_REFUSED reason=marker-invalid-or-expired — corré --vault-doctor --project ... --dry-run de nuevo")
            return 1
        if recorded.get("fingerprint") != _plan_fingerprint(plan):
            print("VAULT_DOCTOR_REPAIR_REFUSED reason=plan-changed-since-dry-run — el estado del disco cambió, corré --dry-run de nuevo")
            return 1
        rc = apply_vault_migration(
            project_path, resolved_vault, vault_side, plan, exclude_notes=recorded.get("exclude_notes", True),
        )
        if rc == 0:
            print(f"VAULT_DOCTOR_REPAIRED project={project_path} action={plan['action']}")
        return rc

    if dry_run:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps({
            "fingerprint": _plan_fingerprint(plan),
            "exclude_notes": bool(exclude_notes),
            "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }))
        print(f"VAULT_DOCTOR_PLAN project={project_path} action={plan['action']}")
        for key in ("files", "already_present", "conflicts"):
            if plan.get(key):
                print(f"  {key}: {', '.join(plan[key])}")
        return 0

    print(f"VAULT_DOCTOR project={project_path} action={plan['action']}")
    return 0


# context_pack.py: --context (AC-18, read-only) leaf helpers. `_resolve_within` is also used
# above by `apply_vault_migration`. `cmd_context` itself stays defined here (not in
# context_pack.py): it calls `find_vault`/`read_vault_registry`, and `find_vault` must stay in
# this file too (see context_pack.py's own module docstring for why moving it would be a
# circular import).
from context_pack import (  # noqa: E402
    CONTEXT_BYTE_CAP, CONTEXT_SECTION_BYTE_CAP, _RESERVED_VAULT_CHILDREN, _cap_text_bytes,
    _read_capped, _extract_section, _resolve_company_dir, _UNTRUSTED_OPEN, _UNTRUSTED_CLOSE,
    _mark_untrusted, _resolve_within,
)


def cmd_context(project=None, as_json=False):
    """Read-only (ORQ-1/AC-18/AC-19). Degrades honestly at every step, never crashes, never
    fabricates: no vault -> VAULT_NOT_FOUND-shaped result; no company dir -> hub-only; no project
    note -> reported absent (null), not invented. NEVER reads credential surfaces -- it touches
    exactly four paths (hub, company contexto.md, the project's own note, nothing else) and none
    of them is under a CLI's auth store.
    """
    project_path = Path(project or ".").expanduser().resolve()
    vault = find_vault(project_path)
    if vault is None:
        result = {"hub": None, "company": None, "project": None, "pending": None}
        if as_json:
            print(json.dumps(result))
        else:
            print("CONTEXT_VAULT_NOT_FOUND")
        return 0
    hub = _read_capped(vault / VAULT_HUB)
    company_dir = _resolve_company_dir(vault)
    company = _read_capped(company_dir / "contexto.md") if company_dir else None
    registry = read_vault_registry(vault)
    entry = registry.get(str(project_path))
    if entry and entry.get("topology") == "private":
        # SEC-002: the registry is an externally-writable, Syncthing-synced file. A
        # `vault_path` pointing outside the vault, or a note file that is itself a symlink
        # escaping it, must never reach _read_capped -- that's how a fake `vault_path` or a
        # planted symlink turned this read-only, credential-surface-excluded command into a
        # generic file-exfiltration primitive (demonstrated against a fake auth.json).
        candidate = Path(entry["vault_path"]) / "00 - Proyecto.md"
        project_note_path = _resolve_within(candidate, vault)
    else:
        project_note_path = project_path / "docs" / "notas" / "00 - Proyecto.md"
    project_note = _read_capped(project_note_path) if project_note_path else None
    # SEC-006: `pending` is extracted from the RAW note, before marking -- otherwise the
    # marker text itself would leak into the extracted section, or get extracted twice.
    pending = _extract_section(project_note, "## Qué falta")
    result = {
        "hub": _mark_untrusted(hub), "company": _mark_untrusted(company),
        "project": _mark_untrusted(project_note), "pending": _mark_untrusted(pending),
    }
    if as_json:
        print(json.dumps(result))
        return 0
    print("CONTEXT_OK" if hub is not None else "CONTEXT_HUB_ABSENT")
    for label, value in result.items():
        if value:
            print(f"--- {label} ---")
            print(value)
    return 0


# graph_wrapper.py: --graph, a thin subprocess wrapper (its own `cmd_graph`, distinct from
# feature_state_lib/graph.py's internal `cmd_graph` used by feature-state.py itself).
from graph_wrapper import cmd_graph as _graph_wrapper_cmd_graph  # noqa: E402


def cmd_graph(feature_ids=None, project=None, out=None):
    return _graph_wrapper_cmd_graph(feature_ids, project, out, root=ROOT)


_VAULT_INTRO = "El vault de empresa junta las notas de todos tus proyectos en un solo grafo Obsidian."


def vault_menu():
    # F-03: the intro line travels as `header=` into every picker's own frame instead of being
    # print()ed to the normal screen right before the FIRST picker's alternate screen erases it
    # (AC-25/AC-26 nested composition: a single `TerminalSession` wraps all 3 chained pickers so
    # none of them re-swaps the alternate screen for what is one interaction, not three).
    style = {"color": color, "bold": bold, "dim": dim}
    with tui.TerminalSession():
        target_result = tui.run_picker(
            (), freetext_allowed=True, style=style, header=_VAULT_INTRO,
            prompt="Directorio de la empresa (ej ~/acme; Esc vuelve):",
        )
        target = target_result.value.strip() if isinstance(target_result, tui.FreeText) else ""
        if not target:
            return
        # cmd_vault_init prints/creates seed files -- suspend so it runs in cooked mode
        # (AC-26) rather than under the still-active alternate screen the pickers share.
        with tui.suspend_terminal():
            cmd_vault_init(target)
        project_result = tui.run_picker(
            (), freetext_allowed=True, style=style, header=_VAULT_INTRO,
            prompt="¿Linkear un proyecto ahora? (path; Esc salta):",
        )
        project = project_result.value.strip() if isinstance(project_result, tui.FreeText) else ""
        if not project:
            return
        private_choice = tui.run_picker(
            ("No — notas en el repo (hybrid)", "Sí — notas solo en el vault (privado)"),
            style=style, header=_VAULT_INTRO,
            prompt="¿Privado? Las notas privadas quedan FUERA del git del proyecto:",
        )
        # F-07: cancelling this step (Esc/Ctrl-C/EOF) must never fall through to a default --
        # same "cancel never reaches a mutating command" contract every other chained picker in
        # this module keeps (mcp_menu's action/harness steps).
        if not isinstance(private_choice, tui.Selected):
            return
        private = private_choice.index == 1
    cmd_vault_link(project, str(Path(target).expanduser() / "obsidian"), private)


# ------------------------------------------------------------------- plugins

def claude_settings_path():
    return Path.home() / ".claude/settings.json"


def _plugins_data():
    """AC-28: the data cmd_plugins()/plugins_menu() both render -- [(name, enabled), ...]."""
    return sorted(read_json(claude_settings_path()).get("enabledPlugins", {}).items())


def cmd_plugins():
    plugins = _plugins_data()
    if not plugins:
        print("PLUGINS_NONE")
    for name, enabled in plugins:
        print(f"PLUGIN {name} enabled={'true' if enabled else 'false'}")
    return 0


def cmd_plugin_set(name, enabled):
    if name == "engram@engram":
        print("PLUGIN_MANAGED engram@engram — la política del repo lo fuerza apagado en cada install")
        return 1
    data = read_json_for_write(claude_settings_path())
    data.setdefault("enabledPlugins", {})[name] = enabled
    atomic_write(claude_settings_path(), json.dumps(data, indent=2) + "\n")
    print(f"PLUGIN_SET {name} enabled={'true' if enabled else 'false'}")
    return 0


_MCP_ACTIONS = ("Agregar", "Encender", "Apagar", "Remover")


def mcp_menu():
    """AC-24/AC-26/AC-29: three chained pickers instead of three raw `input()` lines --
    server (free-text ALLOWED: a name outside the catalog is still valid for --mcp-remove-style
    cleanup, same as the old input() line accepted anything), then action and harness, both
    CLOSED enums with no free text at all. Closing the enums is what "mcp_menu's free-text
    inputs validated" (AC-29) means in practice: action/harness can no longer be a garbage
    string `cmd_mcp_toggle` silently ignores -- they are picked, not typed. There is no raw
    `input()` left in this function at all, so the AC-26 terminal-handoff concern that applied
    to the old input() lines doesn't even arise here anymore; every step is its own picker.
    """
    data = _mcp_data()
    targets = mcp_targets()
    header_lines = [f"harnesses detectados: {', '.join(targets)}"]
    for name, states in data:
        rendered = ", ".join(f"{h}:{s}" for h, s in states)
        header_lines.append(f"  {name:<12} {rendered}")
    header = "\n".join(header_lines)
    style = {"color": color, "bold": bold, "dim": dim}
    catalog = [name for name, _ in data]
    # F-03: `header` carries this context into EVERY chained picker's own frame (it stays
    # visible across all 3 steps, not just the first), and the whole chain shares ONE
    # `TerminalSession` so picking "Server" -> "Acción" -> "Harness" swaps the alternate screen
    # once for the interaction, not three times.
    with tui.TerminalSession():
        server_choice = tui.run_picker(catalog, freetext_allowed=True, style=style, header=header, prompt="Server:")
        if isinstance(server_choice, tui.Selected):
            name = catalog[server_choice.index]
        elif isinstance(server_choice, tui.FreeText):
            name = server_choice.value.strip()
        else:
            return
        if not name:
            return
        action_choice = tui.run_picker(_MCP_ACTIONS, style=style, header=header, prompt="Acción:")
        if not isinstance(action_choice, tui.Selected):
            return
        harness_options = ("Todos",) + tuple(targets)
        harness_choice = tui.run_picker(harness_options, style=style, header=header, prompt="Harness:")
        if not isinstance(harness_choice, tui.Selected):
            return
    harness = None if harness_choice.index == 0 else harness_options[harness_choice.index]
    action = _MCP_ACTIONS[action_choice.index]
    if action == "Agregar":
        cmd_mcp_add(name, harness)
    elif action == "Encender":
        cmd_mcp_toggle(name, harness, True)
    elif action == "Apagar":
        cmd_mcp_toggle(name, harness, False)
    elif action == "Remover":
        cmd_mcp_remove(name, harness)


def plugins_menu():
    # AC-29: human-readable text, never the raw machine format cmd_plugins() prints for
    # scripted callers -- rendered straight from _plugins_data(), not by shelling out to
    # cmd_plugins()'s own stdout.
    plugins = _plugins_data()
    if not plugins:
        print("(sin plugins instalados)")
        return
    items = [f"{name} — {'activado' if enabled else 'apagado'}" for name, enabled in plugins]
    choice = tui.run_picker(items, style={"color": color, "bold": bold, "dim": dim})
    if isinstance(choice, tui.Selected):
        name, enabled = plugins[choice.index]
        cmd_plugin_set(name, not enabled)


# ---------------------------------------------------------------------- menu

def cmd_scaffold(target: str | None) -> int:
    """Create only the P1 project marker, generic state helpers, and stable identity."""
    root = Path(target or os.getcwd()).resolve()
    created: list[str] = []
    conflicts: list[str] = []
    skips: list[str] = []
    features = root / "ai/state/features"
    if not features.exists():
        features.mkdir(parents=True)
        created.append("ai/state/features")
    elif not _real_directory(features):
        print("SCAFFOLD_CONFLICT path=ai/state/features reason=not_directory")
        print("SCAFFOLD_CONFLICTS n=1")
        return 1
    else:
        skips.append("ai/state/features")
    template_dir = ROOT / "PROYECTO/ai/scripts"
    feature_state_lib_dir = template_dir / "feature_state_lib"
    feature_state_lib_names = tuple(
        f"feature_state_lib/{path.name}"
        for path in sorted(feature_state_lib_dir.glob("*.py"))
    ) if feature_state_lib_dir.is_dir() else ()
    for name in ("feature-state.py", *feature_state_lib_names, "check-owned-paths.py"):
        source, destination = template_dir / name, root / "ai/scripts" / name
        if not source.is_file():
            conflicts.append(f"ai/scripts/{name}")
            print(f"SCAFFOLD_CONFLICT path=ai/scripts/{name} reason=template_missing")
            continue
        try:
            destination.lstat()
        except FileNotFoundError:
            pass
        except OSError:
            conflicts.append(f"ai/scripts/{name}")
            print(f"SCAFFOLD_CONFLICT path=ai/scripts/{name} reason=unreadable")
            continue
        else:
            existing = _safe_read(destination, limit=_MAX_FEATURE_BYTES)
            source_bytes = source.read_bytes()
            if existing != source_bytes:
                conflicts.append(f"ai/scripts/{name}")
                print(f"SCAFFOLD_CONFLICT path=ai/scripts/{name} reason=differs")
            else:
                skips.append(f"ai/scripts/{name}")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
        destination.chmod(0o755)
        created.append(f"ai/scripts/{name}")
    identity = root / "ai/state/project.json"
    try:
        identity.lstat()
    except FileNotFoundError:
        identity_exists = False
    except OSError:
        identity_exists = True
    else:
        identity_exists = True
    if identity_exists:
        try:
            key = project_key_for(root, require_persisted=True)
        except ValueError:
            conflicts.append("ai/state/project.json")
            print("SCAFFOLD_CONFLICT path=ai/state/project.json reason=invalid_identity")
            key = None
        else:
            skips.append("ai/state/project.json")
    else:
        key = "proj1_" + secrets.token_hex(16)
        payload = {"schema": 1, "project_key": key, "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
        identity.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
        identity.chmod(0o644)
        created.append("ai/state/project.json")
    if conflicts:
        print(f"SCAFFOLD_CONFLICTS n={len(conflicts)}")
        return 1
    for path in created:
        print(f"SCAFFOLD_CREATED path={path}")
    for path in skips:
        print(f"SCAFFOLD_SKIP path={path}")
    _scaffold_attempt_obsidian_once(root)
    print(f"SCAFFOLD_OK project={root} project_key={key}")
    return 0


OBSIDIAN_INSTALL_MARKER = "obsidian-install.json"


def _scaffold_attempt_obsidian_once(root):
    """AC-21: attempt the Obsidian install exactly once per project, ever — never inside a
    retry loop, and never letting the outcome (ok/declined/manual/no-method) propagate as a
    `--scaffold` failure. The file vault (docs/notas/, git-tracked markdown) works with or
    without Obsidian installed; this only affects whether there's a GUI to browse it in.
    """
    marker = root / "ai/state" / OBSIDIAN_INSTALL_MARKER
    if marker.exists():
        return  # already attempted (any outcome) -- never re-prompt on a later --scaffold
    if shutil.which("obsidian"):
        outcome = "already-installed"
    else:
        try:
            rc = cmd_tools_install("obsidian", dry=False, yes=False)
        except Exception:
            rc = 1
        outcome = "ok" if rc == 0 else "declined"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({
        "outcome": outcome,
        "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }))


def cmd_routing_migrate() -> int:
    try:
        key = project_key_for(ROOT, require_persisted=True)
        # Production keeps ADR-0005's fixed store root. The existing seam is
        # used only by hermetic tests, so migration can be exercised safely.
        rows, backup, moved_from, moved_to = _routing_store().migrate(key)
    except (ValueError, routing.RoutingError, OSError) as exc:
        print("ROUTING_MIGRATE_FAILED", file=sys.stderr)
        # 007 AC-05: a database that genuinely cannot be migrated says which object
        # diverged.  Read with getattr so this file never imports the store's class, and
        # printed after the reason code so the first line and the exit code are unchanged.
        detail = getattr(exc, "schema_diagnostic", None)
        if detail:
            print(detail, file=sys.stderr)
        return 2
    # 007 AC-14: the observed versions, not a hardcoded pair. ADR-0008 D8 pinned the literal
    # `from=4 to=5`; ADR-0010 D4 supersedes that clause and only that clause. The format is
    # unchanged — same keys, same order — because once schema 6 exists `from=4 to=5` is a
    # false statement rather than a formatting choice.
    print(f"ROUTING_MIGRATE_OK from={moved_from} to={moved_to} rows={rows} backup={backup}")
    return 0


def run_tty(command):
    """Foreground child with inherited TTY: sudo/login prompts must reach the user. AC-26:
    wrapped with `tui.suspend_terminal()` so a subprocess launched while a picker session is
    still active (nested composition) gets cooked mode for its prompts too -- a no-op under
    the normal per-call picker sessions this module uses today, where control is already back
    in cooked mode by the time any menu branch reaches here."""
    with tui.suspend_terminal():
        return subprocess.run(command, check=False).returncode


DRIFT_BADGE = {
    "ok": lambda: color("OK", "32"),
    "stale": lambda: color("DESACTUALIZADO", "33"),
    "unknown": lambda: "?",
}


# ------------------------------------------------------------ menu panels
def _term_width():
    try:
        return max(40, shutil.get_terminal_size().columns)
    except (ValueError, OSError):
        return 80


def _clip(line, width):
    """Truncate a plain (no-ANSI) line to the real terminal width."""
    return line if len(line) <= width else line[: width - 1] + "…"


def table_lines(rows, indent="  "):
    """Aligned plain-text columns clamped to the live terminal width — the shared
    renderer for every menu panel (Estado, Modelos header, Herramientas). Pure on
    its inputs except for the width read; no hardcoded widths, no ANSI inside
    (escape codes break the length math), colors get applied by callers on whole lines."""
    rows = [tuple(str(cell) for cell in row) for row in rows]
    if not rows:
        return []
    columns = max(len(row) for row in rows)
    widths = [max((len(row[i]) for row in rows if len(row) > i), default=0) for i in range(columns)]
    width = _term_width()
    lines = []
    for row in rows:
        cells = [row[i].ljust(widths[i]) for i in range(len(row))]
        lines.append(_clip((indent + "  ".join(cells)).rstrip(), width))
    return lines


def _estado_general_lines(data):
    """The 'Estado general' panel: everything --doctor-all knows, formatted for
    humans — harnesses with version+auth, install scope, catalog CLIs, live
    providers. Reuses _status_data's rows (already probed) and the shared probe
    cache; never prints credential material.

    ADR-0043 (022 PKG-3, AC-10): this is the first-menu-item 'vidriera' surface —
    probes against the SAME cache root `--route-decide` uses (`_probe_cache_root()`),
    never the legacy `STATE_DIR` one, and best-effort prunes the stale legacy sibling
    on the way (same discipline as `_write_probe_cache`).

    AC-19 (022 PKG-5): THE surface this AC names explicitly as "la vidriera" -- what a
    non-technical user checks to see "¿el harness ya ve mi suscripción nueva?" -- so the
    `listado`/`usable` split lands here too, not only in `--route-doctor`. `listado` is
    the raw, pre-ceiling count the provider's own CLI reports; `usable` is what survives
    the curated ceiling and is therefore actually routable."""
    lines = ["Harnesses"]
    lines += table_lines([(cli, version, auth) for cli, version, auth in data["rows"]])
    lines += table_lines([("pi", {"yes": "instalado", "via-pnpm-dlx": "vía pnpm dlx",
                                  "no": "FALTA (sin pnpm)"}[_pi_lane_state()], "-")])
    scope = _install_scope()
    if isinstance(scope, list):
        lines += ["", "Alcance de instalación", *table_lines([(", ".join(scope) or "none",)])]
    lines.append("")
    lines.append("Herramientas (catálogo)")
    lines += table_lines([(name, "instalado" if installed else "falta") for name, installed in _tools_data()])
    lines.append("")
    lines.append("Proveedores autenticados (probe)")
    try:
        from routing_core.catalog import prune_legacy_probe_cache, probe_listed_and_usable
        prune_legacy_probe_cache(STATE_DIR)
        listed, usable = probe_listed_and_usable(models_config.load_config(), cache_root=_probe_cache_root())
        all_pairs = sorted(set(listed) | set(usable))
        pairs = [(provider, runtime, f"listado={len(listed.get((runtime, provider), set()))} "
                                     f"usable={len(usable.get((runtime, provider), set()))}")
                 for (runtime, provider) in all_pairs]
        lines += table_lines(pairs) if pairs else ["  (ninguno — logueate en al menos una herramienta)"]
    except Exception:
        lines.append("  probe no disponible ahora (corré set-agents --doctor-all)")
    if data["drift"] == "stale":
        lines += ["", "drift: la instalación quedó atrás del repo → Instalar / Reparar o ./build.sh --install"]
    return lines


# Instalar / Reparar wizard: which AI CLI to install or apply the harness to
# (gentle-ai-style onboarding); values feed install.sh --harness verbatim.
HARNESS_CHOICES = (
    ("Todos (recomendado)", "all"),
    ("Claude Code (incluye el lane pi)", "claude"),
    ("OpenCode", "opencode"),
    ("Codex", "codex"),
    ("Solo Pi", "pi"),
)


# AC-24/AC-29: the single source of truth for the main menu's order -- Vault sits right
# before Salir (closing the menu-debt finding: the old numbered grid had it AFTER Salir, at
# index 9 while Salir was 8). Arrow-key navigation makes the bracketed numbers themselves
# cosmetic history, not a contract -- README.md/INSTALACION.md (AC-30) describe the selector,
# not literal [N] numbers.
#
# AC-01 (025/D1, ADR-0050): no emoji as structural icons -- they depend on the font, break
# alignment (proof was already IN this tuple: "🗒  Vault Obsidian"/"⏻  Salir" carried a
# patched-in second space because those two glyphs render at a different width than every
# other entry's emoji), and can't be themed. Hierarchy is now carried by `tui._render_items`
# alone: the `›` marker plus `bold()` on the selected row (already existed, unrelated to this
# change) IS the espaciado/peso the spec asks for -- consistent one-space `marker + text`,
# nothing here needs to compensate for glyph width ever again.
MENU_ITEMS = (
    "Estado general",
    "Instalar / Reparar",
    "Actualizar",
    "Modelos",
    "Herramientas (CLIs)",
    "Proponer herramienta nueva",
    "MCPs",
    "Plugins Claude Code",
    "Vault Obsidian",
    "Salir",
)


def menu():
    print()
    banner()
    if first_run():
        print()
        print(bold(f"Primera vez acá → leé README.md (sección {platform_label()}) para saber qué esperar."))
        write_app_config(auto_update=True)
    print(dim("· chequeando updates…"))
    update_badge = launch_update_check()
    # Drift regenerates a full staging (~2 s): cache it and refresh only after
    # actions that can change it, instead of on every redraw.
    drift = drift_state()
    style = {"color": color, "bold": bold, "dim": dim}
    while True:
        # F-03: this "=== SET-AGENTS sha === / drift: ... | update: ..." banner used to be
        # print()ed to the normal screen right before `run_picker` switched to the alternate
        # screen and cleared it -- invisible exactly while the user is choosing. It now also
        # travels as the menu picker's `header=`, so it stays on screen inside the picker's own
        # frame too.
        menu_header = (
            f"=== SET-AGENTS {short_sha()} ===\n"
            f"drift: {DRIFT_BADGE[drift]()} | update: {color(update_badge, '36')} | "
            + dim(f"auto-update: {'on' if auto_update_enabled() else 'off'}")
        )
        print()
        print(menu_header)
        # AC-29: Esc/Ctrl-C/EOF resolve to `None` INSIDE run_picker (never a raised
        # EOFError/KeyboardInterrupt reaching here) -- treated the same as picking Salir.
        choice = tui.run_picker(MENU_ITEMS, style=style, header=menu_header)
        if not isinstance(choice, tui.Selected):
            return 0
        index = choice.index
        if index == 0:
            # Estado general: the doctor-all panel, formatted, as the toggle
            # picker's header (F-03's lesson: print()s die with the alt-screen).
            drift = drift_state()
            print(dim("· relevando estado…"))
            status_data = _status_data(rows=True)
            estado_lines = _estado_general_lines(status_data)
            estado_header = "\n".join([_status_machine_line(status_data), ""] + estado_lines)
            toggle = tui.run_picker(
                (f"Togglear auto-update (hoy: {'on' if auto_update_enabled() else 'off'})", "Volver"),
                style=style, header=estado_header)
            if isinstance(toggle, tui.Selected) and toggle.index == 0:
                set_auto_update(not auto_update_enabled())
        elif index == 1:
            # gentle-ai-style onboarding: pick which AI CLI to install or apply
            # the harness to; Esc backs out without running anything.
            picked = tui.run_picker(
                [label for label, _ in HARNESS_CHOICES], style=style,
                header="¿Qué CLI de IA querés instalar o aplicarle el harness?")
            if isinstance(picked, tui.Selected):
                harness = HARNESS_CHOICES[picked.index][1]
                if run_tty([str(ROOT / "install.sh"), "--harness", harness]) != 0:
                    print(color("El instalador terminó con error — revisá la salida de arriba.", "31"))
                drift = drift_state()
        elif index == 2:
            if cmd_update() == 0:
                update_badge = "al día"
            drift = drift_state()
        elif index == 3:
            if run_tty([str(ROOT / "setup-models.sh")]) != 0:
                print(color("El wizard terminó con error — revisá la salida de arriba.", "31"))
            drift = drift_state()
        elif index == 4:
            tools_menu()
        elif index == 5:
            tools_propose_menu()
        elif index == 6:
            mcp_menu()
        elif index == 7:
            plugins_menu()
        elif index == 8:
            vault_menu()
        elif index == 9:
            return 0


# AC-02 (025/D1, ADR-0050) -- three groups, same criterion applied to each: what a
# spawn/orchestrator/wizard invokes but a human never types at a terminal is hidden;
# what a human actually reads about in README.md or a wizard panel stays visible.
#
# GROUP 1 -- machine-lifecycle routing primitives: mutate a run's state (decide/
# dispatch/close) or are pure modifiers of one of those, plus the one live E2E gate.
# Evidence for "only a spawn/CI invokes these, never a human at a terminal":
# `coord_policy.SAFE_ARGV`'s `--rout(e|ing)-\S+` entry is the sanctioned automation
# channel, and `grep`ing every spawn CLI (`opencode_spawn.py`, `codex_spawn.py`,
# `claude_code_spawn.py`, `set_agents_spawn.py`) shows `--route-decide`/`--route-dispatched`/
# `--route-terminal`/`--route-quota-exhausted` (+ their `--quota-error`/`--latency-ms`/
# `--usage`/`--fresh-probes` modifiers) called ONLY from `_run_app_cli`, always with
# `--json`, never suggested to a human anywhere. `--quota-failover-e2e` is a manual live
# gate (AC-06) that only ever shows up in past packages' evidence logs -- an engineering
# verification tool, not everyday surface.
#
# GROUP 2 -- harness observability surfaces (D1-F03 repair): `--context`, `--graph`,
# `--feature-id`, `--out`, `--routing-report`, `--routing-open-runs`,
# `--routing-recent-writers`, `--routing-decisions`, `--limit`. These are the
# orchestrator's OWN recovery/audit channel (see Global/_canonical/agents/orchestrator.md:
# every one of these is a literal, pasted "Run exactly:" command in that doctrine) and
# `--context` additionally has its own `coord_policy.SAFE_ARGV` entry, like GROUP 1.
# Corrected evidence (the ORIGINAL comment here overclaimed this): `setup_models.py`'s
# "Modelos" wizard panel suggests exactly TWO flags to a human, `--route-doctor` (twice)
# and `--model-preference-show` (ai/scripts/setup_models.py:228,252,254,238 measured
# `--route-explain` too, in the same citation style as `--route-doctor` -- kept visible
# alongside it) -- `--routing-report`/`--routing-decisions`/`--routing-open-runs`/
# `--routing-recent-writers` do NOT appear in that file, or in README.md/INSTALACION.md/
# COMO-CAMBIAR-MODELO.md/CONTRIBUTING.md, at all (grepped, zero hits): nothing human-
# facing ever named them. `--route-doctor`/`--route-explain`/`--routing-migrate` stay
# VISIBLE (ADR-0010/ADR-0035 document `--routing-migrate`/`--route-doctor` as
# operator-driven diagnostics, and the wizard cites `--route-explain`), unlike this group.
#
# GROUP 3 -- the `providers.toml` registry CLI (022 PKG-4, AC-11/AC-12): `--provider-add`,
# `--provider-remove`, `--provider-verify`, `--provider-list`, `--base-url`, `--npm`,
# `--label`, `--model`, `--include-legacy`, `--prune-dead`. Zero mentions in any
# human-facing doc (grepped, same four files as GROUP 2) -- the human path for editing
# `providers.toml` is the "Modelos" wizard (`setup-models.sh`), never this raw CLI by
# hand.
#
# NEVER remove a flag from this set without also removing its `add_argument` call --
# `test_internal_flags_cannot_be_silently_deleted` (tests/test_harness.py) fails the
# build the moment one goes missing, hidden or not.
_INTERNAL_FLAGS = frozenset({
    # GROUP 1 -- routing lifecycle primitives + modifiers + E2E gate.
    "--route-decide", "--route-dispatched", "--route-terminal", "--route-quota-exhausted",
    "--quota-error", "--latency-ms", "--usage", "--fresh-probes", "--quota-failover-e2e",
    # GROUP 2 -- harness observability (orchestrator-only, D1-F03).
    "--context", "--graph", "--feature-id", "--out", "--routing-report",
    "--routing-open-runs", "--routing-recent-writers", "--routing-decisions", "--limit",
    # GROUP 3 -- providers.toml registry CLI (wizard-only, D1-F03).
    "--provider-add", "--provider-remove", "--provider-verify", "--provider-list",
    "--base-url", "--npm", "--label", "--model", "--include-legacy", "--prune-dead",
})


def _hidden_help(advanced, text):
    """AC-02: `argparse.SUPPRESS` for one of `_INTERNAL_FLAGS`' `help=` UNLESS `advanced`
    -- never a second source of truth for what the flag does, just whether `--help` prints
    it. `--help --avanzado` (main()'s own early interception) rebuilds this SAME parser
    with `advanced=True`, so the real text always comes from here."""
    return argparse.SUPPRESS if not advanced else text


def _build_parser(advanced=False):
    """The one argparse parser set-agents/main() dispatches against. `advanced=True`
    reveals `_INTERNAL_FLAGS`' real help text (AC-02's `--help --avanzado`) -- every other
    behavior (defaults, choices, dest, parsing) is IDENTICAL between the two calls; only
    `help=` differs, so nothing here can silently change what a flag does depending on
    which mode built the parser."""
    parser = argparse.ArgumentParser(
        prog="set-agents",
        description=__doc__,
        # F-14 repair: --tools-propose/--tools-approve are intercepted above BEFORE this
        # parser is even built (see the comment there), so --help never showed them --
        # mentioned here in prose only, deliberately NOT declared as real argparse
        # arguments (doing that would reopen F-08's SAFE_ARGV gap the moment argparse
        # knows the verb; fixing that too is a separate, larger change no AC asks for).
        epilog=(
            "Primera vez: leé README.md — explica qué vas a ver según tu sistema operativo.\n"
            "Dos verbos más (ADR-0038, interceptados antes de este parser, no listados arriba): "
            "--tools-propose <name> --kind cli|mcp|skill --detect <bin> --install-<method> "
            '"<cmd>" --why "<motivo>" (valida y imprime la pregunta consolidada, nunca instala) '
            "y --tools-approve <name> (la aprobación humana -- nunca la corre un agente, sea "
            "cual sea su rol).\n"
            "AC-02 (ADR-0050): algunas flags de uso interno (spawns/orquestador) están "
            "ocultas de esta lista -- siguen funcionando igual; --help --avanzado las muestra."
        ),
    )
    parser.add_argument("--status", action="store_true", help="estado en una línea (APP_STATUS ...)")
    parser.add_argument("--route-explain", metavar="TASK_CLASS")
    parser.add_argument("--routing-report", action="store_true",
                        help=_hidden_help(advanced, "USO INTERNO (orquestador) -- reporte de latencia/retención "
                                          "del store de ruteo (solo lectura)"))
    parser.add_argument("--route-doctor", action="store_true",
                        help="ADR-0035, solo lectura: por par OpenCode, auth/modelos listados/billing y diagnóstico del cache; expone credenciales sin CLI id verificado (M-1)")
    parser.add_argument("--route-decide", metavar="FILE",
                        help=_hidden_help(advanced, "USO INTERNO (spawns/orquestador, nunca a mano) -- descriptor JSON "
                                          "('-' = stdin); decide y, para writers, autoriza"))
    parser.add_argument("--route-dispatched", metavar="RUN_ID",
                        help=_hidden_help(advanced, "USO INTERNO (spawns) -- marca run_id como dispatched"))
    parser.add_argument("--route-terminal", nargs=2, metavar=("RUN_ID", "OUTCOME"),
                        help=_hidden_help(advanced, "USO INTERNO (spawns) -- cierra run_id con outcome success|failure"))
    parser.add_argument("--route-quota-exhausted", metavar="RUN_ID",
                        help=_hidden_help(advanced, "USO INTERNO (spawns) -- cierra run_id agotado y autoriza el reemplazo"))
    parser.add_argument("--quota-failover-e2e", action="store_true",
                        help=_hidden_help(advanced, "USO INTERNO (gate E2E manual, AC-06) -- bloquea hasta verificar una "
                                          "suscripción agotada controlada"))
    parser.add_argument("--quota-error", metavar="JSON",
                        help=_hidden_help(advanced, "USO INTERNO -- con --route-quota-exhausted: detalle del error de cuota"))
    parser.add_argument("--routing-open-runs", action="store_true",
                        help=_hidden_help(advanced, "USO INTERNO (orquestador) -- runs de ruteo abiertos "
                                          "ahora mismo (solo lectura)"))
    parser.add_argument("--routing-recent-writers", action="store_true",
                        help=_hidden_help(advanced, "USO INTERNO (orquestador) -- último writer verificado por "
                                          "role_class, para review_of_run_id cuando se perdió el contexto "
                                          "(solo lectura)"))
    parser.add_argument("--routing-decisions", action="store_true",
                        help=_hidden_help(advanced, "USO INTERNO (orquestador) -- tail del log de decisiones "
                                          "por spawn (ADR-0031, solo lectura)"))
    parser.add_argument("--limit", type=int, default=None,
                        help=_hidden_help(advanced, "USO INTERNO -- con --routing-decisions: máximo de "
                                          "entradas (default 50)"))
    parser.add_argument("--routing-migrate", action="store_true", help="migra explícitamente la DB de routing al schema actual")
    parser.add_argument("--project", metavar="DIR", help="ancla explícita del proyecto para ruteo")
    parser.add_argument("--scaffold", nargs="?", metavar="DIR", const="", help="crea el estado portable mínimo del proyecto")
    parser.add_argument("--fresh-probes", action="store_true",
                        help=_hidden_help(advanced, "USO INTERNO -- con --route-decide: saltea el cache de probes"))
    parser.add_argument("--latency-ms", type=int, default=None,
                        help=_hidden_help(advanced, "USO INTERNO -- con --route-terminal: latencia observada"))
    parser.add_argument("--usage", metavar="JSON",
                        help=_hidden_help(advanced, "USO INTERNO -- con --route-terminal: uso/costo del spawn"))
    parser.add_argument("--json", action="store_true", help="salida JSON para comandos de observabilidad (routing, --context)")
    parser.add_argument("--check-update", action="store_true")
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--no-install", action="store_true")
    parser.add_argument("--auto-update", choices=("on", "off"))
    parser.add_argument("--tools", action="store_true", help="TOOL <name> installed=yes/no")
    parser.add_argument("--tools-install", metavar="NAME")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--mcp", action="store_true", help="MCP <name> harness=<h> state=...")
    parser.add_argument("--mcp-add", metavar="NAME")
    parser.add_argument("--mcp-remove", metavar="NAME")
    parser.add_argument("--mcp-on", metavar="NAME")
    parser.add_argument("--mcp-off", metavar="NAME")
    # 022 PKG-4 (AC-11/AC-12): the `providers.toml` registry CLI -- list/add/remove/
    # verify, never a raw JSON edit. `--provider-verify` alone (no ID) checks every
    # registered entry; `--provider-verify ID` checks just one.
    parser.add_argument("--provider-list", action="store_true",
                        help=_hidden_help(advanced, "USO INTERNO (setup-models.sh) -- lista providers.toml "
                                          "(solo lectura)"))
    parser.add_argument("--provider-add", metavar="ID",
                        help=_hidden_help(advanced, "USO INTERNO (setup-models.sh) -- agrega/reemplaza un "
                                          "provider local en providers.toml (con --base-url y --model, al "
                                          "menos uno)"))
    parser.add_argument("--provider-remove", metavar="ID",
                        help=_hidden_help(advanced, "USO INTERNO (setup-models.sh) -- saca un provider de "
                                          "providers.toml"))
    parser.add_argument("--provider-verify", nargs="?", const="", metavar="ID",
                        help=_hidden_help(advanced, "USO INTERNO (setup-models.sh) -- chequea la forma "
                             "declarada de un provider (o de todos, sin ID) y, para origin=user "
                             "(AC-18), liveness real: GET {baseURL}/models, 2s, alive|dead|unreachable"))
    parser.add_argument("--include-legacy", action="store_true",
                        help=_hidden_help(advanced, "USO INTERNO -- con --provider-verify: además de "
                             "origin=user (AC-18), suma origin=harness-legacy -- "
                             "el caso ollama post-P4 (--provider-remove es la otra salida documentada)"))
    parser.add_argument("--prune-dead", action="store_true",
                        help=_hidden_help(advanced, "USO INTERNO -- con --provider-verify: saca de "
                             "providers.toml los providers que ESTA corrida midió "
                             "dead (nunca unreachable) -- requiere ./build.sh --install para reflejarse"))
    parser.add_argument("--base-url", metavar="URL",
                        help=_hidden_help(advanced, "USO INTERNO -- con --provider-add: baseURL del endpoint "
                                          "OpenAI-compatible"))
    parser.add_argument("--npm", metavar="PACKAGE",
                        help=_hidden_help(advanced, "USO INTERNO -- con --provider-add: paquete npm del "
                                          "adaptador (default @ai-sdk/openai-compatible)"))
    parser.add_argument("--label", metavar="NAME",
                        help=_hidden_help(advanced, "USO INTERNO -- con --provider-add: nombre visible del "
                                          "provider (default: el ID)"))
    parser.add_argument("--model", action="append", metavar="ID[:NOMBRE]",
                        help=_hidden_help(advanced, "USO INTERNO -- con --provider-add: modelo declarado, "
                                          "repetible, al menos uno"))
    parser.add_argument("--harness", choices=("opencode", "claude", "codex", "cursor", "gemini", "pi"))
    parser.add_argument("--doctor", action="store_true", help="chequeo redactado del harness (usar con --harness pi)")
    parser.add_argument("--doctor-all", action="store_true", help="qué detecta esta máquina: harnesses, CLIs y proveedores autenticados")
    parser.add_argument("--plugins", action="store_true")
    parser.add_argument("--plugin-on", metavar="NAME")
    parser.add_argument("--plugin-off", metavar="NAME")
    parser.add_argument("--vault-init", metavar="DIR", help="crea el vault Obsidian de la empresa en DIR/obsidian")
    parser.add_argument("--vault-link", metavar="PROYECTO", help="linkea docs/notas del proyecto al vault")
    parser.add_argument("--vault", metavar="DIR", help="vault explícito para --vault-link")
    parser.add_argument("--context", action="store_true",
                        help=_hidden_help(advanced, "USO INTERNO (orquestador/agentes) -- hub + contexto de "
                             "empresa + nota del proyecto + qué falta (solo lectura)"))
    parser.add_argument("--graph", action="store_true",
                        help=_hidden_help(advanced, "USO INTERNO (orquestador) -- grafo de ejecución (mermaid): "
                             "findings, reviews, verificaciones, repairs, blockers (solo lectura)"))
    parser.add_argument("--feature-id", action="append", metavar="ID",
                        help=_hidden_help(advanced, "USO INTERNO -- con --graph: limita a esta feature "
                             "(repetible; sin ninguna, todas)"))
    parser.add_argument("--out", metavar="FILE",
                        help=_hidden_help(advanced, "USO INTERNO -- con --graph: escribe el mermaid en FILE "
                             "en vez de stdout"))
    parser.add_argument("--vault-doctor", action="store_true", help="estado del vault: symlinks sanos, drift, no-registrados (report-only)")
    parser.add_argument("--repair", action="store_true", help="con --vault-doctor --project: aplica lo que el --dry-run inmediatamente anterior confirmó")
    # SEC-005: DEC-5/AC-16 say notes exclusion is "written/kept" as part of migration, full
    # stop -- no opt-in mentioned. An --exclude-notes flag defaulting to False inverted that:
    # a real migration left client notes untracked-but-visible in git until the caller
    # remembered the flag. Privacy is now the default; --include-notes is the explicit opt-out.
    parser.add_argument("--include-notes", action="store_true", help="con --vault-doctor --project --dry-run: docs/notas queda DENTRO del git del proyecto tras migrar (opt-out explícito; por defecto DEC-5 lo excluye)")
    parser.add_argument("--private", action="store_true",
                        help="con --vault-link: las notas viven en el vault y el repo queda con un symlink excluido de git")
    parser.add_argument("--company", metavar="NAME")
    # 014-model-preference-policy AC-02: --provider is repeatable-ordered, the same idiom
    # --feature-id already establishes above (order of appearance IS the ranked list).
    parser.add_argument("--model-preference-set", metavar="CLASS", choices=_MODEL_PREFERENCE_CLASSES,
                        help="escribe [preference].CLASS en model-preference.toml; combinar con --provider (repetible, ordenado)")
    parser.add_argument("--provider", action="append", metavar="NAME",
                        help="con --model-preference-set: proveedor, repetible, el orden en la línea de comando es la preferencia")
    parser.add_argument("--model-preference-role-override", nargs=2, metavar=("ROLE", "CLASS"),
                        help="escribe [role_override].ROLE = CLASS en model-preference.toml")
    parser.add_argument("--model-preference-show", action="store_true", help="lee model-preference.toml (solo lectura)")
    # ADR-0032: pin de modelo por rol (o global con el literal '*') — el router lo
    # respeta como override blando: pin > decisión dinámica > fallback curado.
    parser.add_argument("--model-pin-set", nargs=2, metavar=("ROLE", "PROVIDER/MODEL"),
                        help="escribe [model_pin].ROLE en model-preference.toml (ROLE puede ser '*')")
    parser.add_argument("--model-pin-clear", metavar="ROLE",
                        help="borra [model_pin].ROLE de model-preference.toml")
    return parser


def main():
    # ADR-0038: --tools-propose/--tools-approve are intercepted here, before the main
    # argparse parser is even built, because --install-<method> is a dynamic flag NAME
    # argparse cannot declare (metavar/choices only constrain a flag's VALUE) -- the same
    # reasoning coord_policy's own argv-walkers use: a fixed declarative grammar can't
    # express this shape, so it's walked by hand instead (_dispatch_tools_discovery).
    # This keeps the rest of main()'s mode-exclusivity machinery (_mode_flags/other_mode
    # below) completely untouched -- these two verbs never reach `parser.parse_args()`.
    if len(sys.argv) > 1 and sys.argv[1] in ("--tools-propose", "--tools-approve"):
        return _dispatch_tools_discovery(sys.argv[1], sys.argv[2:])
    # AC-02: `--help --avanzado` (either order) rebuilds the SAME parser with
    # `_INTERNAL_FLAGS`' real help text restored, prints it, and returns -- checked
    # against raw `sys.argv` (like the interception above), NEVER via the normal parser's
    # own `-h/--help` action, because `--avanzado` is not itself a registered argument
    # (declaring it as one would make it a real, discoverable, un-hidden flag -- the
    # opposite of the point) and argparse's own unrecognized-argument error would fire
    # before the built-in `-h` action gets a chance to short-circuit in the order that
    # matters here.
    rest = sys.argv[1:]
    if "--avanzado" in rest and ("--help" in rest or "-h" in rest):
        _build_parser(advanced=True).print_help()
        return 0
    parser = _build_parser(advanced=False)
    args = parser.parse_args()

    # This gate is intentionally outside the ordinary routing modes.  It has no
    # credentials or mock fallback and performs no durable mutation while blocked.
    if args.quota_failover_e2e:
        return cmd_quota_failover_e2e()

    # AC-03 (025/D1): default is human text (to stderr, `_routing_output`'s existing
    # split) regardless of whether stdout is a TTY -- only an explicit `--json` switches
    # to the byte-identical machine envelope on stdout. Every real machine consumer
    # (opencode_spawn.py/codex_spawn.py/claude_code_spawn.py/set_agents_spawn.py's
    # `_run_app_cli` calls, `docs/adr/*`) already passes `--json` explicitly -- grepped,
    # none rely on the old isatty-gated default -- so this only changes what a human
    # sees when stdout happens to be piped/redirected without asking for JSON.
    routing_human = not args.json
    # Routing modes are total: JSON is a rendering modifier, per-mode modifiers are the only
    # exemptions (--fresh-probes with decide, --latency-ms with terminal), and no other argument —
    # operational command or modifier — may be silently combined with a routing mode. Comparing every
    # parsed argument against its parser default keeps this exhaustive when new flags are added.
    # F08/N11: presence is checked with `is not None` for value-bearing flags, NEVER truthiness —
    # `--route-decide ""` is a present-but-EMPTY string, which is falsy and would otherwise fall
    # straight through every mode check into the interactive menu/help instead of failing closed.
    _mode_flags = (args.route_explain is not None, args.routing_report, args.route_decide is not None,
                   args.route_dispatched is not None, args.route_terminal is not None, args.route_quota_exhausted is not None,
                   args.routing_open_runs, args.routing_recent_writers, args.routing_decisions, args.routing_migrate,
                   args.route_doctor)
    routing_mode = any(_mode_flags)
    _routing_args = {"json", "route_explain", "routing_report", "route_decide", "route_dispatched",
                     "route_terminal", "route_quota_exhausted", "quota_error", "routing_open_runs", "routing_recent_writers",
                     "routing_decisions", "limit", "routing_migrate", "fresh_probes", "latency_ms", "usage", "project",
                     "route_doctor"}
    other_mode = any(value != parser.get_default(name)
                     for name, value in vars(args).items() if name not in _routing_args)
    modifier_misuse = (args.fresh_probes and args.route_decide is None) or \
                      (args.latency_ms is not None and args.route_terminal is None and args.route_quota_exhausted is None) or \
                      (args.usage is not None and args.route_terminal is None and args.route_quota_exhausted is None) or \
                      (args.quota_error is not None and args.route_quota_exhausted is None) or \
                      (args.route_quota_exhausted is not None and args.quota_error is None) or \
                      (args.limit is not None and not args.routing_decisions)
    if (sum(_mode_flags) > 1) or (routing_mode and other_mode) or modifier_misuse:
        _routing_output(routing.cli_envelope(False, "routing", {}, (), ("ROUTING_INPUT_INVALID",)), routing_human)
        return 2
    # SEC-001: --context is the third sanctioned read-only channel (coord_policy.SAFE_ARGV,
    # generate.py's OpenCode glob) and, like the routing modes above, must be total. Without
    # this, dispatch below is plain flag-precedence, so `--context --scaffold X` (or --update
    # --yes, --tools-install, --vault-doctor --repair, ...) reached its handler untouched --
    # demonstrated writing real files through the allowlisted argv shape.
    _context_args = {"context", "project", "json"}
    if args.context and any(value != parser.get_default(name)
                            for name, value in vars(args).items() if name not in _context_args):
        _routing_output(routing.cli_envelope(False, "context", {}, (), ("CONTEXT_INPUT_INVALID",)), routing_human)
        return 2
    if args.scaffold is not None:
        return cmd_scaffold(args.scaffold or None)
    global PROJECT_ROOT, PROJECT_KEY, ROUTING_WARNINGS
    if routing_mode and not args.routing_migrate:
        try:
            PROJECT_ROOT = resolve_project_root(Path.cwd(), args.project)
            if PROJECT_ROOT is None:
                if args.route_decide is not None:
                    _routing_output(routing.cli_envelope(False, "route-decide", {}, ("PROJECT_ROOT_UNRESOLVED",), ("ROUTING_UNAVAILABLE",)), routing_human)
                else:
                    _routing_output(routing.cli_envelope(False, "routing", {}, ("PROJECT_ROOT_UNRESOLVED",), ("ROUTING_UNAVAILABLE",)), routing_human)
                return 1
            PROJECT_KEY = project_key_for(PROJECT_ROOT)
            os.environ["SET_AGENTS_PROJECT"] = str(PROJECT_ROOT)
            # Schema migration is operator-driven.  The probe is read-only and
            # merely adds a stable diagnosis to the normal fail-closed envelope.
            ROUTING_WARNINGS = (("ROUTING_SCHEMA_MIGRATION_REQUIRED",)
                                if _routing_store().migration_required() else ())
        except ProjectIdentityError:
            _routing_output(routing.cli_envelope(False, "routing", {}, ("PROJECT_IDENTITY_INVALID",),
                                                  ("ROUTING_UNAVAILABLE",)), routing_human)
            return 1
        except ValueError:
            _routing_output(routing.cli_envelope(False, "routing", {}, (), ("ROUTING_INPUT_INVALID",)), routing_human)
            return 2
    if args.route_explain is not None:
        return cmd_route_explain(args.route_explain, human=routing_human)
    if args.routing_report:
        return cmd_routing_report(human=routing_human)
    if args.route_doctor:
        return cmd_route_doctor(human=routing_human)
    if args.route_decide is not None:
        return cmd_route_decide(args.route_decide, human=routing_human, fresh=args.fresh_probes)
    if args.route_dispatched is not None:
        return cmd_route_dispatched(args.route_dispatched, human=routing_human)
    if args.route_terminal is not None:
        return cmd_route_terminal(args.route_terminal[0], args.route_terminal[1], args.latency_ms,
                                  args.usage, human=routing_human)
    if args.route_quota_exhausted is not None:
        return cmd_route_quota_exhausted(args.route_quota_exhausted, args.quota_error, args.latency_ms,
                                         args.usage, human=routing_human)
    if args.routing_open_runs:
        return cmd_routing_open_runs(human=routing_human)
    if args.routing_recent_writers:
        return cmd_routing_recent_writers(human=routing_human)
    if args.routing_decisions:
        return cmd_routing_decisions(limit=50 if args.limit is None else args.limit, human=routing_human)
    if args.routing_migrate:
        return cmd_routing_migrate()
    if args.doctor:
        return cmd_doctor(args.harness, human=routing_human)
    if args.doctor_all:
        return cmd_doctor_all()

    if args.status:
        return cmd_status(human=sys.stdout.isatty())
    if args.check_update:
        return cmd_check_update()
    if args.update:
        return cmd_update(yes=args.yes, no_install=args.no_install)
    if args.auto_update:
        set_auto_update(args.auto_update == "on")
        return 0
    if args.model_preference_show:
        try:
            return cmd_model_preference_show()
        except ModelPreferenceError as exc:
            print(f"model-preference: {exc}", file=sys.stderr)
            return 2
    # 014-model-preference-policy AC-02, round-3 R3-F-04(b)/(c): --provider is co-required
    # with --model-preference-set (an argparse-level rejection, not a silent ignore), and
    # a --model-preference-set with zero --provider is rejected before any write.
    if args.model_preference_set is not None or args.provider:
        if args.model_preference_set is None:
            print("model-preference: --provider requires --model-preference-set", file=sys.stderr)
            return 2
        if not args.provider:
            print("model-preference: --model-preference-set requires at least one --provider", file=sys.stderr)
            return 2
        if len(args.provider) != len(set(args.provider)):
            print("model-preference: duplicate --provider value", file=sys.stderr)
            return 2
        try:
            return cmd_model_preference_set(args.model_preference_set, args.provider)
        except ModelPreferenceError as exc:
            print(f"model-preference: {exc}", file=sys.stderr)
            return 2
    if args.model_preference_role_override:
        try:
            return cmd_model_preference_role_override(*args.model_preference_role_override)
        except ModelPreferenceError as exc:
            print(f"model-preference: {exc}", file=sys.stderr)
            return 2
    if args.model_pin_set:
        try:
            return cmd_model_pin_set(*args.model_pin_set)
        except ModelPreferenceError as exc:
            print(f"model-preference: {exc}", file=sys.stderr)
            return 2
    if args.model_pin_clear:
        try:
            return cmd_model_pin_clear(args.model_pin_clear)
        except ModelPreferenceError as exc:
            print(f"model-preference: {exc}", file=sys.stderr)
            return 2
    if args.tools:
        return cmd_tools()
    if args.tools_install:
        return cmd_tools_install(args.tools_install, dry=args.dry_run, yes=args.yes)
    if args.mcp:
        return cmd_mcp()
    if args.mcp_add:
        return cmd_mcp_add(args.mcp_add, args.harness)
    if args.mcp_remove:
        return cmd_mcp_remove(args.mcp_remove, args.harness)
    if args.mcp_on:
        return cmd_mcp_toggle(args.mcp_on, args.harness, True)
    if args.mcp_off:
        return cmd_mcp_toggle(args.mcp_off, args.harness, False)
    if args.provider_list:
        return cmd_provider_list()
    if args.provider_add:
        return cmd_provider_add(args.provider_add, args.base_url, npm=args.npm, label=args.label, models=args.model or ())
    if args.provider_remove:
        return cmd_provider_remove(args.provider_remove)
    if args.provider_verify is not None:
        return cmd_provider_verify(args.provider_verify or None, include_legacy=args.include_legacy, prune_dead=args.prune_dead)
    if args.plugins:
        return cmd_plugins()
    if args.plugin_on:
        return cmd_plugin_set(args.plugin_on, True)
    if args.plugin_off:
        return cmd_plugin_set(args.plugin_off, False)
    if args.vault_init:
        return cmd_vault_init(args.vault_init, args.company)
    if args.vault_link:
        return cmd_vault_link(args.vault_link, args.vault, args.private)
    if args.vault_doctor:
        return cmd_vault_doctor(args.project, args.vault, args.dry_run, args.repair, not args.include_notes)
    if args.context:
        return cmd_context(args.project, args.json)
    if args.graph:
        return cmd_graph(args.feature_id, args.project, args.out)
    if not sys.stdin.isatty():
        parser.print_help()
        return 2
    return menu()


if __name__ == "__main__":
    raise SystemExit(main())
