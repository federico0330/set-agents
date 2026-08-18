#!/usr/bin/env python3
"""Interactive and scriptable editor for models.toml (model routing per area/role).

Non-interactive core: --status, --check, --set, --add-model, --add, --drop.
Interactive wizard (no arguments): menu over the same primitives, then offers
a full-generate smoke test (`build.sh --output`, see `_generate_smoke_test`;
NOT `build.sh --check`, whose job since ADR-0041 is comparing Global/, not
validating a config nothing has regenerated Global/ from yet) and --install.
Writing is atomic and always validated in memory first (all three lanes); an
invalid change never reaches the file.

ADR-0048 (024 C2): [subscriptions] is the one field this file never writes into
models.toml -- the wizard's Suscripciones and the --add/--drop flags write the
per-machine overlay (`models_config.subscriptions_overlay_path()`, under
`$STATE_DIR`) instead, immediately, so a machine's own credentials can never
dirty the tracked tree (that used to block `--update` forever, tree_clean()).
"""

import argparse
import copy
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import models_config
import tui
from models_config import LANES, ModelsError, die

ROOT = Path(__file__).resolve().parents[2]
AREA_SIMPLE_FIELDS = ("claude", "codex", "codex_effort")

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


def parse_address(config, roster, address):
    """<duty>.<field> | <duty>.opencode.<lane> | role:<role>... | session.opencode_small_model.<lane>"""
    tokens = address.split(".")
    if tokens[0] == "session":
        if len(tokens) != 3 or tokens[1] != "opencode_small_model" or tokens[2] not in LANES:
            die(f"invalid address: {address}")
        return config["session"]["opencode_small_model"], tokens[2]
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
    if len(tokens) == 1 and tokens[0] in AREA_SIMPLE_FIELDS:
        return target, tokens[0]
    if len(tokens) == 2 and tokens[0] == "opencode" and tokens[1] in LANES:
        return target.setdefault("opencode", {}), tokens[1]
    die(f"invalid address: {address}")


def validate(config, roles_path):
    """Every lane must stay generable: emit to a temp file and load each profile."""
    # TOML is UTF-8 by specification; the locale never gets a vote.
    with tempfile.NamedTemporaryFile(
        "w", suffix=".toml", delete=False, encoding="utf-8"
    ) as handle:
        handle.write(models_config.emit(config))
        temp = handle.name
    try:
        for lane in LANES:
            models_config.load_roles(lane, roles_path, temp)
    finally:
        os.unlink(temp)


def _generate_smoke_test(profile):
    """Full generate() pipeline for `profile`, to a throwaway dir -- never Global/.

    Before ADR-0041, `build.sh --check` doubled as this smoke test purely as a side effect of
    always building its STAGING tree, and never actually compared it against anything. Now that
    `--check` means "does Global/ match a fresh go-zen build" (AC-01), it is the wrong question
    right after writing a NEW models.toml that nothing has regenerated Global/ from yet -- every
    real edit would report drift against a tree the edit hasn't touched. `build.sh --output DIR
    --profile P` is the same "does this fully generate" validation `--check` used to provide
    (same generate.py call, same die()s on an incoherent config), without the Global/ diff.
    """
    with tempfile.TemporaryDirectory() as tmp:
        return subprocess.run(
            [str(ROOT / "build.sh"), "--output", tmp, "--profile", profile],
        )


def dropped_cells(config, roster, subscription):
    """Every role/lane whose resolved opencode model consumes the given subscription."""
    affected = []
    for row in roster:
        for lane in LANES:
            resolved = models_config.resolve_role(row, config, lane)
            model = resolved["opencode_model"]
            if models_config.subscription_of(model, config) == subscription:
                affected.append((row["role"], lane, model))
    for lane in LANES:
        model = config["session"]["opencode_small_model"][lane]
        if models_config.subscription_of(model, config) == subscription:
            affected.append(("(session small_model)", lane, model))
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


