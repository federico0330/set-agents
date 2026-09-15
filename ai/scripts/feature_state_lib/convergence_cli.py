"""HCE convergence CLI commands — six NEW verbs."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any

from feature_state_lib import model
from feature_state_lib.convergence_constants import (
    CHILD_A_PACKAGE_ID,
    CHILD_B_PACKAGE_ID,
    PARENT_PACKAGE_ID,
    PROFILE,
)
from feature_state_lib.convergence_errors import HceCommittedRenderFailed, HceDenial
from feature_state_lib.convergence_git import (
    check_clean_worktree,
    diff_paths_and_lines,
    git_common_dir,
    head_commit_and_tree,
    measure_child_output_paths,
    measure_combined_identity,
    measure_original_identity,
    output_paths_b64,
    paths_digest_b64,
    validate_canonical_state_path,
)
from feature_state_lib.convergence_policy import (
    build_authorization,
    build_consumption,
    build_prepared_exception,
    canonical_json_digest,
    compute_binding_digest,
    finding_snapshot_from_package,
    get_exception,
    rederive_frozen_binding,
    validate_authorize_context,
    validate_bindings_match,
    validate_child_output_paths,
    validate_combined_measurement,
    validate_consume_ready,
    validate_inspect_eligible,
    validate_prepare_context,
    validate_profile,
    validate_receipt_chain,
    validate_reenter_context,
    validate_verify_outcome,
    _package_map,
)
from feature_state_lib.cli_lifecycle import state_file_arg
from feature_state_lib.model import now, package_by_id, print_json


def _replayed(data: dict[str, Any], event: str, event_id: str | None) -> bool:
    if not event_id:
        return False
    return any(
        item.get("event_id") == event_id and item.get("event") == event
        for item in data.get("history", [])
    )


def _require_mutation_args(args: argparse.Namespace) -> None:
    if not getattr(args, "actor", None):
        raise HceDenial("HCE_DENIED", "missing --actor")
    if not getattr(args, "event_id", None):
        raise HceDenial("HCE_DENIED", "missing --event-id")
    if getattr(args, "expect_revision", None) is None:
        raise HceDenial("HCE_DENIED", "missing --expect-revision")
    if int(args.expect_revision) < 0:
        raise HceDenial("HCE_DENIED", "expect-revision must be non-negative")


def _canonical_state_path(path: Path) -> Path:
    return validate_canonical_state_path(path)


def _worktree_from_cwd() -> Path:
    return Path.cwd().resolve()


def _context(args: argparse.Namespace) -> tuple[Path, Path, Path, str, str]:
    state_path = _canonical_state_path(state_file_arg(args))
    worktree = _worktree_from_cwd()
    repo = git_common_dir(worktree)
    return state_path, worktree, repo, str(state_path), str(repo)


def _success_payload(result: str, data: dict[str, Any], package_id: str, exc: dict[str, Any], **extra: Any) -> dict[str, Any]:
    payload = {
        "ok": True,
        "result": result,
        "feature_id": data.get("feature_id"),
        "package_id": package_id,
        "exception_id": exc.get("exception_id"),
        "revision": data.get("revision"),
    }
    payload.update(extra)
    return payload


def _deny(exc: HceDenial, data: dict[str, Any] | None = None, package_id: str | None = None,
          exception_id: str | None = None) -> int:
    revision = data.get("revision") if data else None
    feature_id = data.get("feature_id") if data else None
    print_json(exc.to_payload(
        feature_id=feature_id,
        package_id=package_id,
        exception_id=exception_id,
        revision=revision,
    ))
    return 2


def _invocation_snapshot(args: argparse.Namespace, command: str) -> dict[str, Any]:
    snapshot: dict[str, Any] = {
        "command": command,
        "package_id": getattr(args, "package_id", None),
        "actor": getattr(args, "actor", None),
        "event_id": getattr(args, "event_id", None),
    }
    if command == "prepare-convergence":
        snapshot.update({
            "profile": getattr(args, "profile", None),
            "authorized_by": getattr(args, "authorized_by", None),
            "reason": getattr(args, "reason", None),
            "approval_evidence": getattr(args, "approval_evidence", None),
        })
    elif command in {"reenter-convergence", "authorize-convergence", "consume-convergence"}:
        snapshot["exception_id"] = getattr(args, "exception_id", None)
    if command == "authorize-convergence":
        snapshot.update({
            "authorized_by": getattr(args, "authorized_by", None),
            "reason": getattr(args, "reason", None),
            "approval_evidence": getattr(args, "approval_evidence", None),
        })
    return snapshot


def _replay_invocation_matches(data: dict[str, Any], event: str, event_id: str, snapshot: dict[str, Any]) -> bool:
    for item in data.get("history", []):
        if item.get("event_id") != event_id or item.get("event") != event:
            continue
        metadata = item.get("metadata") or {}
        stored = metadata.get("invocation_snapshot")
        if not isinstance(stored, dict) or not stored:
            return False
        return stored == snapshot
    return False


def cmd_prepare_convergence(args: argparse.Namespace) -> int:
    try:
        validate_profile(getattr(args, "profile", None))
        _require_mutation_args(args)
        state_path, worktree, repo, state_real, repo_real = _context(args)
        package_id = args.package_id

        invocation = _invocation_snapshot(args, "prepare-convergence")

        def update(data: dict[str, Any]) -> bool:
            package = package_by_id(data, package_id)
            exc_existing = package.get("convergence_exception")
            if _replayed(data, "prepare-convergence", args.event_id):
                if not exc_existing or not _replay_invocation_matches(
                    data, "prepare-convergence", args.event_id, invocation
                ):
                    raise HceDenial("HCE_REPLAY", "event-id replay without matching snapshot")
                return False
            fresh_original = measure_original_identity(worktree, package.get("candidate_identity") or {})
            validate_prepare_context(data, package, fresh_original)
            exc = build_prepared_exception(
                state_realpath=state_real,
                repo_realpath=repo_real,
                worktree_realpath=None,
                package=package,
                fresh_original=fresh_original,
                actor=args.actor,
                event_id=args.event_id,
                authorized_by=args.authorized_by,
                reason=args.reason,
                approval_evidence=args.approval_evidence,
                at=now(),
            )
            package["convergence_exception"] = exc
            model.record_event(
                data, "prepare-convergence", data["phase"], data["phase"],
                args.actor, package_id,
                {"exception_id": exc["exception_id"], "invocation_snapshot": invocation},
                args.event_id,
            )
            return True

        data, changed = model.mutate(state_path, args, "prepare-convergence", update)
        exc = package_by_id(data, package_id)["convergence_exception"]
        print_json(_success_payload("HCE_PREPARED", data, package_id, exc))
        return 0
    except HceDenial as err:
        try:
            data = model.load_state(state_file_arg(args))
        except Exception:
            data = None
        return _deny(err, data, getattr(args, "package_id", None))


def _live_combined(exc: dict[str, Any], worktree: Path) -> dict[str, Any]:
    origin = exc.get("repair_origin") or {}
    base_commit = origin.get("candidate_ref")
    if not base_commit:
        raise HceDenial("HCE_STALE", "missing repair_origin candidate_ref")
    check_clean_worktree(worktree)
    return measure_combined_identity(worktree, base_commit)


def _fresh_child_outputs(data: dict[str, Any], worktree: Path) -> dict[str, tuple[list[str], str]]:
    packages = _package_map(data)
    child_a = packages.get(CHILD_A_PACKAGE_ID)
    child_b = packages.get(CHILD_B_PACKAGE_ID)
    if not child_a or not child_b:
        raise HceDenial("HCE_STALE", "missing fixed child packages")
    return {
        CHILD_A_PACKAGE_ID: measure_child_output_paths(worktree, child_a["candidate_identity"]),
        CHILD_B_PACKAGE_ID: measure_child_output_paths(worktree, child_b["candidate_identity"]),
    }


def cmd_inspect_convergence(args: argparse.Namespace) -> int:
    try:
        state_path, worktree, repo, state_real, repo_real = _context(args)
        data = model.load_state(state_path)
        package = package_by_id(data, args.package_id)
        exc = get_exception(package, args.exception_id)
        validate_bindings_match(exc, state_real, repo_real, str(worktree))
        combined = _live_combined(exc, worktree)
        validate_inspect_eligible(exc, combined)
        print_json(_success_payload("HCE_ELIGIBLE", data, args.package_id, exc))
        return 0
    except HceDenial as err:
        try:
            data = model.load_state(state_file_arg(args))
        except Exception:
            data = None
        return _deny(err, data, getattr(args, "package_id", None), getattr(args, "exception_id", None))


def cmd_consume_convergence(args: argparse.Namespace) -> int:
    try:
        _require_mutation_args(args)
        state_path, worktree, repo, state_real, repo_real = _context(args)
        package_id = args.package_id
        exception_id = args.exception_id

        def update(data: dict[str, Any]) -> bool:
            package = package_by_id(data, package_id)
            exc = get_exception(package, exception_id)
            validate_bindings_match(exc, state_real, repo_real, str(worktree))
            combined = _live_combined(exc, worktree)
            rederive_frozen_binding(
                exc, data, package, combined,
                fresh_child_outputs=_fresh_child_outputs(data, worktree),
            )
            validate_consume_ready(exc, combined)
            consumption = build_consumption(
                exc,
                actor=args.actor,
                event_id=args.event_id,
                at=now(),
                revision=int(data.get("revision", 0)),
            )
            exc["status"] = "consumed"
            exc["consumption"] = consumption
            gates = package.setdefault("gates", [])
            gate = {
                "name": "repair-ceiling",
                "status": "pass",
                "required": True,
                "evidence": f"HCE outcome {consumption['outcome_id']}",
                "at": now(),
                "convergence_outcome_id": consumption["outcome_id"],
            }
            replaced = False
            for idx, existing in enumerate(gates):
                if existing.get("name") == "repair-ceiling":
                    gates[idx] = gate
                    replaced = True
                    break
            if not replaced:
                gates.append(gate)
            model.record_event(
                data, "consume-convergence", data["phase"], data["phase"],
                args.actor, package_id,
                {
                    "exception_id": exception_id,
                    "outcome_id": consumption["outcome_id"],
                    "invocation_snapshot": _invocation_snapshot(args, "consume-convergence"),
                },
                args.event_id,
            )
            return True

        data, _changed = model.mutate(state_path, args, "consume-convergence", update)
        package = package_by_id(data, package_id)
        exc = package["convergence_exception"]
        consumption = exc["consumption"]
        combined = exc.get("combined_review_identity") or {}
        print_json(_success_payload(
            "HCE_PASS", data, package_id, exc,
            outcome_id=consumption["outcome_id"],
            combined_review_identity=combined,
            changed_lines=combined.get("changed_lines"),
            budget_lines=exc.get("repair_ceiling_initialization", {}).get("budget_lines"),
        ))
        return 0
    except HceCommittedRenderFailed:
        raise
    except HceDenial as err:
        try:
            data = model.load_state(state_file_arg(args))
        except Exception:
            data = None
        return _deny(err, data, getattr(args, "package_id", None), getattr(args, "exception_id", None))


def cmd_verify_convergence_outcome(args: argparse.Namespace) -> int:
    try:
        state_path, worktree, repo, state_real, repo_real = _context(args)
        data = model.load_state(state_path)
        package = package_by_id(data, args.package_id)
        exc = get_exception(package, args.exception_id)
        validate_bindings_match(exc, state_real, repo_real, str(worktree))
        combined = _live_combined(exc, worktree)
        outcome_id = validate_verify_outcome(
            exc, package, combined,
            data=data,
            fresh_child_outputs=_fresh_child_outputs(data, worktree),
        )
        print_json(_success_payload(
            "HCE_REGISTERED_VALID", data, args.package_id, exc,
            outcome_id=outcome_id,
            combined_review_identity=exc.get("combined_review_identity"),
            changed_lines=(exc.get("combined_review_identity") or {}).get("changed_lines"),
            budget_lines=exc.get("repair_ceiling_initialization", {}).get("budget_lines"),
        ))
        return 0
    except HceDenial as err:
        try:
            data = model.load_state(state_file_arg(args))
        except Exception:
            data = None
        return _deny(err, data, getattr(args, "package_id", None), getattr(args, "exception_id", None))


def _child_record(worktree: Path, package: dict[str, Any], package_id: str) -> dict[str, Any]:
    identity = deepcopy(package["candidate_identity"])
    receipt = deepcopy(package["receipt"])
    paths, _ = diff_paths_and_lines(worktree, identity["base_tree"], identity["candidate_tree"])
    return {
        "package_id": package_id,
        "candidate_identity": identity,
        "receipt": receipt,
        "receipt_digest": canonical_json_digest(receipt),
        "candidate_commit": identity["candidate_ref"],
        "output_paths_b64": output_paths_b64(paths),
        "output_paths_digest": paths_digest_b64(paths),
    }


def cmd_reenter_convergence(args: argparse.Namespace) -> int:
    try:
        _require_mutation_args(args)
        state_path, worktree, repo, state_real, repo_real = _context(args)
        check_clean_worktree(worktree)
        package_id = args.package_id
        exception_id = args.exception_id

        invocation = _invocation_snapshot(args, "reenter-convergence")

        def update(data: dict[str, Any]) -> bool:
            package = package_by_id(data, package_id)
            exc = get_exception(package, exception_id)
            if _replayed(data, "reenter-convergence", args.event_id):
                if not _replay_invocation_matches(
                    data, "reenter-convergence", args.event_id, invocation
                ):
                    raise HceDenial("HCE_REPLAY", "event-id replay without matching snapshot")
                return False
            validate_bindings_match(exc, state_real, repo_real, str(worktree))
            validate_reenter_context(data, package, exc)
            packages = _package_map(data)
            child_a = packages.get(CHILD_A_PACKAGE_ID)
            child_b = packages.get(CHILD_B_PACKAGE_ID)
            if not child_a or not child_b:
                raise HceDenial("HCE_STALE", "missing fixed child packages")
            origin = exc.get("repair_origin") or {}
            head_commit, head_tree = head_commit_and_tree(worktree)
            validate_receipt_chain(origin, child_a, child_b, head_commit=head_commit, head_tree=head_tree)
            combined = measure_combined_identity(worktree, origin["candidate_ref"])
            validate_combined_measurement(combined, origin, head_commit)
            child_records = [
                _child_record(worktree, child_a, CHILD_A_PACKAGE_ID),
                _child_record(worktree, child_b, CHILD_B_PACKAGE_ID),
            ]
            validate_child_output_paths(child_records)
            combined_stored = {k: v for k, v in combined.items() if k != "changed_paths"}
            exc["children"] = child_records
            exc["combined_review_identity"] = combined_stored
            exc["worktree_realpath"] = str(worktree)
            exc["repository_common_dir_realpath"] = repo_real
            exc["binding_digest"] = compute_binding_digest(exc)
            exc["reentry"] = {"at": now(), "actor": args.actor, "event_id": args.event_id}
            data["current_package_id"] = PARENT_PACKAGE_ID
            data["phase"] = "PACKAGE_REVIEW"
            package["status"] = "review"
            package["diff_ref"] = combined_stored["candidate_commit"]
            package["integrated"] = True
            from_phase = "PACKAGE_PLANNING"
            model.record_event(
                data, "reenter-convergence", from_phase, "PACKAGE_REVIEW",
                args.actor, package_id,
                {
                    "exception_id": exception_id,
                    "binding_digest": exc["binding_digest"],
                    "invocation_snapshot": invocation,
                },
                args.event_id,
            )
            return True

        data, _changed = model.mutate(state_path, args, "reenter-convergence", update)
        exc = package_by_id(data, package_id)["convergence_exception"]
        print_json(_success_payload("HCE_REENTERED", data, package_id, exc))
        return 0
    except HceDenial as err:
        try:
            data = model.load_state(state_file_arg(args))
        except Exception:
            data = None
        return _deny(err, data, getattr(args, "package_id", None), getattr(args, "exception_id", None))


def cmd_authorize_convergence(args: argparse.Namespace) -> int:
    try:
        _require_mutation_args(args)
        if not getattr(args, "authorized_by", None) or not getattr(args, "reason", None) or not getattr(args, "approval_evidence", None):
            raise HceDenial("HCE_DENIED", "authorize requires --authorized-by, --reason and --approval-evidence")
        state_path, worktree, repo, state_real, repo_real = _context(args)
        package_id = args.package_id
        exception_id = args.exception_id

        invocation = _invocation_snapshot(args, "authorize-convergence")

        def update(data: dict[str, Any]) -> bool:
            package = package_by_id(data, package_id)
            exc = get_exception(package, exception_id)
            if _replayed(data, "authorize-convergence", args.event_id):
                if not _replay_invocation_matches(
                    data, "authorize-convergence", args.event_id, invocation
                ):
                    raise HceDenial("HCE_REPLAY", "event-id replay without matching snapshot")
                return False
            validate_bindings_match(exc, state_real, repo_real, str(worktree))
            check_clean_worktree(worktree)
            combined = _live_combined(exc, worktree)
            rederive_frozen_binding(
                exc, data, package, combined,
                fresh_child_outputs=_fresh_child_outputs(data, worktree),
            )
            validate_authorize_context(data, package, exc)
            exc["authorization"] = build_authorization(
                exc,
                actor=args.actor,
                event_id=args.event_id,
                authorized_by=args.authorized_by,
                reason=args.reason,
                approval_evidence=args.approval_evidence,
                at=now(),
            )
            exc["status"] = "authorized"
            model.record_event(
                data, "authorize-convergence", data["phase"], data["phase"],
                args.actor, package_id,
                {
                    "exception_id": exception_id,
                    "binding_digest": exc["binding_digest"],
                    "invocation_snapshot": invocation,
                },
                args.event_id,
            )
            return True

        data, _changed = model.mutate(state_path, args, "authorize-convergence", update)
        exc = package_by_id(data, package_id)["convergence_exception"]
        print_json(_success_payload("HCE_AUTHORIZED", data, package_id, exc))
        return 0
    except HceDenial as err:
        try:
            data = model.load_state(state_file_arg(args))
        except Exception:
            data = None
        return _deny(err, data, getattr(args, "package_id", None), getattr(args, "exception_id", None))
