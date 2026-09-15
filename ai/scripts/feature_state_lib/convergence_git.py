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


def validate_canonical_state_path(path: Path) -> Path:
    """Reject relative paths, .., symlink components, hardlinks, and lexical aliases."""
    raw = str(path)
    if not raw:
        raise HceDenial("HCE_STATE_PATH_MISMATCH", "empty state path")
    if not os.path.isabs(raw):
        raise HceDenial("HCE_STATE_PATH_MISMATCH", "state path must be absolute")
    if ".." in Path(raw).parts:
        raise HceDenial("HCE_STATE_PATH_MISMATCH", "state path must not contain ..")
    if os.path.islink(raw):
        raise HceDenial("HCE_STATE_PATH_MISMATCH", "state path is a symlink")
    resolved = Path(os.path.realpath(raw))
    if Path(os.path.abspath(raw)) != resolved:
        raise HceDenial("HCE_STATE_PATH_MISMATCH", "state path is not canonical")
    current = resolved
    while True:
        if os.path.islink(current):
            raise HceDenial("HCE_STATE_PATH_MISMATCH", "state path contains a symlink component")
        parent = current.parent
        if parent == current:
            break
        current = parent
    try:
        stat = os.stat(raw, follow_symlinks=False)
    except OSError as exc:
        raise HceDenial("HCE_STATE_PATH_MISMATCH", f"cannot stat state path: {exc}") from exc
    if stat.st_nlink != 1:
        raise HceDenial("HCE_STATE_PATH_MISMATCH", "state path is hardlinked")
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


def paths_digest_b64(paths: list[str]) -> str:
    records = b"".join(
        len(p.encode()).to_bytes(8, "big") + p.encode()
        for p in sorted(paths, key=lambda x: x.encode())
    )
    return "sha256:" + hashlib.sha256(records).hexdigest()


def output_paths_b64(paths: list[str]) -> list[str]:
    return sorted(base64.b64encode(p.encode()).decode("ascii") for p in paths)


def _validate_mode(old_mode: str, new_mode: str, path: str) -> None:
    if old_mode in FORBIDDEN_MODES or new_mode in FORBIDDEN_MODES:
        raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", f"symlink/gitlink entry: {path}")
    if old_mode not in {"000000", *ALLOWED_MODES}:
        raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", f"unsupported old mode {old_mode}: {path}")
    if new_mode not in ALLOWED_MODES:
        raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", f"unsupported new mode {new_mode}: {path}")
    if old_mode not in {"000000", new_mode} and old_mode != new_mode:
        raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", f"type change {old_mode}->{new_mode}: {path}")


def _parse_raw_diff(raw: bytes) -> list[str]:
    paths: list[str] = []
    parts = raw.split(b"\0")
    i = 0
    while i < len(parts):
        record = parts[i]
        if not record:
            i += 1
            continue
        if not record.startswith(b":"):
            i += 1
            continue
        if i + 1 >= len(parts) or not parts[i + 1]:
            raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", "malformed raw diff record")
        header = record[1:].decode("ascii", "strict")
        path_bytes = parts[i + 1]
        try:
            path = path_bytes.decode("utf-8", "strict")
        except UnicodeDecodeError as exc:
            raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", "non-UTF8 path in raw diff") from exc
        fields = header.split()
        if len(fields) < 5:
            raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", f"malformed raw diff header: {path}")
        old_mode, new_mode = fields[0], fields[1]
        _validate_mode(old_mode, new_mode, path)
        paths.append(path)
        i += 2
    return paths


def _parse_numstat(raw: bytes) -> int:
    total_lines = 0
    parts = raw.split(b"\0")
    i = 0
    while i < len(parts):
        chunk = parts[i]
        if not chunk:
            i += 1
            continue
        if b"\t" in chunk:
            fields = chunk.split(b"\t")
            if len(fields) >= 3:
                added, removed = fields[0], fields[1]
                path = fields[2].decode("utf-8", "strict")
                if added == b"-" or removed == b"-":
                    raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", f"binary entry: {path}")
                if added.isdigit():
                    total_lines += int(added)
                if removed.isdigit():
                    total_lines += int(removed)
            i += 1
        else:
            if i + 1 < len(parts):
                i += 2
            else:
                i += 1
    return total_lines


def diff_paths_and_lines(worktree: Path, base_tree: str, candidate_tree: str) -> tuple[list[str], int]:
    common = [
        "diff", "--no-ext-diff", "--no-textconv", "--no-renames",
        base_tree, candidate_tree,
    ]
    raw_out = _run_git([*common, "--raw", "-z"], worktree)
    numstat_out = _run_git([*common, "--numstat", "-z"], worktree)
    paths = sorted(set(_parse_raw_diff(raw_out)))
    total_lines = _parse_numstat(numstat_out)
    return paths, total_lines


def check_clean_worktree(worktree: Path) -> None:
    status = _run_git(["status", "--porcelain", "-z", "--untracked-files=all"], worktree)
    for entry in status.split(b"\0"):
        if not entry or len(entry) < 4:
            continue
        code = entry[:2].decode("ascii", "replace")
        path = entry[3:].decode("utf-8", "errors=replace")
        if code.strip() and code != "??":
            raise HceDenial("HCE_DIRTY_WORKTREE", f"tracked dirt: {path}")
        if code == "??" and (path.startswith(PROFILE_SOURCE_ROOT + "/") or path == PROFILE_SOURCE_ROOT):
            raise HceDenial("HCE_DIRTY_WORKTREE", f"untracked under profile root: {path}")


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
