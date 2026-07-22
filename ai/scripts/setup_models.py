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


def status(config, roster, profile):
    subs = ", ".join(f"{k}={'on' if v else 'off'}" for k, v in sorted(config["subscriptions"].items()))
    print(f"profile: {profile}    subscriptions: {subs}")
    print(f"{'AREA':<10} {'CLAUDE':<8} {'CODEX':<14} {'EFFORT':<7} OPENCODE[{profile}]")
    duties = [d for d in models_config.DUTY_ORDER if d in config["areas"]]
    duties += sorted(set(config["areas"]) - set(duties))
    for duty in duties:
        area = config["areas"][duty]
        print(
            f"{duty:<10} {area.get('claude', '-'):<8} {area.get('codex', '-'):<14} "
            f"{area.get('codex_effort', '-'):<7} {area.get('opencode', {}).get(profile, '-')}"
        )
    overrides = config.get("roles", {})
    if overrides:
        print("overrides:")
        for role in sorted(overrides):
            fields = []
            for key, value in overrides[role].items():
                if key == "opencode":
                    fields += [f"opencode.{lane}={model}" for lane, model in value.items()]
                else:
                    fields.append(f"{key}={value}")
            print(f"  {role}: " + ", ".join(fields))


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


def choose(prompt, options):
    """Numbered menu with free-text fallback. Returns None on empty input."""
    for index, option in enumerate(options, 1):
        print(f"  [{index}] {option}")
    answer = input(f"{prompt} (número o texto libre, Enter cancela): ").strip()
    if not answer:
        return None
    if answer.isdigit() and 1 <= int(answer) <= len(options):
        return options[int(answer) - 1]
    return answer


def wizard(config, roster, profile, roles_path, models_out):
    if not sys.stdin.isatty():
        print("Sin cambios pedidos y sin TTY: usá --status/--check/--set (ver --help).", file=sys.stderr)
        return 2
    dirty = False
    while True:
        print()
        status(config, roster, profile)
        print()
        print("[1] cambiar un área  [2] cambiar un rol  [3] suscripciones  [4] guardar  [5] salir sin guardar")
        option = input("> ").strip()
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
            subscription = choose("Suscripción a activar/desactivar", sorted(config["subscriptions"]))
            if not subscription:
                continue
            enabled = config["subscriptions"].get(subscription, False)
            if enabled:
                affected = dropped_cells(config, roster, subscription)
                if affected:
                    print(f"AFFECTED={len(affected)} — celdas que usan '{subscription}':")
                    for role, lane, model in affected:
                        print(f"  {role} [{lane}] {model}")
                    print("Reasignalas primero (opción 1/2) y después dala de baja.")
                    continue
            config["subscriptions"][subscription] = not enabled
            dirty = True
            print(f"OK: {subscription} = {'on' if not enabled else 'off'}")
        elif option == "4":
            if not dirty:
                print("Sin cambios.")
                return 0
            try:
                validate(config, roles_path)
            except ModelsError as exc:
                print(f"NO GUARDADO: {exc}")
                continue
            atomic_write(models_out, models_config.emit(config))
            print(f"MODELS_WRITTEN {models_out}")
            if input("¿Correr ./build.sh --check ahora? [Y/n] ").strip().lower() not in {"n", "no"}:
                subprocess.run([str(ROOT / "build.sh"), "--check"], check=True)
                if input("¿Instalar globalmente (./build.sh --install)? [y/N] ").strip().lower() in {"y", "yes", "s", "si"}:
                    subprocess.run([str(ROOT / "build.sh"), "--install"], check=False)
            return 0
        elif option == "5":
            return 0


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
    profile = args.profile or (ROOT / "active-profile").read_text().strip()

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
        atomic_write(output, models_config.emit(config))
        print(f"MODELS_WRITTEN {output}")
        if not plumbing:
            subprocess.run([str(ROOT / "build.sh"), "--check"], check=True)
            if not args.no_install:
                install = [str(ROOT / "build.sh"), "--install"]
                if args.yes:
                    install.append("--yes")
                subprocess.run(install, check=True)
        return 0
    except ModelsError as exc:
        print(f"MODELS_INVALID: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
