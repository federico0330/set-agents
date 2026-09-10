#!/usr/bin/env python3
"""Interactive and scriptable editor for models.toml (model routing per area/role).

Non-interactive core: --status, --check, --set, --add-model, --add, --drop.
Interactive wizard (no arguments): menu over the same primitives, then offers
a full-generate smoke test (`build.sh --output`, see `_generate_smoke_test`;
NOT `build.sh --check`, whose job since ADR-0041 is comparing Global/, not
validating a config nothing has regenerated Global/ from yet) and --install.
Writing is atomic and always validated in memory first; an
invalid change never reaches the file.

ADR-0048 (024 C2): [subscriptions] is the one field this file never writes into
models.toml -- the wizard's Suscripciones and the --add/--drop flags write the
per-machine overlay (`models_config.subscriptions_overlay_path()`, under
`$STATE_DIR`) instead, immediately, so a machine's own credentials can never
dirty the tracked tree (that used to block `--update` forever, tree_clean()).
"""

import argparse
import copy
import dataclasses
import fcntl
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import models_config
import model_state
import tui
import ui
from models_config import ModelsError, die

ROOT = Path(__file__).resolve().parents[2]
_MODEL_ID_MAX = 256
_CHILD_BUDGET = 1024 * 1024
_CATALOG_TIMEOUT = 20
_INSTALL_TIMEOUT = 120


def _sanitize_model_id(value):
    """ASCII-only model ids; reject C0/C1, Unicode Cf, and oversize strings."""
    if not isinstance(value, str) or not (0 < len(value) <= _MODEL_ID_MAX) or "/" not in value:
        return None
    for ch in value:
        code = ord(ch)
        if code < 32 or code == 127 or 0x80 <= code <= 0x9F or code > 126:
            return None
        if unicodedata.category(ch) in ("Cc", "Cf", "Cs"):
            return None
    return value


def _bounded_run(argv, *, timeout, cwd=None):
    status, output, _size = model_state._bounded_child(argv, cwd, timeout, _CHILD_BUDGET)
    return status, output.decode("utf-8", errors="replace")


def _run_installer(runtime):
    status, _output = _bounded_run(
        [str(ROOT / "build.sh"), "--install", "--target", runtime, "--yes"],
        timeout=_INSTALL_TIMEOUT, cwd=ROOT)
    return 0 if status == "ok" else 1


@dataclasses.dataclass(frozen=True)
class Action:
    """Same shape the home menu uses (`set_agents_app.Action`): a stable key, a label free to
    be rewritten, and a one-line hint."""

    key: str
    label: str
    hint: str = ""


def _style():
    """The same visual system the home menu uses. Every picker in this file goes through
    here -- before this, none of them passed a style, so the Modelos screens rendered with
    the identity (colourless) style while the rest of the app was themed."""
    import set_agents_app
    return set_agents_app.menu_style()
AREA_SIMPLE_FIELDS = ("claude", "codex", "codex_effort", "cursor")
# 045 AC-D.1: effort offered per lane; only codex_effort has a curated consumer.
OVERRIDE_FIELDS = (
    "claude", "codex", "codex_effort", "opencode", "cursor",
    "claude_effort", "opencode_effort", "cursor_effort",
)
# Lanes whose effort row is offered but has no curated consumer yet (ADR-0073).
EFFORT_NAMED_ABSENCE = {
    "claude_effort": "sin consumidor curado (Claude Code no tiene flag de effort)",
    "opencode_effort": "sin consumidor curado en [areas] (opencode usa --variant en spawn)",
    "cursor_effort": "sin consumidor curado (Cursor pins no llevan effort aparte)",
}

# ADR-0032: which catalog list suggests models for a pinned provider.
PIN_PROVIDER_CATALOGS = {"openai-codex": "codex", "anthropic": "claude",
                         "opencode-zen": "opencode_zen", "opencode-go": "opencode_go"}


def _resolve_live_discovered(config):
    """ADR-0035 (AC-16): resolves `[routing].discovered_providers == "auto"` against the
    live probed inventory (`routing_core.catalog.resolve_discovered_providers`) -- never
    iterates the string itself. `None` on any failure (missing routing_core state, a
    broken probe), distinguishable from an empty tuple (`"auto"`, but nothing live right
    now) -- the panel renders each differently. Uses the same cached probe root the CLI
    uses (`set_agents_app.STATE_DIR`), so a warm cache keeps this cheap on every wizard
    redraw; a cold one pays the same probe cost `--route-decide`/`--route-doctor` would."""
    try:
        from routing_core.catalog import probe_inventory, resolve_discovered_providers
        import set_agents_app
        inventory = probe_inventory(config, cache_root=set_agents_app.STATE_DIR)
        return resolve_discovered_providers(config, inventory)
    except Exception:
        return None


def _load_pins():
    """ADR-0032: the user's [model_pin] table from model-preference.toml, via the same
    loader the routing CLI uses. Degrades to None (panel shows 'no legible') on any
    error — the wizard must never crash because a sibling config is malformed."""
    try:
        import set_agents_app
        return set_agents_app.load_model_pin()
    except Exception:
        return None


def _pin_cli(*args):
    """Write path for pins: the sanctioned CLI, never a hand-rolled TOML writer here."""
    return subprocess.run([sys.executable, str(ROOT / "ai/scripts/set_agents_app.py"), *args],
                          check=False).returncode


def _current_cell_value(config, prefix, field):
    """Read a wizard cell with .get() only — never insert keys (AC-3.4)."""
    if prefix.startswith("role:"):
        target = (config.get("roles") or {}).get(prefix[len("role:"):])
    else:
        target = (config.get("areas") or {}).get(prefix)
    if not isinstance(target, dict):
        return None
    if field == "opencode":
        return target.get("opencode")
    return target.get(field)


def parse_address(config, roster, address):
    """<duty>.<field> | <duty>.opencode | role:<role>... | session.opencode_small_model"""
    tokens = address.split(".")
    if tokens[0] == "session":
        if tokens[1:] != ["opencode_small_model"]:
            die(f"invalid address: {address}")
        return config["session"], "opencode_small_model"
    if tokens[0].startswith("role:"):
        role = tokens[0][len("role:"):]
        if role not in {row["role"] for row in roster}:
            die(f"unknown role: {role}")
        target = config["roles"].setdefault(role, {})
        tokens = tokens[1:]
    else:
        duty = tokens[0]
        if duty not in config["areas"]:
            die(f"unknown area: {duty}")
        target = config["areas"][duty]
        tokens = tokens[1:]
    if len(tokens) == 1 and tokens[0] in AREA_SIMPLE_FIELDS + ("opencode",) + tuple(EFFORT_NAMED_ABSENCE):
        return target, tokens[0]
    die(f"invalid address: {address}")


