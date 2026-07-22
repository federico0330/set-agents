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
import tempfile
import tomllib
from pathlib import Path

# SET_AGENTS_ROOT/SET_AGENTS_STATE are test seams; real runs never set them.
ROOT = Path(os.environ.get("SET_AGENTS_ROOT") or Path(__file__).resolve().parents[2])
STATE_DIR = Path(os.environ.get("SET_AGENTS_STATE") or Path.home() / ".local/state/set-agentes")
APP_CONFIG = STATE_DIR / "config.toml"
MANAGED_MCP = ("engram", "context7", "playwright", "brave-cdp")
HARNESS_CLIS = ("opencode", "claude", "codex")


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


# --------------------------------------------------------------------- tools

def load_catalog():
    return tomllib.loads((ROOT / "tools.toml").read_text())


def platform_pm():
    if sys.platform == "darwin":
        return "brew" if shutil.which("brew") else None
    for pm, binary in (("pacman", "pacman"), ("apt", "apt-get")):
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


def cmd_tools():
    for name, entry in load_catalog().get("cli", {}).items():
        installed = bool(shutil.which(entry["detect"]))
        print(f"TOOL {name} installed={'yes' if installed else 'no'}")
    return 0


def cmd_tools_install(name, dry=False, yes=False):
    entry = load_catalog().get("cli", {}).get(name)
    if entry is None:
        print(f"TOOL_UNKNOWN {name} — agregalo en tools.toml")
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
    if command.startswith("sudo "):
        # Never silent sudo (same contract as install.sh), even with --yes.
        if not sys.stdin.isatty():
            print(f"TOOL_MANUAL {name}: necesita sudo — corré: {command}")
            return 1
        print(f"Se necesita privilegio de administrador para:\n    {command}")
        if input("¿Ejecutar ese comando? [y/N] ").strip().lower() not in {"y", "yes", "s", "si"}:
            return 1
    elif not yes and sys.stdin.isatty():
        if input(f"¿Ejecutar '{command}'? [y/N] ").strip().lower() not in {"y", "yes", "s", "si"}:
            return 1
    result = subprocess.run(["bash", "-c", command], check=False)
    if result.returncode == 0:
        print(f"TOOL_OK {name}")
        if entry.get("note"):
            print(f"NOTA: {entry['note']}")
        return 0
    print(f"TOOL_FAIL {name} rc={result.returncode} — {entry['install'].get('doc', '')}")
    return 1


def tools_menu():
    catalog = load_catalog().get("cli", {})
    names = list(catalog)
    print()
    for index, name in enumerate(names, 1):
        installed = bool(shutil.which(catalog[name]["detect"]))
        state = color("instalado", "32") if installed else "falta"
        print(f"  [{index}] {name:<10} {state}")
    answer = input("¿Cuál instalo? (número, Enter vuelve): ").strip()
    if answer.isdigit() and 1 <= int(answer) <= len(names):
        cmd_tools_install(names[int(answer) - 1])


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
        atomic_write(path, "\n".join(lines).rstrip() + "\n" if lines else "")
        return
    data = read_json(path)
    servers = data.setdefault(_servers_key(harness), {})
    if remove:
        servers.pop(name, None)
    elif enabled is not None and harness == "opencode" and name in servers:
        servers[name]["enabled"] = enabled
    elif spec is not None and name not in servers:
        servers[name] = _mcp_json_entry(harness, spec)
    atomic_write(path, json.dumps(data, indent=2) + "\n")


def _mcp_spec(name):
    spec = load_catalog().get("mcp", {}).get(name)
    if spec is None:
        print(f"MCP_UNKNOWN {name} — agregalo en tools.toml")
    return spec


def _mcp_selected(harness):
    targets = mcp_targets()
    if harness:
        if harness not in targets:
            print(f"MCP_NO_HARNESS {harness} (no detectado en esta máquina)")
            return {}
        return {harness: targets[harness]}
    return targets


def cmd_mcp():
    targets = mcp_targets()
    for name in load_catalog().get("mcp", {}):
        for harness, target in targets.items():
            print(f"MCP {name} harness={harness} state={mcp_state(harness, target, name)}")
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
    spec = _mcp_spec(name)
    if spec is None:
        return 2
    for h, target in _mcp_selected(harness).items():
        state = mcp_state(h, target, name)
        if h in ("opencode", "codex"):
            if state == "absent" and h == "opencode" and name not in MANAGED_MCP:
                print(f"MCP_ABSENT {name} harness={h} (primero --mcp-add)")
                continue
            mcp_write(h, target, name, enabled=enabled)
        else:
            # No disable flag in these formats: on == present, off == removed.
            if enabled and state == "absent":
                mcp_write(h, target, name, spec=spec)
            elif not enabled and state != "absent":
                mcp_write(h, target, name, remove=True)
        print(f"MCP_SET {name} harness={h} state={mcp_state(h, target, name)}")
    return 0


def cmd_mcp_remove(name, harness=None):
    for h, target in _mcp_selected(harness).items():
        if h == "opencode" and name in MANAGED_MCP:
            print(f"MCP_MANAGED {name} harness=opencode — no se remueve un server gestionado")
            continue
        mcp_write(h, target, name, remove=True)
        print(f"MCP_REMOVED {name} harness={h}")
    return 0


# ------------------------------------------------------------------- plugins

