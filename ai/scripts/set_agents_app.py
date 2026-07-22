#!/usr/bin/env python3
"""set-agents: unified console app for the SET-AGENTS harness (gentle-ai style).

A TTY menu plus a scriptable CLI over the same primitives: install/repair
(install.sh), self-update (git pull --ff-only + managed reinstall), model
routing (setup-models.sh), and — in later sections — the optional tools
catalog, MCP servers, and Claude Code plugins.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

# SET_AGENTS_ROOT/SET_AGENTS_STATE are test seams; real runs never set them.
ROOT = Path(os.environ.get("SET_AGENTS_ROOT") or Path(__file__).resolve().parents[2])
STATE_DIR = Path(os.environ.get("SET_AGENTS_STATE") or Path.home() / ".local/state/set-agentes")
APP_CONFIG = STATE_DIR / "config.toml"
MANAGED_MCP = ("engram", "context7", "playwright", "brave-cdp")
HARNESS_CLIS = ("opencode", "claude", "codex")


def color(text, code):
    return f"\033[{code}m{text}\033[0m" if sys.stdout.isatty() else text


def bold(text):
    return color(text, "1")


# ---------------------------------------------------------------- app config

def app_config():
    try:
        return tomllib.loads(APP_CONFIG.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def auto_update_enabled():
    return app_config().get("auto_update", True)


def set_auto_update(enabled):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    APP_CONFIG.write_text(f"auto_update = {'true' if enabled else 'false'}\n")
    print(f"AUTO_UPDATE={'on' if enabled else 'off'}")


# ----------------------------------------------------------------------- git

def git(*args, timeout=None):
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True, text=True, timeout=timeout, check=False,
    )


def fetch(timeout=10):
    try:
        return git("fetch", "--quiet", timeout=timeout).returncode == 0
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


def auth_state(cli):
    if not shutil.which(cli):
        return "missing"
    if cli == "opencode":
        result = subprocess.run(["opencode", "auth", "list"], capture_output=True, text=True, check=False)
        return "ok" if result.returncode == 0 and result.stdout.strip() else "needed"
    if cli == "codex":
        result = subprocess.run(["codex", "login", "status"], capture_output=True, check=False)
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


def cmd_status(human=False):
    behind = rev_count("HEAD..origin/main")
    drift = drift_state()
    print(
        f"APP_STATUS sha={short_sha()} drift={drift} "
        f"update={behind if behind is not None else '?'} "
        f"auto_update={'on' if auto_update_enabled() else 'off'}"
    )
    if not human:
        return 0
    print()
    print(f"{'CLI':<10} {'VERSIÓN':<28} AUTH")
    for cli in HARNESS_CLIS:
        installed = shutil.which(cli)
        version = version_of(cli) if installed else "FALTA"
        print(f"{cli:<10} {version:<28} {auth_state(cli) if installed else '-'}")
    if drift == "stale":
        print("\ndrift: la instalación quedó atrás del repo → opción [1] o ./build.sh --install")
    return 0


# -------------------------------------------------------------------- update

def cmd_check_update():
    online = fetch()
    behind = rev_count("HEAD..origin/main")
    suffix = "" if online else " (sin red: valor cacheado)"
    print(f"UPDATE_AVAILABLE={behind if behind is not None else '?'}{suffix}")
    return 0 if behind is not None else 2


def cmd_update(yes=False, no_install=False, assume_fetched=False):
    if not tree_clean():
        print("UPDATE_BLOCKED: hay cambios locales sin commitear — resolvelos y reintentá.")
        return 1
    if not assume_fetched:
        fetch()
    behind = rev_count("HEAD..origin/main")
    ahead = rev_count("origin/main..HEAD")
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
    print(git("log", "--oneline", "HEAD..origin/main").stdout.rstrip())
    pull = git("pull", "--ff-only")
    if pull.returncode != 0:
        print(f"UPDATE_BLOCKED: git pull falló:\n{pull.stderr.strip()}")
        return 1
    print(f"UPDATE_APPLIED {old}..{short_sha()}")
    if no_install:
        return 0
    install = [str(ROOT / "build.sh"), "--install"]
    if yes:
        install.append("--yes")
    # No capture: build.sh shows the managed diff and asks on the caller's TTY.
    return subprocess.run(install, check=False).returncode


def launch_update_check():
    """Menu-open behavior: auto-update with notice, or just a badge."""
    online = fetch(timeout=6)
    behind = rev_count("HEAD..origin/main")
    if not online and behind is None:
        return "sin red"
    if not behind:
        return "al día"
    if not auto_update_enabled():
        return f"{behind} commits nuevos (auto-update off → opción [2])"
    if not tree_clean() or rev_count("origin/main..HEAD"):
        return f"{behind} commits nuevos (repo local con cambios → opción [2])"
    print(bold(f"Actualización disponible ({behind} commits) — aplicando automáticamente…"))
    cmd_update(yes=True, assume_fetched=True)
    return "al día (recién actualizado)"


# ---------------------------------------------------------------------- menu

def run_tty(command):
    """Foreground child with inherited TTY: sudo/login prompts must reach the user."""
    return subprocess.run(command, check=False).returncode


def menu():
    update_badge = launch_update_check()
    while True:
        drift = {"ok": "OK", "stale": color("DESACTUALIZADO", "33"), "unknown": "?"}[drift_state()]
        print()
        print(bold(f"=== SET-AGENTS {short_sha()} ==="))
        print(f"drift: {drift} | update: {update_badge} | auto-update: {'on' if auto_update_enabled() else 'off'}")
        print()
        print("[1] Instalar / Reparar")
        print("[2] Actualizar")
        print("[3] Modelos")
        print("[7] Estado")
        print("[8] Salir")
        choice = input("> ").strip()
        if choice == "1":
            run_tty([str(ROOT / "install.sh")])
        elif choice == "2":
            cmd_update()
            update_badge = "al día"
        elif choice == "3":
            run_tty([str(ROOT / "setup-models.sh")])
        elif choice == "7":
            cmd_status(human=True)
            answer = input("auto-update: [t]oggle / Enter para volver: ").strip().lower()
            if answer == "t":
                set_auto_update(not auto_update_enabled())
        elif choice == "8":
            return 0


def main():
    parser = argparse.ArgumentParser(prog="set-agents", description=__doc__)
    parser.add_argument("--status", action="store_true", help="estado en una línea (APP_STATUS ...)")
    parser.add_argument("--check-update", action="store_true")
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--no-install", action="store_true")
    parser.add_argument("--auto-update", choices=("on", "off"))
    args = parser.parse_args()

    if args.status:
        return cmd_status(human=sys.stdout.isatty())
    if args.check_update:
        return cmd_check_update()
    if args.update:
        return cmd_update(yes=args.yes, no_install=args.no_install)
    if args.auto_update:
        set_auto_update(args.auto_update == "on")
        return 0
    if not sys.stdin.isatty():
        parser.print_help()
        return 2
    return menu()


if __name__ == "__main__":
    raise SystemExit(main())
