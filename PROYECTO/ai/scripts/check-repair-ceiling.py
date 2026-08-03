#!/usr/bin/env python3
"""Fail when a package's repair diff exceeds its frozen repair_ceiling.budget_lines
(docs/adr/0023-*.md). Structural sibling of check-owned-paths.py: same
--state-file/--package-id/--baseline shape, same git-diff-against-the-working-tree
convention, same PASS/FAIL print + exit code pattern.
"""

from __future__ import annotations

import argparse
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


def changed_lines_from_git(baseline: str) -> int:
    result = subprocess.run(
        ["git", "diff", "--numstat", baseline, "--"],
        text=True, capture_output=True, check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"GIT_DIFF_FAILED: {result.stderr.strip()}")
    total = 0
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        added, removed = parts[0], parts[1]
        if added.isdigit():
            total += int(added)
        if removed.isdigit():
            total += int(removed)
    return total


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-file", required=True)
    parser.add_argument("--package-id", required=True)
    parser.add_argument("--baseline")
    parser.add_argument("--changed-lines", type=int,
                        help="skip the git measurement and check this number instead (tests only)")
    args = parser.parse_args()

    data = load_state(Path(args.state_file))
    package = package_by_id(data, args.package_id)
    ceiling = package.get("repair_ceiling")
    if not ceiling:
        # Additive-only (docs/adr/0023-*.md): a package whose repair never had a
        # candidate_identity to compute a ceiling from has nothing to check against --
        # this is not a failure, it's the mechanism not yet applying to this package.
        payload = {"ok": True, "package_id": args.package_id,
                   "reason": "no repair_ceiling frozen for this package -- nothing to check"}
        print(json.dumps(payload, indent=2, sort_keys=True))
        print("REPAIR_CEILING_PASS")
        return 0

    baseline = args.baseline or (package.get("candidate_identity") or {}).get("candidate_tree")
    if not baseline and args.changed_lines is None:
        raise SystemExit("REPAIR_CEILING_NO_BASELINE: pass --baseline, or freeze-candidate must have run first")

    changed = args.changed_lines if args.changed_lines is not None else changed_lines_from_git(baseline)
    budget = ceiling.get("budget_lines")
    ok = budget is not None and changed <= budget

    payload = {
        "ok": ok,
        "package_id": args.package_id,
        "changed_lines": changed,
        "budget_lines": budget,
        "baseline": baseline,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not ok:
        print("REPAIR_CEILING_FAIL")
        return 2
    print("REPAIR_CEILING_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
