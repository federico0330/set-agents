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
import provider_registry

parser = argparse.ArgumentParser()
# --staging is required for an install (the source tree to copy/merge FROM) but
# --uninstall never reads staging at all -- it only ever consults what this
# installer already recorded writing (MANIFEST / SPECIAL_KEYS_MANIFEST), so
# forcing a caller to fabricate a staging dir just to uninstall would be a
# needless (and confusing) precondition. Validated by hand below instead of
# argparse's required=True.
parser.add_argument("--staging")
parser.add_argument("--home", required=True)
parser.add_argument("--target", action="append", choices=("opencode", "claude-code", "codex", "pi", "cursor"))
parser.add_argument("--preview", action="store_true")
# D4/AC-10: uninstall from exactly the target(s) named by --target, and ONLY
# those -- there is deliberately no "uninstall everything" default the way
# install's bare (no --target) call means "all four" (install.py:36). An
# uninstall is destructive; a missing --target is a usage error, never a guess
# (F07/F08 -- inventing a scope here is the exact bug this package exists to
# close, not one to reopen from the other direction).
parser.add_argument("--uninstall", action="store_true")
args = parser.parse_args()

if args.uninstall:
    if not args.target:
        print(
            "UNINSTALL_ABORTED_NO_TARGET\n"
            "  --uninstall requires at least one explicit --target -- there is no\n"
            "  'uninstall everything' default. Pass --target claude-code/opencode/codex/pi/cursor.",
            file=sys.stderr,
        )
        raise SystemExit(2)
elif not args.staging:
    parser.error("--staging is required (unless --uninstall)")

