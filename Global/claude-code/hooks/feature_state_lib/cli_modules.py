"""AC-20 (019-harness-evolution PKG-3, ADR-0036): `record-module-impact` and
`module-impact-detect`. Same argparse/mutate shape as cli_lifecycle.py's other commands.
Lives in its own module (not cli_lifecycle.py, not model.py) because it needs
`render_modules`, which itself needs `render_status.status_root` -- importing it from
model.py would close a cycle (model -> render_modules -> render_status -> model), the same
kind cli_integration.py's own docstring documents avoiding.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from feature_state_lib import model
from feature_state_lib.model import StateError, now, load_state, fail_if_invalid, package_by_id, print_json
from feature_state_lib.cli_lifecycle import state_file_arg, output_state
from feature_state_lib.render_modules import (
    modules_toml_path, load_modules_toml, detect_module_candidates,
    package_candidate_paths, unmatched_candidate_paths,
)
from feature_state_lib.check_anchors import check_anchors


def cmd_record_module_impact(args: argparse.Namespace) -> int:
    path = state_file_arg(args)
    waived = bool(args.module_impact_waived)

    def update(data: dict[str, Any]) -> bool:
        package = package_by_id(data, args.package_id)
        if waived:
            if args.module or args.cambio or args.modelo_mental:
                raise StateError(
                    "--module-impact-waived cannot combine with --module/--cambio/--modelo-mental "
                    "-- it is the other mode of this command, not an addition to it"
                )
            reason = (args.reason or "").strip()
            if not reason:
                raise StateError("--module-impact-waived requires --reason")
            package["module_impact_waiver"] = {"reason": reason, "at": now(), "actor": args.actor}
            model.record_event(
                data, "record-module-impact", data["phase"], data["phase"], args.actor, args.package_id,
                {"waived": True, "reason": reason}, args.event_id,
            )
            return True
        module = (args.module or "").strip()
        cambio = (args.cambio or "").strip()
        modelo_mental = (args.modelo_mental or "").strip()
        if not module or not cambio or not modelo_mental:
            raise StateError(
                "record-module-impact requires --module, --cambio and --modelo-mental "
                "(or --module-impact-waived --reason)"
            )
        toml_path = modules_toml_path(path)
        modules = load_modules_toml(toml_path) if toml_path else {}
        if module not in modules:
            raise StateError(
                f"unknown module slug: {module!r} -- declare it in docs/modules/modules.toml first "
                "(see module-impact-detect for candidates)"
            )
        package.setdefault("module_impacts", []).append({
            "module": module,
            "cambio": cambio,
            "modelo_mental": modelo_mental,
            "feature_id": data.get("feature_id"),
            "package_id": args.package_id,
            "at": now(),
            "actor": args.actor,
        })
        model.record_event(
            data, "record-module-impact", data["phase"], data["phase"], args.actor, args.package_id,
            {"module": module}, args.event_id,
        )
        return True

    data, changed = model.mutate(path, args, "record-module-impact", update)
    if changed and not waived:
        # AC-20: the "Impacto humano" block, ready for the orchestrator to paste into the
        # narration -- P4 (ADR-0036 sibling) fixes the exact placement, this only mints the
        # four lines from the command's own arguments.
        toml_path = modules_toml_path(path)
        modules = load_modules_toml(toml_path) if toml_path else {}
        nombre = modules.get(args.module, {}).get("nombre", args.module)
        print("Impacto humano:")
        print(f"Módulo: {nombre}")
        print(f"Cambio de modelo mental: {args.cambio.strip()}")
        print(f"Tenés que saber: {args.modelo_mental.strip()}")
    return output_state(data, changed, path)


def cmd_module_impact_detect(args: argparse.Namespace) -> int:
    """Read-only: lists module slugs whose declared globs match this package's
    owned_paths/repair changed_files. Never mutates."""
    path = state_file_arg(args)
    data = load_state(path)
    fail_if_invalid(data)
    package = package_by_id(data, args.package_id)
    toml_path = modules_toml_path(path)
    modules = load_modules_toml(toml_path) if toml_path else {}
    candidates = detect_module_candidates(package, modules)
    already_covered = bool(package.get("module_impacts") or package.get("module_impact_waiver"))
    # F-06 (P3 review): paths that matched no module pattern at all -- advisory only,
    # never blocks anything -- surfaced in its own section, clearly distinct from
    # `candidates`, so a caller can tell "add me as an impact" from "consider registering
    # this as a new module in modules.toml".
    unmatched = unmatched_candidate_paths(package_candidate_paths(package), modules)
    print_json({
        "ok": True,
        "package_id": args.package_id,
        "candidates": candidates,
        "known_modules": sorted(modules),
        "already_covered": already_covered,
        "unmatched_paths": unmatched,
    })
    return 0


def cmd_check_anchors(args: argparse.Namespace) -> int:
    """AC-06/AC-07 (020-honest-dashboard PKG-2, ADR-0040): read-only `file:line` anchor
    verifier for docs/modules/*.md. NOT a gate of any phase (spec no-goal) -- a caller
    that wants this to block something has to decide that itself; this command only
    reports and sets its own exit code."""
    repo_root = Path(args.repo_root) if args.repo_root else Path.cwd()
    modules_dir = Path(args.modules_dir) if args.modules_dir else None
    result = check_anchors(repo_root, modules_dir, only_module=args.module)
    for item in result["broken"]:
        print(f"ANCHOR_BROKEN {item['doc']}:{item['line']} {item['raw']} -> {item['reason']}")
    if result["ok"]:
        print(f"ANCHORS_OK checked={len(result['checked_docs'])} anchors={result['anchor_count']}")
    print_json(result)
    return 0 if result["ok"] else 1
