#!/usr/bin/env python3
"""Executable package-workflow state machine.

The state file is compact, atomic, and deterministic. It is intentionally not a
conversation log: agents record decisions, gates, findings, repairs, and a small
event history that lets the orchestrator resume without re-running prior steps.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
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
    "PACKAGE_REPAIR": {"DELTA_REVIEW", "PACKAGE_TESTING", "BLOCKED"},
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
    "extend-review-panel",
    "record-late-review",
    "record-verification",
    "record-repair",
    "record-delta-review",
    "record-testing",
    "record-runtime-qa",
    "accept-package",
    "block",
    "reopen",
}
NON_ACCEPTING_ACTORS = {"implementer", "frontend-engineer", "refactor-specialist", "repair-agent"}
# Refuting retires a blocking finding with no code change: it is an authorization verb,
# not bookkeeping, so it needs its own actor gate.  Enforcing separation of duties one
# step downstream of the verb that defeats the gate is not enforcement.  `upheld`
# verdicts and the cost waiver stay open to the coordinator; only refutation is closed.
REFUTING_ACTORS = {"finding-verifier"}
# Physical budgets per triage mode: ceremony must be proportional to risk, not to diff size.
# Every reader of `max_verifications_per_package` must default to the SAME number: the key
# is optional (state files predate it), so a mismatch means the command authorises a pass
# that `validate_state` then rejects — an ungoverned StateError instead of a recorded
# blocker, which is the failure shape this budget exists to prevent.
DEFAULT_MAX_VERIFICATIONS = 6
# `max_verifications_per_package` is a runaway backstop, NOT the anti-retry control —
# that is `verified_verdict` stickiness, which makes an `upheld` finding unjudgeable a
# second time.  It must therefore be dimensioned against the flows the other budgets
# already allow: each review cycle can produce a repair round, each delta review can
# reopen one with new findings that now REQUIRE a verdict before repair, and one pass may
# legitimately be split across two calls.  Sized below `max_deep_review_cycles` it would
# BLOCK a package that is inside every other budget.
MODE_BUDGETS = {
    "feature": {"max_spawns_per_package": 12, "max_deep_review_cycles": 2, "max_gate_failures_per_package": 3, "max_verifications_per_package": 6},
    "scoped": {"max_spawns_per_package": 8, "max_deep_review_cycles": 2, "max_gate_failures_per_package": 3, "max_verifications_per_package": 6},
    "quick-fix": {"max_spawns_per_package": 4, "max_deep_review_cycles": 1, "max_gate_failures_per_package": 2, "max_verifications_per_package": 3},
    "incident": {"max_spawns_per_package": 6, "max_deep_review_cycles": 1, "max_gate_failures_per_package": 2, "max_verifications_per_package": 3},
}
# --no-render: high-frequency intra-phase writes (record-spawn, log-narrative)
# defer STATUS/bitacora/notes regeneration; sync-notes consolidates later.
RENDER_SKIP = False


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
            "max_gate_failures_per_package": 3,
            "max_verifications_per_package": DEFAULT_MAX_VERIFICATIONS,
        },
        "metrics": {
            "task_deep_reviews": 0,
            "package_reviews": 0,
            "repair_batches": 0,
            "verifications": 0,
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
        # Deliberately not merged into `reviews`: that list is read both as a verdict and
        # as the proof a deep review happened at all, so a late entry there would let the
        # exception channel stand in for the panel it is an exception to.  Every read of
        # this key uses .get(): nine state files on disk predate it.
        "late_reviews": [],
        "findings": [],
        "verifications": [],
        "repairs": [],
        "delta_reviews": [],
        "testing": [],
        "runtime_qa": [],
        # AC-01 (010-spawn-provenance): purely additive, same precedent this file already
        # documents for `late_reviews` above -- every reader uses `.get()`, no backfill for
        # the packages that predate this key.
        "spawns": [],
        "attempts": {
            "deep_review_cycles": 0,
            "repair_batches": 0,
            "verifications": 0,
            "verification_waivers": 0,
            "subdivisions": 0,
            "spawns": 0,
        },
        "integrated": False,
        "diff_ref": None,
        "runtime_surface": True,
        "status": "planned",
        "complexity": None,
        "selected_role": None,
        "selected_model": None,
        "routing_reason": None,
        "context_pack": None,
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
        if attempts.get("gate_failures", 0) > budgets.get("max_gate_failures_per_package", 3):
            errors.append(f"{pid}: gate failure budget exceeded")
        finding_ids = [f.get("id") for f in package.get("findings", []) if isinstance(f, dict)]
        duplicates = {fid for fid in finding_ids if fid and finding_ids.count(fid) > 1}
        if duplicates:
            # Every finding lookup is first-match, so a duplicate is invisible to every
            # command and visible only to has_open_findings: the package deadlocks.
            errors.append(f"{pid}: duplicate finding ids: {', '.join(sorted(duplicates))}")
        # Defaulted, not required: state files written before this budget existed stay valid.
        verification_budget = budgets.get("max_verifications_per_package", DEFAULT_MAX_VERIFICATIONS)
        if attempts.get("verifications", 0) > verification_budget:
            errors.append(f"{pid}: verification budget exceeded")
        if attempts.get("verification_waivers", 0) > verification_budget:
            errors.append(f"{pid}: verification waiver budget exceeded")
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


def replayed(data: dict[str, Any], event: str, event_id: str | None) -> bool:
    """Has *this exact call* already run?

    Keyed on the command as well as the id, because "already applied" is a claim about a
    call and not about a string.  Scoping it by `event_id` alone made an id reused across
    two different commands read as a replay of the second one: the caller got
    `{"ok": true, "changed": false}` and nothing happened — the silent success-shaped
    no-op this feature exists to abolish, and on `record-late-review` it meant a verified
    critical finding disappearing with exit 0.  Every guard that asks the question asks it
    here, so the updaters and `record_event` can never disagree about the answer: if they
    did, a call could pass its own guard and then have its history entry silently dropped.
    """
    if not event_id:
        return False
    return any(item.get("event_id") == event_id and item.get("event") == event
               for item in data.get("history", []))


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
    if replayed(data, event, event_id):
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
        only = data.get("feature_id")
        render_status(path)
        render_bitacora(path, only_feature=only)
        render_notes(path, only_feature=only)
    return data, before != data


# A finding leaves the open set three ways: it was repaired (`closed`), it was
# explicitly accepted as won't-fix (`accepted`), or `finding-verifier` refuted it
# before it ever reached repair (`refuted`).  A refuted finding is never deleted —
# it keeps its verdict and evidence in the package record.
TERMINAL_FINDING_STATUSES = {"closed", "accepted", "refuted"}


def has_open_findings(package: dict[str, Any], severities: set[str] | None = None) -> bool:
    for finding in package.get("findings", []):
        if finding.get("status", "open") in TERMINAL_FINDING_STATUSES:
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
    unwaived_repairs = [item for item in package.get("repairs", []) if not item.get("delta_waived")]
    if unwaived_repairs and not package.get("delta_reviews"):
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
    # AC-04 (010-spawn-provenance): the same falsy filter summarize_feature() already
    # applies below (`not b.get("resolved_at")`) -- a non-empty `blockers` list is not
    # itself descalifying; a hand-written `"resolved_at": null` still counts as
    # unresolved (a falsy check, not "key absent"), so it keeps blocking too.
    if any(not blocker.get("resolved_at") for blocker in data.get("blockers", [])):
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
        if package and not package.get("verifications") and has_open_findings(package, {"critical", "high", "medium"}):
            # `next` is the machine advisor the orchestrator consults. Sending it to
            # DELTA_REVIEW here recommends a command that now refuses to run.
            return {"phase": phase, "next": "PACKAGE_REPAIR",
                    "reason": "record-verification is required before repair"}
        return {"phase": phase, "next": "DELTA_REVIEW", "reason": "repair batch recorded"}
    if phase == "DELTA_REVIEW":
        if package and package.get("delta_reviews"):
            verdict = package["delta_reviews"][-1].get("verdict")
            if package["delta_reviews"][-1].get("requires_full_review"):
                return {"phase": phase, "next": "PACKAGE_REVIEW", "reason": "delta review requires full review"}
            return {"phase": phase, "next": "PACKAGE_TESTING" if verdict == "pass" else "PACKAGE_REPAIR", "reason": f"latest delta verdict={verdict}"}
    if phase == "PACKAGE_TESTING":
        if package and has_open_findings(package, {"critical", "high", "medium"}):
            # `next` is the machine advisor — leaving it on PACKAGE_RUNTIME_QA walks the
            # orchestrator into an accept-package that package_accept_ready then refuses,
            # which is verbatim the failure already fixed once for verification below.
            # The reason names the state, not a cause: this branch was first written
            # blaming record-late-review, and the review panel proved that wrong.
            # `cmd_record_review` sets PACKAGE_TESTING on `pass` without checking
            # has_open_findings — unlike finalize-review-panel and record-delta-review —
            # so the same state is reachable with no late review anywhere in the history.
            # That asymmetry is real and is registered as debt rather than repaired here:
            # record-review is outside this package's criteria and every package in flight
            # uses it.
            return {"phase": phase, "next": "PACKAGE_REPAIR",
                    "reason": "a blocking finding is open; repair or refute it before testing can advance"}
        if package and package.get("testing"):
            status = package["testing"][-1].get("status")
            return {"phase": phase, "next": "PACKAGE_RUNTIME_QA" if status == "pass" else "PACKAGE_REPAIR", "reason": f"latest testing status={status}"}
        return {"phase": phase, "next": "PACKAGE_TESTING", "reason": "run regression/integration tests"}
    if phase == "PACKAGE_RUNTIME_QA":
        if package and has_open_findings(package, {"critical", "high", "medium"}):
            return {"phase": phase, "next": "PACKAGE_REPAIR",
                    "reason": "a blocking finding is open; acceptance refuses until it is repaired or refuted"}
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


def status_root(state_file: Path) -> tuple[Path, Path]:
    """Return (features_dir, status_dir) for a given state file.

    Canonical layout is ai/state/features/<id>.json with STATUS.md one level up
    in ai/state/. Arbitrary --state-file locations (tests, ad-hoc runs) keep
    everything in the state file's own directory.
    """
    parent = state_file.resolve().parent
    if parent.name == "features":
        return parent, parent.parent
    return parent, parent


def summarize_feature(data: dict[str, Any]) -> dict[str, Any]:
    budgets = data.get("budgets", {})
    packages = data.get("packages", [])
    current = None
    try:
        current = package_by_id(data)
    except StateError:
        pass
    spawns = sum(p.get("attempts", {}).get("spawns", 0) for p in packages)
    cycles = current.get("attempts", {}).get("deep_review_cycles", 0) if current else 0
    open_findings = sum(
        1
        for p in packages
        for f in p.get("findings", [])
        if f.get("status", "open") not in TERMINAL_FINDING_STATUSES
    )
    blockers = [b for b in data.get("blockers", []) if not b.get("resolved_at")]
    history = data.get("history", [])
    last = history[-1] if history else {}
    return {
        "feature_id": data.get("feature_id", "?"),
        "mode": data.get("mode") or "feature",
        "phase": data.get("phase", "?"),
        "package": f"{current.get('package_id')} ({current.get('status')})" if current else "-",
        "accepted": f"{sum(1 for p in packages if p.get('status') == 'accepted')}/{len(packages)}",
        "spawns": f"{spawns}/{budgets.get('max_spawns_per_package', '?')}",
        "reviews": f"{cycles}/{budgets.get('max_deep_review_cycles', '?')}",
        "open_findings": open_findings,
        # Raw here would put agent-authored newlines and pipes into a markdown TABLE in
        # a file memory-scribe and adversarial-judge read.  `_short` collapses the
        # whitespace; the pipe escape keeps the row a row.
        "blocker": _short(blockers[-1].get("reason", ""), 160).replace("|", "\\|") if blockers else "-",
        "next": (next_transition(data).get("next") or "-"),
        "last_event": f"{last.get('timestamp', '')} {last.get('event', '')}".strip() or "-",
    }


NARRATIVE_LOG = "narrative-log.jsonl"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if not path.exists():
        return entries
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            entries.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return entries


def collect_narrative(features_dir: Path, out_dir: Path) -> list[dict[str, Any]]:
    """Merge the two sources of narration into one chronological list.

    The opening block of a delegation rides on `record-spawn` metadata, so it
    stays attached to the budget it consumed. Every other block — closings,
    consult, quick-fix — lands in narrative-log.jsonl. Reading both is what
    makes the story hole-free.
    """
    entries: list[dict[str, Any]] = []
    for entry in read_jsonl(out_dir / NARRATIVE_LOG):
        if entry.get("client") or entry.get("tech"):
            entries.append(entry)
    for path in sorted(features_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for event in data.get("history", []):
            meta = event.get("metadata") or {}
            if not (meta.get("client") or meta.get("tech")):
                continue
            entries.append({
                "at": event.get("timestamp", ""),
                "feature_id": data.get("feature_id", path.stem),
                "package_id": event.get("package_id") or "-",
                "role": meta.get("role") or event.get("event", "-"),
                "result": "started",
                "client": meta.get("client", ""),
                "tech": meta.get("tech", ""),
                "actor": event.get("actor", "-"),
            })
    # Timestamps have second resolution, so an opening and its closing block can
    # tie. Break the tie on result so a delegation never reads as having finished
    # before it started.
    entries.sort(key=lambda item: (
        item.get("at", ""),
        item.get("feature_id", ""),
        0 if item.get("result") == "started" else 1,
    ))
    return entries


def format_narrative(entry: dict[str, Any]) -> list[str]:
    """One narration block: a header line plus the two labelled registers."""
    tail = " · ".join(
        part for part in (entry.get("package_id"), entry.get("role"), entry.get("result"))
        if part and part != "-"
    )
    return [
        f"[{entry.get('at', '?')}] {tail}".rstrip(),
        f"Cliente: {_short(entry.get('client'), 400) or '-'}",
        f"Ingeniería: {_short(entry.get('tech'), 400) or '-'}",
        "",
    ]


def bitacora_path(out_dir: Path, feature_id: str) -> Path:
    """Prefer the client-facing delivery folder; fall back to internal state.

    docs/specs/<feature_id>/ is what a client actually receives (sibling of
    evidence/), so the narration belongs there when the feature has one.
    """
    root = out_dir.parent.parent
    delivery = root / "docs" / "specs" / feature_id
    if delivery.is_dir():
        return delivery / "bitacora.md"
    return out_dir / "bitacora" / f"{feature_id}.md"


def render_bitacora(state_file: Path, only_feature: str | None = None) -> None:
    """Rebuild the cumulative per-feature narration log.

    STATUS.md keeps only the tail; this file keeps the whole story in the
    language the user can hand to a client. Fully regenerated from state
    history plus narrative-log.jsonl, so it is never hand-edited and never
    drifts. Never raises: narration must not block a state mutation.

    only_feature limits the rebuild to that feature's bitacora — mutations
    touch one feature, so rewriting every other feature's log is waste.
    """
    if RENDER_SKIP:
        return
    try:
        features_dir, out_dir = status_root(state_file)
        by_feature: dict[str, list[dict[str, Any]]] = {}
        for entry in collect_narrative(features_dir, out_dir):
            by_feature.setdefault(entry.get("feature_id") or "sin-feature", []).append(entry)
        for feature_id, items in by_feature.items():
            if only_feature and feature_id != only_feature:
                continue
            lines = [
                f"# Bitácora — {feature_id}",
                "",
                "_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la "
                "justificación de ingeniería. No editar a mano._",
                "",
                f"Actualizado: {now()}",
                "",
            ]
            for entry in items:
                lines += format_narrative(entry)
            target = bitacora_path(out_dir, feature_id)
            target.parent.mkdir(parents=True, exist_ok=True)
            payload = "\n".join(lines).rstrip() + "\n"
            with tempfile.NamedTemporaryFile(
                "w", dir=str(target.parent), delete=False, encoding="utf-8"
            ) as handle:
                handle.write(payload)
                tmp_name = handle.name
            os.replace(tmp_name, target)
    except Exception:  # narration is best-effort by contract, never blocks state
        pass


def render_status(state_file: Path) -> None:
    """Rebuild the multi-feature STATUS.md dashboard next to the state files.

    Called after every successful mutation so the dashboard is always fresh
    without any extra orchestration step. Never raises: a broken dashboard must
    not block a state mutation.
    """
    if RENDER_SKIP:
        return
    try:
        features_dir, out_dir = status_root(state_file)
        rows = []
        for path in sorted(features_dir.glob("*.json")):
            try:
                rows.append(summarize_feature(load_state(path)))
            except Exception:  # legacy/malformed schemas degrade to a row, never a crash
                rows.append({"feature_id": path.stem, "mode": "?", "phase": "INVALID_STATE",
                             "package": "-", "accepted": "-", "spawns": "-", "reviews": "-",
                             "open_findings": "-", "blocker": "state file failed to parse",
                             "next": "-", "last_event": "-"})
        lines = [
            "# Estado del desarrollo",
            "",
            "_Generado por `feature-state.py` en cada mutación de estado. No editar a mano._",
            "",
            f"Actualizado: {now()}",
            "",
            "## Features",
            "",
            "| Feature | Modo | Fase | Paquete | Aceptados | Spawns | Reviews | Findings abiertos | Blocker | Próximo paso | Último evento |",
            "|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        if rows:
            for row in rows:
                lines.append(
                    "| {feature_id} | {mode} | {phase} | {package} | {accepted} | {spawns} | {reviews} "
                    "| {open_findings} | {blocker} | {next} | {last_event} |".format(**row)
                )
        else:
            lines.append("| _sin features registradas_ | | | | | | | | | | |")
        lines += ["", "## Quick-fixes recientes", ""]
        entries = read_jsonl(out_dir / "quickfix-log.jsonl")
        if entries:
            for entry in entries[-10:][::-1]:
                files = ", ".join(entry.get("files", [])) or "-"
                lines.append(
                    f"- [{entry.get('at', '?')}] {entry.get('summary', '?')} — archivos: {files} "
                    f"— gate: {entry.get('gate', '-')} — resultado: {entry.get('result', '-')}"
                )
        else:
            lines.append("- _sin quick-fixes registrados_")
        lines += ["", "## Bitácora (últimos 15)", ""]
        narrative = collect_narrative(features_dir, out_dir)
        if narrative:
            for entry in narrative[-15:][::-1]:
                lines += format_narrative(entry)
        else:
            lines.append("- _sin narración registrada_")
        out_dir.mkdir(parents=True, exist_ok=True)
        payload = "\n".join(lines) + "\n"
        with tempfile.NamedTemporaryFile("w", dir=str(out_dir), delete=False) as handle:
            handle.write(payload)
            tmp_name = handle.name
        os.replace(tmp_name, out_dir / "STATUS.md")
    except Exception:  # the dashboard is best-effort by contract, never blocks state
        pass


# ------------------------------------------------------------ living notes ---
# Obsidian-friendly living docs under docs/notas/: a project hub, one note per
# feature, one per package, and one per logged decision, all wired with
# [[wikilinks]]. Same contract as STATUS.md/bitacora: fully regenerated from
# state on every mutation, atomic writes, never raises. Opt-in by directory:
# a repo without docs/notas/ never gets notes written.

NOTES_AUTO_BEGIN = "<!-- notas:auto -->"
NOTES_AUTO_END = "<!-- /notas:auto -->"
DECISIONS_LOG = "decisions-log.jsonl"


def slugify(text: str) -> str:
    slug = "".join(ch if ch.isalnum() else "-" for ch in text.lower())
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "decision"


def notes_root(state_file: Path, notes_dir: str | None = None) -> Path | None:
    """Notes are mandatory for any harness-managed project (ADR-0012/AC-13): the marker is
    `ai/state/` existing, never an arbitrary or third-party directory someone merely changed
    into, and never "does docs/notas already exist" (that opt-in-by-directory rule is what let
    a project silently go without notes forever). `write_note` creates the directory tree.
    """
    if notes_dir:
        return Path(notes_dir)
    _, out_dir = status_root(state_file)
    if not (out_dir.is_dir() and out_dir.name == "state" and out_dir.parent.name == "ai"):
        return None
    return out_dir.parent.parent / "docs" / "notas"


def merge_note(existing: str | None, title: str, body: str) -> str:
    """Regenerate only the machine-owned block; everything else is the human's."""
    # Defense in depth behind `_short`: the split below uses maxsplit=1, so a body
    # carrying either marker would silently redefine the block boundary.
    body = body.replace(NOTES_AUTO_END, "--›").replace(NOTES_AUTO_BEGIN, "‹!--")
    generated = f"{NOTES_AUTO_BEGIN}\n{body.rstrip()}\n{NOTES_AUTO_END}"
    if existing and NOTES_AUTO_BEGIN in existing and NOTES_AUTO_END in existing:
        prefix, rest = existing.split(NOTES_AUTO_BEGIN, 1)
        _, suffix = rest.split(NOTES_AUTO_END, 1)
        return prefix + generated + suffix
    return (
        f"# {title}\n\n{generated}\n\n"
        "## Notas propias\n\n_Lo que escribas fuera del bloque auto se preserva en cada regeneración._\n"
    )