def validate(config, roles_path):
    """The config must stay generable: emit to a temp file and load_roles."""
    # TOML is UTF-8 by specification; the locale never gets a vote.
    with tempfile.NamedTemporaryFile(
        "w", suffix=".toml", delete=False, encoding="utf-8"
    ) as handle:
        handle.write(models_config.emit(config))
        temp = handle.name
    try:
        models_config.load_roles(roles_path, temp)
    finally:
        os.unlink(temp)


def _generate_smoke_test():
    """Full generate() pipeline, to a throwaway dir -- never Global/.

    Before ADR-0041, `build.sh --check` doubled as this smoke test purely as a side effect of
    always building its STAGING tree, and never actually compared it against anything. Now that
    `--check` means "does Global/ match a fresh build" (AC-01), it is the wrong question
    right after writing a NEW models.toml that nothing has regenerated Global/ from yet -- every
    real edit would report drift against a tree the edit hasn't touched. `build.sh --output DIR`
    is the same "does this fully generate" validation `--check` used to provide
    (same generate.py call, same die()s on an incoherent config), without the Global/ diff.
    """
    with tempfile.TemporaryDirectory() as tmp:
        return subprocess.run(
            [str(ROOT / "build.sh"), "--output", tmp],
        )


def dropped_cells(config, roster, subscription):
    """Every role whose resolved opencode model consumes the given subscription."""
    affected = []
    for row in roster:
        resolved = models_config.resolve_role(row, config)
        model = resolved["opencode_model"]
        if models_config.subscription_of(model, config) == subscription:
            affected.append((row["role"], model))
    model = config["session"]["opencode_small_model"]
    if isinstance(model, str) and models_config.subscription_of(model, config) == subscription:
        affected.append(("(session small_model)", model))
    return affected


def _subscription_candidates(config):
    """ADR-0048 (024 C2): the wizard/`--add`/`--drop` candidate universe. A neutral
    tracked file (AC-03) has an EMPTY `[subscriptions]`, so offering only its keys
    (the pre-024 behavior) would leave nothing to pick; the audited
    `SUBSCRIPTION_BY_PREFIX` targets are the real closed universe, extended by any
    repo `[providers]` addition and by whatever this machine (tracked file or
    overlay) already names, so a hand-edited exotic subscription still shows up."""
    names = set(models_config.SUBSCRIPTION_BY_PREFIX.values())
    names |= set(config.get("providers", {}).values())
    names |= set(config.get("subscriptions", {}))
    names |= set(config.get("_subscriptions_overlay", {}))
    return sorted(names)


def _opencode_display(area):
    value = area.get("opencode") if isinstance(area, dict) else None
    return value if isinstance(value, str) else "-"


def _status_lines(config, roster):
    """Human status for TUI detail — area table + role count. Never dumps Python dicts
    (tiers={...}). `--status` CLI reuses this; verbosity beyond the table stays out of TUI."""
    subs = models_config.effective_subscriptions(config)
    on = [k for k, v in sorted(subs.items()) if v]
    off = [k for k, v in sorted(subs.items()) if v is False]
    accounts = ", ".join(on) if on else "(ninguna fijada)"
    lines = [
        f"cuentas activas: {accounts}",
    ]
    if off:
        lines.append(f"cuentas off: {', '.join(off)}")
    lines.append(f"{'AREA':<10} {'CLAUDE':<8} {'CODEX':<14} {'EFFORT':<7} OPENCODE")
    duties = [d for d in models_config.DUTY_ORDER if d in config["areas"]]
    duties += sorted(set(config["areas"]) - set(duties))
    for duty in duties:
        area = config["areas"][duty]
        lines.append(
            f"{duty:<10} {area.get('claude', '-'):<8} {area.get('codex', '-'):<14} "
            f"{area.get('codex_effort', '-'):<7} {_opencode_display(area)}"
        )
    overrides = config.get("roles", {})
    if overrides:
        lines.append(f"{len(overrides)} roles distintos (editar de a uno en Preferir un modelo)")
    return lines


def status(config, roster):
    for line in _status_lines(config, roster):
        print(line)


_LIVE_UNSET = object()
_LIVE_PENDING = object()
SUBSCRIPTION_PROBE_FAILED = "cuentas: no se pudo medir ahora"
REFRESH_ITEM = "Refrescar suscripciones y catalogo"


