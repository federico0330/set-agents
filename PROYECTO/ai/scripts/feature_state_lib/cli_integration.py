"""RDD-inspired integration primitives (docs/adr/0020-*.md and siblings):
freeze-candidate mints/bumps a package's `candidate_identity`, record-receipt
mints its `receipt` once every existing acceptance gate already passes and
the frozen identity re-derives clean against the live repo. Same
argparse/mutate shape as cli_lifecycle.py's other commands.

`integration_ready` lives here rather than in model.py to avoid a circular
import: it needs `candidate_identity.rederive_and_compare`, and
`candidate_identity` itself imports from `model`. It is NOT yet called from
`cmd_transition` -- wiring `--to-phase INTEGRATION` to this precondition, and
the tool-call-blocking hook triad that makes it un-bypassable, is a later,
separately-reviewed package (docs/adr/0020-*.md's integration-receipt ADR).
"""

from __future__ import annotations

import argparse
from typing import Any

from feature_state_lib import model, candidate_identity
from feature_state_lib.model import StateError, now, package_by_id, package_accept_ready
from feature_state_lib.cli_lifecycle import state_file_arg, output_state


def cmd_freeze_candidate(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        if data["phase"] not in {"PACKAGE_GATES", "PACKAGE_REPAIR"}:
            raise StateError(f"cannot freeze candidate from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        frozen = candidate_identity.freeze(args.baseline, args.candidate_ref or "HEAD")
        previous = package.get("candidate_identity") or {}
        # A repair cycle re-freezes: generation bumps so the receipt (and any later
        # re-derivation) can tell which review round a given frozen candidate belongs to.
        frozen["generation"] = previous.get("generation", 0) + 1
        frozen["frozen_at"] = now()
        frozen["frozen_by"] = args.actor
        package["candidate_identity"] = frozen
        model.record_event(
            data, "freeze-candidate", data["phase"], data["phase"], args.actor, args.package_id,
            {"generation": frozen["generation"], "changed_lines": frozen["changed_lines"]}, args.event_id,
        )
        return True

    data, changed = model.mutate(path, args, "freeze-candidate", update)
    return output_state(data, changed, path)


def cmd_record_receipt(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        if data["phase"] not in {"PACKAGE_RUNTIME_QA", "PACKAGE_ACCEPTED"}:
            raise StateError(f"cannot record receipt from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        frozen = package.get("candidate_identity")
        if not frozen:
            raise StateError("record-receipt requires a prior freeze-candidate")
        errors = package_accept_ready(data, package, args.actor)
        if errors:
            raise StateError("cannot record receipt: " + "; ".join(errors))
        # Re-derive live -- never trust the stored freeze. If code changed after the
        # last freeze-candidate without a new one, this is exactly what catches it.
        matches, fresh = candidate_identity.rederive_and_compare(frozen)
        if not matches:
            raise StateError(
                "record-receipt: candidate no longer matches its frozen identity "
                f"(base_tree {frozen.get('base_tree')}->{fresh['base_tree']}, "
                f"candidate_tree {frozen.get('candidate_tree')}->{fresh['candidate_tree']}) "
                "-- run freeze-candidate again against the current diff before minting a receipt"
            )
        review_verdict = package["reviews"][-1].get("verdict") if package.get("reviews") else None
        delta_review_verdict = package["delta_reviews"][-1].get("verdict") if package.get("delta_reviews") else None
        upheld = sum(len(item.get("upheld", [])) for item in package.get("verifications", []))
        refuted = sum(len(item.get("refuted", [])) for item in package.get("verifications", []))
        package["receipt"] = {
            "schema": "set-agentes.integration-receipt/v1",
            "package_id": args.package_id,
            "generation": frozen["generation"],
            "base_tree": frozen["base_tree"],
            "candidate_tree": frozen["candidate_tree"],
            "paths_digest": frozen["paths_digest"],
            "review_verdict": review_verdict,
            "delta_review_verdict": delta_review_verdict,
            "verifications_summary": {"upheld": upheld, "refuted": refuted},
            "terminal_state": "accepted",
            "minted_at": now(),
            "minted_by": args.actor,
        }
        model.record_event(
            data, "record-receipt", data["phase"], data["phase"], args.actor, args.package_id,
            {"generation": frozen["generation"]}, args.event_id,
        )
        return True

    data, changed = model.mutate(path, args, "record-receipt", update)
    return output_state(data, changed, path)


def integration_ready(package: dict[str, Any]) -> list[str]:
    """Preconditions for `INTEGRATION`, re-derived live -- not yet called by
    `cmd_transition` (see module docstring). Mirrors `package_accept_ready`'s
    shape: a list of reasons, empty means ready."""
    errors: list[str] = []
    receipt = package.get("receipt")
    if not receipt:
        errors.append("receipt is required")
        return errors
    if receipt.get("terminal_state") != "accepted":
        errors.append(f"receipt terminal_state is {receipt.get('terminal_state')!r}, not accepted")
    frozen = package.get("candidate_identity")
    if not frozen:
        errors.append("candidate_identity is missing even though a receipt exists")
        return errors
    for field in ("base_tree", "candidate_tree", "paths_digest"):
        if receipt.get(field) != frozen.get(field):
            errors.append(f"receipt.{field} does not match the current candidate_identity.{field}")
    if errors:
        return errors
    matches, fresh = candidate_identity.rederive_and_compare(frozen)
    if not matches:
        errors.append(
            "candidate_identity no longer matches the live repo "
            f"(candidate_tree {frozen.get('candidate_tree')} -> {fresh['candidate_tree']})"
        )
    return errors