def write_note(path: Path, title: str, body: str) -> bool:
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    payload = merge_note(existing, title, body)
    if existing == payload:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=str(path.parent), delete=False, encoding="utf-8") as handle:
        handle.write(payload)
        tmp_name = handle.name
    os.replace(tmp_name, path)
    return True


def _short(text: Any, limit: int = 120) -> str:
    text = " ".join(str(text or "").split())
    # `merge_note` splits on the FIRST NOTES_AUTO_END, so a generated body able to emit
    # that terminator moves the machine/human boundary permanently: the text below it is
    # promoted into the human-owned region and re-promoted on every regeneration.  Every
    # agent-authored field rendered from state passes through here — neutralize once.
    text = text.replace("<!--", "‹!--").replace("-->", "--›")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _decision_name(entry: dict[str, Any]) -> str:
    return f"{entry.get('at', '')[:10]} {entry.get('slug', 'decision')}".strip()


def _unique_decisions(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keyed: dict[str, dict[str, Any]] = {}
    for entry in entries:
        keyed[_decision_name(entry)] = entry  # last write wins per (date, slug)
    return list(keyed.values())


def _dicts(seq: Any) -> list[dict[str, Any]]:
    return [item for item in (seq or []) if isinstance(item, dict)]


def _snake_key(key: str) -> str:
    if not key.isidentifier() or key[0].isupper() or not any(ch.isupper() for ch in key):
        return key
    return "".join(f"_{ch.lower()}" if ch.isupper() else ch for ch in key)


def _normalize_note_state(node: Any) -> Any:
    """Best-effort camelCase→snake_case for legacy state files. Rendering only —
    the state on disk is never written back through this."""
    if isinstance(node, dict):
        return {(_snake_key(key) if isinstance(key, str) else key): _normalize_note_state(value)
                for key, value in node.items()}
    if isinstance(node, list):
        return [_normalize_note_state(item) for item in node]
    return node


def _note_packages(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize packages for the notes renderer: legacy states keyed them by id
    (dict) or named fields in camelCase (id/ownershipPaths)."""
    packages = data.get("packages", [])
    if isinstance(packages, dict):
        packages = [
            {**value, "package_id": value.get("package_id", key)} if isinstance(value, dict) else {"package_id": key}
            for key, value in packages.items()
        ]
    normalized = []
    for package in packages:
        if not isinstance(package, dict):
            continue
        if "package_id" not in package and package.get("id"):
            package = {**package, "package_id": package["id"]}
        if "owned_paths" not in package and package.get("ownership_paths"):
            package = {**package, "owned_paths": package["ownership_paths"]}
        normalized.append(package)
    return normalized


def _pending_bits(data: dict[str, Any]) -> list[str]:
    bits = []
    try:
        step = next_transition(data)
    except Exception:  # legacy states may predate the transition schema
        step = {}
    if step.get("next"):
        bits.append(f"→ `{step['next']}` — {step.get('reason', '')}")
    for blocker in data.get("blockers", []):
        if isinstance(blocker, dict):
            if not blocker.get("resolved_at"):
                bits.append(f"⛔ bloqueo: {_short(blocker.get('reason', ''))}")
        elif blocker:
            bits.append(f"⛔ bloqueo: {_short(blocker)}")
    open_findings = sum(
        1
        for package in _note_packages(data)
        for finding in package.get("findings", [])
        if finding.get("status", "open") not in TERMINAL_FINDING_STATUSES
    )
    if open_findings:
        bits.append(f"{open_findings} hallazgos abiertos")
    try:
        package = package_by_id(data)
    except Exception:
        package = None
    if package:
        pending = [t.get("id", "?") for t in package.get("tasks", []) if t.get("status") != "completed"]
        if pending:
            bits.append(f"tareas pendientes en {package.get('package_id')}: {', '.join(pending)}")
    return bits


def _hub_body(states: list[dict[str, Any]], out_dir: Path, decisions: list[dict[str, Any]]) -> str:
    lines = ["## Features", ""]
    if not states:
        lines.append("- _todavía no hay features en el state_")
    for data in states:
        fid = data.get("feature_id", "?")
        packages = _note_packages(data)
        accepted = sum(1 for p in packages if p.get("status") == "accepted")
        tail = f" · **{data['final_state']}**" if data.get("final_state") else ""
        lines.append(
            f"- [[features/{fid}|{fid}]] — fase `{data.get('phase')}` · paquetes {accepted}/{len(packages)}{tail}"
        )
    lines += ["", "## Qué falta", ""]
    pending_any = False
    for data in states:
        for bit in _pending_bits(data):
            lines.append(f"- **{data.get('feature_id')}** {bit}")
            pending_any = True
    if not pending_any:
        lines.append("- _nada pendiente en features activas_ ✅")
    quickfixes = read_jsonl(out_dir / "quickfix-log.jsonl")
    if quickfixes:
        lines += ["", "## Quick-fixes recientes", ""]
        for entry in quickfixes[-5:][::-1]:
            lines.append(f"- {entry.get('at', '')[:16]} — {_short(entry.get('summary', ''))} ({entry.get('result', '')})")
    if decisions:
        lines += ["", "## Decisiones", ""]
        for entry in decisions[-8:][::-1]:
            lines.append(f"- [[decisiones/{_decision_name(entry)}|{entry.get('title', '')}]]")
    updated = max((data.get("updated_at", "") for data in states), default="-")
    lines += [
        "", "## Referencias", "",
        "- `ai/state/STATUS.md` — dashboard técnico",
        "- `docs/adr/` — decisiones formales de arquitectura",
        "", f"_Actualizado: {updated}_",
    ]
    return "\n".join(lines)


def _feature_body(
    data: dict[str, Any], out_dir: Path,
    narrative: list[dict[str, Any]], decisions: list[dict[str, Any]],
) -> str:
    fid = data.get("feature_id", "?")
    lines = ["## Estado", "", f"- fase: `{data.get('phase')}` · modo: {data.get('mode') or 'feature'} · revisión {data.get('revision', 0)}"]
    if data.get("final_state"):
        lines.append(f"- estado final: **{data['final_state']}**")
    spec = data.get("approved_spec") or {}
    if spec.get("path"):
        lines.append(f"- spec: `{spec['path']}` (hash `{str(spec.get('hash', ''))[:12]}`)")
    criteria = data.get("acceptance_criteria", [])
    if criteria:
        lines += ["", "## Criterios de aceptación", ""] + [f"- {item}" for item in criteria]
    packages = _note_packages(data)
    if packages:
        lines += ["", "## Paquetes", ""]
        for package in packages:
            pid = package.get("package_id", "?")
            lines.append(f"- [[features/{fid}/{pid}|{pid}]] — {package.get('status')} · {_short(package.get('objective', ''), 90)}")
    approach = []
    for package in packages:
        if package.get("routing_reason"):
            approach.append(f"- ruteo {package.get('package_id')}: {_short(package['routing_reason'])}")
    for entry in [e for e in narrative if e.get("feature_id") == fid and e.get("tech")][-6:]:
        approach.append(f"- [{entry.get('at', '')[:10]}] {entry.get('role', '-')}: {_short(entry.get('tech', ''), 180)}")
    for entry in decisions:
        if entry.get("feature_id") == fid:
            approach.append(f"- decisión: [[decisiones/{_decision_name(entry)}|{entry.get('title', '')}]]")
    if approach:
        lines += ["", "## Approach y decisiones", ""] + approach
    pending = _pending_bits(data)
    lines += ["", "## Qué falta", ""] + ([f"- {bit}" for bit in pending] or ["- _nada pendiente_ ✅"])
    budgets = data.get("budgets", {})
    spawns = sum(p.get("attempts", {}).get("spawns", 0) for p in packages)
    lines += [
        "", "## Presupuestos", "",
        f"- spawns: {spawns} (máx {budgets.get('max_spawns_per_package', '?')}/paquete) · "
        f"deep review máx {budgets.get('max_deep_review_cycles', '?')} ciclos",
        "", f"[[00 - Proyecto|⌂ Proyecto]] · [[features/{fid}/grafo|grafo]] · bitácora: `{bitacora_path(out_dir, fid)}`",
        "", f"_Actualizado: {data.get('updated_at', '-')}_",
    ]
    return "\n".join(lines)


def _package_body(fid: str, package: dict[str, Any]) -> str:
    lines = ["## Motivo", "", f"- objetivo: {package.get('objective', '-')}"]
    if package.get("routing_reason"):
        lines.append(f"- ruteo: {_short(package['routing_reason'])} → {package.get('selected_role', '?')} ({package.get('selected_model', '?')})")
    if package.get("complexity"):
        lines.append(f"- complejidad: {package['complexity']}")
    for risk in package.get("risks", []):
        lines.append(f"- riesgo: {_short(risk)}")
    if package.get("owned_paths"):
        lines.append("- paths: `" + "`, `".join(package["owned_paths"]) + "`")
    if package.get("dependencies"):
        lines.append(f"- depende de: {', '.join(package['dependencies'])}")
    tasks = package.get("tasks", [])
    if tasks:
        lines += ["", "## Tareas", ""]
        for task in tasks:
            if not isinstance(task, dict):  # legacy states listed tasks as plain strings
                task = {"id": task, "status": "planned"}
            mark = "x" if task.get("status") == "completed" else " "
            extra = f" · {', '.join(task.get('local_validations', []))}" if task.get("local_validations") else ""
            lines.append(f"- [{mark}] {task.get('id')} ({task.get('status')}){extra}")
    findings = [f for f in package.get("findings", []) if isinstance(f, dict)]
    if findings:
        lines += ["", "## Hallazgos", ""]
        for finding in findings:
            label = finding.get("category") or finding.get("summary") or ""
            line = f"- {finding.get('id')} [{finding.get('severity')}] {finding.get('status', 'open')} — {_short(label)}"
            if finding.get("status") == "refuted":
                # The grounds AND the proof belong in the record, not in a chat log: a
                # reason without its evidence is the claim without the burden.
                line += (
                    f" · refutado por {finding.get('verified_by', '?')}:"
                    f" {_short(finding.get('verdict_reason', ''))}"
                    f" [{_short(finding.get('verdict_evidence', ''), 80)}]"
                )
            lines.append(line)
    trail = []
    for review in _dicts(package.get("reviews")):
        trail.append(f"- review: {review.get('verdict')} ({len(review.get('findings', []))} hallazgos)")
    for late in _dicts(package.get("late_reviews")):
        # Listed as its own kind, not folded into `review`: the note is where a human
        # looks to see that a finding arrived after the panel had already closed.
        trail.append(
            f"- review tardía ({late.get('role', '?')}): {len(late.get('findings', []))} hallazgos"
        )
    for verification in _dicts(package.get("verifications")):
        if verification.get("skipped"):
            trail.append(f"- verificación: salteada ({_short(verification.get('reason', ''))})")
        else:
            trail.append(
                f"- verificación: {len(verification.get('refuted', []))} refutados, "
                f"{len(verification.get('upheld', []))} sostenidos"
            )
    for repair in _dicts(package.get("repairs")):
        trail.append(f"- repair: {', '.join(repair.get('finding_ids', []))} → {len(repair.get('changed_files', []))} archivos")
    for delta in _dicts(package.get("delta_reviews")):
        trail.append(f"- delta review: {delta.get('verdict')}")
    for testing in _dicts(package.get("testing")):
        trail.append(f"- testing: {testing.get('status')}")
    for qa in _dicts(package.get("runtime_qa")):
        trail.append(f"- runtime QA: {qa.get('status')}{' (waived)' if qa.get('waived') else ''}")
    for gate in _dicts(package.get("gates")):
        trail.append(f"- gate `{gate.get('name')}`: {gate.get('status')}")
    if trail:
        lines += ["", "## Recorrido", ""] + trail
    if package.get("context_pack"):
        lines += ["", f"context pack: `{package['context_pack']}`"]
    lines += ["", f"↩ [[features/{fid}|{fid}]]"]
    return "\n".join(lines)


def _decision_body(entry: dict[str, Any]) -> str:
    lines = [f"- fecha: {entry.get('at', '')[:10]} · actor: {entry.get('actor', '-')}"]
    links = []
    if entry.get("feature_id"):
        links.append(f"[[features/{entry['feature_id']}|{entry['feature_id']}]]")
        if entry.get("package_id"):
            links.append(f"[[features/{entry['feature_id']}/{entry['package_id']}|{entry['package_id']}]]")
    if links:
        lines.append("- alcance: " + " · ".join(links))
    lines += ["", "## Contexto", "", entry.get("context", "-"), "", "## Decisión", "", entry.get("decision", "-")]
    if entry.get("consequences"):
        lines += ["", "## Consecuencias", "", entry["consequences"]]
    return "\n".join(lines)


RENDER_FAILURE_LOG = "render-failures.log"
RENDER_FAILURE_LOG_CAP = 200_000  # bytes; single-generation rotation past this


def _log_render_failure(out_dir: Path, context: str, exc: BaseException) -> None:
    """Best-effort, PER-PROJECT (out_dir is this project's own ai/state/, per AC-20's
    cross-project isolation requirement — a render failure in project Y's ai/state/ can never
    land in project X's log because each project's out_dir is its own directory). Never raises:
    a broken logger must not break render_notes's own never-raises invariant.
    """
    try:
        path = out_dir / RENDER_FAILURE_LOG
        if path.exists() and path.stat().st_size > RENDER_FAILURE_LOG_CAP:
            path.replace(path.with_name(path.name + ".1"))
        # SEC-004: `context` carries a caller-supplied `feature_id` and `str(exc)` can
        # carry arbitrary exception text (which, in turn, can embed a caller-supplied
        # value) -- neither is bounded or newline-safe. `_short()` collapses whitespace
        # (so a `\n` inside either can never forge a second, fake log entry with its own
        # timestamp) and truncates, exactly like every other agent-authored field that
        # lands in a generated file elsewhere in this module.
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"{now()} {_short(context)}: {type(exc).__name__}: {_short(str(exc))}\n")
    except OSError:
        pass


def render_notes(
    state_file: Path,
    notes_dir: str | None = None,
    project_name: str | None = None,
    only_feature: str | None = None,
    force: bool = False,
) -> list[str]:
    """Rebuild the living docs. Never raises: a broken note must not block state.

    only_feature keeps the hub fresh but regenerates feature/package notes for
    that feature alone and skips decision notes (they only change on
    log-decision). force ignores --no-render: sync-notes is the consolidation
    point and must always render everything.
    """
    written: list[str] = []
    if RENDER_SKIP and not force:
        return written
    try:
        fallback_out_dir = status_root(state_file)[1]
    except Exception:
        fallback_out_dir = None
    try:
        notes = notes_root(state_file, notes_dir)
        if notes is None:
            return written
        features_dir, out_dir = status_root(state_file)
        states = []
        for path in sorted(features_dir.glob("*.json")):
            try:
                states.append(_normalize_note_state(json.loads(path.read_text(encoding="utf-8"))))
            except (OSError, json.JSONDecodeError):
                continue
        narrative = collect_narrative(features_dir, out_dir)
        decisions = _unique_decisions(read_jsonl(out_dir / DECISIONS_LOG))
        project = project_name or notes.resolve().parent.parent.name
        if write_note(notes / "00 - Proyecto.md", f"{project} — notas", _hub_body(states, out_dir, decisions)):
            written.append("00 - Proyecto.md")
        for data in states:
            try:
                fid = data.get("feature_id", "?")
                if only_feature and fid != only_feature:
                    continue
                if write_note(notes / "features" / f"{fid}.md", fid, _feature_body(data, out_dir, narrative, decisions)):
                    written.append(f"features/{fid}.md")
                for package in _note_packages(data):
                    pid = package.get("package_id", "?")
                    if write_note(notes / "features" / fid / f"{pid}.md", f"{fid} · {pid}", _package_body(fid, package)):
                        written.append(f"features/{fid}/{pid}.md")
                # AC-24: same construction the `graph` subcommand uses (build_execution_graph
                # + render_mermaid), never a second copy of the join logic. Best-effort on
                # the same terms as every other note above -- a broken graph render lands in
                # the `except` below with the rest of this feature's notes, never raises.
                # PR-05: `features_dir` is THIS function's own, from `status_root()` above --
                # passed straight through rather than re-derived from `out_dir.parent.parent`
                # a second time by convention-chasing a DIFFERENT path.
                graph_state, graph_missing = build_execution_graph(
                    out_dir.parent.parent, [fid], features_dir=features_dir)
                grafo_body = "```mermaid\n" + render_mermaid(graph_state, graph_missing) + "```\n"
                if write_note(notes / "features" / fid / "grafo.md", f"{fid} · grafo", grafo_body):
                    written.append(f"features/{fid}/grafo.md")
            except Exception as exc:  # one malformed feature must not block the rest
                _log_render_failure(out_dir, f"feature={data.get('feature_id', '?')}", exc)
                continue
        if not only_feature:
            for entry in decisions:
                name = _decision_name(entry)
                if write_note(notes / "decisiones" / f"{name}.md", entry.get("title", "Decisión"), _decision_body(entry)):
                    written.append(f"decisiones/{name}.md")
    except Exception as exc:  # the living docs are best-effort by contract
        if fallback_out_dir is not None:
            _log_render_failure(fallback_out_dir, "render_notes", exc)
    return written


# --------------------------------------------------------------------------- P3-graph-view
#
# AC-20..AC-27, AC-29: the execution graph is derived in READ from the state files that
# already exist -- no new store, no materialized index (see ADR-0013). `build_execution_graph`
# walks one or more `ai/state/features/<fid>.json` files and produces nodes/edges by
# STRUCTURAL join only (membership in a list, an id matching another record's id) -- never
# by timestamp proximity, even when two entries share a timestamp by construction.
# `render_mermaid` is the one place that turns that graph into text; both `graph` (AC-22)
# and `render_notes` (AC-24) call the same two functions, never a second copy of either.

GRAPH_NODE_TYPES = ("feature", "package", "finding", "review", "verification", "repair", "commit", "blocker",
                    "spawn")
# The closed, five-member edge vocabulary this feature promises. Spanish on purpose --
# these are the verbs the spec and the ADR name, and inventing an English pair for the
# same concept would just be a second vocabulary nobody asked for.
GRAPH_EDGE_TYPES = ("produjo", "verificó", "refutó", "reparó", "bloqueó")
# Mermaid keywords a bare (unquoted) id can never collide with. Checked in lowercase
# because `_norm()` already lowercases every id this module mints.
MERMAID_RESERVED_WORDS = frozenset({"end", "graph", "subgraph", "o", "x"})


def _norm(text: Any) -> str:
    """AC-22's `norm()`: lowercase, then every character outside [a-z0-9] becomes `_`."""
    return re.sub(r"[^a-z0-9]", "_", str(text if text is not None else "").lower())


# SEC-001/PR-04: mermaid has NO backslash-escape mechanism inside a quoted label -- a
# `"` "escaped" with a leading backslash still closes the string exactly as if the
# backslash were not there (the previous implementation of this function relied on a
# Python/JS-only convention mermaid never implements, which let a crafted label break
# out of its `["..."]`/`subgraph ...["..."]` quotes and inject arbitrary mermaid text,
# including `click` directives, into a committed, rendered document). Mermaid's actual
# escape mechanism is HTML entities.
_MERMAID_ESCAPE_MAP = {
    "#": "#35;",
    '"': "#quot;",
    "\\": "#92;",
    "[": "#91;",
    "]": "#93;",
    "(": "#40;",
    ")": "#41;",
    "<": "#60;",
    ">": "#62;",
    "%": "#37;",
    ";": "#59;",
    "|": "#124;",
}
# A SINGLE pass over the ORIGINAL text, substituting every matched character for its
# entity via a callback -- `re.sub` never re-scans the replacement text it just
# produced. Every entity above contains `#` and/or `;`, both themselves in the escape
# table; a sequence of independent `str.replace()` calls (the first cut of this fix)
# re-escaped the `;`/`#` an EARLIER replacement in the same pass had just inserted,
# corrupting labels containing more than one escaped character. One pass closes that.
_MERMAID_ESCAPE_RE = re.compile("[" + re.escape("".join(_MERMAID_ESCAPE_MAP)) + "]")


def _mermaid_escape(text: Any) -> str:
    """Escape a value for a quoted mermaid label using mermaid's OWN escape mechanism
    (HTML entities), never backslashes. `_short()` runs first -- the same truncation
    every other agent-authored field rendered into a generated document gets, and its
    whitespace collapse also removes newlines before the entity table below ever sees
    them, so a label can never smuggle a real line break into the document either.
    """
    value = _short(text)
    return _MERMAID_ESCAPE_RE.sub(lambda m: _MERMAID_ESCAPE_MAP[m.group(0)], value)


class _GraphState:
    """Accumulates nodes/edges and their feature/package grouping while
    `build_execution_graph` walks one or more state files. One small object instead of a
    handful of dicts threaded by hand through every join helper below.
    """

    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, str]] = {}       # node_id -> {"type": ..., "label": ...}
        self.edges: list[tuple[str, str, str]] = []       # (src_id, dst_id, edge_label)
        self._counters: dict[tuple[str, str, str | None], int] = {}
        self.feature_order: list[str] = []
        # feature_id -> {"members": [node_id, ...] (feature-scoped only),
        #                "packages": {package_id: {"members": [node_id, ...], "order": int}}}
        self.features: dict[str, dict[str, Any]] = {}
        # PR-03: `_norm()` is lossy by design (AC-22) -- two distinct raw ids like
        # "P1-a b" and "P1-a-b" both norm to "p1_a_b". `scope -> norm text -> {raw: index}`
        # remembers, per disambiguation scope, which raw value first claimed a given
        # norm text (index 0, no suffix -- every existing id shape is unchanged) and
        # assigns any later, DISTINCT raw value that collides with it a numeric suffix
        # instead of silently reusing the first value's node/subgraph id.
        self._collision_index: dict[tuple[Any, ...], dict[str, dict[str, int]]] = {}

    def disambiguated_norm(self, scope: tuple[Any, ...], raw: Any) -> str:
        table = self._collision_index.setdefault(scope, {})
        normed = _norm(raw)
        seen = table.setdefault(normed, {})
        raw_key = str(raw)
        if raw_key not in seen:
            seen[raw_key] = len(seen)
        index = seen[raw_key]
        return normed if index == 0 else f"{normed}_dup{index}"

    def _feature_slot(self, feature_id: str) -> dict[str, Any]:
        if feature_id not in self.features:
            self.features[feature_id] = {"members": [], "packages": {}}
            self.feature_order.append(feature_id)
        return self.features[feature_id]

    def _package_slot(self, feature_id: str, package_id: str) -> dict[str, Any]:
        feature = self._feature_slot(feature_id)
        if package_id not in feature["packages"]:
            feature["packages"][package_id] = {"members": [], "order": len(feature["packages"])}
        return feature["packages"][package_id]

    def add_node(self, node_type: str, feature_id: str, package_id: str | None, label: str) -> str:
        """AC-22's id scheme: `{type}_{norm(feature_id)}[_{norm(package_id)}]_{ordinal}` --
        an explicit ordinal, never reliance on `norm()`/`slugify()` alone, which collides
        distinct raw ids inside the same package. PR-03: the feature/package components
        themselves go through `disambiguated_norm` rather than bare `_norm()`, so two
        raw ids that collide under `_norm()` alone still mint distinct node ids."""
        key = (node_type, feature_id, package_id)
        self._counters[key] = self._counters.get(key, 0) + 1
        ordinal = self._counters[key]
        node_id = f"{node_type}_{self.disambiguated_norm(('feature',), feature_id)}"
        if package_id is not None:
            node_id += f"_{self.disambiguated_norm(('package', feature_id), package_id)}"
        node_id += f"_{ordinal}"
        self.nodes[node_id] = {"type": node_type, "label": label}
        if package_id is not None:
            self._package_slot(feature_id, package_id)["members"].append(node_id)
        else:
            self._feature_slot(feature_id)["members"].append(node_id)
        return node_id

    def add_edge(self, src_id: str, dst_id: str, label: str) -> None:
        self.edges.append((src_id, dst_id, label))


