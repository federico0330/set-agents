"""Pure HCE convergence policy — no subprocess/filesystem imports."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import re
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

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.I,
)
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z)$")
EXPECTED_CHILD_ORDER = (CHILD_A_PACKAGE_ID, CHILD_B_PACKAGE_ID)

CONVERGENCE_TOP_KEYS = frozenset({
    "schema", "exception_id", "profile", "feature_id", "parent_package_id", "status",
    "state_file_realpath", "repository_common_dir_realpath", "worktree_realpath",
    "repair_origin", "repair_ceiling_initialization", "finding_snapshot",
    "parent_repair_batches_initial", "finding_map", "ownership_snapshot", "children",
    "combined_review_identity", "binding_digest", "preparation", "reentry",
    "final_panel_id", "authorization", "consumption",
})

FINDING_SNAPSHOT_KEYS = frozenset({
    "id", "severity", "status", "repair_attempts", "verification_digest", "definition_digest",
})

CHILD_RECORD_KEYS = frozenset({
    "package_id", "candidate_identity", "receipt", "receipt_digest", "candidate_commit",
    "output_paths_b64", "output_paths_digest",
})

COMBINED_IDENTITY_KEYS = frozenset({
    "generation", "base_commit", "base_tree", "candidate_commit", "candidate_tree",
    "paths_digest", "changed_lines",
})

RECEIPT_SCHEMA = "set-agentes.integration-receipt/v1"
RECEIPT_KEYS = frozenset({
    "schema", "package_id", "generation", "base_tree", "candidate_tree", "paths_digest",
    "review_verdict", "delta_review_verdict", "verifications_summary", "terminal_state",
    "minted_at", "minted_by",
})
VERIFICATIONS_SUMMARY_KEYS = frozenset({"upheld", "refuted"})
REPAIR_ORIGIN_KEYS = frozenset({
    "baseline_ref", "candidate_ref", "base_tree", "candidate_tree", "paths_digest",
    "changed_lines", "generation", "frozen_at", "frozen_by",
})
REPAIR_CEILING_KEYS = frozenset({"original_changed_lines", "budget_lines", "cap_source", "frozen_at"})
PREPARATION_KEYS = frozenset({"at", "actor", "event_id", "authorized_by", "reason", "approval_evidence"})
REENTRY_KEYS = frozenset({"at", "actor", "event_id"})
AUTHORIZATION_KEYS = frozenset({
    "at", "actor", "event_id", "authorized_by", "reason", "approval_evidence",
    "panel_id", "binding_digest",
})
CONSUMPTION_KEYS = frozenset({
    "outcome_id", "at", "actor", "event_id", "binding_digest",
    "combined_review_identity", "panel_id", "committed_revision",
})
OWNERSHIP_ENTRY_KEYS = frozenset({"child_package_id", "owned_paths"})
FINDING_MAP_ENTRY_KEYS = frozenset({"child_package_id", "finding_ids"})
CANDIDATE_IDENTITY_KEYS = frozenset({
    "baseline_ref", "candidate_ref", "base_tree", "candidate_tree", "paths_digest",
    "changed_lines", "generation", "frozen_at", "frozen_by",
})


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
        verification_digest = finding.get("verification_digest")
        definition_digest = finding.get("definition_digest")
        if not verification_digest or not definition_digest:
            raise HceDenial("HCE_DENIED", f"finding {fid} missing verification/definition digest")
        if not DIGEST_RE.match(str(verification_digest)) or not DIGEST_RE.match(str(definition_digest)):
            raise HceDenial("HCE_DENIED", f"finding {fid} has invalid digest format")
        expected_verification = canonical_json_digest({
            "id": fid,
            "evidence": finding.get("evidence", ""),
        })
        expected_definition = canonical_json_digest({
            "id": fid,
            "required_outcome": finding.get("required_outcome", ""),
            "severity": finding.get("severity", "high"),
        })
        if verification_digest != expected_verification:
            raise HceDenial("HCE_DENIED", f"finding {fid} verification_digest mismatch")
        if definition_digest != expected_definition:
            raise HceDenial("HCE_DENIED", f"finding {fid} definition_digest mismatch")
        snapshot.append({
            "id": fid,
            "severity": finding.get("severity", "high"),
            "status": finding.get("status", "open"),
            "repair_attempts": int(finding.get("repair_attempts", 0)),
            "verification_digest": verification_digest,
            "definition_digest": definition_digest,
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


def _validate_planned_tasks(package: dict[str, Any]) -> None:
    circular = None
    for task in package.get("tasks", []):
        task_id = task.get("id")
        status = task.get("status")
        if task_id == CIRCULAR_TASK:
            circular = task
            if status != "planned":
                raise HceDenial("HCE_DENIED", "exact circular task must remain planned")
            continue
        if status == "planned":
            raise HceDenial("HCE_DENIED", f"unexpected planned task: {task_id}")
    if not circular:
        raise HceDenial("HCE_DENIED", "exact circular task must remain planned")


def validate_original_identity_fresh(stored: dict[str, Any], fresh: dict[str, Any]) -> None:
    for field in ("base_tree", "candidate_tree", "paths_digest", "changed_lines"):
        if stored.get(field) != fresh.get(field):
            raise HceDenial("HCE_STALE", f"original identity mismatch on {field}")
    if stored.get("baseline_ref") != fresh.get("baseline_ref"):
        raise HceDenial("HCE_STALE", "original baseline_ref mismatch")
    if stored.get("candidate_ref") != fresh.get("candidate_ref"):
        raise HceDenial("HCE_STALE", "original candidate_ref mismatch")


def validate_prepare_context(
    data: dict[str, Any],
    package: dict[str, Any],
    fresh_original: dict[str, Any],
) -> None:
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
    validate_original_identity_fresh(identity, fresh_original)
    if fresh_original.get("changed_lines") != ORIGINAL_CHANGED_LINES:
        raise HceDenial("HCE_STALE", f"changed_lines must be {ORIGINAL_CHANGED_LINES}")
    panels = [p for p in package.get("review_panels", []) if p.get("status") == "completed"]
    if not panels:
        raise HceDenial("HCE_DENIED", "completed historical panel required")
    finding_snapshot_from_package(package)
    _validate_planned_tasks(package)


def build_prepared_exception(
    *,
    state_realpath: str,
    repo_realpath: str,
    worktree_realpath: str | None,
    package: dict[str, Any],
    fresh_original: dict[str, Any],
    actor: str,
    event_id: str,
    authorized_by: str,
    reason: str,
    approval_evidence: str,
    at: str,
) -> dict[str, Any]:
    identity = {k: v for k, v in fresh_original.items() if k != "changed_paths"}
    for provenance in ("frozen_at", "frozen_by", "generation"):
        if provenance in (package.get("candidate_identity") or {}):
            identity[provenance] = package["candidate_identity"][provenance]
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


def _validate_receipt_exact(receipt: dict[str, Any], package_id: str, identity: dict[str, Any]) -> None:
    if not isinstance(receipt, dict):
        raise HceDenial("HCE_STALE", f"{package_id} receipt must be object")
    unknown = set(receipt) - RECEIPT_KEYS
    if unknown:
        raise HceDenial("HCE_STALE", f"{package_id} receipt unknown keys: {sorted(unknown)}")
    missing = RECEIPT_KEYS - set(receipt)
    if missing:
        raise HceDenial("HCE_STALE", f"{package_id} receipt missing keys: {sorted(missing)}")
    if receipt.get("schema") != RECEIPT_SCHEMA:
        raise HceDenial("HCE_STALE", f"{package_id} receipt schema mismatch")
    if receipt.get("package_id") != package_id:
        raise HceDenial("HCE_STALE", f"{package_id} receipt package_id mismatch")
    if receipt.get("terminal_state") != "accepted":
        raise HceDenial("HCE_STALE", f"{package_id} receipt not accepted")
    if receipt.get("review_verdict") != "pass":
        raise HceDenial("HCE_STALE", f"{package_id} receipt review_verdict must be pass")
    if receipt.get("delta_review_verdict") != "pass":
        raise HceDenial("HCE_STALE", f"{package_id} receipt delta_review_verdict must be pass")
    summary = receipt.get("verifications_summary")
    if not isinstance(summary, dict) or set(summary) != VERIFICATIONS_SUMMARY_KEYS:
        raise HceDenial("HCE_STALE", f"{package_id} receipt verifications_summary shape mismatch")
    for key in VERIFICATIONS_SUMMARY_KEYS:
        if not isinstance(summary.get(key), int) or summary[key] < 0:
            raise HceDenial("HCE_STALE", f"{package_id} receipt verifications_summary.{key} invalid")
    for field in ("base_tree", "candidate_tree", "paths_digest", "generation"):
        value = receipt.get(field)
        if field in ("base_tree", "candidate_tree") and not SHA_RE.match(str(value)):
            raise HceDenial("HCE_STALE", f"{package_id} receipt invalid {field}")
        if field == "paths_digest" and not DIGEST_RE.match(str(value)):
            raise HceDenial("HCE_STALE", f"{package_id} receipt invalid paths_digest")
        if field == "generation" and (not isinstance(value, int) or value < 1):
            raise HceDenial("HCE_STALE", f"{package_id} receipt invalid generation")
        if value != identity.get(field):
            raise HceDenial("HCE_STALE", f"{package_id} receipt mismatch on {field}")
    for field in ("minted_at", "minted_by"):
        if not isinstance(receipt.get(field), str) or not receipt[field]:
            raise HceDenial("HCE_STALE", f"{package_id} receipt missing {field}")


def validate_child_package(pkg: dict[str, Any], package_id: str) -> dict[str, Any]:
    if pkg.get("status") != "accepted":
        raise HceDenial("HCE_STALE", f"{package_id} must be accepted")
    receipt = pkg.get("receipt")
    identity = pkg.get("candidate_identity")
    if not receipt or not identity:
        raise HceDenial("HCE_STALE", f"{package_id} missing receipt or candidate_identity")
    if not isinstance(identity, dict):
        raise HceDenial("HCE_STALE", f"{package_id} candidate_identity must be object")
    unknown_identity = set(identity) - CANDIDATE_IDENTITY_KEYS
    if unknown_identity:
        raise HceDenial("HCE_STALE", f"{package_id} candidate_identity unknown keys: {sorted(unknown_identity)}")
    _validate_receipt_exact(receipt, package_id, identity)
    if identity.get("candidate_ref") and not SHA_RE.match(str(identity["candidate_ref"])):
        raise HceDenial("HCE_STALE", f"{package_id} invalid candidate_ref")
    return identity


def validate_receipt_chain(
    origin: dict[str, Any],
    child_a: dict[str, Any],
    child_b: dict[str, Any],
    *,
    head_commit: str,
    head_tree: str,
) -> None:
    id_a = validate_child_package(child_a, CHILD_A_PACKAGE_ID)
    id_b = validate_child_package(child_b, CHILD_B_PACKAGE_ID)
    if child_a["receipt"]["base_tree"] != origin.get("candidate_tree"):
        raise HceDenial("HCE_STALE", "child A receipt base_tree must equal original candidate tree")
    if child_b["receipt"]["base_tree"] != id_a.get("candidate_tree"):
        raise HceDenial("HCE_STALE", "child B receipt base_tree must equal child A candidate tree")
    if id_b.get("candidate_ref") != head_commit:
        raise HceDenial("HCE_STALE", "child B candidate_ref must equal HEAD commit")
    if id_b.get("candidate_tree") != head_tree:
        raise HceDenial("HCE_STALE", "child B candidate_tree must equal HEAD tree")
    if child_b["receipt"].get("candidate_tree") != head_tree:
        raise HceDenial("HCE_STALE", "child B receipt candidate_tree must equal HEAD tree")


def _decode_output_paths_b64(encoded_paths: list[Any], *, label: str) -> list[str]:
    paths: list[str] = []
    for item in encoded_paths:
        if not isinstance(item, str):
            raise HceDenial("HCE_STALE", f"{label} output_paths_b64 entries must be strings")
        try:
            paths.append(base64.b64decode(item, validate=True).decode("utf-8"))
        except (binascii.Error, UnicodeDecodeError) as exc:
            raise HceDenial("HCE_STALE", f"{label} output_paths_b64 malformed") from exc
    return paths


def validate_child_output_paths(child_records: list[dict[str, Any]]) -> None:
    expected = {
        CHILD_A_PACKAGE_ID: OWNERSHIP_SNAPSHOT[0]["owned_paths"],
        CHILD_B_PACKAGE_ID: OWNERSHIP_SNAPSHOT[1]["owned_paths"],
    }
    if len(child_records) != 2:
        raise HceDenial("HCE_STALE", "expected exactly two child records")
    for record in child_records:
        package_id = record.get("package_id")
        paths = _decode_output_paths_b64(record.get("output_paths_b64", []), label=str(package_id))
        if package_id not in expected:
            raise HceDenial("HCE_STALE", f"unexpected child package {package_id}")
        if sorted(paths) != sorted(expected[package_id]):
            raise HceDenial("HCE_STALE", f"{package_id} output paths mismatch")
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


def _live_child_record_digest(pkg: dict[str, Any], package_id: str) -> str:
    receipt = pkg.get("receipt")
    if not isinstance(receipt, dict):
        raise HceDenial("HCE_STALE", f"{package_id} missing receipt")
    return canonical_json_digest(receipt)


FreshChildOutputs = dict[str, tuple[list[str], str]]


def validate_verify_finding_evolution(exc: dict[str, Any], package: dict[str, Any]) -> None:
    """Allow unchanged snapshot or exact linked-repair successor; deny unlinked drift."""
    stored_by_id = {item["id"]: item for item in exc.get("finding_snapshot") or []}
    live_by_id: dict[str, dict[str, Any]] = {}
    for finding in package.get("findings", []):
        if isinstance(finding, dict) and finding.get("id"):
            live_by_id[finding["id"]] = finding
    if set(live_by_id.keys()) != set(stored_by_id.keys()):
        raise HceDenial("HCE_STALE", "finding set changed")
    initial_batch = int(exc.get("parent_repair_batches_initial", 0))
    live_batch = int((package.get("attempts") or {}).get("repair_batches", 0))
    any_change = False
    all_linked_successor = True
    for fid, stored in stored_by_id.items():
        live = live_by_id[fid]
        if live.get("severity") != stored.get("severity"):
            raise HceDenial("HCE_STALE", f"finding {fid} severity drift")
        if live.get("verification_digest") != stored.get("verification_digest"):
            raise HceDenial("HCE_STALE", f"finding {fid} verification_digest drift")
        if live.get("definition_digest") != stored.get("definition_digest"):
            raise HceDenial("HCE_STALE", f"finding {fid} definition_digest drift")
        if live.get("verified_verdict") != "upheld":
            raise HceDenial("HCE_STALE", f"finding {fid} verdict no longer upheld")
        stored_status = stored.get("status")
        stored_attempts = int(stored.get("repair_attempts", 0))
        live_status = live.get("status")
        live_attempts = int(live.get("repair_attempts", 0))
        if live_status != stored_status or live_attempts != stored_attempts:
            any_change = True
        if live_status != "closed" or live_attempts != stored_attempts + 1:
            all_linked_successor = False
    if not any_change:
        if live_batch != initial_batch:
            raise HceDenial("HCE_STALE", "repair_batches changed without linked repair")
        return
    if all_linked_successor and live_batch == initial_batch + 1:
        return
    raise HceDenial("HCE_STALE", "unlinked finding evolution")


def _compare_stored_children(
    exc: dict[str, Any],
    child_a: dict[str, Any],
    child_b: dict[str, Any],
    *,
    fresh_child_outputs: FreshChildOutputs | None = None,
) -> None:
    stored_children = exc.get("children") or []
    if len(stored_children) != 2:
        raise HceDenial("HCE_STALE", "stored child records missing")
    live_by_id = {CHILD_A_PACKAGE_ID: child_a, CHILD_B_PACKAGE_ID: child_b}
    for stored in stored_children:
        package_id = stored.get("package_id")
        live_pkg = live_by_id.get(package_id)
        if not live_pkg:
            raise HceDenial("HCE_STALE", f"unexpected stored child {package_id}")
        validate_child_package(live_pkg, package_id)
        live_identity = live_pkg["candidate_identity"]
        live_receipt = live_pkg["receipt"]
        stored_identity = stored.get("candidate_identity")
        stored_receipt = stored.get("receipt")
        if not isinstance(stored_identity, dict) or stored_identity != live_identity:
            raise HceDenial("HCE_STALE", f"{package_id} stored candidate_identity drift")
        if not isinstance(stored_receipt, dict) or stored_receipt != live_receipt:
            raise HceDenial("HCE_STALE", f"{package_id} stored receipt drift")
        live_digest = _live_child_record_digest(live_pkg, package_id)
        if stored.get("receipt_digest") != live_digest:
            raise HceDenial("HCE_STALE", f"{package_id} receipt_digest drift")
        for field in ("candidate_commit", "output_paths_digest"):
            if stored.get(field) is None:
                raise HceDenial("HCE_STALE", f"{package_id} stored child missing {field}")
        if stored.get("candidate_commit") != live_identity.get("candidate_ref"):
            raise HceDenial("HCE_STALE", f"{package_id} stored candidate_commit drift")
        if fresh_child_outputs is not None:
            measured = fresh_child_outputs.get(package_id)
            if measured is None:
                raise HceDenial("HCE_STALE", f"{package_id} missing fresh child output measurement")
            fresh_b64, fresh_digest = measured
            if stored.get("output_paths_b64") != fresh_b64:
                raise HceDenial("HCE_STALE", f"{package_id} output_paths_b64 drift")
            if stored.get("output_paths_digest") != fresh_digest:
                raise HceDenial("HCE_STALE", f"{package_id} output_paths_digest drift")


def rederive_frozen_binding(
    exc: dict[str, Any],
    data: dict[str, Any],
    package: dict[str, Any],
    combined_live: dict[str, Any],
    *,
    fresh_child_outputs: FreshChildOutputs | None = None,
    allow_successor_finding_evolution: bool = False,
) -> None:
    """Freshly rederive findings/receipts/panel/binding before authorize/consume/verify."""
    if allow_successor_finding_evolution:
        validate_verify_finding_evolution(exc, package)
    else:
        fresh_findings = finding_snapshot_from_package(package)
        stored_findings = exc.get("finding_snapshot") or []
        if canonical_json_digest({"items": stored_findings}) != canonical_json_digest({"items": fresh_findings}):
            raise HceDenial("HCE_STALE", "finding snapshot drift")
    packages = _package_map(data)
    child_a = packages.get(CHILD_A_PACKAGE_ID)
    child_b = packages.get(CHILD_B_PACKAGE_ID)
    if not child_a or not child_b:
        raise HceDenial("HCE_STALE", "missing fixed child packages")
    origin = exc.get("repair_origin") or {}
    head_commit = combined_live.get("candidate_commit")
    head_tree = combined_live.get("candidate_tree")
    if not head_commit or not head_tree:
        raise HceDenial("HCE_STALE", "missing live HEAD identity")
    validate_receipt_chain(origin, child_a, child_b, head_commit=head_commit, head_tree=head_tree)
    _compare_stored_children(exc, child_a, child_b, fresh_child_outputs=fresh_child_outputs)
    stored = exc.get("combined_review_identity") or {}
    for key in ("candidate_commit", "candidate_tree", "paths_digest", "changed_lines", "base_commit", "base_tree"):
        if stored.get(key) != combined_live.get(key):
            raise HceDenial("HCE_STALE", f"combined identity drift on {key}")
    if exc.get("finding_map") != FINDING_MAP:
        raise HceDenial("HCE_STALE", "finding_map drift")
    if exc.get("ownership_snapshot") != OWNERSHIP_SNAPSHOT:
        raise HceDenial("HCE_STALE", "ownership_snapshot drift")
    expected_digest = compute_binding_digest(exc)
    if exc.get("binding_digest") != expected_digest:
        raise HceDenial("HCE_STALE", "binding_digest drift")


def validate_verify_outcome(
    exc: dict[str, Any],
    package: dict[str, Any],
    combined_live: dict[str, Any],
    *,
    data: dict[str, Any] | None = None,
    fresh_child_outputs: FreshChildOutputs | None = None,
) -> str:
    if exc.get("status") != "consumed":
        raise HceDenial("HCE_OUTCOME_INVALID", "outcome not consumed")
    consumption = exc.get("consumption")
    if not consumption or not consumption.get("outcome_id"):
        raise HceDenial("HCE_OUTCOME_INVALID", "missing consumption outcome_id")
    if not isinstance(consumption, dict) or set(consumption) != CONSUMPTION_KEYS:
        raise HceDenial("HCE_OUTCOME_INVALID", "consumption shape mismatch")
    outcome_id = consumption["outcome_id"]
    if not UUID_RE.match(str(outcome_id)):
        raise HceDenial("HCE_OUTCOME_INVALID", "invalid outcome_id format")
    if data is not None:
        rederive_frozen_binding(
            exc, data, package, combined_live,
            fresh_child_outputs=fresh_child_outputs,
            allow_successor_finding_evolution=True,
        )
    stored_combined = consumption.get("combined_review_identity") or {}
    if not isinstance(stored_combined, dict) or set(stored_combined) != COMBINED_IDENTITY_KEYS:
        raise HceDenial("HCE_OUTCOME_INVALID", "consumption combined_review_identity shape mismatch")
    for key in COMBINED_IDENTITY_KEYS:
        if stored_combined.get(key) != combined_live.get(key):
            raise HceDenial("HCE_OUTCOME_INVALID", f"live combined identity mismatch on {key}")
    if consumption.get("binding_digest") != exc.get("binding_digest"):
        raise HceDenial("HCE_OUTCOME_INVALID", "consumption binding_digest mismatch")
    if consumption.get("panel_id") != exc.get("final_panel_id"):
        raise HceDenial("HCE_OUTCOME_INVALID", "consumption panel_id mismatch")
    auth = exc.get("authorization") or {}
    if auth.get("panel_id") != exc.get("final_panel_id"):
        raise HceDenial("HCE_OUTCOME_INVALID", "authorization panel linkage mismatch")
    if auth.get("binding_digest") != exc.get("binding_digest"):
        raise HceDenial("HCE_OUTCOME_INVALID", "authorization binding_digest mismatch")
    committed = consumption.get("committed_revision")
    if not isinstance(committed, int) or committed < 1:
        raise HceDenial("HCE_OUTCOME_INVALID", "consumption committed_revision invalid")
    if data is not None and int(data.get("revision", 0)) < committed:
        raise HceDenial("HCE_OUTCOME_INVALID", "consumption committed_revision ahead of state")
    gate = None
    for item in package.get("gates", []):
        if item.get("name") == "repair-ceiling":
            gate = item
            break
    if not gate or gate.get("status") != "pass":
        raise HceDenial("HCE_OUTCOME_INVALID", "missing required repair-ceiling gate")
    if gate.get("convergence_outcome_id") != outcome_id:
        raise HceDenial("HCE_OUTCOME_INVALID", "repair-ceiling gate outcome linkage mismatch")
    expected_digest = compute_binding_digest(exc)
    if exc.get("binding_digest") != expected_digest:
        raise HceDenial("HCE_OUTCOME_INVALID", "binding_digest drift")
    return outcome_id


def _schema_errors(errors: list[str], package_id: str, label: str, block: Any, required_keys: frozenset[str]) -> None:
    if not isinstance(block, dict):
        errors.append(f"{package_id}: {label} must be an object")
        return
    unknown = set(block) - required_keys
    if unknown:
        errors.append(f"{package_id}: {label} unknown keys: {sorted(unknown)}")
    missing = required_keys - set(block)
    if missing:
        errors.append(f"{package_id}: {label} missing keys: {sorted(missing)}")


def _require_nonempty_str(errors: list[str], package_id: str, label: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{package_id}: {label} must be a nonempty string")


def _require_utc(errors: list[str], package_id: str, label: str, value: Any) -> None:
    if not isinstance(value, str) or not UTC_RE.match(value):
        errors.append(f"{package_id}: {label} must be UTC ISO8601")


def _require_int_not_bool(errors: list[str], package_id: str, label: str, value: Any, *, minimum: int = 0) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        errors.append(f"{package_id}: {label} must be int >= {minimum}")


def _validate_provenance_block(
    errors: list[str],
    package_id: str,
    label: str,
    block: Any,
    required_keys: frozenset[str],
    *,
    require_approval: bool = False,
) -> None:
    _schema_errors(errors, package_id, label, block, required_keys)
    if not isinstance(block, dict):
        return
    _require_utc(errors, package_id, f"{label}.at", block.get("at"))
    _require_nonempty_str(errors, package_id, f"{label}.actor", block.get("actor"))
    _require_nonempty_str(errors, package_id, f"{label}.event_id", block.get("event_id"))
    if require_approval:
        _require_nonempty_str(errors, package_id, f"{label}.authorized_by", block.get("authorized_by"))
        _require_nonempty_str(errors, package_id, f"{label}.reason", block.get("reason"))
        _require_nonempty_str(errors, package_id, f"{label}.approval_evidence", block.get("approval_evidence"))


def _validate_child_record_schema(errors: list[str], package_id: str, child: Any) -> None:
    if not isinstance(child, dict) or set(child) != CHILD_RECORD_KEYS:
        errors.append(f"{package_id}: child record shape mismatch")
        return
    child_id = child.get("package_id")
    if child_id not in EXPECTED_CHILD_ORDER:
        errors.append(f"{package_id}: child package_id invalid: {child_id!r}")
    if not DIGEST_RE.match(str(child.get("receipt_digest", ""))):
        errors.append(f"{package_id}: child receipt_digest invalid")
    if not DIGEST_RE.match(str(child.get("output_paths_digest", ""))):
        errors.append(f"{package_id}: child output_paths_digest invalid")
    if not SHA_RE.match(str(child.get("candidate_commit", ""))):
        errors.append(f"{package_id}: child candidate_commit invalid")
    identity = child.get("candidate_identity")
    if not isinstance(identity, dict) or set(identity) != CANDIDATE_IDENTITY_KEYS:
        errors.append(f"{package_id}: child candidate_identity shape mismatch")
    elif isinstance(identity, dict):
        for field in ("baseline_ref", "candidate_ref", "base_tree", "candidate_tree"):
            if not SHA_RE.match(str(identity.get(field, ""))):
                errors.append(f"{package_id}: child candidate_identity invalid {field}")
        if not DIGEST_RE.match(str(identity.get("paths_digest", ""))):
            errors.append(f"{package_id}: child candidate_identity invalid paths_digest")
        _require_int_not_bool(errors, package_id, "child candidate_identity.changed_lines", identity.get("changed_lines"))
        _require_int_not_bool(errors, package_id, "child candidate_identity.generation", identity.get("generation"), minimum=1)
        _require_utc(errors, package_id, "child candidate_identity.frozen_at", identity.get("frozen_at"))
        _require_nonempty_str(errors, package_id, "child candidate_identity.frozen_by", identity.get("frozen_by"))
    receipt = child.get("receipt")
    if not isinstance(receipt, dict) or set(receipt) != RECEIPT_KEYS:
        errors.append(f"{package_id}: child receipt shape mismatch")
    output_paths = child.get("output_paths_b64")
    if not isinstance(output_paths, list) or not output_paths:
        errors.append(f"{package_id}: child output_paths_b64 must be a nonempty array")
    elif isinstance(output_paths, list):
        for idx, item in enumerate(output_paths):
            if not isinstance(item, str):
                errors.append(f"{package_id}: child output_paths_b64[{idx}] must be string")
            else:
                try:
                    base64.b64decode(item, validate=True)
                except binascii.Error:
                    errors.append(f"{package_id}: child output_paths_b64[{idx}] malformed base64")


def validate_convergence_exception(exc: dict[str, Any], package_id: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(exc, dict):
        return [f"{package_id}: convergence_exception must be an object"]
    unknown = set(exc) - CONVERGENCE_TOP_KEYS
    if unknown:
        errors.append(f"{package_id}: convergence_exception unknown keys: {sorted(unknown)}")
    missing = CONVERGENCE_TOP_KEYS - set(exc)
    if missing:
        errors.append(f"{package_id}: convergence_exception missing keys: {sorted(missing)}")
    if errors:
        return errors
    if exc.get("schema") != SCHEMA:
        errors.append(f"{package_id}: invalid convergence schema")
    if exc.get("profile") != PROFILE:
        errors.append(f"{package_id}: invalid convergence profile")
    if exc.get("feature_id") != FEATURE_ID:
        errors.append(f"{package_id}: invalid convergence feature_id")
    if exc.get("parent_package_id") != PARENT_PACKAGE_ID:
        errors.append(f"{package_id}: invalid parent_package_id")
    status = exc.get("status")
    if status not in {"prepared", "authorized", "consumed"}:
        errors.append(f"{package_id}: invalid convergence status {status!r}")
    if not UUID_RE.match(str(exc.get("exception_id", ""))):
        errors.append(f"{package_id}: invalid exception_id")
    for key in ("state_file_realpath", "repository_common_dir_realpath"):
        value = exc.get(key)
        if not isinstance(value, str) or not os.path.isabs(value):
            errors.append(f"{package_id}: {key} must be absolute path string")
    wt = exc.get("worktree_realpath")
    if wt is not None and (not isinstance(wt, str) or not os.path.isabs(wt)):
        errors.append(f"{package_id}: worktree_realpath must be absolute path string or null")
    _schema_errors(errors, package_id, "repair_origin", exc.get("repair_origin"), REPAIR_ORIGIN_KEYS)
    origin = exc.get("repair_origin") or {}
    if isinstance(origin, dict):
        for field in ("baseline_ref", "candidate_ref", "base_tree", "candidate_tree"):
            if field in origin and not SHA_RE.match(str(origin.get(field, ""))):
                errors.append(f"{package_id}: repair_origin invalid {field}")
        if "paths_digest" in origin and not DIGEST_RE.match(str(origin.get("paths_digest", ""))):
            errors.append(f"{package_id}: repair_origin invalid paths_digest")
        _require_int_not_bool(errors, package_id, "repair_origin.changed_lines", origin.get("changed_lines"))
        _require_int_not_bool(errors, package_id, "repair_origin.generation", origin.get("generation"), minimum=1)
        _require_utc(errors, package_id, "repair_origin.frozen_at", origin.get("frozen_at"))
        _require_nonempty_str(errors, package_id, "repair_origin.frozen_by", origin.get("frozen_by"))
    _schema_errors(errors, package_id, "repair_ceiling_initialization", exc.get("repair_ceiling_initialization"), REPAIR_CEILING_KEYS)
    ceiling = exc.get("repair_ceiling_initialization") or {}
    if isinstance(ceiling, dict):
        if ceiling.get("original_changed_lines") != ORIGINAL_CHANGED_LINES:
            errors.append(f"{package_id}: repair_ceiling_initialization original_changed_lines mismatch")
        if ceiling.get("budget_lines") != BUDGET_LINES:
            errors.append(f"{package_id}: repair_ceiling_initialization budget_lines mismatch")
        if ceiling.get("cap_source") != CAP_SOURCE:
            errors.append(f"{package_id}: repair_ceiling_initialization cap_source mismatch")
        _require_utc(errors, package_id, "repair_ceiling_initialization.frozen_at", ceiling.get("frozen_at"))
    finding_snapshot = exc.get("finding_snapshot")
    if not isinstance(finding_snapshot, list) or len(finding_snapshot) != len(ALL_FINDING_IDS):
        errors.append(f"{package_id}: finding_snapshot must contain ten findings")
    else:
        for item in finding_snapshot:
            if not isinstance(item, dict):
                errors.append(f"{package_id}: finding_snapshot item must be object")
                continue
            if set(item) != FINDING_SNAPSHOT_KEYS:
                errors.append(f"{package_id}: finding_snapshot item keys mismatch")
            _require_int_not_bool(errors, package_id, "finding_snapshot repair_attempts", item.get("repair_attempts"))
            for digest_key in ("verification_digest", "definition_digest"):
                if digest_key in item and not DIGEST_RE.match(str(item[digest_key])):
                    errors.append(f"{package_id}: finding_snapshot invalid {digest_key}")
    finding_map = exc.get("finding_map")
    if finding_map != FINDING_MAP:
        errors.append(f"{package_id}: finding_map must match profile constant")
    elif isinstance(finding_map, list):
        for entry in finding_map:
            if not isinstance(entry, dict) or set(entry) != FINDING_MAP_ENTRY_KEYS:
                errors.append(f"{package_id}: finding_map entry shape mismatch")
    ownership_snapshot = exc.get("ownership_snapshot")
    if ownership_snapshot != OWNERSHIP_SNAPSHOT:
        errors.append(f"{package_id}: ownership_snapshot must match profile constant")
    elif isinstance(ownership_snapshot, list):
        for entry in ownership_snapshot:
            if not isinstance(entry, dict) or set(entry) != OWNERSHIP_ENTRY_KEYS:
                errors.append(f"{package_id}: ownership_snapshot entry shape mismatch")
    combined = exc.get("combined_review_identity")
    if status == "prepared" and exc.get("reentry") is None:
        if combined is not None:
            errors.append(f"{package_id}: combined_review_identity must be null before reentry")
        if exc.get("children"):
            errors.append(f"{package_id}: children must be empty before reentry")
        if exc.get("binding_digest") is not None:
            errors.append(f"{package_id}: binding_digest must be null before reentry")
        if exc.get("worktree_realpath") is not None:
            errors.append(f"{package_id}: worktree_realpath must be null before reentry")
    if combined is not None:
        if not isinstance(combined, dict) or set(combined) != COMBINED_IDENTITY_KEYS:
            errors.append(f"{package_id}: combined_review_identity shape mismatch")
        elif combined.get("generation") != 2:
            errors.append(f"{package_id}: combined generation must be 2")
        else:
            for field in ("base_commit", "base_tree", "candidate_commit", "candidate_tree"):
                if not SHA_RE.match(str(combined.get(field, ""))):
                    errors.append(f"{package_id}: combined_review_identity invalid {field}")
            if not DIGEST_RE.match(str(combined.get("paths_digest", ""))):
                errors.append(f"{package_id}: combined_review_identity invalid paths_digest")
            _require_int_not_bool(errors, package_id, "combined_review_identity.changed_lines", combined.get("changed_lines"))
    children = exc.get("children")
    if not isinstance(children, list):
        errors.append(f"{package_id}: children must be array")
    elif children:
        if len(children) != 2:
            errors.append(f"{package_id}: children must contain exactly two records")
        child_ids = [child.get("package_id") for child in children if isinstance(child, dict)]
        if child_ids != list(EXPECTED_CHILD_ORDER):
            errors.append(f"{package_id}: children must be ordered {list(EXPECTED_CHILD_ORDER)}")
        for child in children:
            _validate_child_record_schema(errors, package_id, child)
    binding = exc.get("binding_digest")
    if binding is not None and not DIGEST_RE.match(str(binding)):
        errors.append(f"{package_id}: invalid binding_digest")
    if binding is not None and combined is not None and children:
        expected = compute_binding_digest(exc)
        if binding != expected:
            errors.append(f"{package_id}: binding_digest mismatch")
    _validate_provenance_block(
        errors, package_id, "preparation", exc.get("preparation"), PREPARATION_KEYS, require_approval=True,
    )
    reentry = exc.get("reentry")
    if reentry is not None:
        _validate_provenance_block(errors, package_id, "reentry", reentry, REENTRY_KEYS)
    elif exc.get("children") or combined is not None:
        errors.append(f"{package_id}: reentry required when children/combined are present")
    authorization = exc.get("authorization")
    if status in {"authorized", "consumed"}:
        _validate_provenance_block(
            errors, package_id, "authorization", authorization, AUTHORIZATION_KEYS, require_approval=True,
        )
        if isinstance(authorization, dict):
            if not DIGEST_RE.match(str(authorization.get("binding_digest", ""))):
                errors.append(f"{package_id}: authorization binding_digest invalid")
            _require_nonempty_str(errors, package_id, "authorization.panel_id", authorization.get("panel_id"))
    elif authorization is not None:
        errors.append(f"{package_id}: authorization must be null while prepared")
    consumption = exc.get("consumption")
    if status == "consumed":
        _validate_provenance_block(errors, package_id, "consumption", consumption, CONSUMPTION_KEYS)
        if isinstance(consumption, dict):
            if not UUID_RE.match(str(consumption.get("outcome_id", ""))):
                errors.append(f"{package_id}: consumption outcome_id invalid")
            stored_combined = consumption.get("combined_review_identity")
            if not isinstance(stored_combined, dict) or set(stored_combined) != COMBINED_IDENTITY_KEYS:
                errors.append(f"{package_id}: consumption combined_review_identity shape mismatch")
            _require_int_not_bool(errors, package_id, "consumption.committed_revision", consumption.get("committed_revision"), minimum=1)
            if not DIGEST_RE.match(str(consumption.get("binding_digest", ""))):
                errors.append(f"{package_id}: consumption binding_digest invalid")
            _require_nonempty_str(errors, package_id, "consumption.panel_id", consumption.get("panel_id"))
    elif consumption is not None:
        errors.append(f"{package_id}: consumption must be null before consumed status")
    if status == "authorized" and consumption is not None:
        errors.append(f"{package_id}: consumption must be null while authorized")
    if status in {"authorized", "consumed"}:
        if not children or len(children) != 2:
            errors.append(f"{package_id}: authorized/consumed requires two child records")
        if combined is None or binding is None:
            errors.append(f"{package_id}: authorized/consumed requires combined_review_identity and binding_digest")
        if wt is None:
            errors.append(f"{package_id}: authorized/consumed requires worktree_realpath")
        if reentry is None:
            errors.append(f"{package_id}: authorized/consumed requires reentry")
    if status == "consumed" and authorization is None:
        errors.append(f"{package_id}: consumed requires authorization")
    _require_int_not_bool(errors, package_id, "parent_repair_batches_initial", exc.get("parent_repair_batches_initial"))
    return errors
