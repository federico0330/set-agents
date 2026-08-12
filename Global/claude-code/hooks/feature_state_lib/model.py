"""Extracted from ai/scripts/feature-state.py by a behavior-preserving refactor
(mechanical reorganization only -- no logic changes). See feature-state.py's own
module docstring and the package-level notes for the split rationale.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
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
# 020-honest-dashboard/AC-01/AC-03 (ADR-0040): the single staleness threshold every
# derived artifact (cmd_digest, cmd_status) reads -- a product assumption, not a measured
# truth (spec SC-10), so it lives as one named constant instead of a number repeated at
# each call site. Changing it is a one-line edit, never a search-and-replace.
STALE_THRESHOLD_DAYS = 7
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
    "freeze-candidate",
    "record-receipt",
    "amend-spec",
    "supersede-package",
    "record-module-impact",
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
# `record_event`/`mutate` are injected here (as plain module attributes) by
# ai/scripts/feature-state.py right after it defines them.  Restriction: their
# real `def` bodies must stay physically inside feature-state.py (a source-text
# invariant a regression test pins), so every other submodule that needs to
# call them does so through the qualified `model.record_event(...)` /
# `model.mutate(...)` spelling -- a normal module attribute lookup, resolved at
# call time, long after both are bound.  `None` until that injection runs.
record_event = None
mutate = None


class StateError(RuntimeError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ---------------------------------------------------------------- honest-dashboard ---
# 020-honest-dashboard/ADR-0040: the ONE predicate every derived artifact (cmd_digest,
# _hub_body, cmd_status) consumes to decide "does this feature still need attention" --
# centralized here, not reimplemented per site, because that duplication (once in
# cli_reporting.py, once in feature-state.py, both wrong the same way) is the defect this
# feature exists to close. Lives in model.py specifically because this module imports
# nothing else in feature_state_lib (see cli_integration.py:1-13 for the import-cycle
# reasoning that generalizes here): every consumer already does
# `from feature_state_lib import model` with no risk of a new cycle.

def feature_is_live(data: dict[str, Any]) -> bool:
    """Excludes only what is genuinely finished. Exact equality against "DONE", never
    truthy-on-any-value: `final_state` is closed vocabulary (`TERMINAL`, all upper-case --
    the only two values any real code path ever writes), and a BLOCKED feature is still
    live -- it needs a human decision, which is exactly what AC-01 surfaces, not hides.
    """
    return data.get("final_state") != "DONE"


def open_blocker(data: dict[str, Any]) -> dict[str, Any] | None:
    """AC-01: the MOST RECENT blocker entry without `resolved_at` -- never the first one
    (a feature can be blocked, reopened, and blocked again, like 002-adaptive's own
    history: one resolved entry followed by the live one), and never `updated_at` used as
    a stand-in for "since when is this actually blocked"."""
    open_ones = [b for b in data.get("blockers", []) if isinstance(b, dict) and not b.get("resolved_at")]
    return open_ones[-1] if open_ones else None


def days_since(timestamp: str | None) -> int | None:
    """Whole days between an ISO 8601 timestamp (the shape every `at`/`updated_at` field
    in this schema is written in) and now, UTC. None when there is nothing to measure --
    never a fake 0 that would misread as "today" for missing or unparsable data."""
    if not timestamp:
        return None
    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return max((datetime.now(timezone.utc) - parsed).days, 0)


def blocked_days(data: dict[str, Any]) -> int | None:
    """AC-04: days since the LAST unresolved blocker -- None when there is none open."""
    blocker = open_blocker(data)
    return days_since(blocker.get("at")) if blocker else None


def stale_days(data: dict[str, Any]) -> int | None:
    """AC-03: only meaningful for a live feature that is NOT blocked -- a blocked feature
    is exempt from the staleness mark by construction (AC-01 already covers it in more
    detail, and marking it here too would be a redundant third mention, spec SC-06). None
    for a finished feature, a blocked one, or one with no `updated_at` to measure from.
    """
    if not feature_is_live(data) or open_blocker(data) is not None:
        return None
    return days_since(data.get("updated_at"))


def feature_is_stale(data: dict[str, Any]) -> bool:
    days = stale_days(data)
    return days is not None and days >= STALE_THRESHOLD_DAYS


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
        # RDD-inspired additions (docs/adr/0020-*.md and siblings 0021-0024). Same precedent
        # as `late_reviews`/`spawns` above: every reader uses `.get()`, no backfill for
        # packages that predate these keys.
        "candidate_identity": None,   # {generation, base_tree, candidate_tree, paths_digest,
                                       #  changed_lines, frozen_at, frozen_by} -- set by freeze-candidate
        "receipt": None,              # {schema, package_id, generation, base_tree, candidate_tree,
                                       #  paths_digest, review_verdict, delta_review_verdict,
                                       #  verifications_summary, terminal_state, minted_at, minted_by}
        "repair_ceiling": None,       # {original_changed_lines, budget_lines, cap_source, frozen_at}
        "strict_tdd": False,          # declared by package-planner at create-package time
        # AC-20 (019/PKG-3, ADR-0036): [{module, cambio, modelo_mental, feature_id, package_id, at,
        # actor}] appended by record-module-impact. Every reader uses .get(): packages that predate
        # this key (every package before this feature) are simply empty, same precedent as `spawns`.
        "module_impacts": [],
        # The cheap valve (ADR-0036): {reason, at, actor} set by
        # `record-module-impact --module-impact-waived --reason`. Mutually exclusive in practice with
        # a non-empty module_impacts (a package either documents its impact or declares why not).
        "module_impact_waiver": None,
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
        # RDD-inspired additions (docs/adr/0020-*.md and siblings). Both are static, pure-dict
        # backstop tripwires -- like `gate_failures` above, real enforcement happens at the
        # command that writes the value (it must never let a violating write land in the first
        # place), so these should never actually fire in normal operation.
        receipt = package.get("receipt")
        if receipt:
            candidate = package.get("candidate_identity") or {}
            for field in ("base_tree", "candidate_tree", "paths_digest"):
                if receipt.get(field) != candidate.get(field):
                    errors.append(f"{pid}: receipt.{field} does not match candidate_identity.{field}")
        ceiling = package.get("repair_ceiling")
        if ceiling:
            budget_lines = ceiling.get("budget_lines")
            for repair in package.get("repairs", []):
                changed = repair.get("changed_lines")
                if isinstance(changed, int) and isinstance(budget_lines, int) and changed > budget_lines:
                    errors.append(f"{pid}: repair changed_lines ({changed}) exceeds repair_ceiling.budget_lines ({budget_lines})")
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


def module_impacts_ready(data: dict[str, Any]) -> list[str]:
    """ADR-0036 (019/PKG-3): every `accepted` package (never `superseded`, same precedent
    as `done_ready`) needs either a recorded module impact or an explicit waiver before the
    feature can enter INTEGRATION. Unlike `candidate_identity.integration_ready` (ADR-0024,
    deliberately kept OUT of `check_transition` because it re-derives against the live repo
    and has no cheap escape hatch), this check is safe as a hard precondition here: it reads
    only the package's own state, and the waiver is a single cheap command
    (`record-module-impact --module-impact-waived --reason`) — never more expensive than the
    documentation it substitutes for. See ADR-0036 for the full comparison.
    """
    errors = []
    for package in data.get("packages", []):
        if package.get("status") in ("superseded",):
            continue
        if package.get("status") != "accepted":
            continue
        if package.get("module_impacts") or package.get("module_impact_waiver"):
            continue
        errors.append(
            f"{package.get('package_id')}: module impact required (record-module-impact) "
            "or waived (--module-impact-waived --reason)"
        )
    return errors


def done_ready(data: dict[str, Any]) -> list[str]:
    errors = []
    # ADR-0028: `superseded` is the second terminal package state — a package the
    # amended scope retired keeps its history and stops blocking the feature.
    if any(package.get("status") not in ("accepted", "superseded") for package in data.get("packages", [])):
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
    covered = {ac for package in data.get("packages", [])
               if package.get("status") != "superseded"
               for ac in package.get("acceptance_criteria", [])}
    required_criteria = set(data.get("acceptance_criteria") or [])
    if required_criteria and not required_criteria.issubset(covered):
        errors.append("not all acceptance criteria are covered by accepted packages")
    # ADR-0036: same-shaped backstop as the receipt tripwire above -- the real enforcement
    # is transitions.check_transition's INTEGRATION precondition; this is the safety net for
    # a caller that somehow reaches DONE without ever passing through it.
    errors += module_impacts_ready(data)
    return errors
