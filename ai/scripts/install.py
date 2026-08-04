#!/usr/bin/env python3
"""Managed, backed-up global installation with rollback on smoke failure."""

import argparse
import datetime as dt
import difflib
import json
import os
import re
import subprocess
import shutil
import sys
import tempfile
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from models_config import MANAGED_MCP

parser = argparse.ArgumentParser()
parser.add_argument("--staging", required=True)
parser.add_argument("--home", required=True)
parser.add_argument("--target", action="append", choices=("opencode", "claude-code", "codex", "pi"))
parser.add_argument("--preview", action="store_true")
args = parser.parse_args()

staging = Path(args.staging)
home = Path(args.home)
all_targets = {
    "opencode": home / ".config/opencode",
    "claude-code": home / ".claude",
    "codex": home / ".codex",
    "pi": home / ".pi/agent",
}
selected = set(args.target or all_targets)
targets = {name: path for name, path in all_targets.items() if name in selected}
SPECIAL = {
    ("opencode", "opencode.json"),
    ("claude-code", "settings.overlay.json"),
    ("codex", "config.snippet.toml"),
}
STATE_DIR = home / ".local/state/set-agentes"
# Record of the per-file targets this installer wrote last run, so a later run can prune
# files it USED to manage but no longer produces (e.g. a renamed skill/agent). Only paths
# recorded here are ever deleted — user-created files are never touched.
MANIFEST = STATE_DIR / "managed-files.json"


def deep_merge(base, overlay):
    result = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


REPO_ROOT = Path(__file__).resolve().parents[2]
PLACEHOLDER = b"__SET_AGENTS_ROOT__"
_UNSAFE_ROOT = re.compile(r"[;|<>`&$\"'\\\\*?\[\]\r\n\x00-\x1f\x7f-\x9f]")


def validate_repo_root():
    """Reject paths which cannot be represented safely in installed policy files."""
    root = str(REPO_ROOT)
    match = _UNSAFE_ROOT.search(root)
    if match:
        char = match.group(0)
        print(
            f"INSTALL_ABORTED_UNSAFE_ROOT root={root} offending={char!r}@offset={match.start()}\n"
            "  The harness path must not contain shell, quoting, or glob metacharacters.\n"
            "  Move or rename the clone (a SPACE is fine) and re-run ./build.sh --install.",
            file=sys.stderr,
        )
        raise SystemExit(2)


def substitute_root(data: bytes, *, json_escaped: bool = False) -> bytes:
    """Bake HARNESS_HOME into an installed artifact without decoding its bytes."""
    replacement = json.dumps(str(REPO_ROOT))[1:].encode("utf-8") if json_escaped else str(REPO_ROOT).encode("utf-8")
    # json.dumps()[1:] is deliberately wrong for an ordinary string; retain only its
    # interior, matching the historical JSON merge replacement exactly.
    if json_escaped:
        replacement = json.dumps(str(REPO_ROOT))[1:-1].encode("utf-8")
    return data.replace(PLACEHOLDER, replacement)


def merged_json(current, overlay, union_lists=False):
    base = json.loads(current.read_text()) if current.exists() else {}
    update = json.loads(overlay.read_text())
    result = deep_merge(base, update)
    if union_lists:
        for key, value in update.items():
            if isinstance(value, list):
                result[key] = sorted(set(base.get(key, [])) | set(value))
    # Tracked templates stay machine-independent; the live config gets this repo's
    # root, JSON-escaped so a clone path with quotes/backslashes can't break the file.
    return substitute_root((json.dumps(result, indent=2) + "\n").encode(), json_escaped=True).decode()


def managed_files():
    result = []
    for harness, target in targets.items():
        for relative in (staging / harness / "managed-files.txt").read_text().splitlines():
            if not relative or (harness, relative) in SPECIAL or relative == "managed-files.txt":
                continue
            source = staging / harness / relative
            result.append((source, target / relative))
    return result


def effective_specials():
    result = []
    if "opencode" in targets:
        oc = targets["opencode"] / "opencode.json"
        result.append((merged_json(oc, staging / "opencode/opencode.json"), oc))
    if "claude-code" in targets:
        cc = targets["claude-code"] / "settings.json"
        result.append((merged_json(cc, staging / "claude-code/settings.overlay.json", union_lists=True), cc))
    if "codex" in targets:
        cx = targets["codex"] / "config.toml"
        result.append((merge_codex(cx), cx))
    return result