def _status_lines(config, roster, profile):
    """The lines `status()` prints -- factored out so `wizard()` can ALSO pass them as the
    WIZARD_ITEMS picker's `header=` (F-03): the config table used to be print()ed to the normal
    screen right before `run_picker` cleared it into the alternate screen, invisible exactly
    while the user is choosing what to change."""
    subs = ", ".join(f"{k}={'on' if v else 'off'}" for k, v in sorted(models_config.effective_subscriptions(config).items()))
    lines = [
        f"profile: {profile}    subscriptions: {subs}",
        f"{'AREA':<10} {'CLAUDE':<8} {'CODEX':<14} {'EFFORT':<7} OPENCODE[{profile}]",
    ]
    duties = [d for d in models_config.DUTY_ORDER if d in config["areas"]]
    duties += sorted(set(config["areas"]) - set(duties))
    for duty in duties:
        area = config["areas"][duty]
        lines.append(
            f"{duty:<10} {area.get('claude', '-'):<8} {area.get('codex', '-'):<14} "
            f"{area.get('codex_effort', '-'):<7} {area.get('opencode', {}).get(profile, '-')}"
        )
    overrides = config.get("roles", {})
    if overrides:
        lines.append("overrides:")
        for role in sorted(overrides):
            fields = []
            for key, value in overrides[role].items():
                if key == "opencode":
                    fields += [f"opencode.{lane}={model}" for lane, model in value.items()]
                else:
                    fields.append(f"{key}={value}")
            lines.append(f"  {role}: " + ", ".join(fields))
    return lines


def status(config, roster, profile):
    for line in _status_lines(config, roster, profile):
        print(line)


_LIVE_UNSET = object()
SUBSCRIPTION_PROBE_FAILED = "suscripciones: no se pudo medir — mostrando pins"
REFRESH_ITEM = "Refrescar suscripciones y catálogo"


