"""Extracted from ai/scripts/feature-state.py by a behavior-preserving refactor
(mechanical reorganization only -- no logic changes). See feature-state.py's own
module docstring and the package-level notes for the split rationale.
"""

from __future__ import annotations

import argparse
import hashlib
from copy import deepcopy
from pathlib import Path
from typing import Any

from feature_state_lib import model
from feature_state_lib.model import (
    StateError, now, state_path, print_json, parse_json_object, parse_bool, base_state,
    compact_package, load_state, atomic_write, validate_state, fail_if_invalid,
    package_by_id, task_by_id, MODE_BUDGETS, TERMINAL,
)
from feature_state_lib.transitions import check_transition, next_transition
from feature_state_lib.render_status import render_status
from feature_state_lib.render_bitacora import render_bitacora
from feature_state_lib import axes


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


def spec_drift(data: dict[str, Any]) -> str | None:
    """017/AC-11 (ADR-0028): re-hash the approved spec against the record.

    `verify_spec_hash` runs at init only; this is the mid-flight counterpart.
    Returns a human-actionable message (never raises) so callers choose their
    own severity: `resume`/`next` warn, `accept-package` refuses.
    """
    spec = data.get("approved_spec") or {}
    path, recorded = spec.get("path"), spec.get("hash")
    if not path or not recorded:
        return None
    spec_file = Path(path)
    if not spec_file.is_file():
        return f"SPEC_NOT_FOUND: {path} — el contrato aprobado ya no está en disco"
    digest = hashlib.sha256(spec_file.read_bytes()).hexdigest()
    if digest != recorded:
        return (
            f"SPEC_DRIFT: recorded={recorded[:12]} disk={digest[:12]} path={path} — "
            "el spec cambió después de la aprobación; registrá el cambio con `amend-spec` "
            "(y consultá al usuario) antes de aceptar más paquetes. Nunca `init --force`."
        )
    return None


def cmd_amend_spec(args: argparse.Namespace) -> int:
    """ADR-0028: record a new approved version of the contract WITHOUT destroying
    history. The user's confirmation is a precondition the orchestrator's own
    Question policy already authorizes — this command only persists it."""
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        spec = data.get("approved_spec") or {}
        new_path = args.spec_path or spec.get("path")
        spec_file = Path(new_path)
        if not spec_file.is_file():
            raise StateError(f"SPEC_NOT_FOUND: {new_path}")
        new_hash = hashlib.sha256(spec_file.read_bytes()).hexdigest()
        if new_hash == spec.get("hash") and new_path == spec.get("path"):
            raise StateError("amend-spec: el spec en disco es idéntico al ya aprobado — nada que enmendar")
        amendment = {
            "at": now(),
            "old_path": spec.get("path"),
            "old_hash": spec.get("hash"),
            "path": new_path,
            "hash": new_hash,
            "reason": args.reason,
            "approved_by": args.approved_by,
            "actor": args.actor,
        }
        data.setdefault("spec_amendments", []).append(amendment)
        data["approved_spec"] = {"path": new_path, "hash": new_hash, "approved_at": amendment["at"]}
        if args.ac is not None:
            data["acceptance_criteria"] = args.ac
        model.record_event(data, "amend-spec", data["phase"], data["phase"], args.actor,
                           metadata={"reason": args.reason, "approved_by": args.approved_by,
                                     "new_hash": new_hash}, event_id=args.event_id)
        return True

    data, changed = model.mutate(path, args, "amend-spec", update)
    return output_state(data, changed, path)


def cmd_supersede_package(args: argparse.Namespace) -> int:
    """ADR-0028: retire a package the amended scope obsoleted, keeping its history.
    A superseded package no longer blocks `done_ready` and its acceptance criteria
    no longer count as covered — the amendment must have re-homed or removed them."""
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        package = model.package_by_id(data, args.package_id)
        if package.get("status") == "accepted":
            raise StateError("supersede-package: un paquete aceptado no se retira — el alcance nuevo "
                             "se implementa en un paquete nuevo")
        if package.get("status") == "superseded":
            return False
        package["status"] = "superseded"
        package["superseded"] = {"at": now(), "reason": args.reason,
                                 "amendment_hash": args.amendment_hash or ""}
        model.record_event(data, "supersede-package", data["phase"], data["phase"], args.actor,
                           args.package_id, {"reason": args.reason}, args.event_id)
        return True

    data, changed = model.mutate(path, args, "supersede-package", update)
    return output_state(data, changed, path)


def cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.state_file) if args.state_file else state_path(args.feature_id)
    if path.exists() and not args.force:
        raise StateError(f"state exists: {path}")
    verify_spec_hash(args.spec_path, args.spec_hash)
    data = base_state(args.feature_id, args.spec_path, args.spec_hash)
    data["acceptance_criteria"] = args.ac or []
    data["mode"] = args.mode
    data["budgets"].update(MODE_BUDGETS[args.mode])
    axes_path = axes.axes_log_path(path, getattr(args, "axes_log", None))
    axes_rows = axes.read_axes_log(axes_path)
    axes_errors = axes.validate_rows(axes_rows, args.feature_id)
    if axes_errors:
        raise StateError("axes log invalid: " + "; ".join(axes_errors))
    data["axes_log"] = str(axes_path)
    for key in ("max_deep_review_cycles", "max_repairs_per_finding", "max_package_subdivisions", "max_spawns_per_package"):
        value = getattr(args, key)
        if value is not None:
            data["budgets"][key] = value
    model.record_event(
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
    model.render_notes(path, only_feature=args.feature_id)
    return output_state(data, True, path)


def cmd_record_axis(args: argparse.Namespace) -> int:
    axes_path = Path(args.axes_log)
    row = {
        "at": now(),
        "feature_id": args.feature_id,
        "axis": args.axis,
        "stance": args.stance,
        "origin": args.origin,
        "source": args.source,
        "threshold": args.threshold,
        "next_stance": args.next_stance,
        "revisit": args.revisit,
        "reason": args.reason,
        "asked_at": args.asked_at,
    }
    row_errors = axes.validate_row(row)
    if row_errors:
        raise StateError("invalid axis row: " + "; ".join(row_errors))
    axes.append_axes_row(axes_path, row)
    print_json({"ok": True, "changed": True, "axes_log": str(axes_path), "row": row})
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    path = state_file_arg(args)
    data = load_state(path)
    errors = validate_state(data)
    axes_log = data.get("axes_log")
    if axes_log:
        axes_errors = axes.validate_rows(axes.read_axes_log(Path(axes_log)), data.get("feature_id", ""))
        if axes_errors:
            errors.append("axes_log: " + "; ".join(axes_errors))
    if errors:
        print_json({"ok": False, "errors": errors, "state_file": str(path)})
        return 2
    print_json({"ok": True, "state_file": str(path), "revision": data.get("revision"), "phase": data.get("phase"), "next": next_transition(data)})
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    path = state_file_arg(args)
    data = load_state(path)
    fail_if_invalid(data)
    # AC-04 (020-honest-dashboard, ADR-0040): the same predicate/threshold AC-01/AC-03
    # read (model.blocked_days/model.stale_days) -- a command that told a different truth
    # than the digest/hub is exactly the class of bug this feature closes. Additive on top
    # of `output_state`'s shared shape (every other mutating command still calls
    # `output_state` unchanged); only `status` gains these two keys.
    print_json({
        "ok": True, "changed": False, "state_file": str(path), "state": data,
        "next": next_transition(data),
        "blocked_days": model.blocked_days(data),
        "stale_days": model.stale_days(data),
    })
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    path = state_file_arg(args)
    data = load_state(path)
    fail_if_invalid(data)
    payload = {"ok": True, "state_file": str(path), "next": next_transition(data)}
    # ADR-0028: warn (never fail) on contract drift — the key is absent when clean,
    # so pre-017 consumers of this output see exactly what they always saw.
    drift = spec_drift(data)
    if drift:
        payload["spec_drift"] = drift
    print_json(payload)
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
            #
            # --package-id is optional on this command (P1F-01): resolve via
            # package_by_id, which falls back to current_package_id, so the stale
            # key is still popped when the caller omits --package-id.  If no
            # package can be resolved at all, there is nothing to pop.
            try:
                package_by_id(data, args.package_id).pop("repair_entry", None)
            except StateError:
                pass
        if args.to_phase in TERMINAL:
            data["final_state"] = args.to_phase
        model.record_event(data, "transition", from_phase, args.to_phase, args.actor, args.package_id, {"reason": args.reason}, args.event_id)
        return True

    data, changed = model.mutate(path, args, "transition", update)
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
        # RDD-inspired opt-in (docs/adr/0022-*.md): strict TDD is off by default, same
        # precedent as runtime_surface's fail-safe default but inverted -- this one adds
        # ceremony, so it never turns on silently.
        package["strict_tdd"] = parse_bool(getattr(args, "strict_tdd", None), default=False)
        for task_id in args.task or []:
            package["tasks"].append({"id": task_id, "status": "planned", "local_validations": [], "blockers": []})
        if len(package["tasks"]) < 2 and package["complexity"] != "small":
            raise StateError("normal packages must contain multiple tasks; mark complexity=small for tiny scoped packages")
        data.setdefault("packages", []).append(package)
        data["current_package_id"] = args.package_id
        if data["phase"] == "PACKAGE_ACCEPTED":
            data["phase"] = "PACKAGE_PLANNING"
        model.record_event(data, "create-package", data["phase"], data["phase"], args.actor, args.package_id, {"tasks": args.task or []}, args.event_id)
        return True

    data, changed = model.mutate(path, args, "create-package", update)
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
        if getattr(args, "strict_tdd", None) is not None:
            package["strict_tdd"] = parse_bool(args.strict_tdd)
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
            model.record_event(data, "update-package", data["phase"], data["phase"], args.actor, args.package_id, {}, args.event_id)
            return True
        return False

    data, changed = model.mutate(path, args, "update-package", update)
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
        model.record_event(data, "start-task", data["phase"], data["phase"], args.actor, args.package_id, {"task_id": args.task_id}, args.event_id)
        return True

    data, changed = model.mutate(path, args, "start-task", update)
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
        model.record_event(data, "complete-task", data["phase"], data["phase"], args.actor, args.package_id, {"task_id": args.task_id, "validations": validations}, args.event_id)
        return True

    data, changed = model.mutate(path, args, "complete-task", update)
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
        model.record_event(data, "fail-task", data["phase"], "BLOCKED", args.actor, args.package_id, {"task_id": args.task_id, "reason": args.reason}, args.event_id)
        return True

    data, changed = model.mutate(path, args, "fail-task", update)
    return output_state(data, changed, path)


def block_with_reason(data: dict[str, Any], actor: str, package_id: str | None, reason: str,
                       counter: dict[str, Any] | None = None) -> bool:
    """ADR-0039: `counter`, when given, names EXACTLY the budget counter whose exhaustion
    produced this block -- structured, never inferred from `reason`'s prose (that string is
    free text on several call sites, e.g. `args.evidence or "package testing blocked"`, and
    matching against it would repeat the exact SEC-001 mistake `coord_policy.py` documents
    as expensive). `cmd_reopen` reads this key back to reset ONLY that one counter. Two
    shapes, both closed vocabularies:
      - `{"scope": "attempts", "key": <name>}` for a `package["attempts"][<name>]` counter
        (spawns, deep_review_cycles, gate_failures, verifications, verification_waivers).
      - `{"scope": "finding", "key": "repair_attempts", "finding_id": <id>}` for the
        per-finding `repair_attempts` counter `record-repair` enforces -- it lives on the
        finding, not on `package["attempts"]`, so it needs its own finding_id to locate.
    Omitted (the default) for every block that is not a budget exhaustion -- a manual
    `cmd_block`, or a verdict/testing/runtime-QA refusal the caller phrases in free text.
    `cmd_reopen` then resets nothing for that blocker, which is also what happens for every
    blocker persisted before this key existed: fail-closed, not inferred.
    """
    from_phase = data["phase"]
    data["phase"] = "BLOCKED"
    data["final_state"] = "BLOCKED"
    blocker = {"package_id": package_id, "reason": reason, "at": now()}
    if counter:
        blocker["counter"] = counter
    data.setdefault("blockers", []).append(blocker)
    model.record_event(data, "block", from_phase, "BLOCKED", actor, package_id, {"reason": reason})
    return True


def _reset_blocker_counter(data: dict[str, Any], blocker: dict[str, Any]) -> None:
    """ADR-0039: reset EXACTLY the counter `block_with_reason` tagged on this blocker, and
    nothing else. Malformed or absent `counter` (every blocker persisted before this
    feature, or one of the non-budget blocks that never carries one) is a silent no-op --
    reopen still resolves the blocker and moves the phase, it just resets no counter, same
    as the behaviour before this fix.
    """
    counter = blocker.get("counter")
    if not isinstance(counter, dict):
        return
    scope = counter.get("scope")
    key = counter.get("key")
    package_id = blocker.get("package_id")
    if scope not in {"attempts", "finding"} or not key or not package_id:
        return
    try:
        package = package_by_id(data, package_id)
    except StateError:
        # The package this blocker named no longer exists (supersede-package, a hand-edited
        # fixture) -- nothing to reset, and reopen itself does not need this package to
        # resolve the phase.
        return
    if scope == "attempts":
        attempts = package.get("attempts")
        if isinstance(attempts, dict) and key in attempts:
            attempts[key] = 0
    else:  # scope == "finding"
        finding_id = counter.get("finding_id")
        finding = next((item for item in package.get("findings", []) if item.get("id") == finding_id), None)
        if finding is not None and key in finding:
            finding[key] = 0


def cmd_block(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        return block_with_reason(data, args.actor, args.package_id, args.reason)

    data, changed = model.mutate(path, args, "block", update)
    return output_state(data, changed, path)


def cmd_reopen(args: argparse.Namespace) -> int:
    """ADR-0039: beyond moving BLOCKED back to PACKAGE_PLANNING, this resets the ONE budget
    counter (if any) whose exhaustion produced each blocker this call resolves -- a package
    that hit `max_verifications_per_package` (or any other budget) used to stay permanently
    unable to record a verdict even after reopen, because `attempts[...]` was never touched.
    The reset is directed, never a blanket clear of every counter on the package: see
    `block_with_reason`'s docstring for the structured `counter` key this reads, and
    `_reset_blocker_counter` for the reset itself.

    031-registro-correctivo: `--from-done` extends this to DONE phase.  The flag is required
    when reopening from DONE so the caller explicitly acknowledges the non-standard path.
    Unlike reopening from BLOCKED, no blocker counters are reset (DONE has none), and the
    event written is `reopen-from-done` so the prior closure remains visible in the history.
    """
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        from_phase = data["phase"]
        if not args.reason or not args.authorized_by:
            raise StateError("reopen requires explicit --reason and --authorized-by")
        if from_phase == "DONE":
            if not getattr(args, "from_done", False):
                raise StateError(
                    "cannot reopen from phase DONE without --from-done; "
                    "use --from-done to explicitly reopen a closed feature"
                )
            data["phase"] = "PACKAGE_PLANNING"
            data.pop("final_state", None)
            model.record_event(
                data,
                "reopen-from-done",
                from_phase,
                "PACKAGE_PLANNING",
                args.actor,
                args.package_id,
                {"reason": args.reason, "authorized_by": args.authorized_by},
                args.event_id,
            )
            return True
        if getattr(args, "from_done", False) and from_phase != "DONE":
            raise StateError(
                f"--from-done is only valid when phase is DONE; current phase is {from_phase}"
            )
        if from_phase != "BLOCKED":
            raise StateError(
                f"cannot reopen from phase {from_phase}; "
                "reopen only applies to BLOCKED (or DONE with --from-done)"
            )
        resolved_at = now()
        for blocker in data.get("blockers", []):
            newly_resolved = "resolved_at" not in blocker
            blocker.setdefault("resolved_at", resolved_at)
            blocker.setdefault("resolved_reason", args.reason)
            blocker.setdefault("resolved_by", args.authorized_by)
            if newly_resolved:
                _reset_blocker_counter(data, blocker)
        data["phase"] = "PACKAGE_PLANNING"
        data.pop("final_state", None)
        model.record_event(
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

    data, changed = model.mutate(path, args, "reopen", update)
    return output_state(data, changed, path)


MIN_AMEND_REASON_LEN = 80


def cmd_amend_package(args: argparse.Namespace) -> int:
    """031-registro-correctivo: add work items to an existing, non-accepted package.

    `create-package` no-ops on a duplicate package_id and `update-package` has no
    --task flag, so a package created without tasks has no repair path -- the cycle
    can never reach `package_review_ready` because `tasks_complete` requires at least
    one completed task.  This verb closes that gap.

    Guard: only operates on packages that have not yet been accepted.  Once a package
    carries `status == "accepted"`, `package_accept_ready` has already run against its
    task list; adding tasks after the fact would silently invalidate that verdict.
    The right path after acceptance is a new package.

    The --reason requirement mirrors `record-late-review`: no phase gate witnessed this
    change, so the reason IS the audit trail.
    """
    path = state_file_arg(args)
    reason = (args.reason or "").strip()
    if len(reason) < MIN_AMEND_REASON_LEN:
        raise StateError(
            f"amend-package requires --reason of at least {MIN_AMEND_REASON_LEN} characters: "
            "the reason is the only audit trail for a post-creation task addition"
        )
    new_tasks = args.task or []
    if not new_tasks:
        raise StateError("amend-package requires at least one --task")

    def update(data: dict[str, Any]) -> bool:
        package = package_by_id(data, args.package_id)
        if package.get("status") == "accepted":
            raise StateError(
                f"cannot amend accepted package {args.package_id}; "
                "create a new package for additional work"
            )
        existing_ids = {t["id"] for t in package.get("tasks", [])}
        added: list[str] = []
        for task_id in new_tasks:
            if task_id in existing_ids:
                continue
            package.setdefault("tasks", []).append(
                {"id": task_id, "status": "planned", "local_validations": [], "blockers": []}
            )
            added.append(task_id)
        if not added:
            return False
        model.record_event(
            data,
            "amend-package",
            data["phase"],
            data["phase"],
            args.actor,
            args.package_id,
            {"added_tasks": added, "reason": reason},
            args.event_id,
        )
        return True

    data, changed = model.mutate(path, args, "amend-package", update)
    return output_state(data, changed, path)


def cmd_resume(args: argparse.Namespace) -> int:
    return cmd_next(args)