def _review_label(role: str, verdict: str | None) -> str:
    """AC-27: role+verdict for a record that carries a role (subreview/late-review);
    `late_reviews[]` entries carry no `verdict` field at all, so this degrades to the
    role alone rather than printing a label that promises data the record doesn't have.
    """
    role = role or "?"
    return f"{role}: {verdict}" if verdict else role


def _add_package_findings(state: _GraphState, fid: str, pid: str, package: dict[str, Any],
                          data: dict[str, Any]) -> None:
    findings_by_id = {
        item["id"]: item for item in package.get("findings", []) or []
        if isinstance(item, dict) and item.get("id")
    }
    finding_nodes: dict[str, str] = {}
    for finding_id, finding in findings_by_id.items():
        # AC-27: id + severity always; verified_by only once the finding has one.
        label = f"{finding_id} ({finding.get('severity', '?')})"
        if finding.get("verified_by"):
            label += f" verified_by={finding['verified_by']}"
        finding_nodes[finding_id] = state.add_node("finding", fid, pid, label)

    # produjo: review_panels[].subreviews[] -- AC-20's primary source, always carries a role.
    for panel in package.get("review_panels", []) or []:
        if not isinstance(panel, dict):
            continue
        for subreview in panel.get("subreviews", []) or []:
            if not isinstance(subreview, dict):
                continue
            ids = [i for i in subreview.get("findings", []) or [] if i in finding_nodes]
            if not ids:
                continue
            review_node = state.add_node(
                "review", fid, pid, _review_label(subreview.get("role", "?"), subreview.get("verdict")))
            for finding_id in ids:
                state.add_edge(review_node, finding_nodes[finding_id], "produjo")

    # produjo: late_reviews[] -- a reviewer that returned after its panel closed (AC-10 of
    # the P2 contract this package extends); always carries a role, never a verdict.
    for late in package.get("late_reviews", []) or []:
        if not isinstance(late, dict):
            continue
        ids = [i for i in late.get("findings", []) or [] if i in finding_nodes]
        if not ids:
            continue
        review_node = state.add_node("review", fid, pid, _review_label(late.get("role", "?"), None))
        for finding_id in ids:
            state.add_edge(review_node, finding_nodes[finding_id], "produjo")

    # produjo: delta_reviews[] -- PR-02: a delta review can raise NEW or reopened
    # findings (`new_or_reopened_findings`), and until now this was the one AC-20 source
    # with a real finding-producing field that never fed the join at all (45/195 real
    # findings, 23%, had no produjo edge for exactly this reason). Same shape as
    # late_reviews[] above: the record itself carries everything the label needs, no
    # history join required.
    for delta in package.get("delta_reviews", []) or []:
        if not isinstance(delta, dict):
            continue
        ids = [i for i in delta.get("new_or_reopened_findings", []) or [] if i in finding_nodes]
        if not ids:
            continue
        review_node = state.add_node("review", fid, pid, f"delta: {delta.get('verdict', '?')}")
        for finding_id in ids:
            state.add_edge(review_node, finding_nodes[finding_id], "produjo")

    # produjo: reviews[] entries with no panel_id -- the plain `record-review` path (no
    # panel, no role field on the record itself). `finalize-review-panel` also appends to
    # `reviews[]`, but WITH a panel_id and listing every still-open finding at close time
    # (a summary, not a production event) -- already covered above via subreviews, so
    # panel-tagged entries are skipped here to avoid a second, misleading produjo edge.
    # PR-01: `cmd_record_review` now stamps `actor` directly on the record it appends to
    # `reviews[]`, so that is the primary, per-record source -- never fabricated by
    # pairing with something else. Older records from before that stamp existed (or a
    # future record written by a caller that skips it) have no `actor` key at all;
    # for THOSE, and only when the two lists are still in lockstep (`len` equal), a
    # positional join against the `record-review` history events degrades to the
    # legacy behaviour. When a `verdict: blocked` call appended to `reviews[]` and then
    # returned before emitting its own `record-review` history event (see
    # `cmd_record_review`), the two lists permanently diverge in length -- and rather
    # than let every review after that point pair against the WRONG history event, the
    # positional fallback is skipped entirely and the label just omits the actor.
    plain_reviews = [item for item in package.get("reviews", []) or []
                     if isinstance(item, dict) and not item.get("panel_id")]
    review_events = [event for event in data.get("history", []) or []
                     if isinstance(event, dict) and event.get("event") == "record-review"
                     and event.get("package_id") == pid]
    positional_join_safe = len(plain_reviews) == len(review_events)
    for index, review in enumerate(plain_reviews):
        ids = [i for i in review.get("findings", []) or [] if i in finding_nodes]
        if not ids:
            continue
        actor = review.get("actor")
        if not actor and positional_join_safe:
            actor = review_events[index].get("actor")
        verdict = review.get("verdict")
        label = f"{verdict} ({actor})" if actor else str(verdict)
        review_node = state.add_node("review", fid, pid, label)
        for finding_id in ids:
            state.add_edge(review_node, finding_nodes[finding_id], "produjo")

    # verificó/refutó: verifications[]. A normal verification call stamps EVERY finding it
    # touches with the same `verified_by` (the same `--actor`), so any touched finding's
    # own field is the structural source for the node's label -- no history join needed.
    for verification in package.get("verifications", []) or []:
        if not isinstance(verification, dict) or verification.get("skipped"):
            continue
        refuted = [i for i in verification.get("refuted", []) or []]
        upheld = [i for i in verification.get("upheld", []) or []]
        touched = [i for i in (*refuted, *upheld) if i in finding_nodes]
        if not touched:
            continue
        actor = findings_by_id[touched[0]].get("verified_by")
        verification_node = state.add_node(
            "verification", fid, pid, f"verified_by={actor}" if actor else "verification")
        for finding_id in refuted:
            if finding_id in finding_nodes:
                state.add_edge(verification_node, finding_nodes[finding_id], "refutó")
        for finding_id in upheld:
            if finding_id in finding_nodes:
                state.add_edge(verification_node, finding_nodes[finding_id], "verificó")

    # A waived verification (`record-verification --skip-reason`) touches no finding at
    # all, so AC-27's actor comes from the triggering `record-verification` history event
    # instead -- paired by position against the skip records, same structural join as the
    # plain-reviews case above. AC-22 still requires the node to exist (no finding edges).
    # D-05: same divergence guard PR-01 gave the plain-reviews join above -- today
    # `cmd_record_verification` always appends the record and its history event in the
    # same call with no early return between them, so the two lists stay in lockstep in
    # practice, but the invariant this join relies on (index N of one list is the SAME
    # call as index N of the other) belongs at every positional-join site, not only the
    # one where a divergence is currently reachable.
    skip_records = [item for item in package.get("verifications", []) or []
                    if isinstance(item, dict) and item.get("skipped")]
    skip_events = [event for event in data.get("history", []) or []
                   if isinstance(event, dict) and event.get("event") == "record-verification"
                   and event.get("package_id") == pid and (event.get("metadata") or {}).get("skipped")]
    skip_positional_join_safe = len(skip_records) == len(skip_events)
    for index, _skip in enumerate(skip_records):
        actor = skip_events[index].get("actor") if skip_positional_join_safe else None
        label = f"waived verified_by={actor}" if actor else "verification: waived"
        state.add_node("verification", fid, pid, label)

    # reparó: repairs[], and its commit when AC-21 declared one. "stops at the finding"
    # (AC-21) is not a special case here: the second edge is simply not added when there
    # is no commit sha on the record.
    for repair in package.get("repairs", []) or []:
        if not isinstance(repair, dict):
            continue
        changed_files = repair.get("changed_files", []) or []
        repair_node = state.add_node("repair", fid, pid, f"{len(changed_files)} changed files")
        for finding_id in repair.get("finding_ids", []) or []:
            if finding_id in finding_nodes:
                state.add_edge(repair_node, finding_nodes[finding_id], "reparó")
        commit_sha = repair.get("commit")
        if commit_sha:
            commit_node = state.add_node("commit", fid, pid, commit_sha[:7])
            state.add_edge(repair_node, commit_node, "reparó")


