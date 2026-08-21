"""Extracted from ai/scripts/feature-state.py by a behavior-preserving refactor
(mechanical reorganization only -- no logic changes). See feature-state.py's own
module docstring and the package-level notes for the split rationale.
"""

from __future__ import annotations

import argparse
import re
from typing import Any

from feature_state_lib import model
from feature_state_lib.model import (
    StateError, now, parse_json_object, package_by_id, package_review_ready, has_open_findings,
    TERMINAL_FINDING_STATUSES,
)
from feature_state_lib.cli_lifecycle import state_file_arg, output_state, block_with_reason
from feature_state_lib.cli_repair import normalize_findings, FINDING_BOOKKEEPING


def _roles_without_subreview(package: dict[str, Any], roles: list[str]) -> list[str]:
    subreviewed = {
        item.get("role")
        for panel in package.get("review_panels", [])
        for item in panel.get("subreviews", [])
        if item.get("role")
    }
    return [role for role in roles if role not in subreviewed]


def require_review_panel(package: dict[str, Any]) -> None:
    required = model.resolved_required_reviewers(package)
    if len(required) <= 1:
        return
    missing = _roles_without_subreview(package, required)
    missing_text = ", ".join(missing) if missing else "none (the open panel closes with finalize-review-panel)"
    complexity = package.get("complexity") or "<unset>"
    risk = model.resolve_package_risk(package)
    roles_hint = ", ".join(f"--role {role}" for role in required)
    raise StateError(
        f"REVIEW_PANEL_REQUIRED: {package['package_id']} requires the full review panel "
        f"({', '.join(required)}) for complexity={complexity} risk={risk}; "
        "record-review is the small+low door and cannot record any verdict here. "
        f"Roles with no recorded subreview: {missing_text}. "
        f"Use: start-review-panel {roles_hint}, then record-subreview per role, "
        "then finalize-review-panel."
    )


def _blocking_findings(package: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        finding for finding in package.get("findings", [])
        if finding.get("status", "open") not in TERMINAL_FINDING_STATUSES
        and finding.get("severity") in model.BLOCKING_SEVERITIES
    ]


def require_no_blocking_findings(package: dict[str, Any]) -> None:
    if not has_open_findings(package, model.BLOCKING_SEVERITIES):
        return
    blocking = _blocking_findings(package)
    details = ", ".join(
        f"{finding.get('id', '<unnamed>')} ({finding.get('severity', 'unknown')})"
        for finding in blocking
    )
    raise StateError(
        f"BLOCKING_FINDING_OPEN: cannot pass review with blocking findings open: {details}. "
        "Record --verdict repair_required instead, or refute the finding with record-verification. "
        "Same severities finalize-review-panel refuses: critical, high, medium."
    )


def cmd_record_review(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        if data["phase"] != "PACKAGE_REVIEW":
            raise StateError(f"cannot record package review from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        errors = package_review_ready(package)
        if errors:
            raise StateError("cannot record package review: " + "; ".join(errors))
        require_review_panel(package)
        attempts = package.setdefault("attempts", {})
        if attempts.get("deep_review_cycles", 0) >= data["budgets"]["max_deep_review_cycles"]:
            return block_with_reason(data, args.actor, args.package_id, "deep review budget exhausted",
                                     counter={"scope": "attempts", "key": "deep_review_cycles"})
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
            require_no_blocking_findings(package)
            data["phase"] = "PACKAGE_TESTING"
            package["status"] = "testing_required"
        else:
            return block_with_reason(data, args.actor, args.package_id, args.evidence or "package review blocked")
        model.record_event(data, "record-review", "PACKAGE_REVIEW", data["phase"], args.actor, args.package_id, {"verdict": args.verdict, "finding_count": len(findings)}, args.event_id)
        return True

    data, changed = model.mutate(path, args, "record-review", update)
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
        model.record_event(data, "record-subreview", "PACKAGE_REVIEW", "PACKAGE_REVIEW", args.actor, args.package_id, {"role": args.role, "verdict": args.verdict, "finding_count": len(findings)}, args.event_id)
        return True

    data, changed = model.mutate(path, args, "record-subreview", update)
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
            if has_open_findings(package, model.BLOCKING_SEVERITIES):
                raise StateError("cannot pass review panel with blocking findings open")
            data["phase"] = "PACKAGE_TESTING"
            package["status"] = "testing_required"
        else:
            return block_with_reason(data, args.actor, args.package_id, args.evidence or "review panel blocked")
        model.record_event(data, "finalize-review-panel", "PACKAGE_REVIEW", data["phase"], args.actor, args.package_id, {"panel_id": panel.get("panel_id"), "verdict": args.verdict}, args.event_id)
        return True

    data, changed = model.mutate(path, args, "finalize-review-panel", update)
    return output_state(data, changed, path)



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
# (FINDING_BOOKKEEPING, originally introduced by the same comment, now lives in
# feature_state_lib.cli_repair -- see the note there for why.)
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
