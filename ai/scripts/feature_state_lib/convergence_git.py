"""Strict read-only Git adapter for HCE — argv, shell=False, NUL-safe."""

from __future__ import annotations

import base64
import hashlib
import os
import subprocess
from pathlib import Path
from typing import Any

from feature_state_lib.convergence_constants import PROFILE_SOURCE_ROOT
from feature_state_lib.convergence_errors import HceDenial

GIT_TIMEOUT_SECONDS = 30

ALLOWED_MODES = frozenset({"100644", "100755"})
FORBIDDEN_MODES = frozenset({"120000", "160000"})


def _run_git(args: list[str], cwd: Path) -> bytes:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HceDenial("HCE_GIT_UNAVAILABLE", str(exc)) from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or b"").decode("utf-8", "replace").strip()
        raise HceDenial("HCE_GIT_UNAVAILABLE", detail or "git command failed")
    return proc.stdout


def _validate_canonical_path_components(raw: str, *, label: str) -> Path:
    if not raw:
        raise HceDenial("HCE_STATE_PATH_MISMATCH", f"empty {label}")
    if not os.path.isabs(raw):
        raise HceDenial("HCE_STATE_PATH_MISMATCH", f"{label} must be absolute")
    if ".." in Path(raw).parts:
        raise HceDenial("HCE_STATE_PATH_MISMATCH", f"{label} must not contain ..")
    if os.path.islink(raw):
        raise HceDenial("HCE_STATE_PATH_MISMATCH", f"{label} is a symlink")
    resolved = Path(os.path.realpath(raw))
    if Path(os.path.abspath(raw)) != resolved:
        raise HceDenial("HCE_STATE_PATH_MISMATCH", f"{label} is not canonical")
    current = resolved
    while True:
        if os.path.islink(current):
            raise HceDenial("HCE_STATE_PATH_MISMATCH", f"{label} contains a symlink component")
        parent = current.parent
        if parent == current:
            break
        current = parent
    return resolved


def validate_canonical_state_path(path: Path) -> Path:
    """Reject relative paths, .., symlink components, hardlinks, and lexical aliases."""
    raw = str(path)
    resolved = _validate_canonical_path_components(raw, label="state path")
    try:
        stat = os.stat(raw, follow_symlinks=False)
    except OSError as exc:
        raise HceDenial("HCE_STATE_PATH_MISMATCH", f"cannot stat state path: {exc}") from exc
    if stat.st_nlink != 1:
        raise HceDenial("HCE_STATE_PATH_MISMATCH", "state path is hardlinked")
    return resolved


def validate_canonical_lock_path(path: Path) -> Path:
    """Reject noncanonical/symlink/hardlink lock paths before opening."""
    raw = str(path)
    resolved = _validate_canonical_path_components(raw, label="lock path")
    if os.path.lexists(raw):
        if os.path.islink(raw):
            raise HceDenial("HCE_STATE_PATH_MISMATCH", "lock path is a symlink")
        stat = os.stat(raw, follow_symlinks=False)
        if stat.st_nlink != 1:
            raise HceDenial("HCE_STATE_PATH_MISMATCH", "lock path is hardlinked")
    return resolved


def resolve_realpath(path: Path) -> Path:
    return path.resolve()


def git_common_dir(worktree: Path) -> Path:
    raw = _run_git(["rev-parse", "--git-common-dir"], worktree).decode("utf-8").strip()
    common = Path(raw)
    if not common.is_absolute():
        common = (worktree / common).resolve()
    return common


def resolve_commit(worktree: Path, ref: str) -> str:
    out = _run_git(["rev-parse", ref], worktree).decode("utf-8").strip()
    if len(out) != 40 or not all(c in "0123456789abcdef" for c in out):
        raise HceDenial("HCE_GIT_UNAVAILABLE", f"unsupported ref format: {ref!r}")
    return out


def resolve_tree(worktree: Path, ref: str) -> str:
    out = _run_git(["rev-parse", f"{ref}^{{tree}}"], worktree).decode("utf-8").strip()
    return out


def head_commit_and_tree(worktree: Path) -> tuple[str, str]:
    commit = resolve_commit(worktree, "HEAD")
    tree = resolve_tree(worktree, commit)
    return commit, tree


def paths_digest_b64(paths: list[str | bytes]) -> str:
    raw_paths = [p.encode() if isinstance(p, str) else p for p in paths]
    records = b"".join(
        len(p).to_bytes(8, "big") + p
        for p in sorted(raw_paths)
    )
    return "sha256:" + hashlib.sha256(records).hexdigest()


def output_paths_b64(paths: list[str | bytes]) -> list[str]:
    encoded = []
    for p in paths:
        raw = p.encode() if isinstance(p, str) else p
        encoded.append(base64.b64encode(raw).decode("ascii"))
    return sorted(encoded)


def measure_child_output_paths(
    worktree: Path,
    identity: dict[str, Any],
) -> tuple[list[str], str]:
    paths, _ = diff_paths_and_lines(worktree, identity["base_tree"], identity["candidate_tree"])
    return output_paths_b64(paths), paths_digest_b64(paths)


def _path_bytes_to_str(path_bytes: bytes) -> str:
    try:
        return path_bytes.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", "non-UTF8 path in git diff") from exc