def _add_package_spawns(state: _GraphState, fid: str, pid: str, package: dict[str, Any]) -> None:
    """AC-02 (010-spawn-provenance): a `spawn` node per `package["spawns"]` entry --
    inventory only, no edges. `--caused-by-spawn` and the provenance chain it would join
    are out of this feature's scope (see ADR-0014); this makes a package's spawn spend
    visible next to its findings/reviews/repairs in the same graph, nothing more. A
    package with no `spawns` key at all (every package written before this feature)
    contributes zero nodes here, never an error -- same posture AC-29 already established
    for legacy history predating `--commit`.
    """
    for spawn in package.get("spawns", []) or []:
        if not isinstance(spawn, dict):
            continue
        # AC-02: spawn_id + role are the label floor; purpose is appended only when
        # non-empty (the CLI's own default is ""), never as a dangling empty segment.
        label = f"{spawn.get('spawn_id', '?')} {spawn.get('role', '?')}"
        purpose = spawn.get("purpose")
        if purpose:
            label += f" {purpose}"
        state.add_node("spawn", fid, pid, label)


def _add_feature_to_graph(state: _GraphState, fid: str, data: dict[str, Any]) -> None:
    # D-04: computed BEFORE the feature node is added -- `packages` can be a malformed
    # non-list/non-dict shape (e.g. `null` or an int from a hand-edited state file),
    # which raises `TypeError` inside `_note_packages`/`_normalize_note_state`. Doing
    # this first means that TypeError (caught by `build_execution_graph`, which then
    # treats the whole feature as `missing`) propagates before any node for this
    # feature exists, instead of leaving a dangling empty feature subgraph behind.
    # PR-08: the SAME legacy-tolerant normalization the notes renderer already applies
    # (`_normalize_note_state` for camelCase keys, `_note_packages` for `packages` as a
    # dict indexed by id or `id` instead of `package_id`) -- never a second, narrower
    # assumption that `packages` is always a modern list of `package_id`-keyed dicts.
    # Without this, every one of those legacy shapes made this function silently drop
    # every package (only the feature node was ever emitted).
    packages = _note_packages(_normalize_note_state(data))
    feature_node = state.add_node("feature", fid, None, f"feature: {fid}")
    package_nodes: dict[str, str] = {}
    for package in packages:
        if not isinstance(package, dict):
            continue
        pid = package.get("package_id")
        if not pid:
            continue
        package_nodes[pid] = state.add_node("package", fid, pid, f"package: {pid}")
        _add_package_findings(state, fid, pid, package, data)
        _add_package_spawns(state, fid, pid, package)

    # bloqueó: AC-26. Feature-level `data["blockers"]` alone, never `history`, and never
    # conditioned on resolution state -- every entry gets an edge, resolved or not.
    for entry in data.get("blockers", []) or []:
        if not isinstance(entry, dict):
            continue
        label = "resolved" if entry.get("resolved_at") else "open"
        entry_pid = entry.get("package_id")
        if entry_pid and entry_pid in package_nodes:
            container = package_nodes[entry_pid]
            blocker_node = state.add_node("blocker", fid, entry_pid, f"blocker: {label}")
        else:
            # AC-26's three feature-anchored cases: package_id is None, unset, or set
            # but matching no known package -- all real, none silently dropped.
            container = feature_node
            blocker_node = state.add_node("blocker", fid, None, f"blocker: {label}")
        state.add_edge(container, blocker_node, "bloqueó")


# SEC-002/SEC-005: the closed charset a `feature_id` must satisfy before it is ever
# used to build a filesystem path or interpolated into the generated document. Nothing
# in `validate_state` constrains `feature_id`'s charset (only non-empty), and `graph`'s
# `--feature-id`/`render_notes`'s `data.get("feature_id")` are both reachable with a
# value that never went through `validate_state` at all (an explicit `init --state-file`
# decouples the on-disk filename from the `feature_id` field the JSON body carries) --
# so this module enforces its own gate rather than trusting either source.
_ID_CHARSET_RE = re.compile(r"^[A-Za-z0-9._-]+$")
# Charset-safe on purpose (see _ID_CHARSET_RE): never the raw out-of-charset value, so
# this placeholder always round-trips through `_mermaid_escape` and the `%%` line
# oracle below unchanged, and it can never itself carry an injection.
_INVALID_FEATURE_ID_PLACEHOLDER = "invalid-feature-id"


def build_execution_graph(root: Path, feature_ids: list[str] | None,
                          features_dir: Path | None = None) -> tuple[_GraphState, list[str]]:
    """AC-22/AC-23. With no `feature_ids`, every `<root>/ai/state/features/*.json` present
    is processed. A requested feature with no state file contributes nothing to `state`
    and its id to the returned `missing` list -- the caller renders the AC-23 skeleton
    comment for it instead of aborting the whole run (AC-22's partial-multi-feature rule).

    PR-05: `features_dir` is optional and, when given, used AS-IS instead of being
    re-derived from `root`. `render_notes` already has its own `features_dir` from
    `status_root()` -- the one function that owns "where does this project's state
    live" -- so passing it straight through here means this function's own
    `root / "ai" / "state" / "features"` convention only has to be right in the one
    place that still relies on it, `cmd_graph`'s CLI entry point, instead of being
    re-derived a second time by chaining `.parent` off a DIFFERENT path
    (`render_notes`'s `out_dir`) and trusting the two conventions to stay in lockstep.
    """
    if features_dir is None:
        features_dir = root / "ai" / "state" / "features"
    if feature_ids:
        wanted = list(dict.fromkeys(feature_ids))  # de-dup, preserve caller order
    elif features_dir.is_dir():
        wanted = sorted(path.stem for path in features_dir.glob("*.json"))
    else:
        wanted = []
    state = _GraphState()
    missing: list[str] = []
    resolved_features_dir = features_dir.resolve() if features_dir.exists() else None
    for fid in wanted:
        if not _ID_CHARSET_RE.fullmatch(fid):
            # SEC-002: a feature_id this shape is either a mermaid-injection attempt
            # (quotes, `%`, newlines -- newlines already collapsed by `_short` inside
            # `_mermaid_escape`, but this gate stops it before it is even considered
            # "missing data" rather than relying on escaping alone) or SEC-005's path
            # traversal attempt. Never echoed, escaped or not: a fixed placeholder.
            missing.append(_INVALID_FEATURE_ID_PLACEHOLDER)
            continue
        path = features_dir / f"{fid}.json"
        try:
            resolved_path = path.resolve()
        except OSError:
            missing.append(fid)
            continue
        if resolved_features_dir is None or not resolved_path.is_relative_to(resolved_features_dir):
            # SEC-005 defense in depth: the charset gate above already forbids `/` and
            # rules out traversal through this exact join, but a symlink inside
            # `features_dir` (or a future looser charset) must not be trusted either --
            # the resolved path must still land inside `features_dir`.
            missing.append(fid)
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError:
            missing.append(fid)
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            missing.append(fid)
            continue
        if not isinstance(data, dict):
            missing.append(fid)
            continue
        try:
            _add_feature_to_graph(state, fid, data)
        except (TypeError, AttributeError, KeyError):
            # D-04: a state file with a malformed `packages` (e.g. `null` or an int
            # instead of a list/dict) or a non-string `repairs[].commit` raises here
            # rather than degrading like every other malformed-input case above. In
            # whole-repo mode (glob of every `*.json`), one hand-edited file must not
            # be able to take the entire `graph` command down -- treated the same way
            # as "missing" (unreadable/undecodable/non-dict) rather than propagating.
            missing.append(fid)
            continue
    return state, missing


_MERMAID_ID_RE = re.compile(r"^[a-z0-9_]+$")
# SEC-001: no `\\.` alternative -- mermaid has no backslash-escape mechanism, so a raw
# `"` or `\` inside a label is a structural violation, never an accepted escaped form.
_MERMAID_NODE_LINE_RE = re.compile(r'^(?P<id>[a-z0-9_]+)\["(?P<label>[^"\\]*)"\]$')
_MERMAID_SUBGRAPH_LINE_RE = re.compile(r'^subgraph\s+(?P<id>\S+)\["(?P<label>[^"\\]*)"\]$')
_MERMAID_EDGE_LINE_RE = re.compile(r'^(?P<src>[a-z0-9_]+)\s*-->\|(?P<label>[^|]+)\|\s*(?P<dst>[a-z0-9_]+)$')
# SEC-002: the ONLY two shapes of `%%` line this module ever emits. Any other `%%`
# line -- including a `%%{init: ...}%%` directive -- is a structural violation, not
# silently skipped, so an out-of-band comment can never smuggle mermaid syntax past
# this oracle. PR-06: the second alternative is `cmd_graph`'s whole-repo-with-no-state-
# directory announcement; its `root` interpolation always goes through `_mermaid_escape`
# first (never the raw value). D-03: `.*` there used to accept ANY text -- strictly
# looser than "no data for"'s `[A-Za-z0-9._-]+` charset for no real reason, since a
# properly-escaped `root` can never contain `"`, `\\`, or `%` (all three are in
# `_MERMAID_ESCAPE_MAP`). Denying exactly those three keeps the common case (a real
# filesystem path, which can legitimately contain `/`, spaces, `:`, etc. that an
# allow-list charset would reject) working while still refusing an unescaped or
# mis-escaped value outright instead of rubber-stamping it.
_MERMAID_MISSING_COMMENT_RE = re.compile(
    r'^%% no data for [A-Za-z0-9._-]+$|^%% no state directory at [^"\\%]*$'
)


