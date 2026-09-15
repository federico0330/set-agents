"""Strict read-only Git adapter for HCE — argv, shell=False, NUL-safe."""

from __future__ import annotations

import base64
import hashlib
import subprocess
from pathlib import Path
from typing import Any

from feature_state_lib.convergence_constants import PROFILE_SOURCE_ROOT
from feature_state_lib.convergence_errors import HceDenial

GIT_TIMEOUT_SECONDS = 30


def _run_git(args: list[str], cwd: Path) -> bytes:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HceDenial("HCE_GIT_UNAVAILABLE", str(exc)) from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or b"").decode("utf-8", "replace").strip()
        raise HceDenial("HCE_GIT_UNAVAILABLE", detail or "git command failed")
    return proc.stdout


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


def diff_paths_and_lines(worktree: Path, base_tree: str, candidate_tree: str) -> tuple[list[str], int]:
    raw = _run_git(
        ["diff", "--no-ext-diff", "--no-textconv", "--no-renames", "--numstat", "-z", base_tree, candidate_tree],
        worktree,
    )
    parts = raw.split(b"\0")
    paths: list[str] = []
    total_lines = 0
    i = 0
    while i < len(parts):
        chunk = parts[i]
        if not chunk:
            i += 1
            continue
        if b"\t" in chunk:
            fields = chunk.decode("utf-8", "errors=replace").split("\t")
            if len(fields) >= 3:
                added, removed, path = fields[0], fields[1], fields[2]
                if added == "-" or removed == "-":
                    raise HceDenial("HCE_UNSUPPORTED_GIT_ENTRY", f"binary entry: {path}")
                if added.isdigit():
                    total_lines += int(added)
                if removed.isdigit():
                    total_lines += int(removed)
                paths.append(path)
            i += 1
        else:
            if i + 1 < len(parts):
                path = parts[i + 1].decode("utf-8", "errors=replace")
                paths.append(path)
                i += 2
            else:
                i += 1
    return sorted(set(paths)), total_lines


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
