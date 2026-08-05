#!/usr/bin/env python3
"""Interactive and scriptable editor for models.toml (model routing per area/role).

Non-interactive core: --status, --check, --set, --add-model, --add, --drop.
Interactive wizard (no arguments): menu over the same primitives, then offers
./build.sh --check and --install. Writing is atomic and always validated in
memory first (all three lanes); an invalid change never reaches the file.
"""

import argparse
import copy
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import models_config
import tui
from models_config import LANES, ModelsError, die

ROOT = Path(__file__).resolve().parents[2]
AREA_SIMPLE_FIELDS = ("claude", "codex", "codex_effort")


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
    with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as handle:
        handle.write(models_config.emit(config))
        temp = handle.name
    try:
        for lane in LANES:
            models_config.load_roles(lane, roles_path, temp)
    finally:
        os.unlink(temp)


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


def _status_lines(config, roster, profile):
    """The lines `status()` prints -- factored out so `wizard()` can ALSO pass them as the
    WIZARD_ITEMS picker's `header=` (F-03): the config table used to be print()ed to the normal
    screen right before `run_picker` cleared it into the alternate screen, invisible exactly
    while the user is choosing what to change."""
    subs = ", ".join(f"{k}={'on' if v else 'off'}" for k, v in sorted(config["subscriptions"].items()))
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


def _panel_lines(config, roster, profile, detected=None):
    """The wizard's COMPACT header — replaces the old full `_status_lines` dump
    (10 wide area rows + one line per role override, printed to the normal screen
    AND repeated as header) that the owner reported as "una lista interminable".
    Area table stays (it's the useful core), overrides collapse to a count, and
    each subscription shows its tri-state origin (ADR-0029): ✓pin (true), ✗off
    (false), auto (absent — the probe decides; live state when `detected` came
    from a successful probe). `--status` keeps the full machine dump."""
    subs = []
    subscriptions = config.get("subscriptions", {})
    for key in sorted(set(subscriptions) | (detected or set())):
        if key not in subscriptions:
            live = detected is not None and key in detected
            subs.append(f"{key}=auto{'✓' if live else ''}")
        else:
            subs.append(f"{key}={'✓pin' if subscriptions[key] else '✗off'}")
    discovered = config.get("routing", {}).get("discovered_providers", [])
    tiered = len({key for key, value in config.get("roles", {}).items() if "tiers" in value})
    lines = [
        f"lane: {profile} (auto)    suscripciones: {' '.join(subs) or '-'}",
        "routing dinámico: el router decide por spawn para TODOS los roles (ADR-0030; --route-explain)"
        + (f" · variantes @tier: {tiered} roles" if tiered else ""),
    ]
    if discovered:
        lines.append(f"proveedores descubiertos rutables: {', '.join(discovered)}")
    lines.append("DEFAULTS CURADOS (fallback cuando el lane no aplica la decisión):")
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


def available_opencode_models(config):
    """Suggestions for the wizard: live `opencode models` when possible, config otherwise."""
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


def wizard(config, roster, profile, roles_path, models_out):
    if not sys.stdin.isatty():
        print("Sin cambios pedidos y sin TTY: usá --status/--check/--set (ver --help).", file=sys.stderr)
        return 2
    dirty = False
    # Indexes 0-4 are a pinned contract (immutable suite drives the wizard by
    # Selected(N)); new actions append AFTER them, never reorder.
    WIZARD_ITEMS = ("Cambiar un área", "Cambiar un rol", "Suscripciones", "Guardar", "Salir sin guardar",
                    "Ver detalle completo", "Proveedores descubiertos (routing)")
    # Probe once per wizard run (shared cache): live subscription state for the
    # header's tri-state origins. None on any failure — panel degrades to pins.
    try:
        detected = models_config.detect_subscriptions(config)
    except Exception:
        detected = None
    while True:
        # AC-24/AC-29: Esc/Ctrl-C/EOF resolve to `None` inside run_picker itself -- treated
        # the same as "salir sin guardar", never a raised EOFError/KeyboardInterrupt here.
        # F-03/UI refresh: the state travels ONLY as the picker's `header=` (compact panel);
        # the old duplicate print() to the normal screen is gone with the avalanche.
        panel = _panel_lines(config, roster, profile, detected)
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
            subscription = choose("Suscripción a cambiar", sorted(config["subscriptions"]))
            if not subscription:
                continue
            enabled = config["subscriptions"].get(subscription, False)
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
            if state.index == 2:
                config["subscriptions"].pop(subscription, None)
                print(f"OK: {subscription} = auto (el probe decide)")
            else:
                config["subscriptions"][subscription] = state.index == 0
                print(f"OK: {subscription} = {'on' if state.index == 0 else 'off'}")
            dirty = True
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
            if _safe_input("¿Correr ./build.sh --check ahora? [Y/n] ").strip().lower() not in {"n", "no"}:
                if subprocess.run([str(ROOT / "build.sh"), "--check"], check=False).returncode != 0:
                    print("BUILD_CHECK_FAIL — el archivo quedó escrito; corré ./build.sh --check para ver el detalle")
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
            # ADR-0029 opt-in: which discovered opencode providers become routable.
            routing = config.setdefault("routing", {})
            current = list(routing.get("discovered_providers", []))
            options = []
            for provider in ("opencode-zen", "opencode-go"):
                mark = "rutable" if provider in current else "solo probeable"
                options.append(f"{provider} — hoy: {mark}")
            picked = tui.run_picker(options, prompt="Togglear proveedor descubierto:")
            if not isinstance(picked, tui.Selected):
                continue
            provider = ("opencode-zen", "opencode-go")[picked.index]
            if provider in current:
                current.remove(provider)
            else:
                current.append(provider)
            routing["discovered_providers"] = sorted(current)
            dirty = True
            print(f"OK: discovered_providers = {routing['discovered_providers']} (ADR-0029: la curada gana; "
                  "lo inferido lleva MODEL_METADATA_INFERRED)")


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
        if args.add:
            config["subscriptions"][args.add] = True
            mutated = True
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
            config["subscriptions"][args.drop] = False
            mutated = True

        if not mutated:
            return wizard(config, roster, profile, roles_path, output)

        validate(config, roles_path)
        models_config.emit_atomic(output, config)
        print(f"MODELS_WRITTEN {output}")
        if not plumbing:
            try:
                subprocess.run([str(ROOT / "build.sh"), "--check"], check=True)
                if not args.no_install:
                    install = [str(ROOT / "build.sh"), "--install"]
                    if args.yes:
                        install.append("--yes")
                    subprocess.run(install, check=True)
            except subprocess.CalledProcessError as exc:
                print(f"BUILD_CHECK_FAIL rc={exc.returncode} — corré ./build.sh --check para ver el detalle", file=sys.stderr)
                return 1
        return 0
    except ModelsError as exc:
        print(f"MODELS_INVALID: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