def validate_mermaid_structure(text: str) -> list[str]:
    """AC-22's oracle for "valid mermaid": concrete structural assertions, not the
    unfalsifiable phrase alone. Returns a list of violations (empty means valid):
    first non-empty line is exactly `flowchart TD`; every node id matches [a-z0-9_]+ and
    is never a mermaid reserved word; every `subgraph` has a matching `end` (balanced);
    labels are quoted with their `"`, `[`, `(`, and newlines escaped; no `subgraph` id
    equals any node id (the disjoint `sg_` prefix exists exactly to make that impossible);
    the only `%%` lines this module ever emits are `%% no data for <id>` (per-feature,
    AC-23) and `%% no state directory at <root>` (PR-06, whole-repo mode with no state
    directory at all) -- any other comment line, including a mermaid directive, is a
    structural violation.
    """
    problems: list[str] = []
    lines = text.split("\n")
    non_empty = [line for line in lines if line.strip()]
    if not non_empty or non_empty[0] != "flowchart TD":
        problems.append("first non-empty line must be exactly 'flowchart TD'")
    node_ids: set[str] = set()
    subgraph_ids: set[str] = set()
    duplicate_node_ids: set[str] = set()
    duplicate_subgraph_ids: set[str] = set()
    depth = 0
    for raw_line in lines[1:]:
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("%%"):
            if not _MERMAID_MISSING_COMMENT_RE.fullmatch(line):
                problems.append(f"disallowed comment line: {raw_line!r}")
            continue
        if line == "end":
            depth -= 1
            if depth < 0:
                problems.append(f"unbalanced 'end' with no open subgraph: {raw_line!r}")
            continue
        if line.startswith("subgraph"):
            match = _MERMAID_SUBGRAPH_LINE_RE.match(line)
            depth += 1
            if not match:
                problems.append(f"malformed subgraph line: {raw_line!r}")
                continue
            sg_id = match.group("id")
            if not sg_id.startswith("sg_"):
                problems.append(f"subgraph id not in the disjoint sg_ prefix: {sg_id}")
            if sg_id in subgraph_ids:  # PR-03: a repeated subgraph id is a real collision
                duplicate_subgraph_ids.add(sg_id)
            subgraph_ids.add(sg_id)
            continue
        edge = _MERMAID_EDGE_LINE_RE.match(line)
        if edge:
            for node_id in (edge.group("src"), edge.group("dst")):
                if not _MERMAID_ID_RE.fullmatch(node_id) or node_id in MERMAID_RESERVED_WORDS:
                    problems.append(f"invalid edge endpoint id: {node_id}")
            if edge.group("label") not in GRAPH_EDGE_TYPES:
                problems.append(f"edge label outside the closed vocabulary: {edge.group('label')}")
            continue
        node = _MERMAID_NODE_LINE_RE.match(line)
        if node:
            node_id = node.group("id")
            if node_id in MERMAID_RESERVED_WORDS:
                problems.append(f"node id is a mermaid reserved word: {node_id}")
            if node_id in node_ids:  # PR-03: a repeated node id means one node's
                duplicate_node_ids.add(node_id)  # data silently overwrote another's
            node_ids.add(node_id)
            continue
        problems.append(f"unrecognized line: {raw_line!r}")
    if depth != 0:
        problems.append(f"unbalanced subgraph/end: {depth} still open at end of document")
    if duplicate_node_ids:
        problems.append(f"duplicate node id: {sorted(duplicate_node_ids)}")
    if duplicate_subgraph_ids:
        problems.append(f"duplicate subgraph id: {sorted(duplicate_subgraph_ids)}")
    collisions = subgraph_ids & node_ids
    if collisions:
        problems.append(f"subgraph id collides with a node id: {sorted(collisions)}")
    return problems


def render_mermaid(state: _GraphState, missing: list[str]) -> str:
    """AC-22/AC-23: the one renderer both `graph` and `render_notes` call. With nothing
    to render at all (no feature processed, none missing) this degrades to the bare
    `flowchart TD\\n` header, which is itself valid per `validate_mermaid_structure`.
    """
    lines = ["flowchart TD"]
    for fid in state.feature_order:
        feature = state.features[fid]
        # PR-03: the SAME disambiguated components `add_node` used for this instance's
        # node ids, never a fresh bare `_norm()` call -- otherwise a colliding raw id
        # pair could still mint two identical subgraph ids even after add_node's own
        # node ids were disambiguated.
        fid_component = state.disambiguated_norm(("feature",), fid)
        lines.append(f'subgraph sg_{fid_component}["{_mermaid_escape(fid)}"]')
        for node_id in feature["members"]:
            node = state.nodes[node_id]
            lines.append(f'  {node_id}["{_mermaid_escape(node["label"])}"]')
        for pid, package_slot in feature["packages"].items():
            pid_component = state.disambiguated_norm(("package", fid), pid)
            lines.append(f'  subgraph sg_{fid_component}_{pid_component}["{_mermaid_escape(pid)}"]')
            for node_id in package_slot["members"]:
                node = state.nodes[node_id]
                lines.append(f'    {node_id}["{_mermaid_escape(node["label"])}"]')
            lines.append("  end")
        lines.append("end")
    for fid in missing:
        # AC-23's skeleton, folded into the same combined document AC-22 requires for a
        # partial multi-feature run instead of a second code path. SEC-002: escaped like
        # every other interpolation in this function -- `build_execution_graph` already
        # gates `fid`'s charset before it ever reaches `missing`, so this is defense in
        # depth, not the only thing standing between `fid` and the document.
        lines.append("%% no data for " + _mermaid_escape(fid))
    for src_id, dst_id, label in state.edges:
        lines.append(f"{src_id} -->|{label}| {dst_id}")
    text = "\n".join(lines) + "\n"
    problems = validate_mermaid_structure(text)
    if problems:
        # This module's own generator producing structurally-invalid mermaid is a real
        # bug, never a caller error -- surfaced loudly instead of shipped silently.
        raise StateError("generated an invalid mermaid document: " + "; ".join(problems))
    return text


def cmd_graph(args: argparse.Namespace) -> int:
    root = Path(args.root) if args.root else Path.cwd()
    explicit_feature_ids = args.feature_id or None
    state, missing = build_execution_graph(root, explicit_feature_ids)
    text = render_mermaid(state, missing)
    if not explicit_feature_ids and not (root / "ai" / "state" / "features").is_dir():
        # PR-06: whole-repo mode (no --feature-id) against a root with no state
        # directory at all used to degrade silently to the bare `flowchart TD`
        # skeleton with exit 0 -- indistinguishable from a real project that
        # legitimately has zero features yet. AC-23 already sets the precedent for
        # this exact "nothing to read" case: `cmd_context`'s CONTEXT_VAULT_NOT_FOUND
        # announces it instead of staying silent. `root` is escaped like every other
        # interpolated value in this document (SEC-002); the line's shape is part of
        # `_MERMAID_MISSING_COMMENT_RE`'s closed vocabulary, so this stays a
        # structurally valid comment rather than an unchecked special case.
        text += "%% no state directory at " + _mermaid_escape(str(root)) + "\n"
        # D-03: this append happens AFTER `render_mermaid` already ran its own
        # self-check, so without a second check here the appended line would be the
        # one piece of this command's output the oracle never actually validates.
        # Same defense-in-depth posture as `render_mermaid`'s own check: this
        # module's own output failing its own oracle is a real bug, surfaced loudly.
        problems = validate_mermaid_structure(text)
        if problems:
            raise StateError("generated an invalid mermaid document: " + "; ".join(problems))
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def output_state(data: dict[str, Any], changed: bool = False, path: Path | None = None) -> int:
    print_json({"ok": True, "changed": changed, "state_file": str(path) if path else None, "state": data, "next": next_transition(data)})
    return 0


def state_file_arg(args: argparse.Namespace) -> Path:
    if getattr(args, "state_file", None):
        return Path(args.state_file)
    if getattr(args, "feature_id", None):
        return state_path(args.feature_id)
    raise StateError("--state-file or feature_id is required")


def verify_spec_hash(spec_path: str, spec_hash: str) -> None:
    """Refuse to open a record that attests bytes nobody can produce.

    `PHASES` holds REQUIREMENTS, SPEC_DRAFT, SPEC_CHALLENGE and USER_APPROVAL, and
    `LEGAL_TRANSITIONS` has an entry for none of them, so the `"from": "USER_APPROVAL"`
    this command writes was a label nothing could check -- 009's own state file carried
    an approval timestamp while its spec still read "Not yet challenged".  Whether a
    human said yes is not observable from a file.  *Which bytes* they said it about is,
    and that is the part this enforces.
    """
    spec = Path(spec_path)
    if not spec.is_file():
        raise StateError(
            f"SPEC_NOT_FOUND: {spec_path} — init records the approval of concrete bytes, "
            "and there are none here to hash"
        )
    digest = hashlib.sha256(spec.read_bytes()).hexdigest()
    if digest != spec_hash:
        raise StateError(
            f"SPEC_HASH_MISMATCH: recorded={spec_hash} disk={digest} path={spec_path} — "
            f"run `sha256sum {spec_path}`; if the spec changed after approval, it needs "
            "approving again rather than a record that attests the old bytes"
        )


def cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.state_file) if args.state_file else state_path(args.feature_id)
    if path.exists() and not args.force:
        raise StateError(f"state exists: {path}")
    verify_spec_hash(args.spec_path, args.spec_hash)
    data = base_state(args.feature_id, args.spec_path, args.spec_hash)
    data["acceptance_criteria"] = args.ac or []
    data["mode"] = args.mode
    data["budgets"].update(MODE_BUDGETS[args.mode])
    for key in ("max_deep_review_cycles", "max_repairs_per_finding", "max_package_subdivisions", "max_spawns_per_package"):
        value = getattr(args, key)
        if value is not None:
            data["budgets"][key] = value
    record_event(
        data, "init", "USER_APPROVAL", "PACKAGE_PLANNING", args.actor,
        metadata={
            "spec_path": args.spec_path,
            "spec_hash_verified": True,
            "approved_by": args.approved_by,
        },
    )
    atomic_write(path, data)
    render_status(path)
    render_bitacora(path, only_feature=args.feature_id)
    render_notes(path, only_feature=args.feature_id)
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
            if args.to_phase == "PACKAGE_REPAIR":
                # A manual transition (e.g. orchestrator override) is a sixth entry point
                # into PACKAGE_REPAIR that does not know WHY the package is here -- unlike
                # the five domain sites above, it never sets a specific reason.  Pop any
                # stale value left by an earlier repair pass so `_repair_entered_from_review`
                # falls back to log inference instead of trusting a leftover string
                # (F-03): byte-identical to today's behaviour for every state file, since
                # none of them carry this key yet.
                package.pop("repair_entry", None)
        if args.to_phase in TERMINAL:
            data["final_state"] = args.to_phase
        record_event(data, "transition", from_phase, args.to_phase, args.actor, args.package_id, {"reason": args.reason}, args.event_id)
        return True

    data, changed = mutate(path, args, "transition", update)
    return output_state(data, changed, path)


def cmd_create_package(args: argparse.Namespace) -> int:
    path = state_file_arg(args)
    if args.package_id == "grafo":
        # AC-24: package notes are written at docs/notas/features/<fid>/<pid>.md with
        # the RAW package_id, never slugified -- "grafo" is the only string that can
        # actually collide with the execution-graph note render_notes() also writes
        # there. Case-sensitive on purpose: that is how the raw path is compared too.
        raise StateError("package_id 'grafo' is reserved for the execution-graph note (AC-24)")

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
        package["context_pack"] = args.context_pack
        # Fail-safe default: runtime QA is required unless the planner explicitly
        # declares the package has no observable runtime surface.
        package["runtime_surface"] = parse_bool(args.runtime_surface, default=True)
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
        if args.runtime_surface is not None:
            package["runtime_surface"] = parse_bool(args.runtime_surface)
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
        if args.context_pack:
            package["context_pack"] = args.context_pack
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
            # The gates<->implementation loop was the only cycle without its own cap;
            # repeated gate failures now hit a hard budget instead of burning spawns.
            if attempts["gate_failures"] >= data.get("budgets", {}).get("max_gate_failures_per_package", 3):
                return block_with_reason(data, args.actor, args.package_id, "gate failure budget exhausted")
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
        # A finding is born open, always.  Terminal statuses are set only by the commands
        # that own them (record-repair, record-delta-review --closed-finding,
        # record-verification); a caller-supplied one would bypass their evidence checks
        # and let a critical finding be born already retired.
        if finding.get("status", "open") != "open":
            raise StateError(f"finding cannot be created with status {finding['status']}: {finding['id']}")
        # Blacklisting one key at a time is how the previous three rounds each patched a
        # symptom.  These are the fields the gates READ; a filer that can set them at
        # birth can make its own finding irrefutable (`verified_verdict`) or unbounded
        # (`repair_attempts` seeded negative defeats max_repairs_per_finding).
        smuggled = sorted(FINDING_BOOKKEEPING & set(finding))
        if smuggled:
            raise StateError(f"finding cannot be created carrying {smuggled}: {finding['id']}")
        finding["status"] = "open"
        findings.append(finding)
    return findings