def legacy_prompt_bytes(relative):
    repo = Path(__file__).resolve().parents[2]

    def git_show(ref):
        result = subprocess.run(
            ["git", "show", f"{ref}:{relative.as_posix()}"],
            cwd=repo,
            text=False,
            capture_output=True,
            check=False,
        )
        return result.stdout if result.returncode == 0 else None

    # Prefer the version still shipped at HEAD. Once HEAD drops a legacy prompt, fall
    # back to the version just before its deletion, so the installer keeps recognizing
    # (and cleaning) stale copies left by an older install even after HEAD moves on.
    current = git_show("HEAD")
    if current is not None:
        return current
    deletion = subprocess.run(
        ["git", "rev-list", "-1", "HEAD", "--", relative.as_posix()],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    commit = deletion.stdout.strip()
    if deletion.returncode != 0 or not commit:
        return None
    return git_show(f"{commit}^")


def roster_codex_orchestrator():
    """Session-level model/effort for Codex come from the orchestrator area in models.toml."""
    import models_config

    return models_config.codex_orchestrator()


def merge_codex(current):
    text = current.read_text() if current.exists() else ""
    lines = text.splitlines()

    def set_top_key(key, value):
        end = next((i for i, line in enumerate(lines) if line.startswith("[")), len(lines))
        pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
        for index in range(end):
            if pattern.match(lines[index]):
                lines[index] = f"{key} = {value}"
                return
        lines.insert(0, f"{key} = {value}")

    def set_key(section, key, value):
        header = f"[{section}]"
        try:
            start = lines.index(header)
        except ValueError:
            if lines and lines[-1] != "":
                lines.append("")
            lines.extend([header, f"{key} = {value}"])
            return
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("[") and lines[i].endswith("]")), len(lines))
        pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
        for index in range(start + 1, end):
            if pattern.match(lines[index]):
                lines[index] = f"{key} = {value}"
                return
        lines.insert(start + 1, f"{key} = {value}")

    session_model, session_effort = roster_codex_orchestrator()
    set_top_key("model_reasoning_effort", f'"{session_effort}"')
    set_top_key("model", f'"{session_model}"')
    set_key("features", "multi_agent", "true")
    set_key("agents", "max_depth", "1")
    set_key("agents", "max_threads", "4")
    for server in ("engram", "context7", "playwright", "brave-cdp"):
        section = f"mcp_servers.{server}"
        if f"[{section}]" in lines:
            set_key(section, "enabled", "false")
    return "\n".join(lines).rstrip() + "\n"


def atomic_write(path, content, mode=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content if isinstance(content, bytes) else content.encode())
        if mode is not None:
            os.chmod(temp_name, mode)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def previous_targets():
    """Absolute paths this installer wrote on the last run — the only files eligible for pruning."""
    if not MANIFEST.exists():
        return []
    try:
        stored = json.loads(MANIFEST.read_text())
    except (OSError, json.JSONDecodeError):
        return []
    roots = set(all_targets.values())
    selected_roots = set(targets.values())
    result = []
    for relative in stored:
        candidate = home / relative
        # Hard safety fence: never prune anything outside a managed harness root.
        if any(root in candidate.parents for root in roots) and any(root in candidate.parents for root in selected_roots):
            result.append(candidate)
    return result


def prune_empty_dirs(directory):
    """Remove now-empty directories left by a pruned file, stopping at the harness roots."""
    roots = set(targets.values())
    current = directory
    while current not in roots and current != home and current.is_dir():
        try:
            next(current.iterdir())
            return  # not empty — stop
        except StopIteration:
            parent = current.parent
            try:
                current.rmdir()
            except OSError:
                return
            current = parent


validate_repo_root()
files = managed_files()
specials = effective_specials()
legacy = []
legacy_conflicts = []
if "codex" in targets:
    for prompt in (staging / "codex/agents").glob("*.toml"):
        target = targets["codex"] / "prompts" / f"{prompt.stem}.md"
        expected = legacy_prompt_bytes(Path("Global/codex/prompts") / f"{prompt.stem}.md")
        if expected is None:
            continue
        if target.exists() and target.read_bytes() == expected:
            legacy.append(target)
        elif target.exists():
            legacy_conflicts.append(str(target.relative_to(home)))