def claude_settings_path():
    return Path.home() / ".claude/settings.json"


def cmd_plugins():
    plugins = read_json(claude_settings_path()).get("enabledPlugins", {})
    if not plugins:
        print("PLUGINS_NONE")
    for name, enabled in sorted(plugins.items()):
        print(f"PLUGIN {name} enabled={'true' if enabled else 'false'}")
    return 0


def cmd_plugin_set(name, enabled):
    if name == "engram@engram":
        print("PLUGIN_MANAGED engram@engram — la política del repo lo fuerza apagado en cada install")
        return 1
    data = read_json(claude_settings_path())
    data.setdefault("enabledPlugins", {})[name] = enabled
    atomic_write(claude_settings_path(), json.dumps(data, indent=2) + "\n")
    print(f"PLUGIN_SET {name} enabled={'true' if enabled else 'false'}")
    return 0


def mcp_menu():
    catalog = list(load_catalog().get("mcp", {}))
    targets = mcp_targets()
    print()
    print(f"harnesses detectados: {', '.join(targets)}")
    for name in catalog:
        states = ", ".join(f"{h}:{mcp_state(h, t, name)}" for h, t in targets.items())
        print(f"  {name:<12} {states}")
    name = input("Server (Enter vuelve): ").strip()
    if not name:
        return
    action = input("[a]gregar / [e]ncender / a[p]agar / [r]emover: ").strip().lower()
    harness = input(f"Harness ({'/'.join(targets)}, Enter=todos): ").strip() or None
    if action == "a":
        cmd_mcp_add(name, harness)
    elif action == "e":
        cmd_mcp_toggle(name, harness, True)
    elif action == "p":
        cmd_mcp_toggle(name, harness, False)
    elif action == "r":
        cmd_mcp_remove(name, harness)


def plugins_menu():
    cmd_plugins()
    name = input("Plugin a togglear (Enter vuelve): ").strip()
    if not name:
        return
    current = read_json(claude_settings_path()).get("enabledPlugins", {}).get(name, False)
    cmd_plugin_set(name, not current)


# ---------------------------------------------------------------------- menu

def run_tty(command):
    """Foreground child with inherited TTY: sudo/login prompts must reach the user."""
    return subprocess.run(command, check=False).returncode


DRIFT_BADGE = {
    "ok": lambda: color("OK", "32"),
    "stale": lambda: color("DESACTUALIZADO", "33"),
    "unknown": lambda: "?",
}


def menu():
    print()
    banner()
    if first_run():
        print()
        print(bold(f"📖 Primera vez acá → leé README.md (sección {platform_label()}) para saber qué esperar."))
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        APP_CONFIG.write_text("auto_update = true\n")
    print(dim("· chequeando updates…"))
    update_badge = launch_update_check()
    # Drift regenerates a full staging (~2 s): cache it and refresh only after
    # actions that can change it, instead of on every redraw.
    drift = drift_state()
    while True:
        print()
        print(bold(f"=== SET-AGENTS {short_sha()} ==="))
        print(
            f"drift: {DRIFT_BADGE[drift]()} | update: {color(update_badge, '36')} | "
            + dim(f"auto-update: {'on' if auto_update_enabled() else 'off'}")
        )
        print()
        print("[1] 📦 Instalar / Reparar")
        print("[2] 🔄 Actualizar")
        print("[3] 🧠 Modelos")
        print("[4] 🧰 Herramientas (CLIs)")
        print("[5] 🔌 MCPs")
        print("[6] 🧩 Plugins Claude Code")
        print("[7] 📊 Estado")
        print("[8] ⏻  Salir")
        choice = input("> ").strip()
        if choice == "1":
            run_tty([str(ROOT / "install.sh")])
            drift = drift_state()
        elif choice == "2":
            cmd_update()
            update_badge = "al día"
            drift = drift_state()
        elif choice == "3":
            run_tty([str(ROOT / "setup-models.sh")])
            drift = drift_state()
        elif choice == "4":
            tools_menu()
        elif choice == "5":
            mcp_menu()
        elif choice == "6":
            plugins_menu()
        elif choice == "7":
            drift = drift_state()
            cmd_status(human=True)
            answer = input("auto-update: [t]oggle / Enter para volver: ").strip().lower()
            if answer == "t":
                set_auto_update(not auto_update_enabled())
        elif choice == "8":
            return 0


def main():
    parser = argparse.ArgumentParser(
        prog="set-agents",
        description=__doc__,
        epilog="Primera vez: leé README.md — explica qué vas a ver según tu sistema operativo.",
    )
    parser.add_argument("--status", action="store_true", help="estado en una línea (APP_STATUS ...)")
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
    parser.add_argument("--harness", choices=("opencode", "claude", "codex", "cursor", "gemini"))
    parser.add_argument("--plugins", action="store_true")
    parser.add_argument("--plugin-on", metavar="NAME")
    parser.add_argument("--plugin-off", metavar="NAME")
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
    if args.plugins:
        return cmd_plugins()
    if args.plugin_on:
        return cmd_plugin_set(args.plugin_on, True)
    if args.plugin_off:
        return cmd_plugin_set(args.plugin_off, False)
    if not sys.stdin.isatty():
        parser.print_help()
        return 2
    return menu()


if __name__ == "__main__":
    raise SystemExit(main())