def cmd_record_spawn(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        if replayed(data, "record-spawn", args.event_id):
            # AC-01 (010-spawn-provenance): FIRST, before the phase gate and the budget
            # check -- a retried --event-id that arrives after the spawn already minted
            # its id must not re-spend the spawn budget or mint a second SPAWN-NNN. Same
            # guard, same position, same reason as cmd_start_review_panel's replayed()
            # guard: between the phase gate and the mint sits the budget check, which
            # could BLOCK the whole feature a second time on a pure retry.
            return False
        if data["phase"] in TERMINAL:
            raise StateError(f"cannot record spawn from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        attempts = package.setdefault("attempts", {})
        budget = data.get("budgets", {}).get("max_spawns_per_package", 12)
        if attempts.get("spawns", 0) >= budget:
            return block_with_reason(data, args.actor, args.package_id, "spawn budget exhausted")
        attempts["spawns"] = attempts.get("spawns", 0) + 1
        # AC-01: the id is always derived from the counter, never from
        # len(package["spawns"]) -- a package that already had spawns recorded before
        # this feature existed (e.g. attempts.spawns=8, no spawns[] key at all, the
        # exact shape of 006's own P3 package) continues the SAME counter: its next
        # spawn is SPAWN-009, not SPAWN-001.
        spawn_id = f"SPAWN-{attempts['spawns']:03d}"
        spawns = package.setdefault("spawns", [])
        if any(item.get("spawn_id") == spawn_id for item in spawns):
            # Defense in depth against a desynced counter. Reachable only by a
            # hand-corrupted fixture -- no real caller ever provides spawn_id, only
            # this command mints it.
            raise StateError(f"spawn {spawn_id} already exists on {args.package_id}: counter out of sync")
        spawns.append({
            "spawn_id": spawn_id,
            "role": args.role,
            "purpose": args.purpose,
            "client": args.client,
            "tech": args.tech,
            "at": now(),
        })
        metadata = {"role": args.role, "purpose": args.purpose, "spawns": attempts["spawns"], "spawn_id": spawn_id}
        # The two registers of the opening narration block. Optional so older
        # callers keep working, but the orchestrator doctrine requires them:
        # they are what render_bitacora turns into the durable story.
        if args.client:
            metadata["client"] = args.client
        if args.tech:
            metadata["tech"] = args.tech
        record_event(
            data,
            "record-spawn",
            data["phase"],
            data["phase"],
            args.actor,
            args.package_id,
            metadata,
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
        # PR-01: the record carries its own actor now -- additive, so nothing that reads
        # `reviews[]` for its existing keys breaks. `_add_package_findings`'s join to the
        # `record-review` history event (below, by POSITION) was the only place that ever
        # desynced: a `blocked` verdict appends this record and then returns via
        # `block_with_reason` BEFORE the `record-review` history event is emitted a few
        # lines down, permanently shifting every later positional pairing by one. The
        # actor stamped directly here is never subject to that.
        review = {"verdict": args.verdict, "findings": [item["id"] for item in findings], "at": now(),
                  "evidence": args.evidence, "actor": args.actor}
        package.setdefault("reviews", []).append(review)
        attempts["deep_review_cycles"] = attempts.get("deep_review_cycles", 0) + 1
        data["metrics"]["package_reviews"] += 1
        for finding in findings:
            merge_finding(package, finding)
        if args.verdict == "repair_required":
            data["phase"] = "PACKAGE_REPAIR"
            package["status"] = "repair_required"
            package["repair_entry"] = "review"
        elif args.verdict == "pass":
            data["phase"] = "PACKAGE_TESTING"
            package["status"] = "testing_required"
        else:
            return block_with_reason(data, args.actor, args.package_id, args.evidence or "package review blocked")
        record_event(data, "record-review", "PACKAGE_REVIEW", data["phase"], args.actor, args.package_id, {"verdict": args.verdict, "finding_count": len(findings)}, args.event_id)
        return True

    data, changed = mutate(path, args, "record-review", update)
    return output_state(data, changed, path)


def panel_roles(raw: list[str] | None) -> list[str]:
    """The panel's membership: declared explicitly, or not at all.

    argparse's own `required=True` would refuse an empty list too — on stderr, with a
    usage dump and no `{"ok": false, "error": ...}` envelope, which is the one output
    shape every caller and every test in this repo parses (`main`).  A refusal the
    machine cannot read is not a refusal.  Raising here also lets the message name where
    the list legitimately comes from, which argparse cannot.
    """
    roles: list[str] = []
    for raw_role in raw or []:
        role = raw_role.strip()
        if not role:
            raise StateError("review panel role cannot be empty")
        if role not in roles:
            # A repeated role is satisfied by a single subreview anyway; keeping the
            # duplicate only makes `missing` in finalize-review-panel report it twice.
            roles.append(role)
    if not roles:
        raise StateError(
            "start-review-panel requires at least one --role: a panel cannot be opened without "
            "naming who will review (package-planner declares them in required_reviewers)"
        )
    return roles


def cmd_start_review_panel(args: argparse.Namespace) -> int:
    path = state_file_arg(args)
    # Outside the updater: validating an argument should not need a loadable state file.
    roles = panel_roles(args.role)

    def update(data: dict[str, Any]) -> bool:
        if replayed(data, "start-review-panel", args.event_id):
            # FIRST, before the phase gate: a replayed open legitimately arrives after the
            # panel it created has already closed, and `cannot start review panel from
            # phase PACKAGE_REPAIR` is indistinguishable from a real precondition failure.
            # Same guard, same position, same reason as cmd_record_verification, and the
            # same shared `replayed()` as record_event — which is what stops the updater
            # and the history from disagreeing about whether this call is a retry.
            return False
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
            # Not a no-op: a second open against a live panel_id is either a lost update
            # or an attempt to grow the panel, and both have to say so.  Measured before
            # this existed: with an auto-generated id the silence was worse than silent,
            # because the id derives from the counter this command bumps — the retry
            # minted RP-02, spent the last deep-review cycle, stranded RP-01 in_progress
            # where record-subreview would never reach it again, and left the next
            # legitimate open to BLOCK the feature on `deep review budget exhausted`.
            raise StateError(
                f"review panel {panel_id} already exists on {package['package_id']}; to add a member "
                "to an open panel use extend-review-panel, and to retry a timed-out call pass the "
                "original --event-id"
            )
        panel = {
            "panel_id": panel_id,
            "status": "in_progress",
            "roles": roles,
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
            merge_finding(package, finding)
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
        # Findings still live when the panel closes.  `refuted` joins `closed` here so a
        # finding the verifier killed in cycle 1 cannot reappear in the cycle-2 panel —
        # dedup runs against everything seen, not against what survived.  `accepted`
        # keeps its existing treatment (it stays listed) on purpose.
        panel_findings = [finding.get("id") for finding in package.get("findings", []) if finding.get("status", "open") not in {"closed", "refuted"}]
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
            package["repair_entry"] = "review"
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


def cmd_extend_review_panel(args: argparse.Namespace) -> int:
    """Add a member to an OPEN panel instead of opening a second one.

    `orchestrator.md` already orders a specialist that becomes necessary mid-panel to be
    recorded "as a subreview of the same bounded panel" — impossible unless it was named
    at open time, and AC-08 makes that dead end permanent.  This is that verb.  It never
    touches `deep_review_cycles`, `metrics.package_reviews` or the deep-review budget: the
    panel is ONE cycle no matter how it grows, which is the whole reason it exists.
    """
    path = state_file_arg(args)
    roles = panel_roles(args.role)
    if not (args.reason or "").strip():
        # Without this, a grown panel is indistinguishable in the record from one that
        # named all its members up front — precisely what AC-08 exists to prevent.
        # Extending is the sanctioned loophole, so it has to document itself.
        raise StateError(
            "extend-review-panel requires --reason: why this member became necessary mid-panel"
        )

    def update(data: dict[str, Any]) -> bool:
        if replayed(data, "extend-review-panel", args.event_id):
            return False
        if data["phase"] != "PACKAGE_REVIEW":
            raise StateError(f"cannot extend review panel from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        panels = package.get("review_panels", [])
        if args.panel_id:
            panel = next((item for item in panels if item.get("panel_id") == args.panel_id), None)
            if panel is None:
                raise StateError(f"unknown panel_id: {args.panel_id}")
            if panel.get("status") != "in_progress":
                raise StateError(
                    f"panel {args.panel_id} is {panel.get('status')}; a review that returns after its "
                    "panel closed is recorded with record-late-review"
                )
        else:
            panel = next((item for item in reversed(panels) if item.get("status") == "in_progress"), None)
            if not panel:
                raise StateError("no active review panel")
        existing = panel.setdefault("roles", [])
        already = [role for role in roles if role in existing]
        if already:
            # Silence would let a retry look like a successful extension while the member
            # it named was never added: the same failure shape AC-09 closes one command up.
            raise StateError(f"already on panel {panel['panel_id']}: {', '.join(already)}")
        existing.extend(roles)
        panel.setdefault("extensions", []).append(
            {"roles": roles, "reason": args.reason.strip(), "at": now()}
        )
        record_event(
            data, "extend-review-panel", "PACKAGE_REVIEW", "PACKAGE_REVIEW", args.actor, args.package_id,
            {"panel_id": panel["panel_id"], "added_roles": roles}, args.event_id,
        )
        return True

    data, changed = mutate(path, args, "extend-review-panel", update)
    return output_state(data, changed, path)


def cmd_record_late_review(args: argparse.Namespace) -> int:
    """An independent review that returned after its panel closed (AC-10).

    Phase-agnostic on purpose: `cmd_record_review` and `cmd_record_subreview` both
    hard-gate on `PACKAGE_REVIEW` and `LEGAL_TRANSITIONS["PACKAGE_REPAIR"]` has no edge
    back, so a reviewer that returns late has no door at all — five verified architect
    findings ended up in `decisions-log.jsonl`, where a reader looking at the package will
    never find them.  It consumes NO deep-review cycle: the concurrent panel is one cycle
    by rule, and counting a straggler as a second one would misrepresent the process in
    the opposite direction.  What makes it safe without a new phase is that its findings
    land on `package["findings"]`, which `package_accept_ready` already reads through
    `has_open_findings` — a blocking late finding stops acceptance with no new machinery.
    """
    path = state_file_arg(args)
    role = (args.role or "").strip()
    if not role:
        raise StateError("record-late-review requires a non-empty role")
    evidence = (args.evidence or "").strip()
    if len(evidence) < MIN_EVIDENCE_LEN:
        # This is the one record in the harness that no panel witnessed and no phase gate
        # guarded, so its evidence IS the audit trail — required here even though
        # `record-subreview --evidence` defaults to empty.  The EVIDENCE_SHAPES burden
        # stays where it belongs: on the verb that RETIRES findings, not the one that
        # files them.
        raise StateError(
            f"record-late-review requires --evidence of at least {MIN_EVIDENCE_LEN} characters: "
            "nothing else witnessed this review"
        )

    def update(data: dict[str, Any]) -> bool:
        if replayed(data, "record-late-review", args.event_id):
            return False
        package = package_by_id(data, args.package_id)
        if package.get("status") == "accepted":
            # `package_accept_ready` has already run, so a finding recorded here would be
            # read by nobody, ever: PACKAGE_ACCEPTED has no edge to PACKAGE_REPAIR and
            # `reopen` only applies from BLOCKED.  Recording it anyway would produce a
            # package showing an open blocking finding and an `accepted` status at the
            # same time, which is a worse lie than the refusal.  The gap is registered as
            # debt rather than simulated closed.
            raise StateError(
                f"{package['package_id']} is already accepted and has no path back to repair "
                "(PACKAGE_ACCEPTED has no edge to PACKAGE_REPAIR, and reopen only applies from "
                "BLOCKED); raise this against the integration or block the feature"
            )
        open_panel = next((item for item in package.get("review_panels", [])
                           if item.get("status") == "in_progress"), None)
        if open_panel:
            # While a panel is live the sanctioned channel is the panel; without this the
            # late verb is simply a way around its membership gate.  Checked before the
            # "no closed review" guard below because both fire on an open first panel and
            # this is the one that names what to do instead.
            raise StateError(
                f"panel {open_panel.get('panel_id')} is still open; use record-subreview, or "
                "extend-review-panel first if this role is not yet a member"
            )
        if not package.get("reviews"):
            # Otherwise this is a back door that files findings on a package that never
            # passed package_review_ready and never entered PACKAGE_REVIEW at all.
            raise StateError(
                f"{package['package_id']} has no closed review to be late to"
            )
        if args.panel_id and not any(item.get("panel_id") == args.panel_id
                                     for item in package.get("review_panels", [])):
            raise StateError(f"unknown panel_id: {args.panel_id}")
        findings = normalize_findings(args.finding or [])
        for finding in findings:
            # The same attribution record-subreview stamps.  Without it,
            # cmd_record_verification has nothing to compare and a late reviewer can file
            # a finding and then refute its own.
            finding.setdefault("source_role", role)
        package.setdefault("late_reviews", []).append({
            "role": role,
            "findings": [item["id"] for item in findings],
            "panel_id": args.panel_id,
            "evidence": evidence,
            "at": now(),
        })
        for finding in findings:
            # merge_finding, never a blind append: re-raising a finding the verifier
            # refuted is legitimate here — half the point of a late reviewer — and merging
            # archives the stale verdict so the finding re-enters unjudged.
            merge_finding(package, finding)
        # from == to on purpose: this moves no phase, and saying so keeps the event out of
        # every reader that looks for an entry INTO a phase.
        record_event(
            data, "record-late-review", data["phase"], data["phase"], args.actor, args.package_id,
            {"role": role, "finding_count": len(findings)}, args.event_id,
        )
        return True

    data, changed = mutate(path, args, "record-late-review", update)
    return output_state(data, changed, path)


def block_with_reason(data: dict[str, Any], actor: str, package_id: str | None, reason: str) -> bool:
    from_phase = data["phase"]
    data["phase"] = "BLOCKED"
    data["final_state"] = "BLOCKED"
    data.setdefault("blockers", []).append({"package_id": package_id, "reason": reason, "at": now()})
    record_event(data, "block", from_phase, "BLOCKED", actor, package_id, {"reason": reason})
    return True


# The three shapes the finding-verifier brief enumerates: a source location, a command
# that was actually run, or the acceptance criterion that sanctions the behaviour.
EVIDENCE_SHAPES = (
    re.compile(r"[\w./-]+\.\w+:\d+"),        # path/to/file.py:42
    re.compile(r"(?m)^\s*\$\s*\S"),          # $ command that was run
    re.compile(r"\bAC-\d+\b"),               # AC-07
)
MAX_VERDICT_FIELD = 2000
MIN_EVIDENCE_LEN = 24


def _verdict_text(verdict: dict[str, Any], field: str) -> str:
    value = verdict.get(field)
    # Truthiness is a presence check, not an evidentiary burden: `True`, `{"k": "v"}`
    # and `"   "` are all truthy and none of them is evidence.
    if not isinstance(value, str) or not value.strip():
        raise StateError(f"refuted verdict {field} must be a non-empty string: {verdict['id']}")
    value = value.strip()
    if len(value) > MAX_VERDICT_FIELD:
        raise StateError(f"refuted verdict {field} exceeds {MAX_VERDICT_FIELD} chars: {verdict['id']}")
    return value


def normalize_verdicts(raw_verdicts: list[str]) -> list[dict[str, Any]]:
    verdicts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_verdicts:
        verdict = parse_json_object(raw)
        if not verdict.get("id") or verdict.get("verdict") not in {"upheld", "refuted"}:
            raise StateError("verdict requires id and verdict upheld|refuted")
        if verdict["id"] in seen:
            # Two verdicts for one finding produce a self-contradictory record whose
            # outcome depends on argument order.
            raise StateError(f"duplicate verdict for finding: {verdict['id']}")
        seen.add(verdict["id"])
        if verdict["verdict"] == "refuted":
            # A refutation carries the same evidentiary burden the finding did.
            verdict["reason"] = _verdict_text(verdict, "reason")
            evidence = _verdict_text(verdict, "evidence")
            if len(evidence) < MIN_EVIDENCE_LEN:
                raise StateError(f"refuted verdict evidence is too short to be evidence: {verdict['id']}")
            if not any(shape.search(evidence) for shape in EVIDENCE_SHAPES):
                raise StateError(
                    f"refuted verdict evidence must cite a file:line, a command run, or an AC: {verdict['id']}"
                )
            verdict["evidence"] = evidence
        verdicts.append(verdict)
    return verdicts


def _repair_entered_from_review(data: dict[str, Any], package_id: str | None) -> bool:
    """Did this package reach PACKAGE_REPAIR from the review panel, or from a red gate?

    PACKAGE_REPAIR has four entry points — review, delta review, a failed testing run and
    a failed runtime QA.  Review and delta review are a findings problem; testing and
    runtime QA carry an obligation the finding set cannot see.

    `package["repair_entry"]` is authoritative when present: `"review"`/`"delta_review"`
    answer True, `"testing"`/`"runtime_qa"` answer False, all without touching
    `data["history"]`.  When the key is absent, or present with a value outside those
    four (a corrupt state or a future version of the field), this falls back to the log
    inference below unchanged.
    """
    repair_entry = package_by_id(data, package_id).get("repair_entry")
    if repair_entry in {"review", "delta_review"}:
        return True
    if repair_entry in {"testing", "runtime_qa"}:
        return False
    for event in reversed(data.get("history", [])):
        if event.get("from") == event.get("to"):
            # Intra-phase events carry `to = current phase` and never entered anything.
            # `record-spawn` (mandatory before every delegation) and a second
            # `record-verification` call both land here; counting them would make this
            # answer depend on how the verifier was invoked rather than on how the
            # package arrived.
            continue
        if event.get("to") != "PACKAGE_REPAIR" or event.get("package_id") not in (None, package_id):
            continue
        return event.get("event") in {"record-review", "finalize-review-panel", "record-delta-review"}
    return False


# The verification axis is scoped to the cycle that produced it.  Left on a finding that
# is raised again, a cycle-1 verdict authorises a cycle-2 repair against a different diff:
# a reusable credential.  Archive it and reset, so the finding re-enters unjudged.
# Fields owned by the lifecycle, never by whoever files the finding.
# `source_role` belongs here for the same reason the rest do, and it was missing: the
# commands that file findings stamp it with `setdefault`, which only fills a key that is
# absent, so a filer could name someone else as the raiser inside the `--finding` JSON and
# then refute the finding itself — `cmd_record_verification`'s self-refutation guard reads
# exactly this field.  Attribution is assigned by the command from the role it was handed,
# never accepted from the payload.
FINDING_BOOKKEEPING = frozenset({"verified_verdict", "verified_by", "verified_at", "verdict_reason",
                                 "verdict_evidence", "verification_history", "repair_attempts",
                                 "source_role"})
VERIFICATION_AXIS = ("verified_verdict", "verified_by", "verified_at", "verdict_reason", "verdict_evidence")


def merge_finding(package: dict[str, Any], incoming: dict[str, Any]) -> None:
    """Add a finding, or re-raise an existing one with its verification axis cleared."""
    existing = next((item for item in package.setdefault("findings", [])
                     if item.get("id") == incoming["id"]), None)
    if existing is None:
        package["findings"].append(incoming)
        return
    archived = {key: existing.pop(key) for key in VERIFICATION_AXIS if key in existing}
    if archived:
        archived["archived_at"] = now()
        existing.setdefault("verification_history", []).append(archived)
    existing.update(incoming)


def require_verified(package: dict[str, Any], finding_id: str, action: str) -> dict[str, Any]:
    """Every exit from the open set above `low` needs a verdict, not just repair.

    An invariant on a record must be enforced at EVERY transition of that record; one
    installed only in the command that motivated it leaks through the doors nobody
    reopened.
    """
    finding = next((item for item in package.get("findings", []) if item.get("id") == finding_id), None)
    if not finding:
        raise StateError(f"unknown finding: {finding_id}")
    if finding.get("severity") in {"critical", "high", "medium"} and not finding.get("verified_verdict"):
        raise StateError(f"finding was never verified: {finding_id} (cannot {action})")
    return finding


def _apply_verification_waiver(data: dict[str, Any], package: dict[str, Any], attempts: dict[str, Any],
                                verdicts: list[dict[str, Any]], budget: int, args: argparse.Namespace) -> bool:
    """The `--skip-reason` branch of `record-verification`: waive instead of verdicting."""
    if verdicts:
        raise StateError("--skip-reason cannot be combined with --verdict")
    # Waivers keep their own counter so the cheap path stays reachable once the
    # verification budget is spent — but they are still a loop, and this harness
    # caps every loop.  Same ceiling, separate dimension, no second key to drift.
    if attempts.get("verification_waivers", 0) >= budget:
        return block_with_reason(data, args.actor, args.package_id,
                                 f"verification waiver budget exhausted for {args.package_id}")
    # Physical waiver, not a prose one: skipping verification is legal only
    # when nothing above `low` is open, where the spawn costs more than the
    # repairs it would prevent.
    if has_open_findings(package, {"critical", "high", "medium"}):
        raise StateError("--skip-reason requires all open findings to be low severity")
    if len(args.skip_reason) > MAX_VERDICT_FIELD or len(args.evidence or "") > MAX_VERDICT_FIELD:
        raise StateError(f"waiver fields exceed {MAX_VERDICT_FIELD} chars")
    record = {"skipped": True, "reason": args.skip_reason, "at": now(), "evidence": args.evidence}
    package.setdefault("verifications", []).append(record)
    # Its own counter, not the budgeted one: a waiver is the declaration that no
    # pass was needed, so it must be VISIBLE without consuming the runaway
    # backstop — otherwise the cheap path becomes unreachable at the ceiling.
    attempts["verification_waivers"] = attempts.get("verification_waivers", 0) + 1
    data["metrics"]["verifications"] = data["metrics"].get("verifications", 0) + 1
    record_event(data, "record-verification", "PACKAGE_REPAIR", data["phase"], args.actor,
                 args.package_id, {"skipped": True, "reason": args.skip_reason}, args.event_id)
    return True


def _apply_verdicts(data: dict[str, Any], package: dict[str, Any], attempts: dict[str, Any],
                     verdicts: list[dict[str, Any]], budget: int, args: argparse.Namespace) -> bool:
    """The `--verdict` branch of `record-verification`: refute/uphold each finding."""
    if not verdicts:
        raise StateError("record-verification requires --verdict or --skip-reason")

    # Checked after the waiver branch on purpose: the two counters are separate
    # dimensions, so spending the verification budget never makes the cheap path
    # unreachable.
    if attempts.get("verifications", 0) >= budget:
        return block_with_reason(data, args.actor, args.package_id,
                                 f"verification budget exhausted for {args.package_id}")

    if any(item["verdict"] == "refuted" for item in verdicts) and args.actor not in REFUTING_ACTORS:
        # Retiring a blocking finding with no code change is the verifier's verb
        # alone.  Without this the implementer can clear the findings against its
        # own diff and the package accepts with no repair and no delta review.
        raise StateError(f"{args.actor} cannot refute findings; only {'/'.join(sorted(REFUTING_ACTORS))} may")

    refuted, upheld = [], []
    for verdict in verdicts:
        finding = next((item for item in package.get("findings", []) if item.get("id") == verdict["id"]), None)
        if not finding:
            raise StateError(f"unknown finding: {verdict['id']}")
        if finding.get("status", "open") in TERMINAL_FINDING_STATUSES:
            raise StateError(f"finding is not open: {verdict['id']} ({finding.get('status')})")
        if finding.get("verified_verdict") == "upheld":
            # `upheld` is terminal for verification even though the finding stays
            # open for repair.  Otherwise re-verifying is a retry-until-you-win loop
            # in a harness that caps every other loop.
            raise StateError(f"finding was already upheld and cannot be re-verified: {verdict['id']}")
        if verdict["verdict"] == "refuted" and finding.get("source_role") == args.actor:
            raise StateError(f"{args.actor} raised {verdict['id']} and cannot refute it")
        finding["verified_by"] = args.actor
        finding["verified_at"] = now()
        finding["verified_verdict"] = verdict["verdict"]
        if verdict["verdict"] == "refuted":
            # The finding is never deleted: it keeps its verdict and evidence so the
            # package record shows what was killed and on what grounds.
            finding["status"] = "refuted"
            finding["verdict_reason"] = verdict["reason"]
            finding["verdict_evidence"] = verdict["evidence"]
            refuted.append(finding["id"])
        else:
            upheld.append(finding["id"])

    package.setdefault("verifications", []).append({
        "refuted": refuted, "upheld": upheld, "at": now(), "evidence": args.evidence,
    })
    attempts["verifications"] = attempts.get("verifications", 0) + 1
    data["metrics"]["verifications"] = data["metrics"].get("verifications", 0) + 1

    if not has_open_findings(package) and _repair_entered_from_review(data, args.package_id):
        # Every finding was refuted: there is nothing left to repair, so the repair
        # pass and its delta review are skipped entirely.  That is the whole point.
        # Gated on WHY the package is in PACKAGE_REPAIR: a red test or a failed
        # runtime QA put it here for a reason the finding set knows nothing about.
        data["phase"] = "PACKAGE_TESTING"
        package["status"] = "testing_required"
    record_event(data, "record-verification", "PACKAGE_REPAIR", data["phase"], args.actor, args.package_id,
                 {"refuted": len(refuted), "upheld": len(upheld)}, args.event_id)
    return True


def cmd_record_verification(args: argparse.Namespace) -> int:
    """Adversarial refutation pass between the review panel and repair.

    This is NOT a review cycle: it never touches `deep_review_cycles`.  It is an
    edge inside the cycle the panel already counted.  Dispatches to
    `_apply_verification_waiver` (`--skip-reason`) or `_apply_verdicts` (`--verdict`)
    after the guards shared by both branches.
    """
    path = state_file_arg(args)

    if not args.actor:
        raise StateError("record-verification requires an explicit --actor")

    def update(data: dict[str, Any]) -> bool:
        if replayed(data, "record-verification", args.event_id):
            # Replay of a timed-out call is a no-op, like start-review-panel and
            # record-subreview.  Without this the per-finding guards below fire first and
            # a retry cannot tell "already applied" from "state corrupt".
            return False
        if data["phase"] != "PACKAGE_REPAIR":
            raise StateError(f"cannot record verification from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        attempts = package.setdefault("attempts", {})
        verdicts = normalize_verdicts(args.verdict or [])
        budget = data.get("budgets", {}).get("max_verifications_per_package", DEFAULT_MAX_VERIFICATIONS)

        if args.skip_reason:
            return _apply_verification_waiver(data, package, attempts, verdicts, budget, args)
        return _apply_verdicts(data, package, attempts, verdicts, budget, args)

    data, changed = mutate(path, args, "record-verification", update)
    return output_state(data, changed, path)


# AC-21. `git`'s own abbreviation floor (7) and the full sha length (40); `abcd` is
# well-formed hex but not a plausible sha, so format is gated before any git lookup.
COMMIT_SHA_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")


# A read-only git call's own budget: SEC-003 -- neither call in this module carried a
# timeout before, so a hung git process (a stale lock, a network-backed credential
# helper prompting for input it will never get) hung the entire CLI. Treated the same
# as "git cannot answer at all" everywhere it is caught below.
GIT_TIMEOUT_SECONDS = 10


def _git_answer(args: list[str]) -> tuple[str | None, str | None]:
    """A read-only git call. Returns `(stdout, None)` on success, or `(None, reason)`
    when git could not answer: `"git-unavailable"` (the `git` binary itself could not be
    invoked, or it hung past `GIT_TIMEOUT_SECONDS`) or `"not-a-repo"` (git ran and
    reported failure -- no repository at this cwd, or any other rejection of the
    read-only query itself). SEC-003: the caller needs to know WHY, not just that it
    could not, so a fail-open acceptance leaves an auditable trail instead of being
    indistinguishable from a verified one.
    """
    try:
        proc = subprocess.run(["git", *args], cwd=Path.cwd(), capture_output=True, text=True,
                              check=False, timeout=GIT_TIMEOUT_SECONDS)
    except OSError:
        return None, "git-unavailable"
    except subprocess.TimeoutExpired:
        return None, "git-unavailable"
    if proc.returncode != 0:
        return None, "not-a-repo"
    return proc.stdout, None


def validate_commit_ref(commit: str | None) -> tuple[str | None, bool]:
    """AC-21: format-gate first, then a best-effort, fail-open git lookup.

    Returns `(accepted sha or None, verified)`. `verified` is `False` exactly when the
    sha was accepted WITHOUT git confirming it (SEC-003's fail-open path) so the caller
    can persist which is which, rather than a bare sha string that looks identical
    whether or not anything actually checked it. Raises `StateError` when the format is
    wrong or git affirmatively says the sha does not exist. `--is-shallow-repository` is
    checked BEFORE `cat-file`, on purpose: in a shallow clone `cat-file -e` fails for any
    commit older than the shallow boundary even though it is real -- the exact
    false-rejection shape `check-feature-state.py:79-90` already documents and works
    around for its own git checks. Same posture here: absent git, a non-repo cwd, and a
    shallow clone all mean "cannot answer", never "does not exist".
    """
    if commit is None:
        return None, True
    commit = commit.strip()
    if not COMMIT_SHA_RE.fullmatch(commit):
        raise StateError(f"--commit must be 7-40 hex characters: {commit!r}")
    shallow, reason = _git_answer(["rev-parse", "--is-shallow-repository"])
    if shallow is None:
        print(f"COMMIT_UNVERIFIED {commit} reason={reason}", file=sys.stderr)
        return commit, False
    if shallow.strip() == "true":
        print(f"COMMIT_UNVERIFIED {commit} reason=shallow-clone", file=sys.stderr)
        return commit, False
    try:
        proc = subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            cwd=Path.cwd(), capture_output=True, text=True, check=False, timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        print(f"COMMIT_UNVERIFIED {commit} reason=git-unavailable", file=sys.stderr)
        return commit, False
    if proc.returncode == 0:
        return commit, True
    raise StateError(f"--commit does not resolve to a real commit in this repo: {commit}")


def cmd_record_repair(args: argparse.Namespace) -> int:
    path = state_file_arg(args)
    commit, commit_verified = validate_commit_ref(getattr(args, "commit", None))

    def update(data: dict[str, Any]) -> bool:
        if data["phase"] != "PACKAGE_REPAIR":
            raise StateError(f"cannot record repair from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        attempts = package.setdefault("attempts", {})
        ids = args.finding_id or []
        changed_files = args.changed_file or []
        repaired = []
        if not package.get("verifications") and has_open_findings(package, {"critical", "high", "medium"}):
            # A waiver is only physical when it lives inside the command it waives.
            # Without this, skipping record-verification entirely is free and leaves no
            # trace, and the verification node is mandatory in prose but optional in code.
            raise StateError(
                "record-verification (or its --skip-reason waiver) is required before repairing "
                "findings above low severity"
            )
        for finding_id in ids:
            finding = next((item for item in package.get("findings", []) if item.get("id") == finding_id), None)
            if not finding:
                raise StateError(f"unknown finding: {finding_id}")
            if finding.get("status") == "refuted":
                # The verifier killed it with evidence.  Repairing it anyway would
                # change code for a defect that was shown not to exist.
                raise StateError(f"cannot repair refuted finding: {finding_id}")
            require_verified(package, finding_id, "repair it")
            repaired.append(finding)
        if args.skip_delta:
            # Physical waiver, not a prose one: skipping the delta review is legal
            # only for a demonstrably small, low-severity repair.
            blocking = [f["id"] for f in repaired if f.get("severity") in {"critical", "high"}]
            if blocking:
                raise StateError("--skip-delta requires all repaired findings <= medium severity; blocked by: " + ", ".join(blocking))
            if len(changed_files) > 3:
                raise StateError(f"--skip-delta requires <= 3 changed files, got {len(changed_files)}")
        for finding in repaired:
            finding["repair_attempts"] = finding.get("repair_attempts", 0) + 1
            if finding["repair_attempts"] > data["budgets"]["max_repairs_per_finding"]:
                return block_with_reason(data, args.actor, args.package_id, f"repair budget exhausted for {finding['id']}")
            finding["status"] = "closed"
        repair = {"finding_ids": ids, "changed_files": changed_files, "verification": args.verification or [], "at": now()}
        if commit:
            # AC-21: absent when `--commit` was not declared -- the graph's `reparó`
            # edge never extends past the finding for this repair (AC-20, never a
            # guessed commit).
            repair["commit"] = commit
            # SEC-003: fail-open acceptance is legitimate (D4) but must leave an
            # auditable trail of WHICH shas were actually checked against git and which
            # were accepted on trust alone -- never indistinguishable in the state file.
            repair["commit_verified"] = commit_verified
        if args.skip_delta:
            repair["delta_waived"] = True
            repair["waiver_reason"] = "all findings <= medium and <= 3 changed files"
        package.setdefault("repairs", []).append(repair)
        attempts["repair_batches"] = attempts.get("repair_batches", 0) + 1
        data["metrics"]["repair_batches"] += 1
        if args.skip_delta:
            data["phase"] = "PACKAGE_TESTING"
            package["status"] = "testing_required"
        else:
            data["phase"] = "DELTA_REVIEW"
            package["status"] = "delta_review_required"
        repair_metadata = {"finding_ids": ids, "delta_waived": bool(args.skip_delta)}
        if commit:
            repair_metadata["commit_verified"] = commit_verified
        record_event(data, "record-repair", "PACKAGE_REPAIR", data["phase"], args.actor, args.package_id,
                     repair_metadata, args.event_id)
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
            # The other exit from the open set.  Without this guard a `critical` finding
            # is retired here with no verdict, no repair and no trace — the same failure
            # shape the actor gate closed, surviving on the flank it did not cover.
            finding = require_verified(package, finding_id, "close it in a delta review")
            if finding.get("severity") in {"critical", "high", "medium"} and not finding.get("repair_attempts"):
                # A delta review confirms that a repair closed a finding; it cannot be the
                # thing that closes it.  Otherwise a verified-but-unrepaired critical
                # leaves the open set with no code change and no record.
                raise StateError(
                    f"delta review cannot close an unrepaired {finding['severity']} finding: {finding_id}")
            finding["status"] = "closed"
        for finding in new_findings:
            # Merge, never blind-append: every lookup downstream is first-match, so a
            # duplicate id is invisible to every command and leaves the package with no
            # CLI exit at all.
            merge_finding(package, finding)
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
            package["repair_entry"] = "delta_review"
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
            if package.get("runtime_surface", True):
                package["status"] = "runtime_qa_required"
            else:
                # No observable runtime surface: record a physical waiver so the
                # package is accept-ready without spawning app-runner/runtime-verifier.
                package["status"] = "accept_ready"
                package.setdefault("runtime_qa", []).append({
                    "status": "pass",
                    "waived": True,
                    "reason": "package declared runtime_surface=false at planning",
                    "at": now(),
                })
        elif args.status == "fail":
            data["phase"] = "PACKAGE_REPAIR"
            package["status"] = "repair_required"
            package["repair_entry"] = "testing"
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
            package["repair_entry"] = "runtime_qa"
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


def cmd_reopen(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        from_phase = data["phase"]
        if from_phase != "BLOCKED":
            raise StateError(f"cannot reopen from phase {from_phase}; reopen only applies to BLOCKED")
        if not args.reason or not args.authorized_by:
            raise StateError("reopen requires explicit --reason and --authorized-by")
        resolved_at = now()
        for blocker in data.get("blockers", []):
            blocker.setdefault("resolved_at", resolved_at)
            blocker.setdefault("resolved_reason", args.reason)
            blocker.setdefault("resolved_by", args.authorized_by)
        data["phase"] = "PACKAGE_PLANNING"
        data.pop("final_state", None)
        record_event(
            data,
            "reopen",
            from_phase,
            "PACKAGE_PLANNING",
            args.actor,
            args.package_id,
            {"reason": args.reason, "authorized_by": args.authorized_by},
            args.event_id,
        )
        return True

    data, changed = mutate(path, args, "reopen", update)
    return output_state(data, changed, path)


def cmd_resume(args: argparse.Namespace) -> int:
    return cmd_next(args)


def cmd_render_status(args: argparse.Namespace) -> int:
    anchor = Path(args.state_dir or "ai/state") / "features" / "_anchor.json"
    render_status(anchor)
    render_bitacora(anchor)
    features_dir, out_dir = status_root(anchor)
    print_json({"ok": True, "status_file": str(out_dir / "STATUS.md")})
    return 0


def cmd_log_quickfix(args: argparse.Namespace) -> int:
    log_path = Path(args.log_file) if args.log_file else Path("ai/state/quickfix-log.jsonl")
    entry = {
        "at": now(),
        "summary": args.summary,
        "files": args.file or [],
        "gate": args.gate or "-",
        "result": args.result,
        "actor": args.actor,
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    anchor = log_path.parent / "features" / "_anchor.json"
    render_status(anchor)
    render_notes(anchor)
    print_json({"ok": True, "log_file": str(log_path), "entry": entry})
    return 0


def cmd_log_narrative(args: argparse.Namespace) -> int:
    """Persist one narration block that has no record-spawn of its own.

    Every closing block, and every block emitted in consult or quick-fix mode,
    lands here. Narrating in chat without landing it here is exactly the hole
    this command closes: the chat is gone next week, the bitacora is not.
    """
    log_path = Path(args.log_file) if args.log_file else Path("ai/state") / NARRATIVE_LOG
    entry = {
        "at": now(),
        "feature_id": args.feature_id or "sin-feature",
        "package_id": args.package_id or "-",
        "role": args.role or "-",
        "result": args.result,
        "client": args.client,
        "tech": args.tech,
        "actor": args.actor,
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")
    anchor = log_path.parent / "features" / "_anchor.json"
    only = args.feature_id or None
    render_status(anchor)
    render_bitacora(anchor, only_feature=only)
    render_notes(anchor, only_feature=only)
    print_json({"ok": True, "log_file": str(log_path), "entry": entry})
    return 0


def cmd_log_decision(args: argparse.Namespace) -> int:
    """Persist a decision that outlives its package (the tier below a formal ADR).

    Appends to ai/state/decisions-log.jsonl and re-renders the living notes so
    docs/notas/decisiones/ gets its own [[linked]] note. Idempotent: logging the
    same decision again is a no-op.
    """
    log_path = Path(args.log_file) if args.log_file else Path("ai/state") / DECISIONS_LOG
    slug = args.slug or slugify(args.title)
    duplicate = next(
        (
            entry for entry in read_jsonl(log_path)
            if entry.get("slug") == slug and entry.get("title") == args.title
            and entry.get("decision") == args.decision
        ),
        None,
    )
    entry = duplicate or {
        "at": now(),
        "slug": slug,
        "title": args.title,
        "context": args.context,
        "decision": args.decision,
        "consequences": args.consequences or "",
        "feature_id": args.feature_id or "",
        "package_id": args.package_id or "",
        "actor": args.actor,
    }
    if duplicate is None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")
    render_notes(log_path.parent / "features" / "_anchor.json")
    print_json({"ok": True, "log_file": str(log_path), "entry": entry, "deduped": duplicate is not None})
    return 0


def cmd_sync_notes(args: argparse.Namespace) -> int:
    """Consolidation point: full regen of STATUS, bitacora, and the living notes.

    Intra-phase writes may defer rendering via --no-render; this command always
    renders everything, so run it at phase close and end of turn.
    """
    global RENDER_SKIP
    RENDER_SKIP = False
    state_dir = Path(args.state_dir) if args.state_dir else Path("ai/state")
    # Same root derivation the bitacora uses: ai/state -> repo root.
    default_notes = state_dir.resolve().parent.parent / "docs" / "notas"
    notes_dir = Path(args.notes_dir) if args.notes_dir else default_notes
    notes_dir.mkdir(parents=True, exist_ok=True)
    anchor = state_dir / "features" / "_anchor.json"
    render_status(anchor)
    render_bitacora(anchor)
    written = render_notes(anchor, str(notes_dir), args.project_name, force=True)
    print(f"NOTES_SYNCED n={len(written)}")
    print_json({"ok": True, "notes_dir": str(notes_dir), "written": written})
    return 0


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
    # The bundle carries a high finding, so ADR-0009 D4 requires the verifier: the
    # self-demonstration must show the node, refutation shape included.
    refuted = package["findings"][1]
    refuted.update({
        "status": "refuted",
        "verified_by": "finding-verifier",
        "verified_at": now(),
        "verified_verdict": "refuted",
        "verdict_reason": "an existing regression test already covers the cited path",
        "verdict_evidence": "$ pytest tests/test_example.py -k interleaving\n1 passed, 0 failed",
    })
    upheld = package["findings"][0]
    upheld.update({"verified_by": "finding-verifier", "verified_at": now(), "verified_verdict": "upheld"})
    package["verifications"].append({"refuted": ["F-002"], "upheld": ["F-001"], "at": now(), "evidence": "dry-run refutation pass"})
    package["attempts"]["verifications"] = 1
    data["metrics"]["verifications"] = 1
    record_event(data, "record-verification", "PACKAGE_REPAIR", "PACKAGE_REPAIR", "finding-verifier", "PKG-01", {"refuted": 1, "upheld": 1})
    for finding in package["findings"]:
        if finding["status"] == "refuted":
            continue
        finding["status"] = "closed"
        finding["repair_attempts"] = 1
    package["repairs"].append({"finding_ids": ["F-001"], "changed_files": ["src/example.py"], "verification": ["focused-unit-test"], "at": now()})
    package["attempts"]["repair_batches"] = 1
    data["metrics"]["repair_batches"] = 1
    data["phase"] = "DELTA_REVIEW"
    record_event(data, "record-repair", "PACKAGE_REPAIR", "DELTA_REVIEW", "repair-agent", "PKG-01", {"finding_ids": ["F-001"]})
    package["delta_reviews"].append({"verdict": "pass", "closed_findings": ["F-001"], "new_or_reopened_findings": [], "requires_full_review": False, "reason": "dry-run", "at": now()})
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
    # Required, like `reopen --authorized-by`: an assertion that defaults to a value
    # nobody chose is exactly the assertion this command used to make for free.
    init.add_argument("--approved-by", required=True)
    init.add_argument("--actor", default="orchestrator")
    init.add_argument("--ac", action="append")
    init.add_argument("--max-deep-review-cycles", type=int)
    init.add_argument("--max-repairs-per-finding", type=int)
    init.add_argument("--max-package-subdivisions", type=int)
    init.add_argument("--max-spawns-per-package", type=int)
    # A feature that reaches init already carries a risk signal (quick-fixes
    # close via log-quickfix, no state file), so scoped budgets are the floor;
    # full feature/SDD budgets stay opt-in via explicit --mode feature.
    init.add_argument("--mode", choices=sorted(MODE_BUDGETS), default="scoped")
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
    create.add_argument("--context-pack")
    create.add_argument("--runtime-surface")
    create.set_defaults(func=cmd_create_package)

    update = sub.add_parser("update-package")
    add_common_state_args(update)
    update.add_argument("package_id")
    update.add_argument("--feature-id")
    update.add_argument("--integrated")
    update.add_argument("--runtime-surface")
    update.add_argument("--diff-ref")
    update.add_argument("--complexity", choices=["small", "medium", "high"])
    update.add_argument("--selected-role")
    update.add_argument("--selected-model")
    update.add_argument("--routing-reason")
    update.add_argument("--context-pack")
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
    spawn.add_argument("--client", default="")
    spawn.add_argument("--tech", default="")
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

    extend = sub.add_parser("extend-review-panel")
    add_common_state_args(extend)
    extend.add_argument("package_id")
    extend.add_argument("--feature-id")
    extend.add_argument("--panel-id")
    extend.add_argument("--role", action="append")
    extend.add_argument("--reason")
    extend.set_defaults(func=cmd_extend_review_panel)

    late = sub.add_parser("record-late-review")
    add_common_state_args(late)
    late.add_argument("package_id")
    late.add_argument("role")
    late.add_argument("--feature-id")
    late.add_argument("--panel-id")
    late.add_argument("--finding", action="append")
    # No `verdict` positional, unlike every other review verb: a verdict in this CLI is a
    # token that drives a phase, and this command drives none.  Offering `blocked` without
    # blocking would be a lie, and `pass` would invite the readers of `reviews[-1]` to
    # trust a record that is deliberately not one of them.
    late.add_argument("--evidence", default="")
    late.set_defaults(func=cmd_record_late_review)

    verification = sub.add_parser("record-verification")
    add_common_state_args(verification)
    verification.add_argument("package_id")
    verification.add_argument("--feature-id")
    verification.add_argument("--verdict", action="append")
    verification.add_argument("--skip-reason", default="")
    verification.add_argument("--evidence", default="")
    # `verified_by` IS the independence attribution; silently recording the coordinator's
    # default would erase the one thing the field exists for.  Drop the inherited default
    # so the command can demand an explicit actor.
    verification.set_defaults(func=cmd_record_verification, actor=None)

    repair = sub.add_parser("record-repair")
    add_common_state_args(repair)
    repair.add_argument("package_id")
    repair.add_argument("--feature-id")
    repair.add_argument("--finding-id", action="append")
    repair.add_argument("--changed-file", action="append")
    repair.add_argument("--verification", action="append")
    repair.add_argument("--skip-delta", action="store_true")
    repair.add_argument("--commit", help="AC-21: sha of the commit that repaired this finding (7-40 hex)")
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

    reopen = sub.add_parser("reopen")
    add_common_state_args(reopen)
    reopen.add_argument("--feature-id")
    reopen.add_argument("--package-id")
    reopen.add_argument("--reason", required=True)
    reopen.add_argument("--authorized-by", required=True)
    reopen.set_defaults(func=cmd_reopen)

    render = sub.add_parser("render-status")
    render.add_argument("--state-dir")
    render.set_defaults(func=cmd_render_status)

    quickfix = sub.add_parser("log-quickfix")
    quickfix.add_argument("--summary", required=True)
    quickfix.add_argument("--result", required=True, choices=["done", "reverted", "blocked"])
    quickfix.add_argument("--file", action="append")
    quickfix.add_argument("--gate")
    quickfix.add_argument("--actor", default="orchestrator")
    quickfix.add_argument("--log-file")
    quickfix.set_defaults(func=cmd_log_quickfix)

    narrative = sub.add_parser("log-narrative")
    narrative.add_argument("--client", required=True)
    narrative.add_argument("--tech", required=True)
    narrative.add_argument("--result", default="done", choices=["started", "done", "blocked"])
    narrative.add_argument("--role")
    narrative.add_argument("--package-id")
    narrative.add_argument("--feature-id")
    narrative.add_argument("--actor", default="orchestrator")
    narrative.add_argument("--log-file")
    narrative.set_defaults(func=cmd_log_narrative)

    decision = sub.add_parser("log-decision")
    decision.add_argument("--title", required=True)
    decision.add_argument("--context", required=True)
    decision.add_argument("--decision", required=True)
    decision.add_argument("--consequences")
    decision.add_argument("--feature-id")
    decision.add_argument("--package-id")
    decision.add_argument("--slug")
    decision.add_argument("--actor", default="orchestrator")
    decision.add_argument("--log-file")
    decision.set_defaults(func=cmd_log_decision)

    notes = sub.add_parser("sync-notes")
    notes.add_argument("--state-dir")
    notes.add_argument("--notes-dir")
    notes.add_argument("--project-name")
    notes.set_defaults(func=cmd_sync_notes)

    dry = sub.add_parser("dry-run")
    dry.add_argument("feature_id")
    dry.set_defaults(func=cmd_dry_run)

    graph = sub.add_parser("graph")
    graph.add_argument("--feature-id", action="append")
    graph.add_argument("--root")
    graph.add_argument("--out")
    graph.set_defaults(func=cmd_graph)

    # Available on every subcommand: defer STATUS/bitacora/notes regeneration
    # for high-frequency intra-phase writes; sync-notes always renders anyway.
    for item in sub.choices.values():
        item.add_argument("--no-render", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    global RENDER_SKIP
    RENDER_SKIP = bool(getattr(args, "no_render", False))
    try:
        return args.func(args)
    except (OSError, json.JSONDecodeError, StateError) as exc:
        print_json({"ok": False, "error": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
