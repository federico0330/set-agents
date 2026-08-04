"""Extracted from ai/scripts/feature-state.py by a behavior-preserving refactor
(mechanical reorganization only -- no logic changes). See feature-state.py's own
module docstring and the package-level notes for the split rationale.
"""

from __future__ import annotations

from typing import Any

from feature_state_lib.model import (
    StateError, LEGAL_TRANSITIONS, TERMINAL, has_open_findings, package_by_id,
    package_accept_ready, package_review_ready, tasks_complete, done_ready,
)


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
        # ADR-0028: superseded counts as closed here too, matching done_ready.
        if any(package.get("status") not in ("accepted", "superseded") for package in data.get("packages", [])):
            return {"phase": phase, "next": "PACKAGE_PLANNING", "reason": "remaining packages exist"}
        return {"phase": phase, "next": "INTEGRATION", "reason": "all packages accepted"}
    if phase == "INTEGRATION":
        return {"phase": phase, "next": "DONE", "reason": "run final global gates first"}
    return {"phase": phase, "next": None, "reason": "record required event before continuing"}