new_targets = {target for _, target in files}
special_targets = {target for _, target in specials}
orphans = [
    path for path in previous_targets()
    if path not in new_targets and path not in special_targets and path.exists()
]

# AC-09 (013-pi-interactive-target): fail-closed collision guard, scoped to
# ~/.pi/agent/agents/ — the one write target among the four generated harness trees
# where real, pre-existing third-party content is a standing risk (the gentle-ai
# leftovers, or any future pi-subagents override file a human drops there). A
# pre-existing file this installer would write to but did NOT itself record writing
# last run (per MANIFEST/previous_targets()) means this run is about to clobber
# content it never owned — ADR-0008 D2's "never touch third-party content" doctrine.
# Fires identically in --preview and write mode (round 2, N-01): a dry run must not
# hide a collision a real run would fail on. Exit code 2, matching install.py's own
# INSTALL_ABORTED_UNSAFE_ROOT precedent and check-drift.sh's internal-error
# convention — deliberately NOT 1, which would be indistinguishable from ordinary
# DRIFT_DETECTED (round 3, R3-03).
if "pi" in targets:
    pi_agents_root = all_targets["pi"] / "agents"
    previously_managed = set(previous_targets())
    collisions = sorted(
        str(target.relative_to(home))
        for target in new_targets
        if pi_agents_root in target.parents
        and (target.is_symlink() or target.exists())
        and target not in previously_managed
    )
    if collisions:
        print(
            "INSTALL_ABORTED_UNSAFE_COLLISION targets=" + ",".join(collisions) + "\n"
            "  ~/.pi/agent/agents/ already has file(s) this installer never recorded writing.\n"
            "  Resolve BY HAND, outside the installer (move/rename/delete the file yourself),\n"
            "  then re-run install.py --target pi. No override flag exists — this guard never\n"
            "  silently overwrites third-party content.",
            file=sys.stderr,
        )
        raise SystemExit(2)

if args.preview:
    changes = 0
    for source, target in files:
        before = target.read_text(errors="replace").splitlines(True) if target.exists() else []
        after = substitute_root(source.read_bytes()).decode(errors="replace").splitlines(True)
        if before != after:
            changes += 1
            print("".join(difflib.unified_diff(before, after, fromfile=str(target), tofile=str(target) + " (managed)")), end="")
    for content, target in specials:
        before = target.read_text(errors="replace").splitlines(True) if target.exists() else []
        after = content.splitlines(True)
        if before != after:
            changes += 1
            print("".join(difflib.unified_diff(before, after, fromfile=str(target), tofile=str(target) + " (managed merge)")), end="")
    for target in legacy:
        before = target.read_text(errors="replace").splitlines(True) if target.exists() else []
        after = []
        if before != after:
            changes += 1
            print("".join(difflib.unified_diff(before, after, fromfile=str(target), tofile=str(target) + " (legacy delete)")), end="")
    for target in orphans:
        before = target.read_text(errors="replace").splitlines(True) if target.exists() else []
        if before:
            changes += 1
            print("".join(difflib.unified_diff(before, [], fromfile=str(target), tofile=str(target) + " (prune orphan)")), end="")
    if legacy_conflicts:
        print("LEGACY_CONFLICTS=" + ",".join(sorted(legacy_conflicts)))
    print(f"MANAGED_DIFF_FILES={changes}")
    raise SystemExit(0)

stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S_%f")
backups_root = home / ".local/state/set-agentes/backups"
backup = backups_root / stamp
backup.mkdir(parents=True, exist_ok=False)
# Backups can hold user configs (possibly with keys): keep them private and bounded.
os.chmod(backups_root, 0o700)
os.chmod(backups_root.parent, 0o700)
for old in sorted(backups_root.iterdir())[:-20]:
    shutil.rmtree(old, ignore_errors=True)
affected = [target for _, target in files] + [target for _, target in specials] + legacy + orphans
missing = []
for target in affected:
    relative = target.relative_to(home)
    if target.exists():
        destination = backup / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, destination)
    else:
        missing.append(str(relative))