def _subscription_headline(subs, age_s=None, error=False):
    """AC-2.3/AC-2.4: age stamp or named degradation, then the tri-state pins."""
    detail = " ".join(subs) or "-"
    if error:
        return f"{SUBSCRIPTION_PROBE_FAILED} · {detail}"
    if age_s is not None:
        minutes = int(max(0.0, age_s) // 60)
        return f"suscripciones: hace {minutes} min · {detail}"
    return f"suscripciones: {detail}"


def _panel_lines(config, roster, profile, detected=None, *,
                 subscription_age_s=None, subscription_error=False,
                 live_discovered=_LIVE_UNSET):
    """The wizard's COMPACT header — replaces the old full `_status_lines` dump
    (10 wide area rows + one line per role override, printed to the normal screen
    AND repeated as header) that the owner reported as "una lista interminable".
    Area table stays (it's the useful core), overrides collapse to a count, and
    each subscription shows its tri-state origin (ADR-0029): ✓pin (true), ✗off
    (false), auto (absent — the probe decides; live state when `detected` came
    from a successful probe). `--status` keeps the full machine dump.

    `live_discovered=_LIVE_UNSET` keeps the historical "probe now" path for
    direct unit tests. The wizard always passes an explicit value (cached or
    None) so the first paint never calls probe_inventory (AC-2.1)."""
    subs = []
    # ADR-0048 (024 C2): the EFFECTIVE view (tracked [subscriptions] merged with this
    # machine's overlay) -- a neutral tracked file (AC-03) alone would show every
    # subscription as "auto" even on a machine that curated one off via the overlay.
    subscriptions = models_config.effective_subscriptions(config)
    for key in sorted(set(subscriptions) | (detected or set())):
        if key not in subscriptions:
            live = detected is not None and key in detected
            subs.append(f"{key}=auto{'✓' if live else ''}")
        else:
            subs.append(f"{key}={'✓pin' if subscriptions[key] else '✗off'}")
    # Repair F-03 (P2 review): the effective system default (`models_config.
    # ROUTING_DEFAULTS["discovered_providers"]`) is `"auto"`, not `[]` -- `load_config`
    # always materializes `"auto"` so this default was unreachable through the normal
    # path, but a caller handing this function a raw dict without the key (e.g. a direct
    # unit test or a future caller bypassing `load_config`) rendered the panel as if
    # auto-adoption were off. Aligned with the single source of truth instead of a
    # second, competing default.
    discovered = config.get("routing", {}).get(
        "discovered_providers", models_config.ROUTING_DEFAULTS["discovered_providers"])
    tiered = len({key for key, value in config.get("roles", {}).items() if "tiers" in value})
    lines = [
        f"lane: {profile} (auto)    {_subscription_headline(subs, subscription_age_s, subscription_error)}",
        "routing dinámico: el router decide por spawn para TODOS los roles (ADR-0030; --route-explain)"
        + (f" · variantes @tier: {tiered} roles" if tiered else ""),
    ]
    # ADR-0032/ADR-0034: la política vigente, por rol o global — Automático (el router
    # decide, incluidos los providers descubiertos que ADR-0034 hace routables) o pin
    # explícito del usuario. El origen de cada valor por spawn queda registrado en
    # decisions-v1.jsonl (selection_path: pin|dynamic; el fallback curado se registra en
    # el spawn como MODEL_STATIC_FALLBACK).
    pins = _load_pins()
    if pins is None:
        lines.append("política: Automático — pins no legibles (model-preference.toml inválido; ver --model-preference-show)")
    elif not pins:
        lines.append("política: Automático (recomendado) — sin pins; fijá un modelo con 'Routing: fijar modelo'")
    else:
        rendered = ", ".join(f"{role}={p}/{m}" for role, (p, m) in sorted(pins.items()))
        lines.append(f"política: Automático + {len(pins)} pin(s) — {rendered}")
    # ADR-0035 (AC-16): `"auto"` is a POLICY, never a sequence -- it is resolved against
    # the live probed inventory (`routing_core.catalog.resolve_discovered_providers`),
    # never iterated as a string (the exact `list("auto") == ['a','u','t','o']` defect
    # this replaces, reproduced live before this fix: "proveedores descubiertos rutables:
    # a, u, t, o"). An explicit list is still shown as-is, unchanged from before.
    if discovered == "auto":
        live = (_resolve_live_discovered(config)
                if live_discovered is _LIVE_UNSET else live_discovered)
        if live is None:
            lines.append("proveedores descubiertos rutables: auto → no verificable ahora (probe falló; ver --route-doctor)")
        elif not live:
            lines.append("proveedores descubiertos rutables: auto → ninguno vivo ahora (ver --route-doctor)")
        else:
            from routing_core.catalog import PROVIDER_BILLING_KIND
            billing_es = {"subscription": "suscripción", "metered": "metered"}
            rendered_live = ", ".join(
                f"{provider} ({billing_es.get(PROVIDER_BILLING_KIND.get(provider, 'unknown'), 'desconocido')})"
                for provider in live)
            lines.append(f"proveedores descubiertos rutables: auto → {rendered_live}")
    elif isinstance(discovered, str) and discovered:
        # Repair F-03: any OTHER truthy string (not "auto") is an unexpected shape --
        # `', '.join(discovered)` would silently iterate it character by character (the
        # exact `list("auto") == ['a', 'u', 't', 'o']` defect the comment above already
        # fixed for the literal "auto" case). Degrade to an explicit message instead of
        # ever joining a string as if it were a sequence of provider names.
        lines.append(f"proveedores descubiertos rutables: valor de configuración inesperado ({discovered!r})")
    elif discovered:
        lines.append(f"proveedores descubiertos rutables: {', '.join(discovered)}")
    lines.append("DEFAULTS CURADOS (fallback cuando el lane no aplica la decisión; ADR-0034/ADR-0035):")
    lines.append(f"{'AREA':<10} {'CLAUDE':<8} {'CODEX':<14} {'EFFORT':<7} OPENCODE[{profile}]")
    duties = [d for d in models_config.DUTY_ORDER if d in config.get("areas", {})]
    duties += sorted(set(config.get("areas", {})) - set(duties))
    for duty in duties:
        area = config["areas"][duty]
        lines.append(
            f"{duty:<10} {area.get('claude', '-'):<8} {area.get('codex', '-'):<14} "
            f"{area.get('codex_effort', '-'):<7} {area.get('opencode', {}).get(profile, '-')}"
        )
    overrides = config.get("roles", {})
    if overrides:
        lines.append(f"overrides de rol: {len(overrides)} — detalle: 'Ver detalle completo' o --status")
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
        result = subprocess.run(
            ["opencode", "models"], capture_output=True, text=True, timeout=20, check=False,
        )
        if result.returncode == 0:
            models = {line.strip() for line in result.stdout.splitlines() if "/" in line.strip()}
    if not models:
        for area in config["areas"].values():
            models |= set(area.get("opencode", {}).values())
        for override in config.get("roles", {}).values():
            models |= set(override.get("opencode", {}).values())
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
            return list(cached["ids"])
    models = tui.with_progress("listando modelos", lambda: _fetch_opencode_models(config))
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


def choose(prompt, options):
    """Arrow-key picker with an explicit `/`-triggered free-text fallback (AC-24, P3-tui):
    same "pick a listed option, or type a value that isn't listed" contract the old numbered
    menu + input() line had -- `/` then Enter on an unmatched query is accepted as free text,
    Esc/Ctrl-C/EOF is the new empty-input-cancels equivalent (returns `None` either way)."""
    result = tui.run_picker(options, freetext_allowed=True, prompt=f"{prompt}:")
    if result is None:
        return None
    if isinstance(result, tui.Selected):
        return options[result.index]
    return result.value or None


def _load_subscription_panel_state(now=None):
    """Disk only — never probes. First paint (AC-2.1) reads this."""
    now = time.time() if now is None else now
    entry = models_config.load_wizard_live_cache().get("subscriptions")
    if not isinstance(entry, dict):
        return {"detected": None, "sub_at": None, "sub_error": False, "stale": True}
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
    }