staging = Path(args.staging) if args.staging else None
home = Path(args.home)
all_targets = {
    "opencode": home / ".config/opencode",
    "claude-code": home / ".claude",
    "codex": home / ".codex",
    "pi": home / ".pi/agent",
    # 032/C1 (AC-03): global Cursor config root. `agents/` and `skills/` are read from
    # here by Cursor itself; `commands/` and `rules/` ride along as the source
    # bootstrap_project.py projects into a project, because Cursor reads those two
    # ONLY from the project tree (verified 2026-08-18).
    "cursor": home / ".cursor",
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
# 022 PKG-4 (AC-11/AC-13/AC-15): the single source `opencode.json`'s `provider` object
# renders FROM, same private STATE_DIR as MANIFEST above.
PROVIDERS_TOML = STATE_DIR / provider_registry.PROVIDERS_TOML_NAME
# AC-14: MANIFEST's own file-level orphan-pruning discipline, extended to JSON
# SUBTREES -- `{"opencode.json": ["<provider id>", ...]}`, the provider ids THIS
# installer wrote under `provider.*` last run. Deliberately a SEPARATE file from
# MANIFEST (never a mixed-shape entry in that flat file-path list): `previous_targets()`
# below builds real filesystem `Path`s straight out of MANIFEST's entries, and a
# subtree pointer is not a path -- keeping the two apart means a JSON-subtree id can
# never be misread as a file to unlink.
JSON_MANIFEST = STATE_DIR / "managed-json-paths.json"
# D4/AC-10, F03/F04: the file-level MANIFEST above only ever knows about files
# THIS installer writes whole -- the three SPECIAL files (settings.json,
# config.toml, opencode.json) are merges into a file the USER owns, and until
# now nothing recorded which KEYS inside them the merge actually added or
# overwrote. Keyed by the target's path relative to --home (e.g.
# ".claude/settings.json"); each value is a list of entries
# {"path": [...], "value": <written>, "previous": <before-or-null>,
# "existed": bool, "union_list": bool} -- the DELTA the merge contributed,
# never the file's full content (F03: "el registro graba lo que el overlay
# contiene, no lo que el instalador agregó" was the defect; this is the fix).
# "existed"=False means the key did not exist before this run wrote it, so an
# uninstall that finds the live value still equal to what we wrote removes the
# key outright; "existed"=True means uninstall restores "previous" instead of
# deleting, an actual de-merge rather than a blind delete of user config.
SPECIAL_KEYS_MANIFEST = STATE_DIR / "managed-special-keys.json"
# Which harness trees THIS machine manages -- read by check-drift.sh and by
# cmd_update (set_agents_app.py) so re-installs/updates only ever touch what
# was actually installed here.
SCOPE_PATH = STATE_DIR / "install-targets.json"
# Populated by `apply_provider_registry` (called from `effective_specials()`, which runs
# unconditionally, including under --preview) when `providers.toml` doesn't exist yet --
# the freshly bootstrapped (AC-15 migration-or-seed) content to persist for real, but
# ONLY from the commit section below, after every smoke check passes (same "compute
# early, write only on the success path" discipline MANIFEST's own write already uses).
# A --preview run computes this list too (harmless: it's simply never consulted, since
# --preview exits before the commit section is reached).
_PENDING_PROVIDERS_BOOTSTRAP = []


def deep_merge(base, overlay):
    result = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


_MISSING = object()


def _json_get(obj, path):
    """Walk `obj` along `path` (a sequence of keys); `_MISSING` if any hop misses."""
    current = obj
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return _MISSING
        current = current[key]
    return current


def _leaf_paths(obj, prefix=()):
    """Yield (path tuple, value) for every leaf of a nested dict. A list or
    scalar value is a leaf in its own right (never recursed into) -- a list is
    owned as a whole unit (see `union_list` handling in `_special_delta`)."""
    for key, value in obj.items():
        path = prefix + (key,)
        if isinstance(value, dict):
            yield from _leaf_paths(value, path)
        else:
            yield path, value


def _special_delta(base, overlay, final, union_list_keys=()):
    """F03/F04: the exact keys/values a merge into a SPECIAL (user-owned) file
    contributed this run -- never the file's full content. `base` is the live
    file's content BEFORE this run's merge (already in hand at every call
    site: `merged_json` reads it, `merge_codex` parses the pre-merge text);
    `overlay` is the shape of what we merge in (which keys we ever touch);
    `final` is what actually landed on disk (post-merge, post-substitution),
    so a recorded `value` always matches what a later run will really find
    live -- ownership is verified by comparing AT UNINSTALL TIME, never
    assumed to last forever (F04: "saber qué valor escribimos" is not "ser
    dueños de la clave" -- a user who changes the value by hand after install
    reclaims it; the comparison against `final`/live is what tells the two
    cases apart)."""
    entries = []
    for path, _ in _leaf_paths(overlay):
        is_union = len(path) == 1 and path[0] in union_list_keys
        value = _json_get(final, path)
        if value is _MISSING:
            continue
        previous = _json_get(base, path)
        entries.append({
            "path": list(path),
            "value": value,
            "previous": None if previous is _MISSING else previous,
            "existed": previous is not _MISSING,
            "union_list": bool(is_union and isinstance(value, list)),
        })
    return entries


def _revert_json_special(live, entries):
    """The inverse of `_special_delta`: mutate `live` (a parsed JSON dict) in
    place, removing/restoring only entries whose CURRENT value still matches
    what we recorded writing. Returns (changed: bool, skipped: list[str]) --
    skipped entries are ones the user visibly changed since install, which are
    never touched (F04's non-destructive de-merge). Empty parent dicts left
    behind by a removed leaf are pruned too, so a fully-owned subtree (e.g. an
    mcp server block we created whole) disappears cleanly."""
    changed = False
    skipped = []

    def parent_of(path):
        node = live
        for key in path[:-1]:
            if not isinstance(node, dict) or key not in node:
                return None
            node = node[key]
        return node if isinstance(node, dict) else None

    for entry in entries:
        path = entry["path"]
        if entry["union_list"]:
            parent = parent_of(path)
            key = path[-1]
            if not parent or not isinstance(parent.get(key), list):
                continue
            owned = entry["value"] if isinstance(entry["value"], list) else []
            remaining = [item for item in parent[key] if item not in owned]
            if remaining != parent[key]:
                parent[key] = remaining
                changed = True
            continue
        node = parent_of(path)
        key = path[-1]
        if node is None or key not in node:
            continue
        if node[key] != entry["value"]:
            skipped.append(".".join(str(p) for p in path))
            continue
        if entry["existed"]:
            node[key] = entry["previous"]
        else:
            del node[key]
            changed = True
            continue
        changed = True
    _prune_empty_json_dicts(live, [e["path"] for e in entries if not e["union_list"]])
    return changed, skipped


def _prune_empty_json_dicts(live, paths):
    """After deleting leaves, drop now-empty dicts along their parent chain
    (never the document root itself)."""
    for path in paths:
        for depth in range(len(path) - 1, 0, -1):
            node = live
            ok = True
            for key in path[:depth]:
                if not isinstance(node, dict) or key not in node:
                    ok = False
                    break
                node = node[key]
            if not ok or not isinstance(node, dict) or node:
                continue
            parent = live
            for key in path[: depth - 1]:
                parent = parent[key]
            parent.pop(path[depth - 1], None)


def revert_json_special(target, entries):
    """The inverse of a JSON special merge (settings.json/opencode.json),
    driven by `_special_delta`'s recorded entries. Reads the LIVE file fresh
    (never trusts a stale in-memory copy) and computes the reverted content --
    NEVER writes it (F01/F02: the same computation backs both --preview and
    the real run; only the caller decides whether to persist it, so the two
    modes can never diverge in what they report vs what they do)."""
    if not target.exists():
        return False, [], None
    live = json.loads(target.read_text(encoding="utf-8"))
    changed, skipped = _revert_json_special(live, entries)
    return changed, skipped, (json.dumps(live, indent=2) + "\n") if changed else None


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
    base = json.loads(current.read_text(encoding="utf-8")) if current.exists() else {}
    update = json.loads(overlay.read_text(encoding="utf-8"))
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
        for relative in (staging / harness / "managed-files.txt").read_text(encoding="utf-8").splitlines():
            if not relative or (harness, relative) in SPECIAL or relative == "managed-files.txt":
                continue
            source = staging / harness / relative
            result.append((source, target / relative))
    return result


def _previous_provider_ids():
    """The provider ids `JSON_MANIFEST` says THIS installer wrote under `provider.*`
    last run — the only ids AC-14's prune step is ever allowed to delete."""
    if not JSON_MANIFEST.exists():
        return set()
    try:
        stored = json.loads(JSON_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    return set(stored.get("opencode.json", []))


def apply_provider_registry(content, target):
    """AC-13/AC-14: `opencode.json`'s `provider` object, rendered FROM `providers.toml`
    instead of the merge's passive pass-through (the overlay no longer carries a
    `provider` key at all since `Global/_shared/opencode.json` stopped hardcoding one —
    `deep_merge` alone would just leave whatever the live file already has completely
    untouched, which is correct for ids nobody manages but wrong for the ones the
    registry says should now exist, be updated, or be gone).

    id-by-id, using the SAME manifest-diff discipline `previous_targets()`/`orphans`
    already use for whole files, extended to a JSON subtree (AC-14): an id THIS
    installer wrote last run (`JSON_MANIFEST`) that the registry no longer has is safe
    to delete — we know we own it. Every id currently in the registry is written
    (added or overwritten; the registry is the single source of truth for the ids it
    tracks). Any OTHER live key — one this installer never recorded writing, e.g. a
    block the user hand-added straight into `opencode.json` outside `set-agents`
    entirely — is never touched, added, or removed; it is not even read for comparison,
    only left exactly as `deep_merge` already found it.
    """
    doc = json.loads(content)
    live_block = doc.get("provider")
    if not isinstance(live_block, dict):
        live_block = {}
    entries, bootstrap_text = provider_registry.load_or_bootstrap(PROVIDERS_TOML, live_block)
    if bootstrap_text is not None:
        _PENDING_PROVIDERS_BOOTSTRAP.append((PROVIDERS_TOML, bootstrap_text))
    orphan_ids = _previous_provider_ids() - set(entries)
    block = dict(live_block)
    for provider_id in orphan_ids:
        block.pop(provider_id, None)
    for provider_id, entry in entries.items():
        block[provider_id] = entry.spec
    doc["provider"] = block
    rendered = (json.dumps(doc, indent=2) + "\n").encode()
    # Idempotent re-substitution: `content` already had the placeholder resolved by
    # `merged_json`'s own call below; a provider spec is never expected to carry it, but
    # this costs nothing and stays correct if one someday does.
    return substitute_root(rendered, json_escaped=True).decode()



# D4/AC-10 (F03): populated below as `effective_specials()` computes each merge --
# {relative-path-str: [delta entry, ...]}, persisted to SPECIAL_KEYS_MANIFEST only
# after every smoke check passes (same "compute early, write on the success path
# only" discipline as `_PENDING_PROVIDERS_BOOTSTRAP`/MANIFEST itself).
_PENDING_SPECIAL_KEYS = {}


def _read_json_or_empty(path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def effective_specials():
    result = []
    if "opencode" in targets:
        oc = targets["opencode"] / "opencode.json"
        base = _read_json_or_empty(oc)
        overlay = _read_json_or_empty(staging / "opencode/opencode.json")
        content = apply_provider_registry(merged_json(oc, staging / "opencode/opencode.json"), oc)
        _PENDING_SPECIAL_KEYS[str(oc.relative_to(home))] = _special_delta(base, overlay, json.loads(content))
        result.append((content, oc))
    if "claude-code" in targets:
        cc = targets["claude-code"] / "settings.json"
        base = _read_json_or_empty(cc)
        overlay = _read_json_or_empty(staging / "claude-code/settings.overlay.json")
        content = merged_json(cc, staging / "claude-code/settings.overlay.json", union_lists=True)
        _PENDING_SPECIAL_KEYS[str(cc.relative_to(home))] = _special_delta(
            base, overlay, json.loads(content), union_list_keys={"disabledMcpjsonServers"},
        )
        result.append((content, cc))
    if "codex" in targets:
        cx = targets["codex"] / "config.toml"
        flag_codex_model_change(cx)
        before_text = cx.read_text(encoding="utf-8") if cx.exists() else ""
        content = merge_codex(cx)
        _PENDING_SPECIAL_KEYS[str(cx.relative_to(home))] = _codex_written_keys(before_text, content)
        result.append((content, cx))
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


_CODEX_TOP_KEY = {
    "model": re.compile(r'(?m)^\s*model\s*=\s*"([^"]*)"'),
    "model_reasoning_effort": re.compile(r'(?m)^\s*model_reasoning_effort\s*=\s*"([^"]*)"'),
}


def flag_codex_model_change(current):
    """AC-08 (024/C3): `merge_codex` below silently overwrites the session `model`/
    `model_reasoning_effort` of the user's live `~/.codex/config.toml` -- measured live:
    on a from-scratch install this line is one unified-diff hunk buried inside a
    ~565KB/96-file `--preview` dump, effectively invisible. `model`/`model_reasoning_effort`
    are the only two keys in this managed MERGE (unlike the rest of `config.toml`, which is
    pure harness-owned scaffolding) a user could plausibly have set by hand -- so an actual
    VALUE CHANGE against a pre-existing key gets its own greppable, un-buried line, printed
    unconditionally (both --preview and the real write, and regardless of --yes: --yes is
    consent to proceed, never consent to silence). A file that doesn't exist yet, or a key
    that was never set, is ordinary bootstrap -- nothing of the user's to lose, no line.
    """
    if not current.exists():
        return
    text = current.read_text(encoding="utf-8")
    new_model, new_effort = roster_codex_orchestrator()
    changes = []
    for key, new_value in (("model", new_model), ("model_reasoning_effort", new_effort)):
        match = _CODEX_TOP_KEY[key].search(text)
        if match and match.group(1) != new_value:
            changes.append(f"{key}: {match.group(1)} -> {new_value}")
    if changes:
        print(f"CODEX_GLOBAL_MODEL_CHANGE {'; '.join(changes)} file={current}")


def merge_codex(current):
    text = current.read_text(encoding="utf-8") if current.exists() else ""
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


_CODEX_MANAGED_PATHS = [
    ("model",), ("model_reasoning_effort",),
    ("features", "multi_agent"), ("agents", "max_depth"), ("agents", "max_threads"),
] + [("mcp_servers", server, "enabled") for server in ("engram", "context7", "playwright", "brave-cdp")]


def _codex_written_keys(text_before, text_after):
    """F04: every key `merge_codex` is capable of writing, resolved from the two
    TOML snapshots (before/after this run's text surgery) via `tomllib` -- the
    SAME parser the smoke check already trusts, never a second hand-rolled
    reading of `merge_codex`'s own regex output. A key `merge_codex` did not
    touch this run (e.g. an mcp_servers section that doesn't exist) is simply
    absent from `text_after` at that path and is skipped -- uninstall must
    never claim ownership of a key this run never wrote."""
    def loads(text):
        try:
            return tomllib.loads(text) if text.strip() else {}
        except tomllib.TOMLDecodeError:
            return {}

    before = loads(text_before)
    after = loads(text_after)
    entries = []
    for path in _CODEX_MANAGED_PATHS:
        value = _json_get(after, path)
        if value is _MISSING:
            continue
        previous = _json_get(before, path)
        entries.append({
            "path": list(path),
            "value": value,
            "previous": None if previous is _MISSING else previous,
            "existed": previous is not _MISSING,
            "union_list": False,
        })
    return entries


def _toml_repr(value):
    """Best-effort re-serialization of a PREVIOUS scalar value for restore.
    Only the scalar shapes `merge_codex` itself ever writes (bool/int/str) are
    supported -- an exotic previous value (array, inline table, date) is never
    guessed at; the caller falls back to deleting the line instead (see
    `_codex_restore_key`'s `None`-means-"can't restore" contract)."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value)
    return None


def _codex_restore_top_key(lines, key, previous, existed):
    end = next((i for i, line in enumerate(lines) if line.startswith("[")), len(lines))
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    for index in range(end):
        if pattern.match(lines[index]):
            _codex_apply_restore(lines, index, key, previous, existed)
            return True
    return False


def _codex_restore_key(lines, section, key, previous, existed):
    header = f"[{section}]"
    try:
        start = lines.index(header)
    except ValueError:
        return False
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("[") and lines[i].endswith("]")), len(lines))
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    for index in range(start + 1, end):
        if pattern.match(lines[index]):
            _codex_apply_restore(lines, index, key, previous, existed)
            return True
    return False


def _codex_apply_restore(lines, index, key, previous, existed):
    repr_value = _toml_repr(previous) if existed else None
    if existed and repr_value is not None:
        lines[index] = f"{key} = {repr_value}"
    else:
        del lines[index]


def revert_codex(current, entries):
    """The inverse of `merge_codex`, driven by `_codex_written_keys`' delta:
    for every recorded key whose LIVE value (parsed fresh via tomllib, never
    trusted stale) still equals what this installer last wrote, delete the
    line (key didn't exist before) or restore it to `previous` (key existed
    with a different value) -- section headers are never removed, only the
    single key line this installer owns, so a `[mcp_servers.engram]` block the
    USER created is never deleted out from under them. NEVER writes (F01/F02:
    same computation backs --preview and the real run; the caller decides
    whether to persist)."""
    if not current.exists():
        return False, [], None
    live = tomllib.loads(current.read_text(encoding="utf-8"))
    lines = current.read_text(encoding="utf-8").splitlines()
    changed = False
    skipped = []
    for entry in entries:
        path = entry["path"]
        live_value = _json_get(live, path)
        if live_value != entry["value"]:
            skipped.append(".".join(str(p) for p in path))
            continue
        if len(path) == 1:
            found = _codex_restore_top_key(lines, path[0], entry["previous"], entry["existed"])
        else:
            found = _codex_restore_key(lines, ".".join(path[:-1]), path[-1], entry["previous"], entry["existed"])
        changed = changed or found
    if not changed:
        return False, skipped, None
    new_text = "\n".join(lines).rstrip() + "\n" if lines else ""
    tomllib.loads(new_text)  # never report/write back something that fails to parse
    return True, skipped, new_text


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


def _read_manifest_raw():
    """(exists, entries): entries is None only when MANIFEST exists but failed to
    parse -- callers decide fail-open (install's orphan pruning, unchanged
    long-standing behavior) vs fail-closed (uninstall, F05)."""
    if not MANIFEST.exists():
        return False, []
    try:
        return True, json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return True, None


def _resolved_roots(mapping):
    return [root.resolve() for root in mapping.values()]


def _within_any_root(candidate, roots):
    # F11: resolve() BEFORE the containment check -- Path.parents is purely
    # lexical (never collapses "..").  A MANIFEST entry like
    # ".claude/../../victim.txt" textually has home/.claude as one of its
    # *unresolved* parents, so a lexical check would wrongly call it "inside
    # the claude-code root" even though the real filesystem location it
    # resolves to sits two levels above `home`. Only the resolved path decides.
    resolved = candidate.resolve()
    return any(resolved == root or resolved.is_relative_to(root) for root in roots)


def previous_targets():
    """Absolute paths this installer wrote on the last run — the only files eligible for pruning."""
    exists, stored = _read_manifest_raw()
    if not exists or stored is None:
        return []
    roots = _resolved_roots(all_targets)
    selected_roots = _resolved_roots(targets)
    result = []
    for relative in stored:
        if not isinstance(relative, str):
            continue
        candidate = home / relative
        # Hard safety fence: never prune anything outside a managed harness root.
        if _within_any_root(candidate, roots) and _within_any_root(candidate, selected_roots):
            result.append(candidate)
    return result


def manifest_entries_for_uninstall():
    """F05: a MANIFEST that exists but fails to parse aborts uninstall outright
    (exit 2) instead of silently acting as if nothing were ever installed --
    the previous fail-open behavior printed UNINSTALL_PASS while deleting
    nothing AND (were it not for this same fix) went on to overwrite MANIFEST
    with `[]`, destroying the records of every harness NOT being uninstalled
    this run. Returns (stored, keep, remove): `stored` is the untouched raw
    list (for entries that fail the safety fence, e.g. malformed non-string
    values, which are neither removed nor lost), `keep` is what MANIFEST
    should contain afterward, `remove` is the absolute paths to delete."""
    exists, stored = _read_manifest_raw()
    if exists and stored is None:
        print(
            f"UNINSTALL_ABORTED_UNREADABLE_MANIFEST manifest={MANIFEST}\n"
            "  The file exists but is not valid JSON -- refusing to guess what this\n"
            "  installer owns (that could delete the wrong files, or none at all\n"
            "  while claiming success). Fix or remove the file by hand, then retry.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    stored = stored or []
    roots = _resolved_roots(all_targets)
    selected_roots = _resolved_roots(targets)
    keep, remove = [], []
    for relative in stored:
        if not isinstance(relative, str):
            keep.append(relative)
            continue
        candidate = home / relative
        if _within_any_root(candidate, roots) and _within_any_root(candidate, selected_roots):
            remove.append(candidate)
        else:
            keep.append(relative)
    return stored, keep, remove


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


def new_backup_dir():
    """A fresh, private, rotation-bounded backup directory under STATE_DIR --
    shared by install and uninstall (F15: this was two near-identical, already
    diverging copies; F06 needed uninstall's copy to ALSO cover the registry
    files, which is much safer to guarantee once, here, than twice)."""
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S_%f")
    backups_root = home / ".local/state/set-agentes/backups"
    backup = backups_root / stamp
    backup.mkdir(parents=True, exist_ok=False)
    # Backups can hold user configs (possibly with keys): keep them private and bounded.
    os.chmod(backups_root, 0o700)
    os.chmod(backups_root.parent, 0o700)
    for old in sorted(backups_root.iterdir())[:-20]:
        shutil.rmtree(old, ignore_errors=True)
    return backup


def take_backup(backup, paths):
    missing = []
    for target in paths:
        relative = target.relative_to(home)
        if target.exists():
            destination = backup / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, destination)
        else:
            missing.append(str(relative))
    (backup / "missing.json").write_text(json.dumps(missing, indent=2), encoding="utf-8")


def restore_backup(backup, paths):
    for target in paths:
        relative = target.relative_to(home)
        saved = backup / relative
        if saved.exists():
            atomic_write(target, saved.read_bytes(), saved.stat().st_mode & 0o777)
        elif target.exists():
            target.unlink()


def run_install():
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
            before = target.read_text(errors="replace", encoding="utf-8").splitlines(True) if target.exists() else []
            after = substitute_root(source.read_bytes()).decode(errors="replace").splitlines(True)
            if before != after:
                changes += 1
                print("".join(difflib.unified_diff(before, after, fromfile=str(target), tofile=str(target) + " (managed)")), end="")
        for content, target in specials:
            before = target.read_text(errors="replace", encoding="utf-8").splitlines(True) if target.exists() else []
            after = content.splitlines(True)
            if before != after:
                changes += 1
                print("".join(difflib.unified_diff(before, after, fromfile=str(target), tofile=str(target) + " (managed merge)")), end="")
        for target in legacy:
            before = target.read_text(errors="replace", encoding="utf-8").splitlines(True) if target.exists() else []
            after = []
            if before != after:
                changes += 1
                print("".join(difflib.unified_diff(before, after, fromfile=str(target), tofile=str(target) + " (legacy delete)")), end="")
        for target in orphans:
            before = target.read_text(errors="replace", encoding="utf-8").splitlines(True) if target.exists() else []
            if before:
                changes += 1
                print("".join(difflib.unified_diff(before, [], fromfile=str(target), tofile=str(target) + " (prune orphan)")), end="")
        if legacy_conflicts:
            print("LEGACY_CONFLICTS=" + ",".join(sorted(legacy_conflicts)))
        print(f"MANAGED_DIFF_FILES={changes}")
        raise SystemExit(0)

    backup = new_backup_dir()
    affected = [target for _, target in files] + [target for _, target in specials] + legacy + orphans
    take_backup(backup, affected)

    def rollback():
        restore_backup(backup, affected)

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
            oc = json.loads((targets["opencode"] / "opencode.json").read_text(encoding="utf-8"))
            # Only the managed servers must land disabled; user-added MCPs are theirs to run.
            if any(item.get("enabled") for name, item in oc.get("mcp", {}).items() if name in MANAGED_MCP):
                raise RuntimeError("OpenCode MCP smoke check failed")
        if "claude-code" in targets:
            cc = json.loads((targets["claude-code"] / "settings.json").read_text(encoding="utf-8"))
            if cc.get("enabledPlugins", {}).get("engram@engram") is not False:
                raise RuntimeError("Claude Engram smoke check failed")
        if "codex" in targets:
            for path in (targets["codex"] / "agents").glob("*.toml"):
                tomllib.loads(path.read_text(encoding="utf-8"))
            codex_config = tomllib.loads((targets["codex"] / "config.toml").read_text(encoding="utf-8"))
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
                for relative in json.loads(MANIFEST.read_text(encoding="utf-8")):
                    candidate = home / relative
                    if not any(root in candidate.parents for root in selected_roots):
                        preserved.append(relative)
            except (OSError, json.JSONDecodeError):
                preserved = []
        managed = set(preserved) | {str(t.relative_to(home)) for t in new_targets}
        atomic_write(MANIFEST, json.dumps(sorted(managed), indent=2) + "\n")
        # D4/AC-10 (F03): persist the per-key delta computed by effective_specials()
        # for every special this run touched, same success-path-only discipline.
        # Entries for a special NOT in this run's targets are preserved untouched.
        special_keys_data = _read_json_or_empty(SPECIAL_KEYS_MANIFEST)
        special_keys_data.update(_PENDING_SPECIAL_KEYS)
        atomic_write(SPECIAL_KEYS_MANIFEST, json.dumps(special_keys_data, indent=2) + "\n")
        # 022 PKG-4 (AC-11/AC-15): persist a freshly-bootstrapped `providers.toml` only now
        # that every smoke check passed — a rolled-back install must never leave a registry
        # file behind that the failed run itself invented.
        for bootstrap_path, bootstrap_text in _PENDING_PROVIDERS_BOOTSTRAP:
            atomic_write(bootstrap_path, bootstrap_text)
        # AC-14: record which provider ids THIS run rendered, so the NEXT run's
        # `_previous_provider_ids()` can tell "ours, now gone from the registry — safe to
        # prune" apart from "never ours — never touch". Re-reads `providers.toml` (now
        # guaranteed to exist, pre-existing or just bootstrapped above) rather than
        # threading `entries` out of `apply_provider_registry`, the same "recompute the
        # small thing instead of plumbing state through" choice `previous_targets()` itself
        # makes for MANIFEST.
        if "opencode" in targets:
            json_manifest_data = {}
            if JSON_MANIFEST.exists():
                try:
                    json_manifest_data = json.loads(JSON_MANIFEST.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    json_manifest_data = {}
            json_manifest_data["opencode.json"] = sorted(provider_registry.parse_providers_toml(PROVIDERS_TOML))
            atomic_write(JSON_MANIFEST, json.dumps(json_manifest_data, indent=2) + "\n")
        # Scope record: which harness trees THIS machine manages, so check-drift.sh can
        # compare only what was actually installed (a claude-only machine must not read
        # the never-installed opencode/codex trees as drift). Merged, not replaced: a
        # later `--target` run extends the scope, it never silently narrows it.
        scope = set(targets)
        if SCOPE_PATH.exists():
            try:
                scope |= set(json.loads(SCOPE_PATH.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                pass
        if not args.target:
            scope = set(all_targets)
        atomic_write(SCOPE_PATH, json.dumps(sorted(scope)) + "\n")
    except Exception:
        rollback()
        print(f"INSTALL_ROLLED_BACK backup={backup}")
        raise

    print(f"INSTALL_PASS backup={backup}")


def run_uninstall():
    """D4/AC-10: uninstall exactly the selected --target(s), never guessing a
    wider scope (F07/F08), never touching a file/key it can't prove it wrote
    (F03/F04/F11), fail-closed on a corrupt registry (F05), and reversing the
    file removal AND the registry updates together (F06)."""
    stored, keep, remove = manifest_entries_for_uninstall()

    special_map = {}
    if "opencode" in targets:
        p = targets["opencode"] / "opencode.json"
        special_map[str(p.relative_to(home))] = (p, "json")
    if "claude-code" in targets:
        p = targets["claude-code"] / "settings.json"
        special_map[str(p.relative_to(home))] = (p, "json")
    if "codex" in targets:
        p = targets["codex"] / "config.toml"
        special_map[str(p.relative_to(home))] = (p, "toml")

    special_keys_data = _read_json_or_empty(SPECIAL_KEYS_MANIFEST)
    special_entries = {rel: special_keys_data[rel] for rel in special_map if rel in special_keys_data}

    def compute_reverts():
        results = {}
        for rel, entries in special_entries.items():
            target, kind = special_map[rel]
            if kind == "json":
                results[rel] = revert_json_special(target, entries)
            else:
                results[rel] = revert_codex(target, entries)
        return results

    if args.preview:
        changes = 0
        for target in sorted(remove):
            before = target.read_text(errors="replace", encoding="utf-8").splitlines(True) if target.exists() else []
            if before:
                changes += 1
                print("".join(difflib.unified_diff(before, [], fromfile=str(target), tofile=str(target) + " (uninstall remove)")), end="")
        for rel, (changed, _skipped, new_text) in compute_reverts().items():
            target, _kind = special_map[rel]
            if not changed:
                continue
            before = target.read_text(errors="replace", encoding="utf-8").splitlines(True)
            after = new_text.splitlines(True)
            changes += 1
            print("".join(difflib.unified_diff(before, after, fromfile=str(target), tofile=str(target) + " (uninstall de-merge)")), end="")
        print(f"MANAGED_DIFF_FILES={changes}")
        raise SystemExit(0)

    backup = new_backup_dir()
    registry_paths = [p for p in (MANIFEST, JSON_MANIFEST, SPECIAL_KEYS_MANIFEST, SCOPE_PATH) if p.exists()]
    affected = remove + [target for target, _ in special_map.values()] + registry_paths
    take_backup(backup, affected)

    def rollback():
        restore_backup(backup, affected)

    try:
        removed = []
        for target in remove:
            if target.exists():
                target.unlink()
                removed.append(str(target.relative_to(home)))
            prune_empty_dirs(target.parent)
        if removed:
            print("UNINSTALL_REMOVED=" + ",".join(sorted(removed)))

        reverted, kept_keys = [], []
        for rel, (changed, skipped, new_text) in compute_reverts().items():
            target, _kind = special_map[rel]
            if changed:
                atomic_write(target, new_text)
                reverted.append(rel)
            kept_keys.extend(f"{rel}:{key}" for key in skipped)
        if reverted:
            print("UNINSTALL_DEMERGED=" + ",".join(sorted(reverted)))
        if kept_keys:
            print("UNINSTALL_KEYS_KEPT=" + ",".join(sorted(kept_keys)))

        STATE_DIR.mkdir(parents=True, exist_ok=True)
        atomic_write(MANIFEST, json.dumps(sorted(keep, key=str), indent=2) + "\n")

        remaining_special = {rel: entries for rel, entries in special_keys_data.items() if rel not in special_map}
        atomic_write(SPECIAL_KEYS_MANIFEST, json.dumps(remaining_special, indent=2) + "\n")

        # opencode's provider ids: a total uninstall of opencode drops ALL ids
        # this installer ever recorded, not just the registry's current orphans
        # (apply_provider_registry's own diff is for a live re-render; here
        # nothing is going to re-render `provider.*` afterward).
        if "opencode" in targets and JSON_MANIFEST.exists():
            json_manifest_data = _read_json_or_empty(JSON_MANIFEST)
            provider_ids = set(json_manifest_data.pop("opencode.json", []))
            oc_target = targets["opencode"] / "opencode.json"
            if provider_ids and oc_target.exists():
                doc = json.loads(oc_target.read_text(encoding="utf-8"))
                live_block = doc.get("provider")
                if isinstance(live_block, dict):
                    for provider_id in provider_ids:
                        live_block.pop(provider_id, None)
                    doc["provider"] = live_block
                    atomic_write(oc_target, json.dumps(doc, indent=2) + "\n")
            atomic_write(JSON_MANIFEST, json.dumps(json_manifest_data, indent=2) + "\n")

        # install-targets.json: F07/F08 -- DERIVED from ground truth (what
        # MANIFEST still lists after this removal), never merged/guessed. An
        # uninstalled target's root has no more entries and drops out on its
        # own; a machine that predates this scope file (F10) self-heals too,
        # since the scope is recomputed from real managed files, not trusted
        # prior state.
        remaining_roots = {(home / rel).resolve() for rel in keep if isinstance(rel, str)}
        remaining_scope = sorted(
            name for name, root in all_targets.items()
            if any(p == root.resolve() or p.is_relative_to(root.resolve()) for p in remaining_roots)
        )
        atomic_write(SCOPE_PATH, json.dumps(remaining_scope) + "\n")
    except Exception:
        rollback()
        print(f"UNINSTALL_ROLLED_BACK backup={backup}")
        raise

    print(f"UNINSTALL_PASS backup={backup}")


if args.uninstall:
    run_uninstall()
else:
    run_install()
