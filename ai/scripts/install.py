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
import tempfile
import tomllib
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--staging", required=True)
parser.add_argument("--home", required=True)
parser.add_argument("--preview", action="store_true")
args = parser.parse_args()

staging = Path(args.staging)
home = Path(args.home)
targets = {
    "opencode": home / ".config/opencode",
    "claude-code": home / ".claude",
    "codex": home / ".codex",
}
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


def merged_json(current, overlay, union_lists=False):
    base = json.loads(current.read_text()) if current.exists() else {}
    update = json.loads(overlay.read_text())
    result = deep_merge(base, update)
    if union_lists:
        for key, value in update.items():
            if isinstance(value, list):
                result[key] = sorted(set(base.get(key, [])) | set(value))
    return json.dumps(result, indent=2) + "\n"


def managed_files():
    result = []
    for harness, target in targets.items():
        for relative in (staging / harness / "managed-files.txt").read_text().splitlines():
            if not relative or (harness, relative) in SPECIAL or relative == "managed-files.txt":
                continue
            result.append((staging / harness / relative, target / relative))
    return result


def effective_specials():
    oc = targets["opencode"] / "opencode.json"
    cc = targets["claude-code"] / "settings.json"
    cx = targets["codex"] / "config.toml"
    return [
        (merged_json(oc, staging / "opencode/opencode.json"), oc),
        (merged_json(cc, staging / "claude-code/settings.overlay.json", union_lists=True), cc),
        (merge_codex(cx), cx),
    ]


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


def merge_codex(current):
    text = current.read_text() if current.exists() else ""
    lines = text.splitlines()

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
    roots = set(targets.values())
    result = []
    for relative in stored:
        candidate = home / relative
        # Hard safety fence: never prune anything outside a managed harness root.
        if any(root in candidate.parents for root in roots):
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


files = managed_files()
specials = effective_specials()
legacy = []
legacy_conflicts = []
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

if args.preview:
    changes = 0
    for source, target in files:
        before = target.read_text(errors="replace").splitlines(True) if target.exists() else []
        after = source.read_text(errors="replace").splitlines(True)
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
backup = home / ".local/state/set-agentes/backups" / stamp
backup.mkdir(parents=True, exist_ok=False)
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
        atomic_write(target, source.read_bytes(), source.stat().st_mode & 0o777)
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

    oc = json.loads((targets["opencode"] / "opencode.json").read_text())
    if any(item.get("enabled") for item in oc.get("mcp", {}).values()):
        raise RuntimeError("OpenCode MCP smoke check failed")
    cc = json.loads((targets["claude-code"] / "settings.json").read_text())
    if cc.get("enabledPlugins", {}).get("engram@engram") is not False:
        raise RuntimeError("Claude Engram smoke check failed")
    for path in (targets["codex"] / "agents").glob("*.toml"):
        tomllib.loads(path.read_text())
    codex_config = tomllib.loads((targets["codex"] / "config.toml").read_text())
    if codex_config.get("features", {}).get("multi_agent") is not True or codex_config.get("agents", {}).get("max_depth") != 1:
        raise RuntimeError("Codex multi-agent smoke check failed")
    for name in ("engram", "context7", "playwright", "brave-cdp"):
        if codex_config.get("mcp_servers", {}).get(name, {}).get("enabled", False) is not False:
            raise RuntimeError(f"Codex {name} MCP smoke check failed")
    if os.environ.get("SET_AGENTS_FORCE_SMOKE_FAIL") == "1":
        raise RuntimeError("forced smoke failure")
    # Only after every smoke check passes: record what we manage now, so the next run can
    # prune whatever we stop producing. A rolled-back install never reaches here.
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    atomic_write(MANIFEST, json.dumps(sorted(str(t.relative_to(home)) for t in new_targets), indent=2) + "\n")
except Exception:
    rollback()
    print(f"INSTALL_ROLLED_BACK backup={backup}")
    raise

print(f"INSTALL_PASS backup={backup}")