def _subscription_headline(subs, age_s=None, error=False):
    """Age stamp or named degradation — human account names, not pin jargon."""
    detail = " ".join(subs) or "-"
    if error:
        return f"{SUBSCRIPTION_PROBE_FAILED} · {detail}"
    if age_s is not None:
        minutes = int(max(0.0, age_s) // 60)
        return f"Cuentas (hace {minutes} min): {detail}"
    return f"Cuentas: {detail}"


def _panel_lines(config, roster, detected=None, *,
                 subscription_age_s=None, subscription_error=False,
                 live_discovered=_LIVE_UNSET):
    """End-user wizard header — at most 2 human lines. No ADR, no discovered_providers,
    no models.local.toml, no pin glyphs. Live routing detail stays under Avanzado."""
    del live_discovered  # advanced-only; kept in signature for call-site compatibility
    subscriptions = models_config.effective_subscriptions(config)
    names = []
    for key in sorted(set(subscriptions) | (detected or set())):
        if key not in subscriptions:
            if detected is not None and key in detected:
                names.append(key)
        elif subscriptions[key]:
            names.append(key)
    # Preference count: overlay cells + explicit model pins
    overlay = models_config.load_models_overlay()
    n_overlay = sum(
        len(fields)
        for family in ("areas", "roles")
        for fields in (overlay.get(family) or {}).values()
    )
    pins = _load_pins() or {}
    n_prefs = n_overlay + len(pins)
    if n_prefs == 0:
        mode = "Elige solo"
    elif n_prefs == 1:
        mode = "Elige solo · 1 preferencia tuya"
    else:
        mode = f"Elige solo · {n_prefs} preferencias tuyas"
    accounts = ", ".join(names) if names else "(ninguna medida)"
    if subscription_error:
        line2 = f"{SUBSCRIPTION_PROBE_FAILED} · pins: {', '.join(names) if names else '-'}"
    elif subscription_age_s is not None:
        minutes = int(max(0.0, subscription_age_s) // 60)
        line2 = f"Cuentas (hace {minutes} min): {accounts}"
    else:
        line2 = f"Cuentas: {accounts}"
    return [mode, line2]


def _overrides_matrix_lines(config):
    """Curated defaults matrix — areas as a short table; roles as a count. Never dict repr."""
    lines = ["Preferencias por area (fallback si el router no decide):"]
    lines.append(f"{'AREA':<10} {'CLAUDE':<8} {'CODEX':<14} {'EFFORT':<7} {'CURSOR':<16} OPENCODE")
    duties = [d for d in models_config.DUTY_ORDER if d in config.get("areas", {})]
    duties += sorted(set(config.get("areas", {})) - set(duties))
    for duty in duties:
        area = config["areas"][duty]
        lines.append(
            f"{duty:<10} {area.get('claude', '-'):<8} {area.get('codex', '-'):<14} "
            f"{area.get('codex_effort', '-'):<7} {area.get('cursor', '-'):<16} {_opencode_display(area)}"
        )
    overrides = config.get("roles", {})
    if overrides:
        lines.append(f"{len(overrides)} roles distintos")
        # The @tier variant count lived on the old first panel, which 045 AC-A.1 cut down to
        # two human lines. It is real engineering signal, not jargon, so it moves HERE (behind
        # Overrides) instead of disappearing -- losing it was an unnoticed side effect of that
        # cut, caught by `tests/test_decide_always.py` after this panel was rewritten.
        variants = sum(len(override.get("tiers") or {}) for override in overrides.values()
                       if isinstance(override, dict))
        lines.append(f"variantes @tier: {variants}")
    return lines


def atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(content)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def _fetch_opencode_models(config):
    """Live `opencode models` (or config fallback). No cache, no progress."""
    models = set()
    if shutil.which("opencode"):
        status, stdout = _bounded_run(["opencode", "models"], timeout=_CATALOG_TIMEOUT)
        if status == "ok":
            for line in stdout.splitlines():
                model_id = _sanitize_model_id(line.strip())
                if model_id:
                    models.add(model_id)
    if not models:
        def _collect(value):
            if isinstance(value, str) and "/" in value:
                models.add(value)
            elif isinstance(value, dict):
                for inner in value.values():
                    _collect(inner)
        for area in config["areas"].values():
            _collect(area.get("opencode"))
        for override in config.get("roles", {}).values():
            _collect(override.get("opencode"))
            for tier in (override.get("tiers") or {}).values():
                if isinstance(tier, dict):
                    _collect(tier.get("opencode"))
    return sorted(models)


def available_opencode_models(config, *, force=False, now=None):
    """Suggestions for the wizard: disk cache (AC-2.3, 60 min TTL), else live
    `opencode models` behind tui.with_progress (AC-2.2). Config fallback if the
    CLI is missing or empty — same as before, just not on the first-paint path."""
    now = time.time() if now is None else now
    if not force:
        cached = models_config.load_wizard_live_cache().get("catalog")
        if models_config.wizard_cache_entry_fresh(
                cached, models_config.WIZARD_CATALOG_TTL_SECONDS, now=now):
            return [mid for mid in map(_sanitize_model_id, cached["ids"]) if mid]
    models = [_mid for _mid in map(_sanitize_model_id, tui.with_progress(
        "listando modelos", lambda: _fetch_opencode_models(config))) if _mid]
    models_config.write_wizard_live_cache("catalog", {"at": now, "ids": models})
    return models


def _safe_input(prompt):
    """`input()` that exits cleanly instead of a traceback on EOFError/KeyboardInterrupt
    (AC-29) — used by wizard()'s post-save build.sh confirmations, which run after their
    picker step has already closed (cooked mode already restored by then)."""
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def choose(prompt, options, current=None, *, group_by_provider=False, used_by=None):
    """Arrow-key picker with an explicit `/`-triggered free-text fallback (AC-24, P3-tui):
    same "pick a listed option, or type a value that isn't listed" contract the old numbered
    menu + input() line had -- `/` then Enter on an unmatched query is accepted as free text,
    Esc/Ctrl-C/EOF is the new empty-input-cancels equivalent (returns `None` either way).

    `group_by_provider` (AC-3.1) is opt-in: only the OpenCode model catalog uses section
    headers. Selected.index is mapped back through the rendered items so a header string is
    never returned as the chosen value."""
    items = list(options)
    headers = []
    suffixes = []
    if group_by_provider:
        items, headers = _group_models_by_provider(options)
        usage = used_by or {}
        suffixes = [
            "" if i in headers else _model_suffix(item, usage)
            for i, item in enumerate(items)
        ]
    result = tui.run_picker(
        items,
        freetext_allowed=True,
        style=_style(),
        prompt=f"{prompt}:",
        current=current,
        headers=headers,
        suffixes=suffixes,
    )
    if result is None:
        return None
    if isinstance(result, tui.Selected):
        if result.index in set(headers):
            return None
        return items[result.index]
    return result.value or None


def _provider_prefix(model_id):
    return model_id.split("/", 1)[0] if "/" in model_id else model_id


def _group_models_by_provider(models):
    """Keep first-seen provider order. Header copy is `{prefix} ({n})` (AC-3.1)."""
    groups = []
    by_prefix = {}
    for model in models:
        prefix = _provider_prefix(model)
        if prefix not in by_prefix:
            by_prefix[prefix] = []
            groups.append(prefix)
        by_prefix[prefix].append(model)
    items = []
    headers = []
    for prefix in groups:
        members = by_prefix[prefix]
        headers.append(len(items))
        items.append(f"{prefix} ({len(members)})")
        items.extend(members)
    return items, headers


def _models_in_use(config):
    """Map model id -> unique area/role names, first-seen order (AC-3.5)."""
    used = {}

    def _add(name, value):
        if isinstance(value, str) and value:
            names = used.setdefault(value, [])
            if name not in names:
                names.append(name)
        elif isinstance(value, dict):
            for inner in value.values():
                _add(name, inner)

    for duty, area in config.get("areas", {}).items():
        if isinstance(area, dict):
            _add(duty, area.get("claude"))
            _add(duty, area.get("codex"))
            _add(duty, area.get("opencode"))
    for role, override in config.get("roles", {}).items():
        if not isinstance(override, dict):
            continue
        _add(role, override.get("claude"))
        _add(role, override.get("codex"))
        _add(role, override.get("opencode"))
        for tier in (override.get("tiers") or {}).values():
            if isinstance(tier, dict):
                _add(role, tier.get("opencode"))
    return used


def _model_suffix(model_id, used_by):
    parts = []
    if isinstance(model_id, str) and model_id.endswith("-free"):
        parts.append("free")
    names = used_by.get(model_id) or []
    if names:
        parts.append("← " + ", ".join(names))
    return " ".join(parts)


def _load_subscription_panel_state(now=None):
    """Disk only — never probes. First paint (AC-2.1) reads this."""
    now = time.time() if now is None else now
    entry = models_config.load_wizard_live_cache().get("subscriptions")
    pending = {"live_discovered": _LIVE_PENDING}
    if not isinstance(entry, dict):
        return {"detected": None, "sub_at": None, "sub_error": False, "stale": True, **pending}
    fresh = models_config.wizard_cache_entry_fresh(
        entry, models_config.WIZARD_SUBSCRIPTIONS_TTL_SECONDS, now=now)
    error = bool(entry.get("error"))
    names = entry.get("names")
    detected = None if error or names is None else set(names)
    return {
        "detected": detected,
        "sub_at": entry.get("at"),
        "sub_error": error,
        "stale": not fresh,
        **pending,
    }


def _measure_subscriptions(config, now=None):
    """AC-2.4: named degradation, never a mute except, never an unusable wizard."""
    now = time.time() if now is None else now
    error = False
    holder = []
    try:
        detected = models_config.detect_subscriptions(config, inventory_holder=holder)
        if detected is None:
            error = True
            detected = None
        else:
            detected = set(detected)
    except Exception:
        detected = None
        error = True
    if error:
        live = None
    elif holder:
        try:
            from routing_core.catalog import resolve_discovered_providers
            live = resolve_discovered_providers(config, holder[0])
        except Exception:
            live = None
    else:
        live = ()
    payload = {
        "at": now,
        "names": None if error else sorted(detected),
        "error": error,
    }
    models_config.write_wizard_live_cache("subscriptions", payload)
    return {
        "detected": detected,
        "sub_at": now,
        "sub_error": error,
        "stale": False,
        "live_discovered": live,
    }


def _refresh_subscriptions_live(config):
    """AC-2.2: live probe off the first-paint path, via tui.with_progress."""
    return tui.with_progress("midiendo suscripciones", lambda: _measure_subscriptions(config))


def write_overlay_cell(scope, field, value, *, factory, roles_path, _locked=False):
    """Write one instance-overlay cell ONLY if the resulting EFFECTIVE config still validates.

    ADR-0071 moved area/role taste out of the tracked `models.toml` and into
    `models.local.toml`, and with it the write moved off the one code path that ran
    `validate()`. The separation-of-duties rule -- the harness's first invariant, "el que
    escribe no aprueba" -- lives inside `validate()`, so an overlay write bypassed it
    completely: `--set audit.codex=<the writer's model>` returned 0, `models.toml` stayed
    clean, `--check` (which only ever sees the factory file) still passed, and the config the
    router actually reads was in violation. Reproduced end to end before this fix.

    The candidate is validated IN MEMORY, so an illegal value never reaches the disk -- the
    same fail-closed contract ADR-0071 already states for a value outside `[catalog]`.
    Raises `ModelsError` (rc 2 through `die`) on violation.
    """
    if not _locked:
        handle = _locked_preference_writer()
        try:
            return write_overlay_cell(scope, field, value, factory=factory, roles_path=roles_path, _locked=True)
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()
    family, name = scope
    candidate = copy.deepcopy(models_config.load_models_overlay())
    candidate.setdefault(family, {}).setdefault(name, {})[field] = value
    validate(models_config.effective_models_config(factory, candidate), roles_path)
    return models_config.write_models_overlay_field(scope, field, value)


def _preference_lock_path():
    """One lock for preference persistence and its generated installation.

    The lock lives next to the private overlay, never in the tracked tree.  Nonblocking is
    intentional: a second interactive writer gets a retryable answer *before* it can write.
    """
    return models_config.models_overlay_path().with_name("models-apply.lock")


def _locked_preference_writer():
    path = _preference_lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        raise ModelsError("Hay otro cambio de modelos en curso. Esperá y reintentá.")
    return handle


def apply_overlay_model(scope, field, value, *, factory, roles_path, runtime, home=None,
                        install=None, readback=None):
    """Validate → atomically persist → effective install → exact readback under one lock.

    Persisted intent is never rolled back after an installation error: ModelState can then
    truthfully render ``pending_apply`` and the user can retry without changing a session.
    Seams make the sequence hermetic; production installs only the resolved runtime.
    """
    handle = _locked_preference_writer()
    try:
        write_overlay_cell(scope, field, value, factory=factory, roles_path=roles_path, _locked=True)
        desired_config = models_config.effective_models_config(factory)
        row = next((item for item in models_config.load_roster(roles_path)
                    if item.get("role") == "orchestrator"), None)
        desired = (model_state._desired_from_resolved(
            models_config.resolve_role(row, desired_config), runtime).get("model") if row else None)
        # Installed readback is orchestrator-only; never claim applied for other scopes.
        exact_orchestrator = scope[0] == "roles" and scope[1] == "orchestrator"
        installer = install or (lambda: _run_installer(runtime))
        try:
            install_rc = installer()
        except Exception:
            install_rc = 1
        if install_rc != 0:
            _store_model_state_pending(runtime, desired)
            return {"status": "pending_apply", "desired": desired,
                    "message": "Preferencia guardada; no se pudo aplicar. Podés reintentar."}
        try:
            installed = (readback or model_state.installed_state)(runtime, home or Path.home())
        except Exception:
            installed = None
        if exact_orchestrator and installed and installed.get("status") == "installed" and installed.get("model") == desired:
            state = _load_disk_model_state() or model_state.empty_state(runtime)
            state["desired"] = model_state._desired_from_resolved(
                models_config.resolve_role(row, desired_config), runtime) if row else {"model": desired}
            state["installed"] = installed
            state["convergence"] = {"status": "applied"}
            _sync_model_state_cache(state)
            return {"status": "applied", "desired": desired,
                    "message": "Preferencia aplicada y confirmada."}
        _store_model_state_pending(runtime, desired)
        return {"status": "pending_apply", "desired": desired,
                "message": "Preferencia guardada; falta confirmar la instalación. Podés reintentar."}
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _safe_tty(value):
    out = []
    for ch in str(value):
        code = ord(ch)
        if code < 32 or code == 127 or 0x80 <= code <= 0x9F or unicodedata.category(ch) in ("Cc", "Cf", "Cs"):
            out.append(f"\\x{code:02x}")
        elif 32 <= code <= 126:
            out.append(ch)
        else:
            out.append(f"\\u{code:04x}")
    return "".join(out)


_HUMAN_REASON = {
    "not_checked": "todavía no se midió", "unsupported_runtime": "runtime no soportado",
    "opencode_absent": "OpenCode no está disponible", "project_unresolved": "no se pudo ubicar el proyecto",
    "timeout": "la consulta venció", "invalid_json": "la respuesta no se pudo validar",
    "output_limit": "la respuesta fue demasiado grande", "session_limit": "demasiadas sesiones candidatas",
    "no_project_root": "no hay raíz de proyecto", "no_submitted_message": "sin mensaje enviado",
    "cache_read_failed": "no se pudo leer la caché", "probe_failed": "la medición falló",
    "child_failed": "la consulta no pudo completarse", "not_installed": "todavía no está instalado",
    "unavailable": "sin datos disponibles",
}


def _model_state_lines(state):
    """Four independent facts, with evidence source; never call any subprocess here."""
    labels = (("observed", "Último envío observado"), ("desired", "Default de SET"),
              ("installed", "Instalado"), ("routing", "Routing"))
    lines = [ui.rule("Modelos"), "", "Elige solo: SET define los defaults para sesiones nuevas."]
    refresh = state.get("refresh") or {}
    for key, label in labels:
        fact = state.get(key, {})
        value = _safe_tty(fact.get("model") or fact.get("status", "sin observar"))
        source = _safe_tty(fact.get("source", "sin fuente"))
        reason = fact.get("reason")
        suffix = f" · {_HUMAN_REASON.get(reason, 'estado no disponible')}" if reason else ""
        stale = refresh.get(key, {})
        if stale.get("status") == "stale":
            suffix += " · desactualizado"
        elif stale.get("status") == "error":
            suffix += " · error al medir"
        lines.append(f"{label}: {value} (fuente: {source}){suffix}")
    conv = (state.get("convergence") or {}).get("status")
    if conv == "pending_apply":
        lines.append("Convergencia: pendiente de aplicar — podés reintentar desde Actualizar datos.")
    elif conv == "applied":
        lines.append("Convergencia: aplicada y confirmada.")
    lines.extend(("", "/model es una elección temporal de la sesión abierta; no cambia SET ni la instalación."))
    return lines


def _model_state_cache_path():
    return models_config.models_overlay_path().with_name("model-state.json")


def _load_disk_model_state():
    try:
        state = json.loads(_model_state_cache_path().read_text(encoding="utf-8"))
        if not isinstance(state, dict) or state.get("schema_version") != 1:
            return None
        return state
    except (OSError, ValueError, TypeError):
        return None


def _store_model_state(state):
    try:
        path = _model_state_cache_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        with open(temporary, "x", encoding="utf-8") as handle:
            handle.write(json.dumps(state, ensure_ascii=False))
            handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError:
        pass


def _sync_model_state_cache(state):
    ui.GLOBAL_CACHE.set("model_state", state)
    _store_model_state(state)


def _store_model_state_pending(runtime, desired):
    cached = _load_disk_model_state() or model_state.empty_state(runtime)
    cached["convergence"] = {"status": "pending_apply"}
    if isinstance(cached.get("desired"), dict) and desired is not None:
        cached["desired"]["model"] = desired
    _sync_model_state_cache(cached)


def _cached_model_state(config=None, roster=()):
    cached = ui.GLOBAL_CACHE.get("model_state")
    if cached is not None:
        return cached
    cached = _load_disk_model_state()
    if cached is not None:
        ui.GLOBAL_CACHE.set("model_state", cached)
        return cached
    # SET desired is already in the in-memory configuration the wizard received; deriving it
    # is not an observation and does not touch a child, disk cache, or session.
    runtime = (config or {}).get("runtime", {}).get("primary", "unavailable")
    state = model_state.empty_state(runtime)
    row = next((item for item in roster if item.get("role") == "orchestrator"), None)
    if row is not None:
        state["desired"] = model_state._desired_from_resolved(
            models_config.resolve_role(row, config), runtime)
    return state


def _refresh_model_state():
    """Explicit only; failure keeps prior evidence per source as stale."""
    prior = _cached_model_state()
    try:
        state = model_state.collect_model_state(ROOT, project=ROOT)
        _sync_model_state_cache(state)
        return state, None
    except Exception:
        cached = copy.deepcopy(prior) if prior else model_state.empty_state("unavailable")
        refresh = cached.setdefault("refresh", {})
        for key in ("observed", "desired", "installed", "routing"):
            fact = cached.get(key, {})
            prior_refresh = (prior or {}).get("refresh", {}).get(key, {})
            has_value = bool(fact.get("model") or fact.get("status") not in (None, "unavailable", "unobserved"))
            refresh[key] = {
                "status": "stale" if has_value else "error",
                "checked_at": prior_refresh.get("checked_at"),
                "reason": "unavailable",
            }
        cached["convergence"] = {"status": "pending_apply"}
        _sync_model_state_cache(cached)
        return cached, "No pude actualizar el estado de modelos; conservo lo último conocido. Reintentá."


def restore_set_defaults(*, factory=None, roles_path=None, runtime=None, home=None, install=None, readback=None):
    """Remove only local areas/roles sections, retaining every other byte verbatim."""
    lock_handle = _locked_preference_writer()
    try:
        path = models_config.models_overlay_path()
        try:
            if path.is_symlink():
                raise ModelsError("No puedo restaurar preferencias a través de un enlace simbólico.")
            raw = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return {"changed": False}
        except OSError as exc:
            raise ModelsError("No pude leer preferencias locales.") from exc
        lines, kept, skip = raw.splitlines(keepends=True), [], False
        for line in lines:
            if line.startswith("[") and line.rstrip().endswith("]"):
                section = line.strip()[1:-1]
                skip = section.startswith("areas.") or section.startswith("roles.")
            if not skip:
                kept.append(line)
        content = "".join(kept)
        if content == raw:
            return {"changed": False}
        temporary = None
        try:
            fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.restore-", dir=path.parent)
            temporary = Path(temporary_name)
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as output_handle:
                output_handle.write(content)
                output_handle.flush(); os.fsync(output_handle.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
        if not (factory and roles_path and runtime):
            return {"changed": True, "status": "pending_apply",
                    "message": "Defaults restaurados; falta confirmar la instalación. Podés reintentar."}
        row = next((item for item in models_config.load_roster(roles_path)
                    if item.get("role") == "orchestrator"), None)
        desired_config = models_config.effective_models_config(factory)
        desired = (model_state._desired_from_resolved(
            models_config.resolve_role(row, desired_config), runtime).get("model")
                   if row else None)
        try:
            install_rc = (install or (lambda: _run_installer(runtime)))()
        except Exception:
            install_rc = 1
        if install_rc != 0:
            _store_model_state_pending(runtime, desired)
            return {"changed": True, "status": "pending_apply",
                    "message": "Defaults restaurados; no se pudo aplicar. Podés reintentar."}
        try:
            installed = (readback or model_state.installed_state)(runtime, home or Path.home())
        except Exception:
            installed = None
        if installed and installed.get("status") == "installed" and installed.get("model") == desired:
            state = _load_disk_model_state() or model_state.empty_state(runtime)
            state["desired"] = model_state._desired_from_resolved(
                models_config.resolve_role(row, desired_config), runtime) if row else {"model": desired}
            state["installed"] = installed
            state["convergence"] = {"status": "applied"}
            _sync_model_state_cache(state)
            return {"changed": True, "status": "applied",
                    "message": "Defaults restaurados y confirmados."}
        _store_model_state_pending(runtime, desired)
        return {"changed": True, "status": "pending_apply",
                "message": "Defaults restaurados; falta confirmar la instalación. Podés reintentar."}
    finally:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        lock_handle.close()


def write_host_pin_locked(host_id, field, value):
    """Host pin writes share the same exclusive preference lock."""
    handle = _locked_preference_writer()
    try:
        return models_config.write_host_pin(host_id, field, value)
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def router_choose_automatically():
    """Clear only [model_pin]; local model overrides are deliberately untouched."""
    handle = _locked_preference_writer()
    try:
        import set_agents_app
        doc = set_agents_app._read_model_preference_raw()
        if "model_pin" not in doc:
            return False
        doc = {key: value for key, value in doc.items() if key != "model_pin"}
        set_agents_app.atomic_write(set_agents_app.MODEL_PREFERENCE_PATH,
                                    set_agents_app._serialize_model_preference(doc))
        return True
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def plugin_model_warnings(paths=()):
    """Read-only warning for static external labels; no backup or mutation is ever offered."""
    warnings = []
    for candidate in paths:
        path = Path(candidate)
        try:
            if path.is_file() and "model" in path.read_text(encoding="utf-8", errors="replace").lower():
                warnings.append(f"Plugin externo: {path.name} puede mostrar un modelo estático (no autoritativo).")
        except OSError:
            continue
    return warnings


def _edit_overlay_cell(config, roster, roles_path, models_out, *, kind):
    """Preferir un modelo: kind is 'area' or 'role'. Writes overlay immediately."""
    if kind == "area":
        duties = [d for d in models_config.DUTY_ORDER if d in config["areas"]]
        subject = choose("Area", duties)
        prefix = subject
        scope = ("areas", subject) if subject else None
    else:
        subject = choose("Rol", sorted(row["role"] for row in roster))
        prefix = f"role:{subject}" if subject else None
        scope = ("roles", subject) if subject else None
    if not subject:
        return config
    field = choose("Campo", list(OVERRIDE_FIELDS))
    if not field:
        return config
    if field in EFFORT_NAMED_ABSENCE:
        print(f"AVISO: {field} — {EFFORT_NAMED_ABSENCE[field]}")
        print("Podes guardar el valor igual (reserva de esquema).")
    current_value = _current_cell_value(config, prefix, field)
    if field == "opencode":
        value = choose(
            "Modelo", available_opencode_models(config),
            current=current_value, group_by_provider=True,
            used_by=_models_in_use(config),
        )
    elif field in ("codex_effort", "claude_effort", "opencode_effort", "cursor_effort"):
        value = choose("Effort", sorted(models_config.EFFORTS), current=current_value)
    elif field == "cursor":
        value = choose(
            "Modelo Cursor", sorted(config["catalog"].get("cursor", [])),
            current=current_value,
        )
    else:
        catalog_key = field.split(".")[0]
        value = choose(
            "Modelo", sorted(config["catalog"].get(catalog_key, [])),
            current=current_value,
        )
    if not value:
        return config
    if not _confirm_model_mutation("guardar este default de SET"):
        return config
    try:
        runtime = config.get("runtime", {}).get("primary", "opencode")
        result = apply_overlay_model(
            scope, field, value, factory=models_config.load_config(models_out),
            roles_path=roles_path, runtime=runtime)
        config = models_config.effective_models_config(
            models_config.load_config(models_out))
        print(f"{result['status']}: {prefix}.{field} = {value} — {result['message']}")
    except ModelsError as exc:
        print(f"RECHAZADO: {exc}")
    return config


def _wizard_cuentas(config, roster):
    """Cuentas — tri-state subscription overlay (ADR-0048)."""
    candidates = _subscription_candidates(config)
    subscription = choose("Cuenta a cambiar", candidates)
    if not subscription:
        return config
    effective = models_config.effective_subscriptions(config)
    enabled = effective.get(subscription, False)
    if enabled:
        affected = dropped_cells(config, roster, subscription)
        if affected:
            print(f"AFFECTED={len(affected)} — celdas que usan '{subscription}':")
            for role, model in affected:
                print(f"  {role} {model}")
            print("Reasignalas primero (Preferir un modelo) y despues dala de baja.")
            return config
    state = tui.run_picker(
        ("Activada", "Apagada", "Auto — SET decide"),
        style=_style(), prompt=f"{subscription}:")
    if not isinstance(state, tui.Selected):
        return config
    value = None if state.index == 2 else (state.index == 0)
    config["_subscriptions_overlay"] = models_config.write_subscription_overlay(subscription, value)
    if value is None:
        print(f"OK: {subscription} = auto en este equipo (efectivo ya)")
    else:
        print(f"OK: {subscription} = {'on' if value else 'off'} en este equipo (efectivo ya)")
    return config


def _wizard_save_routing(config, roles_path, models_out, dirty):
    if not dirty:
        print("Sin cambios de routing pendientes.")
        return False
    try:
        factory = models_config.load_config(models_out)
        factory["routing"] = config.get("routing", factory.get("routing", {}))
        validate(factory, roles_path)
    except ModelsError as exc:
        print(f"NO GUARDADO: {exc}")
        return False
    models_config.emit_atomic(models_out, factory)
    print(f"MODELS_WRITTEN {models_out}")
    if _safe_input("Generar y validar ahora? [Y/n] ").strip().lower() not in {"n", "no"}:
        if _generate_smoke_test().returncode != 0:
            print("MODELS_GENERATE_FAIL — el archivo quedo escrito; corre "
                  "./build.sh --output /tmp/x para ver el detalle")
            return "fail"
        if _safe_input("Instalar globalmente (./build.sh --install)? [y/N] ").strip().lower() in {"y", "yes", "s", "si"}:
            subprocess.run([str(ROOT / "build.sh"), "--install"], check=False)
    return True


def _wizard_discovered(config):
    routing = config.setdefault("routing", {})
    current = routing.get("discovered_providers", "auto")
    state = tui.run_picker(
        ("auto (recomendado) — del inventario vivo",
         "Lista manual — elegís vos",
         "Ninguno — desactiva la adopción automática"),
        style=_style(), prompt="Proveedores descubiertos:")
    if not isinstance(state, tui.Selected):
        return False
    if state.index == 0:
        routing["discovered_providers"] = "auto"
        print("OK: discovered_providers = auto")
        return True
    if state.index == 2:
        routing["discovered_providers"] = []
        print("OK: discovered_providers = []")
        return True
    candidates = sorted(models_config.DISCOVERABLE_PROVIDERS)
    manual_current = list(current) if isinstance(current, (list, tuple)) else []
    options = []
    for provider in candidates:
        mark = "rutable" if provider in manual_current else "solo probeable"
        options.append(f"{provider} — hoy: {mark}")
    picked = tui.run_picker(options, style=_style(), prompt="Togglear proveedor descubierto:")
    if not isinstance(picked, tui.Selected):
        return False
    provider = candidates[picked.index]
    if provider in manual_current:
        manual_current.remove(provider)
    else:
        manual_current.append(provider)
    routing["discovered_providers"] = sorted(manual_current)
    print(f"OK: discovered_providers = {routing['discovered_providers']} "
          "(lo inferido lleva MODEL_METADATA_INFERRED)")
    return True


def _wizard_routing_pin(config, roster):
    subject = choose("Rol ('*' = global)", ["*"] + sorted(row["role"] for row in roster))
    if not subject:
        return
    policy = tui.run_picker(
        ("Automático (recomendado)", "Fijar modelo"),
        style=_style(), prompt=f"{subject}:")
    if not isinstance(policy, tui.Selected):
        return
    if policy.index == 0:
        _pin_cli("--model-pin-clear", subject)
        remaining = _load_pins() or {}
        if subject != "*" and "*" in remaining:
            star = "/".join(remaining["*"])
            print(f"OK: {subject} sin pin propio — PERO el pin global '*' = {star} sigue aplicando")
        else:
            print(f"OK: {subject} = automatico (efectivo ya)")
        return
    provider = choose("Proveedor", sorted(PIN_PROVIDER_CATALOGS))
    if not provider:
        return
    suggestions = sorted(config.get("catalog", {}).get(PIN_PROVIDER_CATALOGS[provider], []))
    model = choose("Modelo", suggestions)
    if not model:
        return
    if _pin_cli("--model-pin-set", subject, f"{provider}/{model}") == 0:
        print(f"OK: {subject} = pin {provider}/{model} (efectivo ya)")
    else:
        print("RECHAZADO: ver el error de arriba (--model-pin-set)")


def _wizard_avanzado(config, roster, roles_path, models_out, dirty, panel_state):
    """Nested engineering menu — matrix, discovered, pins, refresh, save routing."""
    ADVANCED = (
        "Ver preferencias (matriz)",
        "Proveedores descubiertos",
        "Routing: fijar modelo / automatico",
        REFRESH_ITEM,
        "Guardar cambios de routing",
        "Volver",
    )
    while True:
        choice = tui.run_picker(ADVANCED, style=_style(), header=ui.rule("Avanzado"))
        if not isinstance(choice, tui.Selected) or choice.index == 5:
            return config, dirty, False
        if choice.index == 0:
            print()
            for line in _overrides_matrix_lines(config):
                print(line)
            print()
            for line in _status_lines(config, roster):
                print(line)
            _safe_input("Enter para volver… ")
        elif choice.index == 1:
            if _wizard_discovered(config):
                dirty = True
        elif choice.index == 2:
            _wizard_routing_pin(config, roster)
        elif choice.index == 3:
            return config, dirty, True  # force_refresh
        elif choice.index == 4:
            result = _wizard_save_routing(config, roles_path, models_out, dirty)
            if result == "fail":
                return config, dirty, False
            if result:
                dirty = False
                return config, dirty, False


# ADR-0074: the wizard dispatches on a stable key, like the home menu. The old code branched
# on `choice.index` and the tests pinned those integers, which meant the pin survived a label
# moving to a different branch.
WIZARD_ACTIONS = (
    Action("preferir", "Cambiar default", "elegir la preferencia de SET para este equipo"),
    Action("roles", "Revisar roles", "ver las preferencias por área y rol"),
    Action("actualizar", "Actualizar datos", "volver a medir estado y catálogos"),
    Action("listo", "Listo", "volver al menú"),
    Action("explicar", "Explicar /model", "entender la elección temporal de una sesión"),
    Action("mas", "Más opciones", "routing, cuentas y restauración"),
)


def _confirm_model_mutation(label):
    """Every destructive wizard action starts on Volver, never on Confirmar."""
    picked = tui.run_picker(("Volver", f"Confirmar: {label}"), style=_style(),
                            current=0, header=ui.rule("Confirmar cambio"))
    return isinstance(picked, tui.Selected) and picked.index == 1


def _more_options(config, roster, roles_path, models_out, dirty, panel_state):
    """Advanced mutations are disclosed progressively, never conflating their universes."""
    choices = (
        "Dejar que el router elija",
        "Restaurar defaults de SET",
        "Cuentas",
        "Avanzado de ingeniería",
        "Volver",
    )
    picked = tui.run_picker(choices, style=_style(), header=ui.rule("Más opciones"))
    if not isinstance(picked, tui.Selected) or picked.index == 4:
        return config, dirty, False
    if picked.index == 0:
        if not _confirm_model_mutation("dejar que el router elija"):
            return config, dirty, False
        router_choose_automatically()
        print("Routing automático: se borraron sólo los pins de routing.")
        return config, dirty, False
    if picked.index == 1:
        if not _confirm_model_mutation("restaurar defaults de SET"):
            return config, dirty, False
        runtime = config.get("runtime", {}).get("primary", "opencode")
        result = restore_set_defaults(factory=models_config.load_config(models_out),
                                      roles_path=roles_path, runtime=runtime)
        print(result.get("message", "Defaults restaurados: se borraron sólo overrides locales de modelos."))
        return models_config.effective_models_config(models_config.load_config(models_out)), dirty, False
    if picked.index == 2:
        return _wizard_cuentas(config, roster), dirty, False
    return _wizard_avanzado(config, roster, roles_path, models_out, dirty, panel_state)


def wizard(config, roster, roles_path, models_out):
    if not sys.stdin.isatty():
        print("Sin cambios pedidos y sin TTY: usa --status/--check/--set (ver --help).", file=sys.stderr)
        return 2
    dirty = False
    # The first paint is cache-only: no subscription, OpenCode, drift, or install probe.
    WIZARD_ITEMS = tuple(action.label for action in WIZARD_ACTIONS)
    panel_state = _load_subscription_panel_state()
    force_refresh = False
    painted_once = False
    auto_probed = False
    config = models_config.effective_models_config(config)
    while True:
        if force_refresh:
            try:
                panel_state = _refresh_subscriptions_live(config)
                available_opencode_models(config, force=True)
            except (OSError, ModelsError) as exc:
                print(ui.warn(f"No pude actualizar catálogo o suscripciones; podés reintentar. ({exc})"))
            force_refresh = False
            auto_probed = True
        age_s = None if panel_state.get("sub_at") is None else max(
            0.0, time.time() - panel_state["sub_at"])
        panel = _model_state_lines(_cached_model_state(config, roster))
        warnings = plugin_model_warnings((ROOT / "Global/opencode/gentle-logo.tsx",))
        panel.extend(warnings)
        choice = tui.run_picker(WIZARD_ITEMS, style=_style(), header="\n".join(panel))
        painted_once = True
        key = WIZARD_ACTIONS[choice.index].key if isinstance(choice, tui.Selected) else "listo"
        if key == "listo":
            if dirty:
                print("Quedan cambios de routing sin guardar — entrá a Avanzado y guardá.")
            return 0
        if key == "preferir":
            kind = tui.run_picker(
                ("Por área", "Por rol", "Volver"),
                style=_style(), header=ui.rule("Preferir un modelo"))
            if isinstance(kind, tui.Selected) and kind.index in (0, 1):
                config = _edit_overlay_cell(
                    config, roster, roles_path, models_out,
                    kind="area" if kind.index == 0 else "role")
        elif key == "roles":
            print("\n" + "\n".join(_overrides_matrix_lines(config)) + "\n")
        elif key == "actualizar":
            _, error = _refresh_model_state()
            if error:
                print(ui.warn(error))
            force_refresh = True
        elif key == "explicar":
            print("/model cambia sólo los próximos envíos de la sesión abierta. SET define defaults para sesiones nuevas; no modifica esa sesión.")
            # This is an informational escape hatch, never a mutation. Returning also
            # preserves the single-frame dismissal contract for non-interactive callers.
            return 0
        elif key == "mas":
            config, dirty, refresh = _more_options(
                config, roster, roles_path, models_out, dirty, panel_state)
            if refresh:
                force_refresh = True
                panel_state["stale"] = True



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--set", action="append", default=[], metavar="ADDR=VALUE")
    parser.add_argument("--add-model", action="append", default=[], metavar="CATALOG=MODEL")
    parser.add_argument("--add", metavar="SUBSCRIPTION")
    parser.add_argument("--drop", metavar="SUBSCRIPTION")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--no-install", action="store_true")
    # Plumbing (tests / advanced): explicit files, no build side effects.
    parser.add_argument("--models")
    parser.add_argument("--roles")
    parser.add_argument("--output-models")
    args = parser.parse_args()

    models_path = Path(args.models or ROOT / "models.toml")
    roles_path = Path(args.roles) if args.roles else ROOT / "roles.tsv"
    output = Path(args.output_models or models_path)
    plumbing = bool(args.models or args.output_models)

    try:
        config = models_config.load_config(models_path)
        # ADR-0048 (024 C2): the per-machine overlay is ALWAYS layered onto the CLI's
        # own view (status/wizard/--add/--drop), independent of `--models` plumbing --
        # a `--models`-pointed fixture/test copy is a different models.toml, but the
        # overlay is a property of THIS machine, not of that file.
        config["_subscriptions_overlay"] = models_config.load_subscriptions_overlay()
        roster = models_config.load_roster(roles_path)

        if args.status:
            status(config, roster)
            return 0
        if args.check:
            validate(config, roles_path)
            print("MODELS_CHECK_PASS")
            return 0

        mutated = False
        overlay_written = False
        for item in args.set:
            address, _, value = item.partition("=")
            if not value:
                die(f"--set needs ADDR=VALUE, got: {item}")
            # ADR-0071: area/role taste → models.local.toml; other addresses still mutate tracked.
            tokens = address.split(".")
            if tokens[0].startswith("role:") and len(tokens) == 2:
                role = tokens[0][len("role:"):]
                field = tokens[1]
                write_overlay_cell(("roles", role), field, value,
                                   factory=config, roles_path=roles_path)
                print(f"OVERLAY_WRITTEN roles.{role}.{field}={value}")
                overlay_written = True
            elif tokens[0] in config.get("areas", {}) and len(tokens) == 2:
                write_overlay_cell(("areas", tokens[0]), tokens[1], value,
                                   factory=config, roles_path=roles_path)
                print(f"OVERLAY_WRITTEN areas.{tokens[0]}.{tokens[1]}={value}")
                overlay_written = True
            else:
                target, key = parse_address(config, roster, address)
                target[key] = value
                mutated = True
        for item in args.add_model:
            catalog_key, _, value = item.partition("=")
            if catalog_key not in ("claude", "codex", "codex_effort") or not value:
                die(f"--add-model needs claude|codex|codex_effort=MODEL, got: {item}")
            if value not in config["catalog"][catalog_key]:
                config["catalog"][catalog_key] = sorted(set(config["catalog"][catalog_key]) | {value})
                mutated = True
        # ADR-0048 (024 C2, AC-05): --add/--drop write the PER-MACHINE overlay,
        # immediately -- same "efectivo ya" contract as the wizard's Suscripciones
        # (option 3) and as --model-pin-set. Never `config["subscriptions"]` (the
        # tracked file): that write is what used to dirty the tree on every
        # subscription change and block --update forever (tree_clean()).
        subscription_written = False
        if args.add:
            config["_subscriptions_overlay"] = models_config.write_subscription_overlay(args.add, True)
            print(f"SUBSCRIPTION_WRITTEN {args.add}=true ({models_config.subscriptions_overlay_path()})")
            subscription_written = True
        if args.drop:
            affected = dropped_cells(config, roster, args.drop)
            if affected:
                print(f"AFFECTED={len(affected)}")
                for role, model in affected:
                    print(f"  {role} {model}")
                print(f"MODELS_NOT_WRITTEN: reassign those cells before dropping '{args.drop}'")
                return 2
            if args.drop in ("anthropic", "openai"):
                print(f"AVISO: sin '{args.drop}' el harness nativo correspondiente queda sin uso (config se conserva).")
            config["_subscriptions_overlay"] = models_config.write_subscription_overlay(args.drop, False)
            print(f"SUBSCRIPTION_WRITTEN {args.drop}=false ({models_config.subscriptions_overlay_path()})")
            subscription_written = True

        if not mutated:
            return 0 if (subscription_written or overlay_written) else wizard(
                models_config.effective_models_config(config), roster, roles_path, output)

        validate(config, roles_path)
        models_config.emit_atomic(output, config)
        print(f"MODELS_WRITTEN {output}")
        if not plumbing:
            smoke = _generate_smoke_test()
            if smoke.returncode != 0:
                print(f"MODELS_GENERATE_FAIL rc={smoke.returncode} — corré "
                      "./build.sh --output /tmp/x para ver el detalle", file=sys.stderr)
                return 1
            if not args.no_install:
                install = [str(ROOT / "build.sh"), "--install"]
                if args.yes:
                    install.append("--yes")
                try:
                    subprocess.run(install, check=True)
                except subprocess.CalledProcessError as exc:
                    print(f"BUILD_INSTALL_FAIL rc={exc.returncode} — corré ./build.sh --install para ver el detalle", file=sys.stderr)
                    return 1
        return 0
    except ModelsError as exc:
        print(f"MODELS_INVALID: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