(backup / "missing.json").write_text(json.dumps(missing, indent=2))


def rollback():
    for target in affected:
        relative = target.relative_to(home)
        saved = backup / relative
        if saved.exists():
            atomic_write(target, saved.read_bytes(), saved.stat().st_mode & 0o777)
        elif target.exists():
            target.unlink()


try:
    for source, target in files:
        atomic_write(target, substitute_root(source.read_bytes()), source.stat().st_mode & 0o777)
    for content, target in specials:
        atomic_write(target, content)
    for path in legacy:
        if path.exists():
            path.unlink()
    for path in orphans:
        if path.exists():
            path.unlink()
        prune_empty_dirs(path.parent)
    if orphans:
        print("PRUNED_ORPHANS=" + ",".join(sorted(str(p.relative_to(home)) for p in orphans)))
    if legacy_conflicts:
        print("LEGACY_CONFLICTS=" + ",".join(sorted(legacy_conflicts)))

    if "opencode" in targets:
        oc = json.loads((targets["opencode"] / "opencode.json").read_text())
        # Only the managed servers must land disabled; user-added MCPs are theirs to run.
        if any(item.get("enabled") for name, item in oc.get("mcp", {}).items() if name in MANAGED_MCP):
            raise RuntimeError("OpenCode MCP smoke check failed")
    if "claude-code" in targets:
        cc = json.loads((targets["claude-code"] / "settings.json").read_text())
        if cc.get("enabledPlugins", {}).get("engram@engram") is not False:
            raise RuntimeError("Claude Engram smoke check failed")
    if "codex" in targets:
        for path in (targets["codex"] / "agents").glob("*.toml"):
            tomllib.loads(path.read_text())
        codex_config = tomllib.loads((targets["codex"] / "config.toml").read_text())
        if codex_config.get("features", {}).get("multi_agent") is not True or codex_config.get("agents", {}).get("max_depth") != 1:
            raise RuntimeError("Codex multi-agent smoke check failed")
        session_model, session_effort = roster_codex_orchestrator()
        if codex_config.get("model") != session_model or codex_config.get("model_reasoning_effort") != session_effort:
            raise RuntimeError("Codex session model smoke check failed")
        for name in ("engram", "context7", "playwright", "brave-cdp"):
            if codex_config.get("mcp_servers", {}).get(name, {}).get("enabled", False) is not False:
                raise RuntimeError(f"Codex {name} MCP smoke check failed")
    if any(PLACEHOLDER in path.read_bytes() for _, path in files if path.exists()):
        raise RuntimeError("Installed managed file retains SET_AGENTS_ROOT placeholder")
    if os.environ.get("SET_AGENTS_FORCE_SMOKE_FAIL") == "1":
        raise RuntimeError("forced smoke failure")
    # Only after every smoke check passes: record what we manage now, so the next run can
    # prune whatever we stop producing. A rolled-back install never reaches here.
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    preserved = []
    selected_roots = set(targets.values())
    if MANIFEST.exists():
        try:
            for relative in json.loads(MANIFEST.read_text()):
                candidate = home / relative
                if not any(root in candidate.parents for root in selected_roots):
                    preserved.append(relative)
        except (OSError, json.JSONDecodeError):
            preserved = []
    managed = set(preserved) | {str(t.relative_to(home)) for t in new_targets}
    atomic_write(MANIFEST, json.dumps(sorted(managed), indent=2) + "\n")
    # Scope record: which harness trees THIS machine manages, so check-drift.sh can
    # compare only what was actually installed (a claude-only machine must not read
    # the never-installed opencode/codex trees as drift). Merged, not replaced: a
    # later `--target` run extends the scope, it never silently narrows it.
    scope_path = STATE_DIR / "install-targets.json"
    scope = set(targets)
    if scope_path.exists():
        try:
            scope |= set(json.loads(scope_path.read_text()))
        except (OSError, json.JSONDecodeError):
            pass
    if not args.target:
        scope = set(all_targets)
    atomic_write(scope_path, json.dumps(sorted(scope)) + "\n")
except Exception:
    rollback()
    print(f"INSTALL_ROLLED_BACK backup={backup}")
    raise

print(f"INSTALL_PASS backup={backup}")