def _validate_mode(old_mode: str, new_mode: str, path: str) -> None:
    if old_mode in FORBIDDEN_MODES or new_mode in FORBIDDEN_MODES:
        raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", f"symlink/gitlink entry: {path}")
    if old_mode not in {"000000", *ALLOWED_MODES}:
        raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", f"unsupported old mode {old_mode}: {path}")
    if new_mode not in ALLOWED_MODES:
        raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", f"unsupported new mode {new_mode}: {path}")
    if old_mode not in {"000000", new_mode} and old_mode != new_mode:
        raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", f"type change {old_mode}->{new_mode}: {path}")


def _parse_raw_diff(raw: bytes) -> tuple[list[str], list[bytes]]:
    paths: list[str] = []
    raw_paths: list[bytes] = []
    parts = raw.split(b"\0")
    i = 0
    while i < len(parts):
        record = parts[i]
        if not record:
            i += 1
            continue
        if not record.startswith(b":"):
            raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", "malformed raw diff record")
        if i + 1 >= len(parts) or not parts[i + 1]:
            raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", "malformed raw diff record")
        header = record[1:].decode("ascii", "strict")
        path_bytes = parts[i + 1]
        path = _path_bytes_to_str(path_bytes)
        fields = header.split()
        if len(fields) < 5:
            raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", f"malformed raw diff header: {path}")
        old_mode, new_mode = fields[0], fields[1]
        _validate_mode(old_mode, new_mode, path)
        paths.append(path)
        raw_paths.append(path_bytes)
        i += 2
    return paths, raw_paths


def _parse_numstat(raw: bytes) -> int:
    total_lines = 0
    parts = raw.split(b"\0")
    i = 0
    while i < len(parts):
        chunk = parts[i]
        if not chunk:
            i += 1
            continue
        if b"\t" not in chunk:
            raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", "malformed numstat record")
        fields = chunk.split(b"\t")
        if len(fields) < 3:
            raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", "malformed numstat record")
        added, removed, path_bytes = fields[0], fields[1], fields[2]
        path = _path_bytes_to_str(path_bytes)
        if added == b"-" or removed == b"-":
            raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", f"binary entry: {path}")
        if not added.isdigit() or not removed.isdigit():
            raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", f"malformed numstat counts: {path}")
        total_lines += int(added) + int(removed)
        i += 1
        if i < len(parts) and parts[i] and b"\t" not in parts[i]:
            i += 1
    return total_lines


def diff_paths_and_lines(worktree: Path, base_tree: str, candidate_tree: str) -> tuple[list[str], int]:
    common = [
        "diff", "--no-ext-diff", "--no-textconv", "--no-renames",
        base_tree, candidate_tree,
    ]
    raw_out = _run_git([*common, "--raw", "-z"], worktree)
    numstat_out = _run_git([*common, "--numstat", "-z"], worktree)
    paths, raw_paths = _parse_raw_diff(raw_out)
    unique: dict[str, bytes] = {}
    for path, raw in zip(paths, raw_paths):
        unique[path] = raw
    paths = sorted(unique)
    total_lines = _parse_numstat(numstat_out)
    return paths, total_lines


def _under_profile_root(path: str) -> bool:
    return path == PROFILE_SOURCE_ROOT or path.startswith(PROFILE_SOURCE_ROOT + "/")


def check_clean_worktree(worktree: Path) -> None:
    status = _run_git(
        ["status", "--porcelain", "-z", "--untracked-files=all", "--ignored"],
        worktree,
    )
    for entry in status.split(b"\0"):
        if not entry or len(entry) < 4:
            continue
        code = entry[:2].decode("ascii", "replace")
        path = entry[3:].decode("utf-8", "errors=replace")
        if code.strip() and code != "??":
            raise HceDenial("HCE_DIRTY_WORKTREE", f"tracked dirt: {path}")
        if code == "??" and _under_profile_root(path):
            raise HceDenial("HCE_DIRTY_WORKTREE", f"untracked under profile root: {path}")
        if code.strip() == "!!" and _under_profile_root(path):
            raise HceDenial("HCE_DIRTY_WORKTREE", f"ignored dirt under profile root: {path}")


def measure_original_identity(worktree: Path, identity: dict[str, Any]) -> dict[str, Any]:
    baseline = identity.get("baseline_ref")
    candidate = identity.get("candidate_ref")
    if not baseline or not candidate:
        raise HceDenial("HCE_STALE", "missing original identity refs")
    base_tree = resolve_tree(worktree, baseline)
    candidate_tree = resolve_tree(worktree, candidate)
    paths, changed_lines = diff_paths_and_lines(worktree, base_tree, candidate_tree)
    return {
        "baseline_ref": baseline,
        "candidate_ref": candidate,
        "base_tree": base_tree,
        "candidate_tree": candidate_tree,
        "paths_digest": paths_digest_b64(paths),
        "changed_lines": changed_lines,
        "changed_paths": paths,
    }


def measure_combined_identity(worktree: Path, base_commit: str) -> dict[str, Any]:
    head_commit, head_tree = head_commit_and_tree(worktree)
    base_tree = resolve_tree(worktree, base_commit)
    paths, changed_lines = diff_paths_and_lines(worktree, base_tree, head_tree)
    return {
        "generation": 2,
        "base_commit": base_commit,
        "base_tree": base_tree,
        "candidate_commit": head_commit,
        "candidate_tree": head_tree,
        "paths_digest": paths_digest_b64(paths),
        "changed_lines": changed_lines,
        "changed_paths": paths,
    }
