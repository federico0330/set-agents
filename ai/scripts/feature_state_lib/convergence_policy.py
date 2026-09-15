"""Pure HCE convergence policy — no subprocess/filesystem imports."""

from __future__ import annotations

import base64
import hashlib
import json
import uuid
from copy import deepcopy
from typing import Any

from feature_state_lib.convergence_constants import (
    ALL_FINDING_IDS,
    BUDGET_LINES,
    CAP_SOURCE,
    CHILD_A_PACKAGE_ID,
    CHILD_B_PACKAGE_ID,
    CIRCULAR_TASK,
    FEATURE_ID,
    FINDING_MAP,
    FOUR_PATH_UNION,
    ORIGINAL_CHANGED_LINES,
    OWNERSHIP_SNAPSHOT,
    PARENT_PACKAGE_ID,
    PROFILE,
    SCHEMA,
)
from feature_state_lib.convergence_errors import HceDenial


def canonical_json_digest(obj: dict[str, Any]) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def finding_snapshot_from_package(package: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = {f["id"]: f for f in package.get("findings", []) if isinstance(f, dict) and f.get("id")}
    snapshot = []
    for fid in ALL_FINDING_IDS:
        finding = by_id.get(fid)
        if not finding:
            raise HceDenial("HCE_DENIED", f"missing finding {fid}")
        if finding.get("verified_verdict") != "upheld":
            raise HceDenial("HCE_DENIED", f"finding {fid} is not upheld")
        snapshot.append({
            "id": fid,
            "severity": finding.get("severity", "high"),
            "status": finding.get("status", "open"),
            "repair_attempts": int(finding.get("repair_attempts", 0)),
            "verification_digest": finding.get("verification_digest") or canonical_json_digest({"id": fid}),
            "definition_digest": finding.get("definition_digest") or canonical_json_digest({"id": fid}),
        })
    return sorted(snapshot, key=lambda x: x["id"])


def binding_core(exc: dict[str, Any]) -> dict[str, Any]:
    return {
        "profile": exc.get("profile"),
        "exception_id": exc.get("exception_id"),
        "feature_id": exc.get("feature_id"),
        "parent_package_id": exc.get("parent_package_id"),
        "state_file_realpath": exc.get("state_file_realpath"),
        "repository_common_dir_realpath": exc.get("repository_common_dir_realpath"),
        "worktree_realpath": exc.get("worktree_realpath"),
        "repair_origin": exc.get("repair_origin"),
        "repair_ceiling_initialization": exc.get("repair_ceiling_initialization"),
        "finding_snapshot": exc.get("finding_snapshot"),
        "parent_repair_batches_initial": exc.get("parent_repair_batches_initial"),
        "finding_map": exc.get("finding_map"),
        "ownership_snapshot": exc.get("ownership_snapshot"),
        "children": exc.get("children"),
        "combined_review_identity": exc.get("combined_review_identity"),
    }


def compute_binding_digest(exc: dict[str, Any]) -> str:
    return canonical_json_digest(binding_core(exc))


def validate_profile(profile: str | None) -> None:
    if profile != PROFILE:
        raise HceDenial("HCE_DENIED", f"unsupported profile: {profile!r}")


def validate_prepare_context(data: dict[str, Any], package: dict[str, Any]) -> None:
    if data.get("feature_id") != FEATURE_ID:
        raise HceDenial("HCE_DENIED", f"feature_id must be {FEATURE_ID}")
    if package.get("package_id") != PARENT_PACKAGE_ID:
        raise HceDenial("HCE_DENIED", f"package must be {PARENT_PACKAGE_ID}")
    if data.get("phase") != "PACKAGE_PLANNING":
        raise HceDenial("HCE_DENIED", f"phase must be PACKAGE_PLANNING, got {data.get('phase')}")
    if package.get("convergence_exception"):
        raise HceDenial("HCE_DENIED", "convergence_exception already present")
    attempts = package.get("attempts") or {}
    if attempts.get("repair_batches", 0) != 0:
        raise HceDenial("HCE_DENIED", "repair_batches must be zero")
    identity = package.get("candidate_identity") or {}
    if identity.get("generation", 1) != 1:
        raise HceDenial("HCE_DENIED", "original generation must be 1")
    if identity.get("changed_lines") != ORIGINAL_CHANGED_LINES:
        raise HceDenial("HCE_STALE", f"changed_lines must be {ORIGINAL_CHANGED_LINES}")
    panels = [p for p in package.get("review_panels", []) if p.get("status") == "completed"]
    if not panels:
        raise HceDenial("HCE_DENIED", "completed historical panel required")
    finding_snapshot_from_package(package)
    circular = next((t for t in package.get("tasks", []) if t.get("id") == CIRCULAR_TASK), None)
    if not circular or circular.get("status") != "planned":
        raise HceDenial("HCE_DENIED", "exact circular task must remain planned")


def build_prepared_exception(
    *,
    state_realpath: str,
    repo_realpath: str,
    worktree_realpath: str | None,
    package: dict[str, Any],
    actor: str,
    event_id: str,
    authorized_by: str,
    reason: str,
    approval_evidence: str,
    at: str,
) -> dict[str, Any]:
    identity = deepcopy(package["candidate_identity"])
    finding_snapshot = finding_snapshot_from_package(package)
    exc_id = str(uuid.uuid4())
    exc: dict[str, Any] = {
        "schema": SCHEMA,
        "exception_id": exc_id,
        "profile": PROFILE,
        "feature_id": FEATURE_ID,
        "parent_package_id": PARENT_PACKAGE_ID,
        "status": "prepared",
        "state_file_realpath": state_realpath,
        "repository_common_dir_realpath": repo_realpath,
        "worktree_realpath": worktree_realpath,
        "repair_origin": identity,
        "repair_ceiling_initialization": {
            "original_changed_lines": ORIGINAL_CHANGED_LINES,
            "budget_lines": BUDGET_LINES,
            "cap_source": CAP_SOURCE,
            "frozen_at": at,
        },
        "finding_snapshot": finding_snapshot,
        "parent_repair_batches_initial": int((package.get("attempts") or {}).get("repair_batches", 0)),
        "finding_map": deepcopy(FINDING_MAP),
        "ownership_snapshot": deepcopy(OWNERSHIP_SNAPSHOT),
        "children": [],
        "combined_review_identity": None,
        "binding_digest": None,
        "preparation": {
            "at": at,
            "actor": actor,
            "event_id": event_id,
            "authorized_by": authorized_by,
            "reason": reason,
            "approval_evidence": approval_evidence,
        },
        "reentry": None,
        "final_panel_id": None,
        "authorization": None,
        "consumption": None,
    }
    return exc


def get_exception(package: dict[str, Any], exception_id: str) -> dict[str, Any]:
    exc = package.get("convergence_exception")
    if not exc or exc.get("exception_id") != exception_id:
        raise HceDenial("HCE_DENIED", f"unknown exception_id: {exception_id}")
    return exc


def validate_bindings_match(exc: dict[str, Any], state_realpath: str, repo_realpath: str, worktree_realpath: str) -> None:
    if exc.get("state_file_realpath") != state_realpath:
        raise HceDenial("HCE_STATE_PATH_MISMATCH", "state file path mismatch")
    if exc.get("repository_common_dir_realpath") != repo_realpath:
        raise HceDenial("HCE_REPO_MISMATCH", "repository common-dir mismatch")
    stored_wt = exc.get("worktree_realpath")
    if stored_wt is not None and stored_wt != worktree_realpath:
        raise HceDenial("HCE_REPO_MISMATCH", "worktree path mismatch")


def validate_inspect_eligible(exc: dict[str, Any], combined_live: dict[str, Any]) -> None:
    if exc.get("status") != "authorized":
        raise HceDenial("HCE_DENIED", f"status must be authorized, got {exc.get('status')}")
    stored = exc.get("combined_review_identity") or {}
    for key in ("candidate_commit", "candidate_tree", "paths_digest", "changed_lines"):
        if stored.get(key) != combined_live.get(key):
            raise HceDenial("HCE_STALE", f"combined identity mismatch on {key}")
    if set(combined_live.get("changed_paths", [])) != set(FOUR_PATH_UNION):
        raise HceDenial("HCE_STALE", "changed path union mismatch")


def validate_consume_ready(exc: dict[str, Any], combined_live: dict[str, Any]) -> None:
    if exc.get("status") == "consumed":
        raise HceDenial("HCE_REPLAY", "already consumed")
    validate_inspect_eligible(exc, combined_live)


def build_consumption(exc: dict[str, Any], *, actor: str, event_id: str, at: str, revision: int) -> dict[str, Any]:
    outcome_id = str(uuid.uuid4())
    return {
        "outcome_id": outcome_id,
        "at": at,
        "actor": actor,
        "event_id": event_id,
        "binding_digest": exc.get("binding_digest"),
        "combined_review_identity": deepcopy(exc.get("combined_review_identity")),
        "panel_id": exc.get("final_panel_id"),
        "committed_revision": revision + 1,
    }


def _package_map(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {p["package_id"]: p for p in data.get("packages", []) if p.get("package_id")}


def validate_reenter_context(data: dict[str, Any], package: dict[str, Any], exc: dict[str, Any]) -> None:
    if exc.get("status") != "prepared":
        raise HceDenial("HCE_DENIED", f"status must be prepared, got {exc.get('status')}")
    if exc.get("children"):
        raise HceDenial("HCE_REPLAY", "reentry already recorded")
    if exc.get("combined_review_identity") is not None:
        raise HceDenial("HCE_REPLAY", "combined identity already set")
    if data.get("phase") != "PACKAGE_PLANNING":
        raise HceDenial("HCE_DENIED", f"phase must be PACKAGE_PLANNING, got {data.get('phase')}")
    current = data.get("current_package_id")
    if current not in {PARENT_PACKAGE_ID, CHILD_B_PACKAGE_ID}:
        raise HceDenial("HCE_DENIED", f"current package must be parent or child B, got {current}")
    if package.get("package_id") != PARENT_PACKAGE_ID:
        raise HceDenial("HCE_DENIED", f"reenter targets parent package {PARENT_PACKAGE_ID}")


def validate_child_package(pkg: dict[str, Any], package_id: str) -> dict[str, Any]:
    if pkg.get("status") != "accepted":
        raise HceDenial("HCE_STALE", f"{package_id} must be accepted")
    receipt = pkg.get("receipt")
    identity = pkg.get("candidate_identity")
    if not receipt or not identity:
        raise HceDenial("HCE_STALE", f"{package_id} missing receipt or candidate_identity")
    if receipt.get("terminal_state") != "accepted":
        raise HceDenial("HCE_STALE", f"{package_id} receipt not accepted")
    for field in ("base_tree", "candidate_tree", "paths_digest", "generation"):
        if receipt.get(field) != identity.get(field):
            raise HceDenial("HCE_STALE", f"{package_id} receipt mismatch on {field}")
    return identity


def validate_receipt_chain(origin: dict[str, Any], child_a: dict[str, Any], child_b: dict[str, Any]) -> None:
    id_a = validate_child_package(child_a, CHILD_A_PACKAGE_ID)
    id_b = validate_child_package(child_b, CHILD_B_PACKAGE_ID)
    if child_a["receipt"]["base_tree"] != origin.get("candidate_tree"):
        raise HceDenial("HCE_STALE", "child A receipt base_tree must equal original candidate tree")
    if child_b["receipt"]["base_tree"] != id_a.get("candidate_tree"):
        raise HceDenial("HCE_STALE", "child B receipt base_tree must equal child A candidate tree")


def validate_child_output_paths(child_records: list[dict[str, Any]]) -> None:
    all_paths: list[str] = []
    for record in child_records:
        paths = [base64.b64decode(item).decode() for item in record.get("output_paths_b64", [])]
        all_paths.extend(paths)
    if sorted(all_paths) != sorted(FOUR_PATH_UNION):
        raise HceDenial("HCE_STALE", "child output path union mismatch")
    if len(all_paths) != len(set(all_paths)):
        raise HceDenial("HCE_STALE", "overlapping child output paths")


def validate_combined_measurement(combined: dict[str, Any], origin: dict[str, Any], head_commit: str) -> None:
    if combined.get("base_commit") != origin.get("candidate_ref"):
        raise HceDenial("HCE_STALE", "combined base_commit must equal original candidate ref")
    if combined.get("candidate_commit") != head_commit:
        raise HceDenial("HCE_STALE", "combined candidate_commit must equal HEAD")
    if set(combined.get("changed_paths", [])) != set(FOUR_PATH_UNION):
        raise HceDenial("HCE_STALE", "combined changed path union mismatch")


def validate_authorize_context(data: dict[str, Any], package: dict[str, Any], exc: dict[str, Any]) -> None:
    if exc.get("status") != "prepared":
        raise HceDenial("HCE_DENIED", f"status must be prepared, got {exc.get('status')}")
    if exc.get("authorization"):
        raise HceDenial("HCE_REPLAY", "authorization already recorded")
    if data.get("phase") != "PACKAGE_REPAIR":
        raise HceDenial("HCE_DENIED", f"phase must be PACKAGE_REPAIR, got {data.get('phase')}")
    panel_id = exc.get("final_panel_id")
    if not panel_id:
        raise HceDenial("HCE_DENIED", "bound final panel required")
    panels = [p for p in package.get("review_panels", []) if p.get("panel_id") == panel_id]
    if not panels or panels[0].get("status") != "completed":
        raise HceDenial("HCE_DENIED", "final panel must be completed")
    if panels[0].get("verdict") != "repair_required":
        raise HceDenial("HCE_DENIED", "final panel verdict must be repair_required")
    if not exc.get("children") or not exc.get("combined_review_identity"):
        raise HceDenial("HCE_DENIED", "reentry snapshots required before authorization")


def build_authorization(
    exc: dict[str, Any],
    *,
    actor: str,
    event_id: str,
    authorized_by: str,
    reason: str,
    approval_evidence: str,
    at: str,
) -> dict[str, Any]:
    return {
        "at": at,
        "actor": actor,
        "event_id": event_id,
        "authorized_by": authorized_by,
        "reason": reason,
        "approval_evidence": approval_evidence,
        "panel_id": exc.get("final_panel_id"),
        "binding_digest": exc.get("binding_digest"),
    }


def validate_verify_outcome(exc: dict[str, Any]) -> str:
    if exc.get("status") != "consumed":
        raise HceDenial("HCE_OUTCOME_INVALID", "outcome not consumed")
    consumption = exc.get("consumption")
    if not consumption or not consumption.get("outcome_id"):
        raise HceDenial("HCE_OUTCOME_INVALID", "missing consumption outcome_id")
    return consumption["outcome_id"]