def _measure_subscriptions(config, now=None):
    """AC-2.4: named degradation, never a mute except, never an unusable wizard."""
    now = time.time() if now is None else now
    error = False
    try:
        detected = models_config.detect_subscriptions(config)
        if detected is None:
            error = True
            detected = None
        else:
            detected = set(detected)
    except Exception:
        detected = None
        error = True
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
        "live_discovered": None,
    }


def _refresh_subscriptions_live(config):
    """AC-2.2: live probe off the first-paint path, via tui.with_progress."""
    return tui.with_progress("midiendo suscripciones", lambda: _measure_subscriptions(config))


def wizard(config, roster, profile, roles_path, models_out):
    if not sys.stdin.isatty():
        print("Sin cambios pedidos y sin TTY: usá --status/--check/--set (ver --help).", file=sys.stderr)
        return 2
    dirty = False
    # Indexes 0-4 are a pinned contract (immutable suite drives the wizard by
    # Selected(N)); new actions append AFTER them, never reorder.
    WIZARD_ITEMS = ("Cambiar un área", "Cambiar un rol", "Suscripciones", "Guardar", "Salir sin guardar",
                    "Ver detalle completo", "Proveedores descubiertos (routing)",
                    "Routing: fijar modelo / automático",
                    REFRESH_ITEM)
    # AC-2.1: first paint is disk only. detect_subscriptions is NOT called
    # here — the historical try/except Exception mute at this site is gone.
    panel_state = _load_subscription_panel_state()
    panel_state.setdefault("live_discovered", None)
    force_refresh = False
    while True:
        # Live probe only on the refresh action (AC-2.3) — never before the
        # first run_picker (AC-2.1/AC-2.5) and never as a hidden second-loop
        # tax on every other wizard action.
        if force_refresh:
            panel_state = _refresh_subscriptions_live(config)
            available_opencode_models(config, force=True)
            force_refresh = False
        # AC-24/AC-29: Esc/Ctrl-C/EOF resolve to `None` inside run_picker itself -- treated
        # the same as "salir sin guardar", never a raised EOFError/KeyboardInterrupt here.
        # F-03/UI refresh: the state travels ONLY as the picker's `header=` (compact panel);
        # the old duplicate print() to the normal screen is gone with the avalanche.
        age_s = None if panel_state.get("sub_at") is None else max(
            0.0, time.time() - panel_state["sub_at"])
        panel = _panel_lines(
            config, roster, profile, panel_state.get("detected"),
            subscription_age_s=age_s,
            subscription_error=bool(panel_state.get("sub_error")),
            live_discovered=panel_state.get("live_discovered"),
        )
        choice = tui.run_picker(WIZARD_ITEMS, header="\n".join(panel))
        option = str(choice.index + 1) if isinstance(choice, tui.Selected) else "5"
        if option == "1" or option == "2":
            if option == "1":
                duties = [d for d in models_config.DUTY_ORDER if d in config["areas"]]
                subject = choose("Área", duties)
                prefix = subject
            else:
                subject = choose("Rol", sorted(row["role"] for row in roster))
                prefix = f"role:{subject}" if subject else None
            if not subject:
                continue
            field = choose("Campo", ["claude", "codex", "codex_effort"] + [f"opencode.{lane}" for lane in LANES])
            if not field:
                continue
            if field.startswith("opencode."):
                value = choose("Modelo", available_opencode_models(config))
            elif field == "codex_effort":
                value = choose("Effort", sorted(config["catalog"]["codex_effort"]))
            else:
                value = choose("Modelo", sorted(config["catalog"][field.split(".")[0]]))
            if not value:
                continue
            snapshot = copy.deepcopy(config)
            try:
                target, key = parse_address(config, roster, f"{prefix}.{field}")
                target[key] = value
                validate(config, roles_path)
                dirty = True
                print(f"OK: {prefix}.{field} = {value}")
            except ModelsError as exc:
                config.clear()
                config.update(snapshot)
                print(f"RECHAZADO: {exc}")
        elif option == "3":
            # ADR-0048 (024 C2, AC-05): the candidate universe is the audited
            # SUBSCRIPTION_BY_PREFIX targets (extended by any repo [providers] and
            # whatever this machine already declared) -- NOT just `config["subscriptions"]`
            # keys, which a neutral tracked file (AC-03) now normally leaves empty.
            candidates = _subscription_candidates(config)
            subscription = choose("Suscripción a cambiar", candidates)
            if not subscription:
                continue
            effective = models_config.effective_subscriptions(config)
            enabled = effective.get(subscription, False)
            if enabled:
                # Pinned contract: this guard fires BEFORE any further picker.
                affected = dropped_cells(config, roster, subscription)
                if affected:
                    print(f"AFFECTED={len(affected)} — celdas que usan '{subscription}':")
                    for role, lane, model in affected:
                        print(f"  {role} [{lane}] {model}")
                    # D-05: same defect as F-09 (fixed in set_agents_app.py) -- "opción 1/2"
                    # stopped meaning anything the day the numbered grid was replaced by the
                    # arrow selector. Reference the actual WIZARD_ITEMS labels directly so this
                    # can't go stale again if their order/wording ever changes.
                    print(f"Reasignalas primero ({WIZARD_ITEMS[0]!r} / {WIZARD_ITEMS[1]!r}) y después dala de baja.")
                    continue
            # Tri-state (ADR-0029): pin true / exclusión false / auto (clave ausente).
            state = tui.run_picker(
                ("Pin activada (true)", "Exclusión dura (false)", "Auto — el probe decide (borrar la línea)"),
                prompt=f"{subscription}:")
            if not isinstance(state, tui.Selected):
                continue
            # AC-05: writes the PER-MACHINE overlay, immediately -- never `config
            # ["subscriptions"]` (the tracked file), which is what used to dirty the
            # tree on every "Guardar" and block --update forever (tree_clean()).
            # "Efectivo ya", same contract as pins (option 8) -- no "Guardar" needed.
            value = None if state.index == 2 else (state.index == 0)
            config["_subscriptions_overlay"] = models_config.write_subscription_overlay(subscription, value)
            if value is None:
                print(f"OK: {subscription} = auto en este equipo (el probe decide; efectivo ya, "
                      "no requiere 'Guardar')")
            else:
                print(f"OK: {subscription} = {'on' if value else 'off'} en este equipo (efectivo ya, "
                      "no requiere 'Guardar')")
        elif option == "4":
            if not dirty:
                print("Sin cambios.")
                return 0
            try:
                validate(config, roles_path)
            except ModelsError as exc:
                print(f"NO GUARDADO: {exc}")
                continue
            models_config.emit_atomic(models_out, config)
            print(f"MODELS_WRITTEN {models_out}")
            if _safe_input("¿Generar y validar ahora? [Y/n] ").strip().lower() not in {"n", "no"}:
                if _generate_smoke_test(profile).returncode != 0:
                    print(f"MODELS_GENERATE_FAIL — el archivo quedó escrito; corré "
                          f"./build.sh --output /tmp/x --profile {profile} para ver el detalle")
                    return 1
                if _safe_input("¿Instalar globalmente (./build.sh --install)? [y/N] ").strip().lower() in {"y", "yes", "s", "si"}:
                    subprocess.run([str(ROOT / "build.sh"), "--install"], check=False)
            return 0
        elif option == "5":
            return 0
        elif option == "6":
            # On demand, on the NORMAL screen (survives after the wizard exits);
            # the picker's header clamps long content, a pause here doesn't.
            print()
            for line in _status_lines(config, roster, profile):
                print(line)
            _safe_input("Enter para volver… ")
        elif option == "7":
            # ADR-0034/ADR-0035 (AC-16): three explicit policies, not a single hardcoded
            # toggle pair -- "auto" (recommended, ADR-0034's new default: derives the
            # routable set from the live probed inventory), "lista manual" (the previous
            # per-provider toggle, but candidates now come from the AUDITED set --
            # `models_config.DISCOVERABLE_PROVIDERS`, never a literal tuple, so a future
            # fifth audited provider appears here without touching this file), or
            # "ninguno" (explicit `[]`, ADR-0034 point 1: total opt-out that survives
            # `emit()`).
            routing = config.setdefault("routing", {})
            current = routing.get("discovered_providers", "auto")
            state = tui.run_picker(
                ("auto (recomendado) — el router decide del inventario vivo (ADR-0034)",
                 "Lista manual — elegís vos, por provider auditado",
                 "Ninguno — desactiva la auto-adopción"),
                prompt="Proveedores descubiertos:")
            if not isinstance(state, tui.Selected):
                continue
            if state.index == 0:
                routing["discovered_providers"] = "auto"
                dirty = True
                print("OK: discovered_providers = auto (ADR-0034: deriva del inventario vivo; "
                      "la fila curada sigue ganando el empate)")
            elif state.index == 2:
                routing["discovered_providers"] = []
                dirty = True
                print("OK: discovered_providers = [] (auto-adopción desactivada)")
            else:
                candidates = sorted(models_config.DISCOVERABLE_PROVIDERS)
                manual_current = list(current) if isinstance(current, (list, tuple)) else []
                options = []
                for provider in candidates:
                    mark = "rutable" if provider in manual_current else "solo probeable"
                    options.append(f"{provider} — hoy: {mark}")
                picked = tui.run_picker(options, prompt="Togglear proveedor descubierto:")
                if not isinstance(picked, tui.Selected):
                    continue
                provider = candidates[picked.index]
                if provider in manual_current:
                    manual_current.remove(provider)
                else:
                    manual_current.append(provider)
                routing["discovered_providers"] = sorted(manual_current)
                dirty = True
                print(f"OK: discovered_providers = {routing['discovered_providers']} (ADR-0034: la curada gana; "
                      "lo inferido lleva MODEL_METADATA_INFERRED)")
        elif option == "8":
            # ADR-0032: política por rol (o global '*') — Automático (el router decide por
            # spawn) o pin explícito. Escribe model-preference.toml vía el CLI sancionado,
            # INMEDIATO (archivo hermano, independiente de 'Guardar'/models.toml).
            subject = choose("Rol ('*' = global)", ["*"] + sorted(row["role"] for row in roster))
            if not subject:
                continue
            policy = tui.run_picker(
                ("Automático (recomendado) — el router decide por spawn", "Fijar modelo — pin explícito"),
                prompt=f"{subject}:")
            if not isinstance(policy, tui.Selected):
                continue
            if policy.index == 0:
                _pin_cli("--model-pin-clear", subject)
                # F-04 (ADR-0032 review repair): "automático" mentiría si el pin global
                # `*` sigue aplicando a este rol (el router cae al `*` sin pin propio).
                remaining = _load_pins() or {}
                if subject != "*" and "*" in remaining:
                    star = "/".join(remaining["*"])
                    print(f"OK: {subject} sin pin propio — PERO el pin global '*' = {star} sigue aplicando; "
                          "para automático real, poné '*' en Automático también")
                else:
                    print(f"OK: {subject} = automático (sin pin; efectivo ya — no requiere 'Guardar')")
                continue
            provider = choose("Proveedor", sorted(PIN_PROVIDER_CATALOGS))
            if not provider:
                continue
            suggestions = sorted(config.get("catalog", {}).get(PIN_PROVIDER_CATALOGS[provider], []))
            model = choose("Modelo (identidad del catálogo de routing)", suggestions)
            if not model:
                continue
            if _pin_cli("--model-pin-set", subject, f"{provider}/{model}") == 0:
                print(f"OK: {subject} = pin {provider}/{model} (efectivo ya — no requiere 'Guardar'; "
                      "el router lo respeta como override y lo registra como MODEL_PINNED)")
            else:
                print("RECHAZADO: ver el error de arriba (--model-pin-set)")
        elif option == "9":
            # AC-2.3: refresh is a new action appended AFTER indexes 0-4.
            force_refresh = True
            panel_state["stale"] = True
            continue


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
    parser.add_argument("--profile")
    args = parser.parse_args()

    models_path = Path(args.models or ROOT / "models.toml")
    roles_path = Path(args.roles) if args.roles else ROOT / "roles.tsv"
    output = Path(args.output_models or models_path)
    plumbing = bool(args.models or args.output_models)
    profile = args.profile or models_config.active_profile()

    try:
        config = models_config.load_config(models_path)
        # ADR-0048 (024 C2): the per-machine overlay is ALWAYS layered onto the CLI's
        # own view (status/wizard/--add/--drop), independent of `--models` plumbing --
        # a `--models`-pointed fixture/test copy is a different models.toml, but the
        # overlay is a property of THIS machine, not of that file.
        config["_subscriptions_overlay"] = models_config.load_subscriptions_overlay()
        roster = models_config.load_roster(roles_path)

        if args.status:
            status(config, roster, profile)
            return 0
        if args.check:
            validate(config, roles_path)
            print("MODELS_CHECK_PASS")
            return 0

        mutated = False
        for item in args.set:
            address, _, value = item.partition("=")
            if not value:
                die(f"--set needs ADDR=VALUE, got: {item}")
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
                for role, lane, model in affected:
                    print(f"  {role} [{lane}] {model}")
                print(f"MODELS_NOT_WRITTEN: reassign those cells before dropping '{args.drop}'")
                return 2
            if args.drop in ("anthropic", "openai"):
                print(f"AVISO: sin '{args.drop}' el harness nativo correspondiente queda sin uso (config se conserva).")
            config["_subscriptions_overlay"] = models_config.write_subscription_overlay(args.drop, False)
            print(f"SUBSCRIPTION_WRITTEN {args.drop}=false ({models_config.subscriptions_overlay_path()})")
            subscription_written = True

        if not mutated:
            return 0 if subscription_written else wizard(config, roster, profile, roles_path, output)

        validate(config, roles_path)
        models_config.emit_atomic(output, config)
        print(f"MODELS_WRITTEN {output}")
        if not plumbing:
            smoke = _generate_smoke_test(profile)
            if smoke.returncode != 0:
                print(f"MODELS_GENERATE_FAIL rc={smoke.returncode} — corré "
                      f"./build.sh --output /tmp/x --profile {profile} para ver el detalle", file=sys.stderr)
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
