#!/usr/bin/env python3
"""Manage compact package-workflow feature state.

Safe commands:
  init FEATURE_ID SPEC_PATH SPEC_HASH
  validate STATE_FILE
  dry-run FEATURE_ID
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


PHASES = [
    "REQUIREMENTS",
    "SPEC_DRAFT",
    "SPEC_CHALLENGE",
    "USER_APPROVAL",
    "PACKAGE_PLANNING",
    "PACKAGE_IMPLEMENTATION",
    "PACKAGE_GATES",
    "PACKAGE_REVIEW",
    "PACKAGE_REPAIR",
    "DELTA_REVIEW",
    "PACKAGE_ACCEPTED",
    "INTEGRATION",
    "DONE",
    "BLOCKED",
]


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def state_path(feature_id: str) -> Path:
    return Path("ai/state/features") / f"{feature_id}.json"


def base_state(feature_id: str, spec_path: str, spec_hash: str) -> dict:
    return {
        "feature_id": feature_id,
        "phase": "PACKAGE_PLANNING",
        "approved_spec": {"path": spec_path, "hash": spec_hash, "approved_at": now()},
        "acceptance_criteria": [],
        "packages": [],
        "gates": [],
        "attempts": {"max_deep_review_cycles_per_package": 2},
        "findings": [],
        "repairs": [],
        "final_state": None,
        "updated_at": now(),
    }


def validate_state(data: dict) -> list[str]:
    errors: list[str] = []
    if not data.get("feature_id"):
        errors.append("missing feature_id")
    if data.get("phase") not in PHASES:
        errors.append(f"invalid phase: {data.get('phase')}")
    spec = data.get("approved_spec") or {}
    if not spec.get("path") or not spec.get("hash"):
        errors.append("approved_spec.path and approved_spec.hash are required")
    for package in data.get("packages", []):
        for key in ("package_id", "objective", "tasks", "ownership_paths", "status"):
            if key not in package:
                errors.append(f"{package.get('package_id', '<unknown>')}: missing {key}")
        attempts = package.get("attempts", {})
        if attempts.get("deep_review_cycles", 0) > data.get("attempts", {}).get("max_deep_review_cycles_per_package", 2):
            errors.append(f"{package.get('package_id')}: deep review budget exceeded")
    return errors


def cmd_init(args: argparse.Namespace) -> int:
    path = state_path(args.feature_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not args.force:
        print(f"STATE_EXISTS: {path}")
        return 2
    path.write_text(json.dumps(base_state(args.feature_id, args.spec_path, args.spec_hash), indent=2) + "\n")
    print(f"STATE_CREATED: {path}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    data = json.loads(Path(args.state_file).read_text())
    errors = validate_state(data)
    if errors:
        print("STATE_INVALID")
        for error in errors:
            print(f"- {error}")
        return 2
    print("STATE_VALID")
    return 0


def cmd_dry_run(args: argparse.Namespace) -> int:
    data = base_state(args.feature_id, "docs/specs/example/spec.md", "dry-run")
    data["acceptance_criteria"] = ["AC-1", "AC-2", "AC-3"]
    data["packages"] = [
        {
            "package_id": "PKG-01",
            "objective": "Deliver one observable vertical slice",
            "acceptance_criteria": ["AC-1", "AC-2"],
            "tasks": [
                {"id": "T-001", "status": "implemented", "local_validations": ["typecheck", "focused-test"]},
                {"id": "T-002", "status": "implemented", "local_validations": ["lint", "contract-test"]},
                {"id": "T-003", "status": "implemented", "local_validations": ["smoke"]},
            ],
            "dependencies": [],
            "ownership_paths": ["src/**", "tests/**"],
            "risks": [],
            "gates": [{"name": "package verify", "status": "pass"}],
            "attempts": {"deep_review_cycles": 1},
            "findings": [{"id": "F-001", "status": "repaired"}],
            "repairs": [{"finding_id": "F-001", "verification": "focused-test pass"}],
            "delta_review": {"status": "pass"},
            "status": "PACKAGE_ACCEPTED",
        }
    ]
    data["phase"] = "DONE"
    data["final_state"] = "DONE"
    errors = validate_state(data)
    print(json.dumps(data, indent=2))
    print("DRY_RUN_PASS" if not errors else "DRY_RUN_FAIL")
    return 0 if not errors else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("feature_id")
    init.add_argument("spec_path")
    init.add_argument("spec_hash")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)
    validate = sub.add_parser("validate")
    validate.add_argument("state_file")
    validate.set_defaults(func=cmd_validate)
    dry = sub.add_parser("dry-run")
    dry.add_argument("feature_id")
    dry.set_defaults(func=cmd_dry_run)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
