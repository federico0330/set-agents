"""Legacy feature-state migration (ADR-0077).

States without ``schema_version == 1`` or with ``packages`` as a dict (pre-list
shape) are upgraded in place after a timestamped backup. History and business
fields are preserved; only the schema shape is normalized enough for
``validate_state``.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from feature_state_lib.model import (
    StateError,
    atomic_write,
    fail_if_invalid,
    load_state,
    print_json,
    validate_state,
)


def is_legacy_state(data: dict[str, Any]) -> bool:
    """True when the on-disk document cannot pass schema_version==1 as-is."""
    if not isinstance(data, dict):
        return False
    if data.get("schema_version") == 1 and not isinstance(data.get("packages"), dict):
        return False
    if "schema_version" not in data:
        return True
    if data.get("schema_version") != 1:
        return True
    if isinstance(data.get("packages"), dict):
        return True
    return False


def migrate_legacy_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Return a deep-copied v1-shaped document. Does not write disk."""
    if not isinstance(data, dict):
        raise StateError("state root must be an object")
    out = deepcopy(data)
    out["schema_version"] = 1
    pkgs = out.get("packages")
    if isinstance(pkgs, dict):
        converted = []
        for key, value in pkgs.items():
            if not isinstance(value, dict):
                raise StateError(f"legacy package {key!r} is not an object")
            row = deepcopy(value)
            row.setdefault("package_id", key)
            converted.append(row)
        out["packages"] = converted
    elif pkgs is None:
        out["packages"] = []
    elif not isinstance(pkgs, list):
        raise StateError("packages must be a list or legacy dict")
    if not isinstance(out.get("revision"), int) or out.get("revision", -1) < 0:
        out["revision"] = 0
    if "history" in out and not isinstance(out["history"], list):
        # Preserve opaque legacy history under a side key; keep a clean list for v1.
        out["legacy_history"] = out["history"]
        out["history"] = []
    out.setdefault("history", [])
    out.setdefault("blockers", [])
    out.setdefault("global_gates", [])
    out.setdefault("acceptance_criteria", [])
    out.setdefault("metrics", {})
    out.setdefault("budgets", {
        "max_deep_review_cycles": 2,
        "max_repairs_per_finding": 2,
        "max_package_subdivisions": 1,
        "max_spawns_per_package": 12,
        "max_gate_failures_per_package": 3,
        "max_verifications_per_package": 3,
    })
    return out


def backup_path_for(path: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return path.with_name(f"{path.name}.bak.{stamp}")


def migrate_legacy_file(path: Path, *, dry_run: bool = False) -> dict[str, Any]:
    data = load_state(path)
    if not is_legacy_state(data):
        return {
            "ok": True,
            "changed": False,
            "state_file": str(path),
            "reason": "already_current",
        }
    migrated = migrate_legacy_payload(data)
    errors = validate_state(migrated)
    # Soft: some legacy files lack approved_spec; still write schema_version + packages
    # list so agents are unblocked, and surface remaining errors to the caller.
    result: dict[str, Any] = {
        "ok": not errors,
        "changed": True,
        "state_file": str(path),
        "errors": errors,
        "schema_version": 1,
    }
    if dry_run:
        result["dry_run"] = True
        return result
    backup = backup_path_for(path)
    shutil.copy2(path, backup)
    atomic_write(path, migrated)
    result["backup"] = str(backup)
    return result


def load_state_auto_migrate(path: Path) -> dict[str, Any]:
    """Load and, when legacy, migrate with backup before returning.

    Used by resume/next/status so the orchestrator never needs the human to type
    migrate-legacy-state (ADR-0077).
    """
    data = load_state(path)
    if not is_legacy_state(data):
        return data
    result = migrate_legacy_file(path, dry_run=False)
    print(
        f"MIGRATED_LEGACY state_file={path} backup={result.get('backup', '-')}",
        file=sys.stderr,
    )
    return load_state(path)


def cmd_migrate_legacy_state(args: argparse.Namespace) -> int:
    path = Path(args.state_file) if args.state_file else None
    if path is None and getattr(args, "feature_id", None):
        from feature_state_lib.model import state_path
        path = state_path(args.feature_id)
    if path is None:
        raise StateError("--state-file or feature_id is required")
    result = migrate_legacy_file(path, dry_run=bool(getattr(args, "dry_run", False)))
    print_json(result)
    return 0 if result.get("ok") or result.get("changed") else 2
