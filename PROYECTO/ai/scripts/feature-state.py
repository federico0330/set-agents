#!/usr/bin/env python3
"""Executable package-workflow state machine.

The state file is compact, atomic, and deterministic. It is intentionally not a
conversation log: agents record decisions, gates, findings, repairs, and a small
event history that lets the orchestrator resume without re-running prior steps.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PHASES = {
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
    "PACKAGE_TESTING",
    "PACKAGE_RUNTIME_QA",
    "PACKAGE_ACCEPTED",
    "INTEGRATION",
    "DONE",
    "BLOCKED",
}

LEGAL_TRANSITIONS = {
    "PACKAGE_PLANNING": {"PACKAGE_IMPLEMENTATION"},
    "PACKAGE_IMPLEMENTATION": {"PACKAGE_GATES", "BLOCKED"},
    "PACKAGE_GATES": {"PACKAGE_REVIEW", "PACKAGE_IMPLEMENTATION", "BLOCKED"},
    "PACKAGE_REVIEW": {"PACKAGE_TESTING", "PACKAGE_REPAIR", "BLOCKED"},
    "PACKAGE_REPAIR": {"DELTA_REVIEW", "BLOCKED"},
    "DELTA_REVIEW": {"PACKAGE_TESTING", "PACKAGE_REPAIR", "PACKAGE_REVIEW", "BLOCKED"},
    "PACKAGE_TESTING": {"PACKAGE_RUNTIME_QA", "PACKAGE_REPAIR", "BLOCKED"},
    "PACKAGE_RUNTIME_QA": {"PACKAGE_ACCEPTED", "PACKAGE_REPAIR", "BLOCKED"},
    "PACKAGE_ACCEPTED": {"PACKAGE_PLANNING", "INTEGRATION"},
    "INTEGRATION": {"DONE", "BLOCKED"},
    "BLOCKED": set(),
    "DONE": set(),
}

TERMINAL = {"DONE", "BLOCKED"}
MUTATING_COMMANDS = {
    "init",
    "transition",
    "create-package",
    "update-package",
    "start-task",
    "complete-task",
    "fail-task",
    "record-gate",
    "record-spawn",
    "record-review",
    "start-review-panel",
    "record-subreview",
    "finalize-review-panel",
    "record-repair",
    "record-delta-review",
    "record-testing",
    "record-runtime-qa",
    "accept-package",
    "block",
}
NON_ACCEPTING_ACTORS = {"implementer", "frontend-engineer", "refactor-specialist", "repair-agent"}
# Physical budgets per triage mode: ceremony must be proportional to risk, not to diff size.
MODE_BUDGETS = {
    "feature": {"max_spawns_per_package": 12, "max_deep_review_cycles": 2},
    "scoped": {"max_spawns_per_package": 8, "max_deep_review_cycles": 2},
    "quick-fix": {"max_spawns_per_package": 4, "max_deep_review_cycles": 1},
    "incident": {"max_spawns_per_package": 6, "max_deep_review_cycles": 1},
}


class StateError(RuntimeError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def state_path(feature_id: str) -> Path:
    return Path("ai/state/features") / f"{feature_id}.json"


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def parse_json_object(raw: str) -> dict[str, Any]:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise StateError("expected JSON object")
    return value


def parse_bool(raw: str | None, default: bool | None = None) -> bool | None:
    if raw is None:
        return default
    lowered = raw.lower()
    if lowered in {"1", "true", "yes", "y"}:
        return True
    if lowered in {"0", "false", "no", "n"}:
        return False
    raise StateError(f"invalid boolean: {raw}")


def base_state(feature_id: str, spec_path: str, spec_hash: str) -> dict[str, Any]:
    stamp = now()
    return {
        "schema_version": 1,
        "revision": 0,
        "feature_id": feature_id,
        "phase": "PACKAGE_PLANNING",
        "approved_spec": {"path": spec_path, "hash": spec_hash, "approved_at": stamp},
        "acceptance_criteria": [],
        "packages": [],
        "current_package_id": None,
        "global_gates": [],
        "budgets": {
            "max_deep_review_cycles": 2,
            "max_repairs_per_finding": 2,
            "max_package_subdivisions": 1,
            "max_spawns_per_package": 12,
        },
        "metrics": {
            "task_deep_reviews": 0,
            "package_reviews": 0,
            "repair_batches": 0,
            "delta_reviews": 0,
            "human_questions_after_approval": 0,
        },
        "blockers": [],
        "history": [],
        "final_state": None,
        "updated_at": stamp,
    }


def compact_package(package_id: str, objective: str) -> dict[str, Any]:
    return {
        "package_id": package_id,
        "objective": objective,
        "acceptance_criteria": [],
        "tasks": [],
        "dependencies": [],
        "owned_paths": [],
        "read_only_paths": [],
        "shared_paths": [],
        "approved_exceptions": [],
        "risks": [],
        "gates": [],
        "reviews": [],
        "review_panels": [],
        "findings": [],
        "repairs": [],
        "delta_reviews": [],
        "testing": [],
        "runtime_qa": [],
        "attempts": {
            "deep_review_cycles": 0,
            "repair_batches": 0,
            "subdivisions": 0,
            "spawns": 0,
        },
        "integrated": False,
        "diff_ref": None,
        "status": "planned",
        "complexity": None,
        "selected_role": None,
        "selected_model": None,
        "routing_reason": None,
    }


def load_state(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise StateError(f"state file not found: {path}") from exc
    if not isinstance(data, dict):
        raise StateError("state root must be an object")
    return data


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile("w", dir=str(path.parent), delete=False) as handle:
        handle.write(payload)
        tmp_name = handle.name
    os.replace(tmp_name, path)


def validate_state(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not isinstance(data.get("revision"), int) or data.get("revision", -1) < 0:
        errors.append("revision must be a non-negative integer")
    if not data.get("feature_id"):
        errors.append("missing feature_id")
    if data.get("phase") not in PHASES:
        errors.append(f"invalid phase: {data.get('phase')}")
    if data.get("mode") is not None and data.get("mode") not in MODE_BUDGETS:
        errors.append(f"invalid mode: {data.get('mode')}")
    spec = data.get("approved_spec") or {}
    if not spec.get("path") or not spec.get("hash"):
        errors.append("approved_spec.path and approved_spec.hash are required")
    budgets = data.get("budgets") or {}
    for key in ("max_deep_review_cycles", "max_repairs_per_finding", "max_package_subdivisions"):
        if not isinstance(budgets.get(key), int) or budgets.get(key) < 0:
            errors.append(f"budgets.{key} must be a non-negative integer")
    package_ids = set()
    criteria = set(data.get("acceptance_criteria") or [])
    for package in data.get("packages", []):
        pid = package.get("package_id")
        if not pid:
            errors.append("package missing package_id")
            continue
        if pid in package_ids:
            errors.append(f"{pid}: duplicate package_id")
        package_ids.add(pid)
        for key in ("objective", "tasks", "owned_paths", "read_only_paths", "status", "attempts"):
            if key not in package:
                errors.append(f"{pid}: missing {key}")
        if not package.get("acceptance_criteria"):
            errors.append(f"{pid}: missing acceptance_criteria")
        for ac in package.get("acceptance_criteria", []):
            if criteria and ac not in criteria:
                errors.append(f"{pid}: unknown acceptance criterion {ac}")
        attempts = package.get("attempts", {})
        if attempts.get("deep_review_cycles", 0) > budgets.get("max_deep_review_cycles", 2):
            errors.append(f"{pid}: deep review budget exceeded")
        if attempts.get("subdivisions", 0) > budgets.get("max_package_subdivisions", 1):
            errors.append(f"{pid}: subdivision budget exceeded")
        if attempts.get("spawns", 0) > budgets.get("max_spawns_per_package", 12):
            errors.append(f"{pid}: spawn budget exceeded")
    current = data.get("current_package_id")
    if current is not None and current not in package_ids:
        errors.append(f"current_package_id references missing package: {current}")
    for event in data.get("history", []):
        for key in ("timestamp", "event", "from", "to", "actor", "metadata"):
            if key not in event:
                errors.append(f"history event missing {key}")
                break
    return errors


def fail_if_invalid(data: dict[str, Any]) -> None:
    errors = validate_state(data)
    if errors:
        raise StateError("; ".join(errors))


def package_by_id(data: dict[str, Any], package_id: str | None = None) -> dict[str, Any]:
    pid = package_id or data.get("current_package_id")
    if not pid:
        raise StateError("package_id is required")
    for package in data.get("packages", []):
        if package.get("package_id") == pid:
            return package
    raise StateError(f"unknown package_id: {pid}")


def task_by_id(package: dict[str, Any], task_id: str) -> dict[str, Any]:
    for task in package.get("tasks", []):
        if task.get("id") == task_id:
            return task
    raise StateError(f"{package.get('package_id')}: unknown task_id {task_id}")


def record_event(
    data: dict[str, Any],
    event: str,
    from_phase: str,
    to_phase: str,
    actor: str,
    package_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    event_id: str | None = None,
) -> bool:
    if event_id and any(item.get("event_id") == event_id for item in data.get("history", [])):
        return False
    entry = {
        "timestamp": now(),
        "event": event,
        "from": from_phase,
        "to": to_phase,
        "actor": actor,
        "package_id": package_id,
        "metadata": metadata or {},
    }
    if event_id:
        entry["event_id"] = event_id
    data.setdefault("history", []).append(entry)
    return True


def mutate(
    path: Path,
    args: argparse.Namespace,
    operation: str,
    updater,
) -> tuple[dict[str, Any], bool]:
    data = load_state(path)
    fail_if_invalid(data)
    expected = getattr(args, "expect_revision", None)
    if expected is not None and data.get("revision") != expected:
        raise StateError(f"stale revision: expected {expected}, found {data.get('revision')}")
    before = deepcopy(data)
    changed = updater(data)
    if changed:
        data["revision"] = int(data.get("revision", 0)) + 1
        data["updated_at"] = now()
        fail_if_invalid(data)
        atomic_write(path, data)
    return data, before != data


def has_open_findings(package: dict[str, Any], severities: set[str] | None = None) -> bool:
    for finding in package.get("findings", []):
        if finding.get("status", "open") in {"closed", "accepted"}:
            continue
        if severities is None or finding.get("severity") in severities:
            return True
    return False


def required_gates(package: dict[str, Any]) -> list[dict[str, Any]]:
    return [gate for gate in package.get("gates", []) if gate.get("required", True)]


def failing_required_gates(package: dict[str, Any]) -> list[str]:
    return [gate.get("name", "<unnamed>") for gate in required_gates(package) if gate.get("status") != "pass"]


def tasks_complete(package: dict[str, Any]) -> bool:
    tasks = package.get("tasks", [])
    return bool(tasks) and all(task.get("status") == "completed" for task in tasks)


def package_review_ready(package: dict[str, Any]) -> list[str]:
    errors = []
    if not tasks_complete(package):
        errors.append("tasks are not all completed")
    if failing_required_gates(package):
        errors.append("required gates are missing or failing")
    if not package.get("diff_ref"):
        errors.append("diff_ref is required")
    if not package.get("integrated"):
        errors.append("package must be integrated locally")
    return errors


def package_accept_ready(data: dict[str, Any], package: dict[str, Any], actor: str) -> list[str]:
    errors = []
    if actor in NON_ACCEPTING_ACTORS:
        errors.append(f"{actor} cannot accept packages")
    if not tasks_complete(package):
        errors.append("tasks are not all completed")
    if failing_required_gates(package):
        errors.append("required gates are missing or failing")
    if not package.get("acceptance_criteria"):
        errors.append("package has no acceptance criteria")
    if has_open_findings(package, {"critical", "high"}):
        errors.append("critical/high findings are still open")
    if has_open_findings(package, {"medium"}):
        errors.append("medium findings need closure or explicit acceptance")
    if package.get("repairs") and not package.get("delta_reviews"):
        errors.append("delta review is required after repair")
    if package.get("delta_reviews") and package["delta_reviews"][-1].get("verdict") != "pass":
        errors.append("latest delta review did not pass")
    if not package.get("reviews"):
        errors.append("package review is required")
    elif package["reviews"][-1].get("verdict") not in {"pass", "repair_required"}:
        errors.append("latest package review is blocked")
    if not package.get("testing") or package["testing"][-1].get("status") != "pass":
        errors.append("package testing must pass before acceptance")
    if not package.get("runtime_qa") or package["runtime_qa"][-1].get("status") != "pass":
        errors.append("runtime QA must pass before acceptance")
    return errors


def done_ready(data: dict[str, Any]) -> list[str]:
    errors = []
    if any(package.get("status") != "accepted" for package in data.get("packages", [])):
        errors.append("all packages must be accepted")
    required = [gate for gate in data.get("global_gates", []) if gate.get("required", True)]
    if not required:
        errors.append("at least one required global gate must be recorded")
    if any(gate.get("status") != "pass" for gate in required):
        errors.append("required global gates are missing or failing")
    if data.get("blockers"):
        errors.append("open blocker exists")
    covered = {ac for package in data.get("packages", []) for ac in package.get("acceptance_criteria", [])}
    required_criteria = set(data.get("acceptance_criteria") or [])
    if required_criteria and not required_criteria.issubset(covered):
        errors.append("not all acceptance criteria are covered by accepted packages")
    return errors


def check_transition(data: dict[str, Any], to_phase: str, package_id: str | None, actor: str) -> None:
    from_phase = data.get("phase")
    if to_phase not in LEGAL_TRANSITIONS.get(from_phase, set()):
        raise StateError(f"illegal transition: {from_phase} -> {to_phase}")
    if to_phase == "PACKAGE_REVIEW":
        errors = package_review_ready(package_by_id(data, package_id))
        if errors:
            raise StateError("cannot enter PACKAGE_REVIEW: " + "; ".join(errors))
    if to_phase == "PACKAGE_ACCEPTED":
        errors = package_accept_ready(data, package_by_id(data, package_id), actor)
        if errors:
            raise StateError("cannot accept package: " + "; ".join(errors))
    if to_phase == "PACKAGE_TESTING":
        package = package_by_id(data, package_id)
        if not package.get("reviews") or package["reviews"][-1].get("verdict") not in {"pass", "repair_required"}:
            raise StateError("cannot enter PACKAGE_TESTING: package review must be recorded first")
        if has_open_findings(package, {"critical", "high", "medium"}):
            raise StateError("cannot enter PACKAGE_TESTING: blocking findings remain open")
    if to_phase == "PACKAGE_RUNTIME_QA":
        package = package_by_id(data, package_id)
        if not package.get("testing") or package["testing"][-1].get("status") != "pass":
            raise StateError("cannot enter PACKAGE_RUNTIME_QA: package testing must pass first")
    if to_phase == "DONE":
        errors = done_ready(data)
        if errors:
            raise StateError("cannot enter DONE: " + "; ".join(errors))


def next_transition(data: dict[str, Any]) -> dict[str, Any]:
    phase = data.get("phase")
    if phase in TERMINAL:
        return {"phase": phase, "next": None, "reason": "terminal"}
    try:
        package = package_by_id(data)
    except StateError:
        package = None
    if phase == "PACKAGE_PLANNING":
        return {"phase": phase, "next": "PACKAGE_IMPLEMENTATION", "reason": "plan next coherent package"}
    if phase == "PACKAGE_IMPLEMENTATION":
        if package and tasks_complete(package):
            return {"phase": phase, "next": "PACKAGE_GATES", "reason": "all package tasks completed"}
        return {"phase": phase, "next": "PACKAGE_IMPLEMENTATION", "reason": "continue local implementation"}
    if phase == "PACKAGE_GATES":
        if package:
            errors = package_review_ready(package)
            return {"phase": phase, "next": "PACKAGE_REVIEW" if not errors else "PACKAGE_IMPLEMENTATION", "reason": "; ".join(errors) if errors else "package ready for deep review"}
    if phase == "PACKAGE_REVIEW":
        if package and package.get("reviews"):
            verdict = package["reviews"][-1].get("verdict")
            return {"phase": phase, "next": "PACKAGE_REPAIR" if verdict == "repair_required" else "PACKAGE_TESTING", "reason": f"latest review verdict={verdict}"}
        if package and package.get("review_panels") and package["review_panels"][-1].get("status") == "in_progress":
            return {"phase": phase, "next": "PACKAGE_REVIEW", "reason": "review panel in progress"}
    if phase == "PACKAGE_REPAIR":
        return {"phase": phase, "next": "DELTA_REVIEW", "reason": "repair batch recorded"}
    if phase == "DELTA_REVIEW":
        if package and package.get("delta_reviews"):
            verdict = package["delta_reviews"][-1].get("verdict")
            if package["delta_reviews"][-1].get("requires_full_review"):
                return {"phase": phase, "next": "PACKAGE_REVIEW", "reason": "delta review requires full review"}
            return {"phase": phase, "next": "PACKAGE_TESTING" if verdict == "pass" else "PACKAGE_REPAIR", "reason": f"latest delta verdict={verdict}"}
    if phase == "PACKAGE_TESTING":
        if package and package.get("testing"):
            status = package["testing"][-1].get("status")
            return {"phase": phase, "next": "PACKAGE_RUNTIME_QA" if status == "pass" else "PACKAGE_REPAIR", "reason": f"latest testing status={status}"}
        return {"phase": phase, "next": "PACKAGE_TESTING", "reason": "run regression/integration tests"}
    if phase == "PACKAGE_RUNTIME_QA":
        if package and package.get("runtime_qa"):
            status = package["runtime_qa"][-1].get("status")
            return {"phase": phase, "next": "PACKAGE_ACCEPTED" if status == "pass" else "PACKAGE_REPAIR", "reason": f"latest runtime QA status={status}"}
        return {"phase": phase, "next": "PACKAGE_RUNTIME_QA", "reason": "run app/browser QA"}
    if phase == "PACKAGE_ACCEPTED":
        if any(package.get("status") != "accepted" for package in data.get("packages", [])):
            return {"phase": phase, "next": "PACKAGE_PLANNING", "reason": "remaining packages exist"}
        return {"phase": phase, "next": "INTEGRATION", "reason": "all packages accepted"}
    if phase == "INTEGRATION":
        return {"phase": phase, "next": "DONE", "reason": "run final global gates first"}
    return {"phase": phase, "next": None, "reason": "record required event before continuing"}


def output_state(data: dict[str, Any], changed: bool = False, path: Path | None = None) -> int:
    print_json({"ok": True, "changed": changed, "state_file": str(path) if path else None, "state": data, "next": next_transition(data)})
    return 0


def state_file_arg(args: argparse.Namespace) -> Path:
    if getattr(args, "state_file", None):
        return Path(args.state_file)
    if getattr(args, "feature_id", None):
        return state_path(args.feature_id)
    raise StateError("--state-file or feature_id is required")


def cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.state_file) if args.state_file else state_path(args.feature_id)
    if path.exists() and not args.force:
        raise StateError(f"state exists: {path}")
    data = base_state(args.feature_id, args.spec_path, args.spec_hash)
    data["acceptance_criteria"] = args.ac or []
    data["mode"] = args.mode
    data["budgets"].update(MODE_BUDGETS[args.mode])
    for key in ("max_deep_review_cycles", "max_repairs_per_finding", "max_package_subdivisions", "max_spawns_per_package"):
        value = getattr(args, key)
        if value is not None:
            data["budgets"][key] = value
    record_event(data, "init", "USER_APPROVAL", "PACKAGE_PLANNING", args.actor, metadata={"spec_path": args.spec_path})
    atomic_write(path, data)
    return output_state(data, True, path)


def cmd_validate(args: argparse.Namespace) -> int:
    path = state_file_arg(args)
    data = load_state(path)
    errors = validate_state(data)
    if errors:
        print_json({"ok": False, "errors": errors, "state_file": str(path)})
        return 2
    print_json({"ok": True, "state_file": str(path), "revision": data.get("revision"), "phase": data.get("phase"), "next": next_transition(data)})
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    path = state_file_arg(args)
    data = load_state(path)
    fail_if_invalid(data)
    return output_state(data, False, path)


def cmd_next(args: argparse.Namespace) -> int:
    path = state_file_arg(args)
    data = load_state(path)
    fail_if_invalid(data)
    print_json({"ok": True, "state_file": str(path), "next": next_transition(data)})
    return 0


def cmd_transition(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        from_phase = data["phase"]
        if from_phase == args.to_phase:
            return False
        check_transition(data, args.to_phase, args.package_id, args.actor)
        data["phase"] = args.to_phase
        if args.package_id:
            data["current_package_id"] = args.package_id
            package = package_by_id(data, args.package_id)
            if args.to_phase not in {"INTEGRATION", "DONE"}:
                package["status"] = args.to_phase.lower()
        if args.to_phase in TERMINAL:
            data["final_state"] = args.to_phase
        record_event(data, "transition", from_phase, args.to_phase, args.actor, args.package_id, {"reason": args.reason}, args.event_id)
        return True

    data, changed = mutate(path, args, "transition", update)
    return output_state(data, changed, path)


def cmd_create_package(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        if data["phase"] not in {"PACKAGE_PLANNING", "PACKAGE_ACCEPTED"}:
            raise StateError(f"cannot create package from phase {data['phase']}")
        if any(package.get("package_id") == args.package_id for package in data.get("packages", [])):
            return False
        package = compact_package(args.package_id, args.objective)
        package["acceptance_criteria"] = args.ac or []
        package["dependencies"] = args.depends_on or []
        package["owned_paths"] = args.owned_path or []
        package["read_only_paths"] = args.read_only_path or []
        package["shared_paths"] = args.shared_path or []
        package["risks"] = args.risk or []
        package["complexity"] = args.complexity
        package["selected_role"] = args.selected_role
        package["selected_model"] = args.selected_model
        package["routing_reason"] = args.routing_reason
        for task_id in args.task or []:
            package["tasks"].append({"id": task_id, "status": "planned", "local_validations": [], "blockers": []})
        if len(package["tasks"]) < 2 and package["complexity"] != "small":
            raise StateError("normal packages must contain multiple tasks; mark complexity=small for tiny scoped packages")
        data.setdefault("packages", []).append(package)
        data["current_package_id"] = args.package_id
        if data["phase"] == "PACKAGE_ACCEPTED":
            data["phase"] = "PACKAGE_PLANNING"
        record_event(data, "create-package", data["phase"], data["phase"], args.actor, args.package_id, {"tasks": args.task or []}, args.event_id)
        return True

    data, changed = mutate(path, args, "create-package", update)
    return output_state(data, changed, path)


def cmd_update_package(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        package = package_by_id(data, args.package_id)
        before = deepcopy(package)
        if args.integrated is not None:
            package["integrated"] = parse_bool(args.integrated)
        if args.diff_ref:
            package["diff_ref"] = args.diff_ref
        if args.complexity:
            package["complexity"] = args.complexity
        if args.selected_role:
            package["selected_role"] = args.selected_role
        if args.selected_model:
            package["selected_model"] = args.selected_model
        if args.routing_reason:
            package["routing_reason"] = args.routing_reason
        for exception in args.exception or []:
            item = parse_json_object(exception)
            if not item.get("path") or item.get("status") != "approved":
                raise StateError("exception requires path and status=approved")
            if item not in package["approved_exceptions"]:
                package["approved_exceptions"].append(item)
        if before != package:
            record_event(data, "update-package", data["phase"], data["phase"], args.actor, args.package_id, {}, args.event_id)
            return True
        return False

    data, changed = mutate(path, args, "update-package", update)
    return output_state(data, changed, path)


def cmd_start_task(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        if data["phase"] != "PACKAGE_IMPLEMENTATION":
            raise StateError(f"cannot start task from phase {data['phase']}")
        task = task_by_id(package_by_id(data, args.package_id), args.task_id)
        if task.get("status") == "in_progress":
            return False
        if task.get("status") == "completed":
            return False
        task["status"] = "in_progress"
        record_event(data, "start-task", data["phase"], data["phase"], args.actor, args.package_id, {"task_id": args.task_id}, args.event_id)
        return True

    data, changed = mutate(path, args, "start-task", update)
    return output_state(data, changed, path)


def cmd_complete_task(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        if data["phase"] != "PACKAGE_IMPLEMENTATION":
            raise StateError(f"cannot complete task from phase {data['phase']}")
        task = task_by_id(package_by_id(data, args.package_id), args.task_id)
        validations = args.validation or []
        if not validations:
            raise StateError("complete-task requires at least one local validation")
        if task.get("status") == "completed" and set(validations).issubset(set(task.get("local_validations", []))):
            return False
        task["status"] = "completed"
        task.setdefault("local_validations", [])
        for validation in validations:
            if validation not in task["local_validations"]:
                task["local_validations"].append(validation)
        record_event(data, "complete-task", data["phase"], data["phase"], args.actor, args.package_id, {"task_id": args.task_id, "validations": validations}, args.event_id)
        return True

    data, changed = mutate(path, args, "complete-task", update)
    return output_state(data, changed, path)


def cmd_fail_task(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        task = task_by_id(package_by_id(data, args.package_id), args.task_id)
        task["status"] = "blocked"
        task.setdefault("blockers", []).append({"reason": args.reason, "at": now()})
        data["phase"] = "BLOCKED"
        data["final_state"] = "BLOCKED"
        data.setdefault("blockers", []).append({"package_id": args.package_id, "task_id": args.task_id, "reason": args.reason, "at": now()})
        record_event(data, "fail-task", data["phase"], "BLOCKED", args.actor, args.package_id, {"task_id": args.task_id, "reason": args.reason}, args.event_id)
        return True

    data, changed = mutate(path, args, "fail-task", update)
    return output_state(data, changed, path)


def cmd_record_gate(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        target = data.setdefault("global_gates", []) if args.global_gate else package_by_id(data, args.package_id).setdefault("gates", [])
        gate = {"name": args.name, "status": args.status, "required": not args.optional, "evidence": args.evidence, "at": now()}
        for index, existing in enumerate(target):
            if existing.get("name") == args.name:
                if existing == gate:
                    return False
                target[index] = gate
                break
        else:
            target.append(gate)
        if not args.global_gate and data["phase"] == "PACKAGE_GATES" and args.status == "fail":
            package = package_by_id(data, args.package_id)
            attempts = package.setdefault("attempts", {})
            attempts["gate_failures"] = attempts.get("gate_failures", 0) + 1
        record_event(data, "record-gate", data["phase"], data["phase"], args.actor, args.package_id, {"name": args.name, "status": args.status, "global": args.global_gate}, args.event_id)
        return True

    data, changed = mutate(path, args, "record-gate", update)
    return output_state(data, changed, path)


def normalize_findings(raw_findings: list[str]) -> list[dict[str, Any]]:
    findings = []
    for raw in raw_findings:
        finding = parse_json_object(raw)
        if not finding.get("id") or finding.get("severity") not in {"critical", "high", "medium", "low"}:
            raise StateError("finding requires id and severity critical|high|medium|low")
        finding.setdefault("status", "open")
        findings.append(finding)
    return findings


def cmd_record_spawn(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        if data["phase"] in TERMINAL:
            raise StateError(f"cannot record spawn from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        attempts = package.setdefault("attempts", {})
        budget = data.get("budgets", {}).get("max_spawns_per_package", 12)
        if attempts.get("spawns", 0) >= budget:
            return block_with_reason(data, args.actor, args.package_id, "spawn budget exhausted")
        attempts["spawns"] = attempts.get("spawns", 0) + 1
        record_event(
            data,
            "record-spawn",
            data["phase"],
            data["phase"],
            args.actor,
            args.package_id,
            {"role": args.role, "purpose": args.purpose, "spawns": attempts["spawns"]},
            args.event_id,
        )
        return True

    data, changed = mutate(path, args, "record-spawn", update)
    return output_state(data, changed, path)


def cmd_record_review(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        if data["phase"] != "PACKAGE_REVIEW":
            raise StateError(f"cannot record package review from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        errors = package_review_ready(package)
        if errors:
            raise StateError("cannot record package review: " + "; ".join(errors))
        attempts = package.setdefault("attempts", {})
        if attempts.get("deep_review_cycles", 0) >= data["budgets"]["max_deep_review_cycles"]:
            return block_with_reason(data, args.actor, args.package_id, "deep review budget exhausted")
        findings = normalize_findings(args.finding or [])
        review = {"verdict": args.verdict, "findings": [item["id"] for item in findings], "at": now(), "evidence": args.evidence}
        package.setdefault("reviews", []).append(review)
        attempts["deep_review_cycles"] = attempts.get("deep_review_cycles", 0) + 1
        data["metrics"]["package_reviews"] += 1
        for finding in findings:
            existing = next((item for item in package["findings"] if item.get("id") == finding["id"]), None)
            if existing:
                existing.update(finding)
            else:
                package["findings"].append(finding)
        if args.verdict == "repair_required":
            data["phase"] = "PACKAGE_REPAIR"
            package["status"] = "repair_required"
        elif args.verdict == "pass":
            data["phase"] = "PACKAGE_TESTING"
            package["status"] = "testing_required"
        else:
            return block_with_reason(data, args.actor, args.package_id, args.evidence or "package review blocked")
        record_event(data, "record-review", "PACKAGE_REVIEW", data["phase"], args.actor, args.package_id, {"verdict": args.verdict, "finding_count": len(findings)}, args.event_id)
        return True

    data, changed = mutate(path, args, "record-review", update)
    return output_state(data, changed, path)


def cmd_start_review_panel(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        if data["phase"] != "PACKAGE_REVIEW":
            raise StateError(f"cannot start review panel from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        errors = package_review_ready(package)
        if errors:
            raise StateError("cannot start review panel: " + "; ".join(errors))
        attempts = package.setdefault("attempts", {})
        if attempts.get("deep_review_cycles", 0) >= data["budgets"]["max_deep_review_cycles"]:
            return block_with_reason(data, args.actor, args.package_id, "deep review budget exhausted")
        panel_id = args.panel_id or f"RP-{attempts.get('deep_review_cycles', 0) + 1:02d}"
        if any(panel.get("panel_id") == panel_id for panel in package.get("review_panels", [])):
            return False
        panel = {
            "panel_id": panel_id,
            "status": "in_progress",
            "roles": args.role or ["package-reviewer"],
            "subreviews": [],
            "started_at": now(),
            "completed_at": None,
        }
        package.setdefault("review_panels", []).append(panel)
        attempts["deep_review_cycles"] = attempts.get("deep_review_cycles", 0) + 1
        data["metrics"]["package_reviews"] += 1
        record_event(data, "start-review-panel", "PACKAGE_REVIEW", "PACKAGE_REVIEW", args.actor, args.package_id, {"panel_id": panel_id, "roles": panel["roles"]}, args.event_id)
        return True

    data, changed = mutate(path, args, "start-review-panel", update)
    return output_state(data, changed, path)


def cmd_record_subreview(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        if data["phase"] != "PACKAGE_REVIEW":
            raise StateError(f"cannot record subreview from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        panel = next((item for item in reversed(package.get("review_panels", [])) if item.get("status") == "in_progress"), None)
        if not panel:
            raise StateError("no active review panel")
        if args.role not in panel.get("roles", []):
            raise StateError(f"role {args.role} is not part of active review panel")
        if any(item.get("role") == args.role for item in panel.get("subreviews", [])):
            return False
        findings = normalize_findings(args.finding or [])
        for finding in findings:
            finding.setdefault("source_role", args.role)
        panel["subreviews"].append({
            "role": args.role,
            "verdict": args.verdict,
            "findings": [item["id"] for item in findings],
            "evidence": args.evidence,
            "at": now(),
        })
        for finding in findings:
            existing = next((item for item in package["findings"] if item.get("id") == finding["id"]), None)
            if existing:
                existing.update(finding)
            else:
                package["findings"].append(finding)
        record_event(data, "record-subreview", "PACKAGE_REVIEW", "PACKAGE_REVIEW", args.actor, args.package_id, {"role": args.role, "verdict": args.verdict, "finding_count": len(findings)}, args.event_id)
        return True

    data, changed = mutate(path, args, "record-subreview", update)
    return output_state(data, changed, path)


def cmd_finalize_review_panel(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        if data["phase"] != "PACKAGE_REVIEW":
            raise StateError(f"cannot finalize review panel from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        panel = next((item for item in reversed(package.get("review_panels", [])) if item.get("status") == "in_progress"), None)
        if not panel:
            raise StateError("no active review panel")
        missing = [role for role in panel.get("roles", []) if not any(item.get("role") == role for item in panel.get("subreviews", []))]
        if missing and not args.allow_missing:
            raise StateError("missing subreviews: " + ", ".join(missing))
        panel["status"] = "completed"
        panel["completed_at"] = now()
        panel["verdict"] = args.verdict
        panel_findings = [finding.get("id") for finding in package.get("findings", []) if finding.get("status", "open") != "closed"]
        package.setdefault("reviews", []).append({
            "verdict": args.verdict,
            "findings": panel_findings,
            "panel_id": panel.get("panel_id"),
            "at": now(),
            "evidence": args.evidence,
        })
        if args.verdict == "repair_required":
            data["phase"] = "PACKAGE_REPAIR"
            package["status"] = "repair_required"
        elif args.verdict == "pass":
            if has_open_findings(package, {"critical", "high", "medium"}):
                raise StateError("cannot pass review panel with blocking findings open")
            data["phase"] = "PACKAGE_TESTING"
            package["status"] = "testing_required"
        else:
            return block_with_reason(data, args.actor, args.package_id, args.evidence or "review panel blocked")
        record_event(data, "finalize-review-panel", "PACKAGE_REVIEW", data["phase"], args.actor, args.package_id, {"panel_id": panel.get("panel_id"), "verdict": args.verdict}, args.event_id)
        return True

    data, changed = mutate(path, args, "finalize-review-panel", update)
    return output_state(data, changed, path)


def block_with_reason(data: dict[str, Any], actor: str, package_id: str | None, reason: str) -> bool:
    from_phase = data["phase"]
    data["phase"] = "BLOCKED"
    data["final_state"] = "BLOCKED"
    data.setdefault("blockers", []).append({"package_id": package_id, "reason": reason, "at": now()})
    record_event(data, "block", from_phase, "BLOCKED", actor, package_id, {"reason": reason})
    return True


def cmd_record_repair(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        if data["phase"] != "PACKAGE_REPAIR":
            raise StateError(f"cannot record repair from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        attempts = package.setdefault("attempts", {})
        ids = args.finding_id or []
        for finding_id in ids:
            finding = next((item for item in package.get("findings", []) if item.get("id") == finding_id), None)
            if not finding:
                raise StateError(f"unknown finding: {finding_id}")
            finding["repair_attempts"] = finding.get("repair_attempts", 0) + 1
            if finding["repair_attempts"] > data["budgets"]["max_repairs_per_finding"]:
                return block_with_reason(data, args.actor, args.package_id, f"repair budget exhausted for {finding_id}")
            finding["status"] = "closed"
        repair = {"finding_ids": ids, "changed_files": args.changed_file or [], "verification": args.verification or [], "at": now()}
        package.setdefault("repairs", []).append(repair)
        attempts["repair_batches"] = attempts.get("repair_batches", 0) + 1
        data["metrics"]["repair_batches"] += 1
        data["phase"] = "DELTA_REVIEW"
        package["status"] = "delta_review_required"
        record_event(data, "record-repair", "PACKAGE_REPAIR", "DELTA_REVIEW", args.actor, args.package_id, {"finding_ids": ids}, args.event_id)
        return True

    data, changed = mutate(path, args, "record-repair", update)
    return output_state(data, changed, path)


def cmd_record_delta_review(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        if data["phase"] != "DELTA_REVIEW":
            raise StateError(f"cannot record delta review from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        new_findings = normalize_findings(args.new_finding or [])
        for finding_id in args.closed_finding or []:
            finding = next((item for item in package.get("findings", []) if item.get("id") == finding_id), None)
            if finding:
                finding["status"] = "closed"
        for finding in new_findings:
            package.setdefault("findings", []).append(finding)
        requires_full = bool(args.requires_full_review)
        review = {
            "verdict": args.verdict,
            "closed_findings": args.closed_finding or [],
            "new_or_reopened_findings": [item["id"] for item in new_findings],
            "requires_full_review": requires_full,
            "reason": args.reason,
            "at": now(),
        }
        package.setdefault("delta_reviews", []).append(review)
        data["metrics"]["delta_reviews"] += 1
        if args.verdict == "pass":
            if has_open_findings(package, {"critical", "high", "medium"}):
                raise StateError("cannot pass delta review with blocking findings open")
            package["status"] = "delta_passed"
            data["phase"] = "PACKAGE_TESTING"
        elif requires_full:
            attempts = package.setdefault("attempts", {})
            if attempts.get("deep_review_cycles", 0) >= data["budgets"]["max_deep_review_cycles"]:
                return block_with_reason(data, args.actor, args.package_id, "deep review budget exhausted before full re-review")
            data["phase"] = "PACKAGE_REVIEW"
            package["status"] = "full_review_required"
        elif args.verdict == "repair_required":
            data["phase"] = "PACKAGE_REPAIR"
            package["status"] = "repair_required"
        else:
            return block_with_reason(data, args.actor, args.package_id, args.reason or "delta review blocked")
        record_event(data, "record-delta-review", "DELTA_REVIEW", data["phase"], args.actor, args.package_id, {"verdict": args.verdict, "requires_full_review": requires_full}, args.event_id)
        return True

    data, changed = mutate(path, args, "record-delta-review", update)
    return output_state(data, changed, path)


def cmd_record_testing(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        if data["phase"] != "PACKAGE_TESTING":
            raise StateError(f"cannot record testing from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        result = {
            "status": args.status,
            "commands": args.command or [],
            "evidence": args.evidence,
            "at": now(),
        }
        package.setdefault("testing", []).append(result)
        if args.status == "pass":
            data["phase"] = "PACKAGE_RUNTIME_QA"
            package["status"] = "runtime_qa_required"
        elif args.status == "fail":
            data["phase"] = "PACKAGE_REPAIR"
            package["status"] = "repair_required"
        else:
            return block_with_reason(data, args.actor, args.package_id, args.evidence or "package testing blocked")
        record_event(data, "record-testing", "PACKAGE_TESTING", data["phase"], args.actor, args.package_id, {"status": args.status, "commands": args.command or []}, args.event_id)
        return True

    data, changed = mutate(path, args, "record-testing", update)
    return output_state(data, changed, path)


def cmd_record_runtime_qa(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        if data["phase"] != "PACKAGE_RUNTIME_QA":
            raise StateError(f"cannot record runtime QA from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        result = {
            "status": args.status,
            "url": args.url,
            "browser": args.browser,
            "screenshots": args.screenshot or [],
            "checks": args.check or [],
            "evidence": args.evidence,
            "at": now(),
        }
        package.setdefault("runtime_qa", []).append(result)
        if args.status == "pass":
            package["status"] = "runtime_qa_passed"
        elif args.status == "fail":
            data["phase"] = "PACKAGE_REPAIR"
            package["status"] = "repair_required"
        else:
            return block_with_reason(data, args.actor, args.package_id, args.evidence or "runtime QA blocked")
        record_event(data, "record-runtime-qa", "PACKAGE_RUNTIME_QA", data["phase"], args.actor, args.package_id, {"status": args.status, "url": args.url}, args.event_id)
        return True

    data, changed = mutate(path, args, "record-runtime-qa", update)
    return output_state(data, changed, path)


def cmd_accept_package(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        if data["phase"] != "PACKAGE_RUNTIME_QA":
            raise StateError(f"cannot accept package from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        errors = package_accept_ready(data, package, args.actor)
        if errors:
            raise StateError("cannot accept package: " + "; ".join(errors))
        package["status"] = "accepted"
        data["phase"] = "PACKAGE_ACCEPTED"
        data["current_package_id"] = args.package_id
        record_event(data, "accept-package", "PACKAGE_RUNTIME_QA", "PACKAGE_ACCEPTED", args.actor, args.package_id, {}, args.event_id)
        return True

    data, changed = mutate(path, args, "accept-package", update)
    return output_state(data, changed, path)


def cmd_block(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        return block_with_reason(data, args.actor, args.package_id, args.reason)

    data, changed = mutate(path, args, "block", update)
    return output_state(data, changed, path)


def cmd_resume(args: argparse.Namespace) -> int:
    return cmd_next(args)


def run_dry_workflow(feature_id: str) -> dict[str, Any]:
    data = base_state(feature_id, "docs/specs/example/spec.md", "dry-run")
    data["acceptance_criteria"] = ["AC-1", "AC-2", "AC-3"]

    def direct(event: str, from_phase: str, to_phase: str, actor: str, package_id: str | None = None, metadata: dict[str, Any] | None = None) -> None:
        if data["phase"] != from_phase:
            raise StateError(f"dry-run expected {from_phase}, found {data['phase']}")
        check_transition(data, to_phase, package_id, actor)
        data["phase"] = to_phase
        record_event(data, event, from_phase, to_phase, actor, package_id, metadata)

    package = compact_package("PKG-01", "Deliver one observable vertical slice")
    package.update({
        "acceptance_criteria": ["AC-1", "AC-2", "AC-3"],
        "tasks": [
            {"id": "T-001", "status": "planned", "local_validations": [], "blockers": []},
            {"id": "T-002", "status": "planned", "local_validations": [], "blockers": []},
            {"id": "T-003", "status": "planned", "local_validations": [], "blockers": []},
        ],
        "owned_paths": ["src/**", "tests/**"],
        "complexity": "medium",
        "selected_role": "implementer",
        "selected_model": "terra",
        "routing_reason": "three related tasks across implementation and tests",
    })
    data["packages"].append(package)
    data["current_package_id"] = "PKG-01"
    record_event(data, "create-package", "PACKAGE_PLANNING", "PACKAGE_PLANNING", "package-planner", "PKG-01")
    direct("transition", "PACKAGE_PLANNING", "PACKAGE_IMPLEMENTATION", "orchestrator", "PKG-01")
    for task in package["tasks"]:
        task["status"] = "completed"
        task["local_validations"] = ["typecheck", "lint", "focused-unit-test"]
        record_event(data, "complete-task", "PACKAGE_IMPLEMENTATION", "PACKAGE_IMPLEMENTATION", "implementer", "PKG-01", {"task_id": task["id"]})
    direct("transition", "PACKAGE_IMPLEMENTATION", "PACKAGE_GATES", "orchestrator", "PKG-01")
    package["integrated"] = True
    package["diff_ref"] = "dry-run-diff"
    package["gates"].append({"name": "package verify", "status": "pass", "required": True, "evidence": "dry-run", "at": now()})
    direct("transition", "PACKAGE_GATES", "PACKAGE_REVIEW", "orchestrator", "PKG-01")
    package["reviews"].append({"verdict": "repair_required", "findings": ["F-001", "F-002"], "at": now(), "evidence": "dry-run consolidated review"})
    package["findings"] = [
        {"id": "F-001", "severity": "high", "category": "correctness", "status": "open"},
        {"id": "F-002", "severity": "medium", "category": "testing", "status": "open"},
    ]
    package["attempts"]["deep_review_cycles"] = 1
    data["metrics"]["package_reviews"] = 1
    data["phase"] = "PACKAGE_REPAIR"
    record_event(data, "record-review", "PACKAGE_REVIEW", "PACKAGE_REPAIR", "package-reviewer", "PKG-01", {"finding_count": 2})
    for finding in package["findings"]:
        finding["status"] = "closed"
        finding["repair_attempts"] = 1
    package["repairs"].append({"finding_ids": ["F-001", "F-002"], "changed_files": ["src/example.py"], "verification": ["focused-unit-test"], "at": now()})
    package["attempts"]["repair_batches"] = 1
    data["metrics"]["repair_batches"] = 1
    data["phase"] = "DELTA_REVIEW"
    record_event(data, "record-repair", "PACKAGE_REPAIR", "DELTA_REVIEW", "repair-agent", "PKG-01", {"finding_ids": ["F-001", "F-002"]})
    package["delta_reviews"].append({"verdict": "pass", "closed_findings": ["F-001", "F-002"], "new_or_reopened_findings": [], "requires_full_review": False, "reason": "dry-run", "at": now()})
    data["metrics"]["delta_reviews"] = 1
    data["phase"] = "PACKAGE_TESTING"
    record_event(data, "record-delta-review", "DELTA_REVIEW", "PACKAGE_TESTING", "delta-reviewer", "PKG-01", {"verdict": "pass"})
    package["testing"].append({"status": "pass", "commands": ["verify", "integration"], "evidence": "dry-run tests", "at": now()})
    data["phase"] = "PACKAGE_RUNTIME_QA"
    record_event(data, "record-testing", "PACKAGE_TESTING", "PACKAGE_RUNTIME_QA", "gate-runner", "PKG-01", {"status": "pass"})
    package["runtime_qa"].append({
        "status": "pass",
        "url": "http://localhost:3000",
        "browser": "playwright",
        "screenshots": ["dry-run-home.png"],
        "checks": ["flow renders", "save works", "no visible secret"],
        "evidence": "dry-run browser QA",
        "at": now(),
    })
    record_event(data, "record-runtime-qa", "PACKAGE_RUNTIME_QA", "PACKAGE_RUNTIME_QA", "runtime-verifier", "PKG-01", {"status": "pass"})
    errors = package_accept_ready(data, package, "orchestrator")
    if errors:
        raise StateError("; ".join(errors))
    package["status"] = "accepted"
    data["phase"] = "PACKAGE_ACCEPTED"
    record_event(data, "accept-package", "PACKAGE_RUNTIME_QA", "PACKAGE_ACCEPTED", "orchestrator", "PKG-01")
    direct("transition", "PACKAGE_ACCEPTED", "INTEGRATION", "orchestrator", "PKG-01")
    data["global_gates"].append({"name": "global verify", "status": "pass", "required": True, "evidence": "dry-run", "at": now()})
    direct("transition", "INTEGRATION", "DONE", "orchestrator", "PKG-01")
    data["final_state"] = "DONE"
    fail_if_invalid(data)
    return data


def cmd_dry_run(args: argparse.Namespace) -> int:
    data = run_dry_workflow(args.feature_id)
    evidence = {
        "deep_reviews_per_task": data["metrics"]["task_deep_reviews"],
        "package_reviews": data["metrics"]["package_reviews"],
        "repair_batches": data["metrics"]["repair_batches"],
        "delta_reviews": data["metrics"]["delta_reviews"],
        "testing_runs": len(data["packages"][0]["testing"]),
        "runtime_qa_runs": len(data["packages"][0]["runtime_qa"]),
        "human_questions_after_approval": data["metrics"]["human_questions_after_approval"],
        "final_state": data["phase"],
    }
    print_json({"ok": True, "evidence": evidence, "state": data})
    print("DRY_RUN_PASS")
    return 0


def add_common_state_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--state-file")
    parser.add_argument("--expect-revision", type=int)
    parser.add_argument("--actor", default="orchestrator")
    parser.add_argument("--event-id")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("feature_id")
    init.add_argument("spec_path")
    init.add_argument("spec_hash")
    init.add_argument("--state-file")
    init.add_argument("--force", action="store_true")
    init.add_argument("--actor", default="orchestrator")
    init.add_argument("--ac", action="append")
    init.add_argument("--max-deep-review-cycles", type=int)
    init.add_argument("--max-repairs-per-finding", type=int)
    init.add_argument("--max-package-subdivisions", type=int)
    init.add_argument("--max-spawns-per-package", type=int)
    init.add_argument("--mode", choices=sorted(MODE_BUDGETS), default="feature")
    init.set_defaults(func=cmd_init)

    for name, func in (("status", cmd_status), ("next", cmd_next), ("resume", cmd_resume), ("validate", cmd_validate)):
        item = sub.add_parser(name)
        item.add_argument("feature_id", nargs="?")
        item.add_argument("--state-file")
        item.set_defaults(func=func)

    transition = sub.add_parser("transition")
    add_common_state_args(transition)
    transition.add_argument("to_phase")
    transition.add_argument("--feature-id")
    transition.add_argument("--package-id")
    transition.add_argument("--reason", default="")
    transition.set_defaults(func=cmd_transition)

    create = sub.add_parser("create-package")
    add_common_state_args(create)
    create.add_argument("package_id")
    create.add_argument("objective")
    create.add_argument("--feature-id")
    create.add_argument("--ac", action="append")
    create.add_argument("--task", action="append")
    create.add_argument("--depends-on", action="append")
    create.add_argument("--owned-path", action="append")
    create.add_argument("--read-only-path", action="append")
    create.add_argument("--shared-path", action="append")
    create.add_argument("--risk", action="append")
    create.add_argument("--complexity", choices=["small", "medium", "high"])
    create.add_argument("--selected-role")
    create.add_argument("--selected-model")
    create.add_argument("--routing-reason")
    create.set_defaults(func=cmd_create_package)

    update = sub.add_parser("update-package")
    add_common_state_args(update)
    update.add_argument("package_id")
    update.add_argument("--feature-id")
    update.add_argument("--integrated")
    update.add_argument("--diff-ref")
    update.add_argument("--complexity", choices=["small", "medium", "high"])
    update.add_argument("--selected-role")
    update.add_argument("--selected-model")
    update.add_argument("--routing-reason")
    update.add_argument("--exception", action="append")
    update.set_defaults(func=cmd_update_package)

    for name, func in (("start-task", cmd_start_task), ("complete-task", cmd_complete_task), ("fail-task", cmd_fail_task)):
        item = sub.add_parser(name)
        add_common_state_args(item)
        item.add_argument("package_id")
        item.add_argument("task_id")
        item.add_argument("--feature-id")
        if name == "complete-task":
            item.add_argument("--validation", action="append")
        if name == "fail-task":
            item.add_argument("--reason", required=True)
        item.set_defaults(func=func)

    gate = sub.add_parser("record-gate")
    add_common_state_args(gate)
    gate.add_argument("name")
    gate.add_argument("status", choices=["pass", "fail", "blocked"])
    gate.add_argument("--feature-id")
    gate.add_argument("--package-id")
    gate.add_argument("--global-gate", action="store_true")
    gate.add_argument("--optional", action="store_true")
    gate.add_argument("--evidence", default="")
    gate.set_defaults(func=cmd_record_gate)

    spawn = sub.add_parser("record-spawn")
    add_common_state_args(spawn)
    spawn.add_argument("package_id")
    spawn.add_argument("role")
    spawn.add_argument("--feature-id")
    spawn.add_argument("--purpose", default="")
    spawn.set_defaults(func=cmd_record_spawn)

    review = sub.add_parser("record-review")
    add_common_state_args(review)
    review.add_argument("package_id")
    review.add_argument("verdict", choices=["pass", "repair_required", "blocked"])
    review.add_argument("--feature-id")
    review.add_argument("--finding", action="append")
    review.add_argument("--evidence", default="")
    review.set_defaults(func=cmd_record_review)

    panel = sub.add_parser("start-review-panel")
    add_common_state_args(panel)
    panel.add_argument("package_id")
    panel.add_argument("--feature-id")
    panel.add_argument("--panel-id")
    panel.add_argument("--role", action="append")
    panel.set_defaults(func=cmd_start_review_panel)

    subreview = sub.add_parser("record-subreview")
    add_common_state_args(subreview)
    subreview.add_argument("package_id")
    subreview.add_argument("role")
    subreview.add_argument("verdict", choices=["pass", "repair_required", "blocked"])
    subreview.add_argument("--feature-id")
    subreview.add_argument("--finding", action="append")
    subreview.add_argument("--evidence", default="")
    subreview.set_defaults(func=cmd_record_subreview)

    finalize = sub.add_parser("finalize-review-panel")
    add_common_state_args(finalize)
    finalize.add_argument("package_id")
    finalize.add_argument("verdict", choices=["pass", "repair_required", "blocked"])
    finalize.add_argument("--feature-id")
    finalize.add_argument("--allow-missing", action="store_true")
    finalize.add_argument("--evidence", default="")
    finalize.set_defaults(func=cmd_finalize_review_panel)

    repair = sub.add_parser("record-repair")
    add_common_state_args(repair)
    repair.add_argument("package_id")
    repair.add_argument("--feature-id")
    repair.add_argument("--finding-id", action="append")
    repair.add_argument("--changed-file", action="append")
    repair.add_argument("--verification", action="append")
    repair.set_defaults(func=cmd_record_repair)

    delta = sub.add_parser("record-delta-review")
    add_common_state_args(delta)
    delta.add_argument("package_id")
    delta.add_argument("verdict", choices=["pass", "repair_required", "blocked"])
    delta.add_argument("--feature-id")
    delta.add_argument("--closed-finding", action="append")
    delta.add_argument("--new-finding", action="append")
    delta.add_argument("--requires-full-review", action="store_true")
    delta.add_argument("--reason", default="")
    delta.set_defaults(func=cmd_record_delta_review)

    testing = sub.add_parser("record-testing")
    add_common_state_args(testing)
    testing.add_argument("package_id")
    testing.add_argument("status", choices=["pass", "fail", "blocked"])
    testing.add_argument("--feature-id")
    testing.add_argument("--command", action="append")
    testing.add_argument("--evidence", default="")
    testing.set_defaults(func=cmd_record_testing)

    runtime = sub.add_parser("record-runtime-qa")
    add_common_state_args(runtime)
    runtime.add_argument("package_id")
    runtime.add_argument("status", choices=["pass", "fail", "blocked"])
    runtime.add_argument("--feature-id")
    runtime.add_argument("--url", default="")
    runtime.add_argument("--browser", default="")
    runtime.add_argument("--screenshot", action="append")
    runtime.add_argument("--check", action="append")
    runtime.add_argument("--evidence", default="")
    runtime.set_defaults(func=cmd_record_runtime_qa)

    accept = sub.add_parser("accept-package")
    add_common_state_args(accept)
    accept.add_argument("package_id")
    accept.add_argument("--feature-id")
    accept.set_defaults(func=cmd_accept_package)

    block = sub.add_parser("block")
    add_common_state_args(block)
    block.add_argument("reason")
    block.add_argument("--feature-id")
    block.add_argument("--package-id")
    block.set_defaults(func=cmd_block)

    dry = sub.add_parser("dry-run")
    dry.add_argument("feature_id")
    dry.set_defaults(func=cmd_dry_run)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except (OSError, json.JSONDecodeError, StateError) as exc:
        print_json({"ok": False, "error": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
