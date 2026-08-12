"""Extracted from ai/scripts/feature-state.py by a behavior-preserving refactor
(mechanical reorganization only -- no logic changes). See feature-state.py's own
module docstring and the package-level notes for the split rationale.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from feature_state_lib import model
from feature_state_lib.model import (
    StateError, now, parse_json_object, package_by_id, has_open_findings, package_accept_ready,
)
from feature_state_lib.cli_lifecycle import state_file_arg, output_state, block_with_reason, spec_drift


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
        if not args.global_gate and args.name == "repair-ceiling" and args.status == "fail":
            # docs/adr/0023-*.md: a repair-ceiling breach is not retryable by design -- the
            # package gets exactly one repair attempt per cycle (gentle-ai's "ordinary
            # lineage admits exactly one correction"), so this bypasses the generic
            # gate_failures 3-strikes accumulator entirely and blocks on the first breach.
            return block_with_reason(data, args.actor, args.package_id, "repair exceeded its frozen line ceiling")
        if not args.global_gate and data["phase"] == "PACKAGE_GATES" and args.status == "fail":
            package = package_by_id(data, args.package_id)
            attempts = package.setdefault("attempts", {})
            attempts["gate_failures"] = attempts.get("gate_failures", 0) + 1
            # The gates<->implementation loop was the only cycle without its own cap;
            # repeated gate failures now hit a hard budget instead of burning spawns.
            if attempts["gate_failures"] >= data.get("budgets", {}).get("max_gate_failures_per_package", 3):
                return block_with_reason(data, args.actor, args.package_id, "gate failure budget exhausted",
                                         counter={"scope": "attempts", "key": "gate_failures"})
        model.record_event(data, "record-gate", data["phase"], data["phase"], args.actor, args.package_id, {"name": args.name, "status": args.status, "global": args.global_gate}, args.event_id)
        return True

    data, changed = model.mutate(path, args, "record-gate", update)
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
#
# Relocated here (from its original position beside VERIFICATION_AXIS) because its sole
# consumer, `normalize_findings`, lives in this module -- feature_state_lib.cli_review
# already needs `normalize_findings` from here, so the reverse import would be circular.
FINDING_BOOKKEEPING = frozenset({"verified_verdict", "verified_by", "verified_at", "verdict_reason",
                                 "verdict_evidence", "verification_history", "repair_attempts",
                                 "source_role"})


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
        from feature_state_lib.cli_review import require_verified  # deferred: see module docstring
        if data["phase"] != "PACKAGE_REPAIR":
            raise StateError(f"cannot record repair from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        # docs/adr/0023-*.md: freeze the repair ceiling on the FIRST record-repair of this
        # cycle (never reset here -- a new deep-review cycle starting fresh at PACKAGE_GATES
        # re-freezes candidate_identity, and the next repair after THAT will see a None
        # repair_ceiling again once that cycle's reviewer sends it back). Additive-only: a
        # package with no candidate_identity yet (freeze-candidate never ran) simply gets no
        # ceiling -- check-repair-ceiling.py treats an absent ceiling as nothing to check.
        if package.get("repair_ceiling") is None:
            original = (package.get("candidate_identity") or {}).get("changed_lines")
            if original is not None:
                cap_by_complexity = {"small": 40, "medium": 100, "high": 200}
                complexity = package.get("complexity")
                cap = cap_by_complexity.get(complexity, 100)
                budget = -(-original // 2)  # ceil(original / 2) without importing math
                package["repair_ceiling"] = {
                    "original_changed_lines": original,
                    "budget_lines": min(cap, budget),
                    "cap_source": f"complexity:{complexity or 'medium(default, complexity unset)'}",
                    "frozen_at": now(),
                }
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
                return block_with_reason(data, args.actor, args.package_id, f"repair budget exhausted for {finding['id']}",
                                         counter={"scope": "finding", "key": "repair_attempts", "finding_id": finding["id"]})
            finding["status"] = "closed"
        repair = {"finding_ids": ids, "changed_files": changed_files, "verification": args.verification or [], "at": now()}
        if getattr(args, "changed_lines", None) is not None:
            # Self-reported bookkeeping only -- check-repair-ceiling.py independently
            # re-measures from git before anything trusts this number as a gate verdict.
            repair["changed_lines"] = args.changed_lines
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
        model.record_event(data, "record-repair", "PACKAGE_REPAIR", data["phase"], args.actor, args.package_id,
                     repair_metadata, args.event_id)
        return True

    data, changed = model.mutate(path, args, "record-repair", update)
    return output_state(data, changed, path)


def cmd_record_delta_review(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        from feature_state_lib.cli_review import require_verified, merge_finding  # deferred: see module docstring
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
                return block_with_reason(data, args.actor, args.package_id, "deep review budget exhausted before full re-review",
                                         counter={"scope": "attempts", "key": "deep_review_cycles"})
            data["phase"] = "PACKAGE_REVIEW"
            package["status"] = "full_review_required"
        elif args.verdict == "repair_required":
            data["phase"] = "PACKAGE_REPAIR"
            package["status"] = "repair_required"
            package["repair_entry"] = "delta_review"
        else:
            return block_with_reason(data, args.actor, args.package_id, args.reason or "delta review blocked")
        model.record_event(data, "record-delta-review", "DELTA_REVIEW", data["phase"], args.actor, args.package_id, {"verdict": args.verdict, "requires_full_review": requires_full}, args.event_id)
        return True

    data, changed = model.mutate(path, args, "record-delta-review", update)
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
        model.record_event(data, "record-testing", "PACKAGE_TESTING", data["phase"], args.actor, args.package_id, {"status": args.status, "commands": args.command or []}, args.event_id)
        return True

    data, changed = model.mutate(path, args, "record-testing", update)
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
        model.record_event(data, "record-runtime-qa", "PACKAGE_RUNTIME_QA", data["phase"], args.actor, args.package_id, {"status": args.status, "url": args.url}, args.event_id)
        return True

    data, changed = model.mutate(path, args, "record-runtime-qa", update)
    return output_state(data, changed, path)


def cmd_accept_package(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        if data["phase"] != "PACKAGE_RUNTIME_QA":
            raise StateError(f"cannot accept package from phase {data['phase']}")
        # ADR-0028: accepting work against a silently-changed contract is the exact
        # waste this check exists to stop. resume/next only warn; HERE it blocks.
        drift = spec_drift(data)
        if drift:
            raise StateError(f"cannot accept package: {drift}")
        package = package_by_id(data, args.package_id)
        errors = package_accept_ready(data, package, args.actor)
        if errors:
            raise StateError("cannot accept package: " + "; ".join(errors))
        package["status"] = "accepted"
        data["phase"] = "PACKAGE_ACCEPTED"
        data["current_package_id"] = args.package_id
        model.record_event(data, "accept-package", "PACKAGE_RUNTIME_QA", "PACKAGE_ACCEPTED", args.actor, args.package_id, {}, args.event_id)
        return True

    data, changed = model.mutate(path, args, "accept-package", update)
    return output_state(data, changed, path)
