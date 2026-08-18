#!/usr/bin/env python3
"""Fail when a package diff touches paths outside its declared ownership."""

from __future__ import annotations

import argparse
import fnmatch
import json
import posixpath
import subprocess
from pathlib import Path
from typing import Any


def load_state(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def package_by_id(data: dict[str, Any], package_id: str) -> dict[str, Any]:
    for package in data.get("packages", []):
        if package.get("package_id", package.get("id")) == package_id:
            return package
    raise SystemExit(f"UNKNOWN_PACKAGE: {package_id}")


def _is_bare_directory_pattern(pattern: str) -> bool:
    """A directory declaration has no glob metacharacters. ``src/**``, ``*.py`` and other
    wildcard patterns keep their existing fnmatch-only behavior untouched by this rule."""
    return bool(pattern) and not any(char in pattern for char in "*?[]")


def _normalize_slashes(value: str) -> str:
    return value.replace("\\", "/")


def _canonical_path(path: str) -> str:
    """Collapse ``.``, ``..`` and duplicate ``/`` separators to the real on-disk location a
    changed path names. Without this, a crafted ``tests/../ai/scripts/pwn.py`` (or
    ``tests/../../etc/passwd``) borrows ``tests``'s ownership boundary from
    ``_is_directory_descendant`` below: a bare ``str.startswith("tests/")`` treats the
    literal ``..`` text as one more path segment nested inside ``tests``, when the file it
    actually names lives somewhere else entirely (or outside the repo). `posixpath.normpath`
    resolves it to the file it really is before any boundary check ever sees the raw text."""
    normalized = _normalize_slashes(path)
    return posixpath.normpath(normalized) if normalized else normalized


def _canonical_declaration(pattern: str) -> str:
    """Same collapsing as `_canonical_path`, for the declaration side, so equivalent
    spellings of the same directory (``/tests``, ``./tests``, ``docs//adr``, ``tests\\sub``)
    all describe the same boundary as the plain ``tests`` / ``docs/adr`` form. A leading
    ``/`` on a declaration is a repo-root anchor, not a filesystem-absolute path -- the
    existing literal-fnmatch branch already tolerates that spelling via
    ``fnmatch("/" + normalized, pattern)`` -- so it is stripped before normalizing; otherwise
    `posixpath.normpath` would keep it absolute and it would never match a relative changed
    path."""
    stripped = _normalize_slashes(pattern).lstrip("/")
    return _canonical_path(stripped)


def _is_directory_descendant(path: str, pattern: str) -> bool:
    """Let a bare directory pattern (with or without a trailing slash, and regardless of its
    leading-slash / dot-slash / double-slash / backslash spelling) own every path below it,
    with a real path-segment boundary -- never a bare ``startswith`` on the raw pattern text,
    so ``tests`` never covers a look-alike sibling like ``tests-extra``, and a ``..`` segment
    on either side never borrows a boundary it does not really cross."""
    directory = _canonical_declaration(pattern)
    if not _is_bare_directory_pattern(directory):
        return False
    return path == directory or path.startswith(directory + "/")


def matches(path: str, patterns: list[str]) -> bool:
    normalized = _canonical_path(path)
    for pattern in patterns:
        if fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch("/" + normalized, pattern):
            return True
        if _is_directory_descendant(normalized, pattern):
            return True
    return False


def approved_exception(package: dict[str, Any], path: str) -> bool:
    for item in package.get("approved_exceptions", []):
        if item.get("status") != "approved":
            continue
        pattern = item.get("path")
        if pattern and matches(path, [pattern]):
            return True
    return False


def changed_files_from_git(baseline: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", baseline, "--"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"GIT_DIFF_FAILED: {result.stderr.strip()}")
    tracked = [line.strip() for line in result.stdout.splitlines() if line.strip()]

    # `git diff --name-only <baseline> --` only ever compares tracked content against
    # <baseline>; a brand-new file that was never `git add`-ed is invisible to it, so a
    # package could create an out-of-scope file and this gate would stay silent (that is
    # exactly how 022/P1's provider_registry.py sailed through unseen). `git status
    # --porcelain --untracked-files=all` is the one call that lists untracked files
    # individually (not collapsed to their containing directory), so it is added here as
    # a second, independent source rather than replacing the diff above -- the diff still
    # owns tracked renames/edits, this only fills the untracked gap. `-z` is load-bearing,
    # not cosmetic: plain (newline) `--porcelain` C-quotes any path containing a space
    # (measured live in this repo: `docs/notas/00 - Proyecto.md` -> `"00 - Proyecto.md"`,
    # literal quote characters included) while `git diff --name-only` never quotes that
    # same path -- parsing the quoted form here would have fed a corrupted, unmatchable
    # path into `matches()`. `-z` guarantees NUL-separated, always-unquoted paths.
    status = subprocess.run(
        ["git", "status", "--porcelain", "-z", "--untracked-files=all"],
        text=True,
        capture_output=True,
        check=False,
    )
    if status.returncode != 0:
        raise SystemExit(f"GIT_STATUS_FAILED: {status.stderr.strip()}")
    untracked = [
        entry[3:]
        for entry in status.stdout.split("\0")
        if entry.startswith("??") and entry[3:]
    ]

    changed = list(tracked)
    for path in untracked:
        if path not in changed:
            changed.append(path)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-file", required=True)
    parser.add_argument("--package-id", required=True)
    parser.add_argument("--baseline")
    parser.add_argument("--changed-file", action="append")
    args = parser.parse_args()

    data = load_state(Path(args.state_file))
    package = package_by_id(data, args.package_id)
    changed = args.changed_file or changed_files_from_git(args.baseline or "HEAD")
    owned = package.get("owned_paths", package.get("ownershipPaths", [])) + package.get("shared_paths", [])
    read_only = package.get("read_only_paths", [])
    violations = []
    read_only_violations = []

    for path in changed:
        if matches(path, read_only) and not approved_exception(package, path):
            read_only_violations.append(path)
            continue
        if not matches(path, owned) and not approved_exception(package, path):
            violations.append(path)

    payload = {
        "ok": not violations and not read_only_violations,
        "package_id": args.package_id,
        "changed_files": changed,
        "owned_paths": owned,
        "read_only_paths": read_only,
        "out_of_scope": violations,
        "read_only_violations": read_only_violations,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if violations or read_only_violations:
        print("OWNERSHIP_FAIL")
        return 2
    print("OWNERSHIP_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
