#!/usr/bin/env python3
"""Fail when a package diff touches paths outside its declared ownership."""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from pathlib import Path
from typing import Any


def load_state(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def package_by_id(data: dict[str, Any], package_id: str) -> dict[str, Any]:
    for package in data.get("packages", []):
        if package.get("package_id", package.get("id")) == package_id:
            return package
    raise SystemExit(f"UNKNOWN_PACKAGE: {package_id}")


def matches(path: str, patterns: list[str]) -> bool:
    normalized = path.replace("\\", "/")
    return any(fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch("/" + normalized, pattern) for pattern in patterns)


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
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


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
