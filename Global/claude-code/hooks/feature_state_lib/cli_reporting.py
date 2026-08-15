"""Extracted from ai/scripts/feature-state.py by a behavior-preserving refactor
(mechanical reorganization only -- no logic changes). See feature-state.py's own
module docstring and the package-level notes for the split rationale.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from feature_state_lib import model
from feature_state_lib.model import (
    StateError, now, base_state, compact_package, fail_if_invalid, print_json, package_accept_ready,
)
from feature_state_lib.transitions import check_transition
from feature_state_lib.render_status import status_root, render_status
from feature_state_lib.render_bitacora import read_jsonl, render_bitacora, NARRATIVE_LOG
from feature_state_lib.render_notes import slugify, DECISIONS_LOG


def cmd_render_status(args: argparse.Namespace) -> int:
    anchor = Path(args.state_dir or "ai/state") / "features" / "_anchor.json"
    render_status(anchor)
    render_bitacora(anchor)
    features_dir, out_dir = status_root(anchor)
    print_json({"ok": True, "status_file": str(out_dir / "STATUS.md")})
    return 0


def cmd_log_quickfix(args: argparse.Namespace) -> int:
    log_path = Path(args.log_file) if args.log_file else Path("ai/state/quickfix-log.jsonl")
    entry = {
        "at": now(),
        "summary": args.summary,
        "files": args.file or [],
        "gate": args.gate or "-",
        "result": args.result,
        "actor": args.actor,
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    anchor = log_path.parent / "features" / "_anchor.json"
    render_status(anchor)
    model.render_notes(anchor)
    print_json({"ok": True, "log_file": str(log_path), "entry": entry})
    return 0


def cmd_log_narrative(args: argparse.Namespace) -> int:
    """Persist one narration block that has no record-spawn of its own.

    Every closing block, and every block emitted in consult or quick-fix mode,
    lands here. Narrating in chat without landing it here is exactly the hole
    this command closes: the chat is gone next week, the bitacora is not.
    """
    log_path = Path(args.log_file) if args.log_file else Path("ai/state") / NARRATIVE_LOG
    entry = {
        "at": now(),
        "feature_id": args.feature_id or "sin-feature",
        "package_id": args.package_id or "-",
        "role": args.role or "-",
        "result": args.result,
        "client": args.client,
        "tech": args.tech,
        "actor": args.actor,
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")
    anchor = log_path.parent / "features" / "_anchor.json"
    only = args.feature_id or None
    render_status(anchor)
    render_bitacora(anchor, only_feature=only)
    model.render_notes(anchor, only_feature=only)
    print_json({"ok": True, "log_file": str(log_path), "entry": entry})
    return 0


def cmd_log_decision(args: argparse.Namespace) -> int:
    """Persist a decision that outlives its package (the tier below a formal ADR).

    Appends to ai/state/decisions-log.jsonl and re-renders the living notes so
    docs/notas/decisiones/ gets its own [[linked]] note. Idempotent: logging the
    same decision again is a no-op.
    """
    log_path = Path(args.log_file) if args.log_file else Path("ai/state") / DECISIONS_LOG
    slug = args.slug or slugify(args.title)
    duplicate = next(
        (
            entry for entry in read_jsonl(log_path)
            if entry.get("slug") == slug and entry.get("title") == args.title
            and entry.get("decision") == args.decision
        ),
        None,
    )
    entry = duplicate or {
        "at": now(),
        "slug": slug,
        "title": args.title,
        "context": args.context,
        "decision": args.decision,
        "consequences": args.consequences or "",
        "feature_id": args.feature_id or "",
        "package_id": args.package_id or "",
        "actor": args.actor,
    }
    if duplicate is None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")
    model.render_notes(log_path.parent / "features" / "_anchor.json")
    print_json({"ok": True, "log_file": str(log_path), "entry": entry, "deduped": duplicate is not None})
    return 0


def _warn_check_anchors_never_raises(state_dir: Path) -> None:
    """AC-09 (020-honest-dashboard PKG-2, ADR-0040): same never-raises contract as
    render_notes.py's own (`render_notes.py:281-285`, `RENDER_FAILURE_LOG`) -- `check-
    anchors` is explicitly NOT a gate of any phase (spec no-goal), so sync-notes runs it
    best-effort and only WARNS on stderr. A broken verifier, or anchors it finds broken,
    must never fail this consolidation command; see
    tests/test_check_anchors.py::SyncNotesNeverRaisesTests for the mutation that pins
    this (a verifier forced to raise still lets sync-notes finish and print
    NOTES_SYNCED)."""
    try:
        from feature_state_lib.check_anchors import check_anchors  # deferred: see module docstring
        repo_root = state_dir.resolve().parent.parent  # ai/state -> repo root, same derivation as default_notes above
        result = check_anchors(repo_root)
        if not result["ok"]:
            broken = result["broken"]
            print(f"ANCHORS_WARN broken={len(broken)} (check-anchors es informativo, no bloquea)", file=sys.stderr)
            for item in broken[:20]:
                print(f"  {item['doc']}:{item['line']} {item['raw']} -> {item['reason']}", file=sys.stderr)
    except Exception as exc:  # never-raises: a broken checker must not break sync-notes
        print(f"ANCHORS_CHECK_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)


def cmd_sync_notes(args: argparse.Namespace) -> int:
    """Consolidation point: full regen of STATUS, bitacora, and the living notes.

    Intra-phase writes may defer rendering via --no-render; this command always
    renders everything, so run it at phase close and end of turn.
    """
    model.RENDER_SKIP = False
    state_dir = Path(args.state_dir) if args.state_dir else Path("ai/state")
    # Same root derivation the bitacora uses: ai/state -> repo root.
    default_notes = state_dir.resolve().parent.parent / "docs" / "notas"
    notes_dir = Path(args.notes_dir) if args.notes_dir else default_notes
    notes_dir.mkdir(parents=True, exist_ok=True)
    anchor = state_dir / "features" / "_anchor.json"
    render_status(anchor)
    render_bitacora(anchor)
    written = model.render_notes(anchor, str(notes_dir), args.project_name, force=True)
    from feature_state_lib.render_modules import render_modules  # deferred: see module docstring
    written += render_modules(anchor, force=True)
    _warn_check_anchors_never_raises(state_dir)
    # AC-14 (028/N3a): this docstring already says "run it at phase close and end of
    # turn" -- that is precisely the cadence AC-14 wants for the digest too, and
    # nowhere else. `log-narrative`/`log-quickfix` (every per-mutation write) call
    # `render_status`/`render_bitacora`/`render_notes` directly and deliberately never
    # reach here, so a package mid-flight never touches the git-tracked
    # `BUENOS-DIAS.md` (024/C1 + 027's owned-paths hardening — see this AC's own
    # rationale in the spec). Regenerating BOTH dashboards in the same command call is
    # also what keeps their two "as of" timestamps from drifting apart (measurable
    # criterion: `BUENOS-DIAS.md`'s "generado" must never trail STATUS.md's
    # "Actualizado" — D-5 measured a 3-day gap under the old "nobody remembers to run
    # digest" regime). Best-effort: a digest hiccup must never break sync-notes' own
    # "always renders everything" contract.
    try:
        cmd_digest(argparse.Namespace(state_dir=str(state_dir), notes_dir=str(notes_dir), since=None))
    except Exception as exc:
        print(f"DIGEST_SKIPPED error={exc}")
    print(f"NOTES_SYNCED n={len(written)}")
    print_json({"ok": True, "notes_dir": str(notes_dir), "written": written})
    return 0


def _digest_since(raw: str | None) -> str:
    """Resolve --since to an ISO prefix. Default and 'ayer' = 24h ago; 'hoy' = today
    00:00 local. Anything else is taken as an ISO timestamp/prefix verbatim (the
    logs' `at` fields are ISO, so plain string comparison is the right filter)."""
    from datetime import datetime, timedelta
    if raw and raw not in ("ayer", "hoy"):
        return raw
    if raw == "hoy":
        return datetime.now().strftime("%Y-%m-%dT00:00:00")
    return (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")


def cmd_digest(args: argparse.Namespace) -> int:
    """017/AC-09 (ADR-0027): the morning-coffee digest, DERIVED from state.

    Regenerates docs/notas/BUENOS-DIAS.md between the notas:auto markers
    (human text outside them is preserved by merge_note) from the three JSONL
    logs plus the live feature states. The hand-written predecessor of this
    file went stale twice and cost two ACs to correct — deriving it is the fix.
    """
    from feature_state_lib.render_bitacora import collect_narrative
    from feature_state_lib.render_notes import _short, write_note, notes_root, _pending_bits
    from feature_state_lib.render_status import status_root

    state_dir = Path(args.state_dir) if args.state_dir else Path("ai/state")
    anchor = state_dir / "features" / "_anchor.json"
    features_dir, out_dir = status_root(anchor)
    since = _digest_since(args.since)

    states = []
    for path in sorted(features_dir.glob("*.json")):
        if path.name == "_anchor.json":
            continue
        try:
            states.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue

    lines = [f"_Ventana: desde `{since}` · generado {now()}_", ""]

    # AC-01 (020-honest-dashboard, ADR-0040): FIRST section in the document, before "Qué
    # quedó listo". Every feature with an unresolved blocker, independent of final_state
    # (the search itself never filters by it, even though today only BLOCKED reaches
    # here) -- days counted from the LAST blocker without `resolved_at`, never
    # `updated_at` blindly (model.open_blocker). Fixed rather than appear-and-disappear: a
    # section that comes and goes reads as noise, a steady one reads as a dashboard (same
    # principle ADR-0027 already applies to "Qué falta").
    lines += ["## Necesita tu decisión", ""]
    needs_decision = [(d, model.open_blocker(d)) for d in states]
    needs_decision = [(d, blocker) for d, blocker in needs_decision if blocker]
    if needs_decision:
        for data, blocker in needs_decision:
            days = model.days_since(blocker.get("at"))
            # AC-13 (028/N3a): this is "Necesita tu decisión" -- the FIRST section of
            # the digest, the one that answers Federico's actual question. Truncating it
            # at 120 chars mid-sentence (the old default `_short` limit) is the D-4d
            # example verbatim: "...five high findings remain and P1 exhau…". `limit=None`
            # renders the reason whole; option (b) from AC-13 ("a short form written on
            # purpose") is not attempted here because a blocker's reason IS already the
            # short form an agent chose to write.
            lines.append(
                f"- **{data.get('feature_id')}** — {_short(blocker.get('reason', ''), None)} (hace {days} días)"
            )
    else:
        lines.append("- _nada pendiente de tu decisión_ ✅")

    finished = [e for e in collect_narrative(features_dir, out_dir)
                if e.get("at", "") >= since and e.get("result") not in ("started", "-", "")]
    lines += ["", "## Qué quedó listo", ""]
    if finished:
        for entry in finished[-20:]:
            head = " · ".join(p for p in (entry.get("feature_id"), entry.get("package_id"),
                                          entry.get("role")) if p and p != "-")
            # AC-13 (028/N3a): "Qué quedó listo" — full text, never a 300-char mid-
            # sentence cut (D-3-style example: `bitacora.md` closes routinely run past
            # 300 chars and today lose the second half of the sentence to `…`).
            lines.append(f"- **{head}** — {_short(entry.get('client') or entry.get('tech'), None)}")
    else:
        lines.append("- _sin cierres registrados en la ventana_")

    # AC-02/AC-03: `live` is the shared predicate's set (feature_is_live -- excludes only
    # genuinely finished features); `working` drops the blocked ones, which AC-01's
    # headline above already covers in more detail -- listing them here too would be a
    # redundant 3rd mention (spec SC-06, tope de dos menciones por feature bloqueada).
    lines += ["", "## Qué se está haciendo", ""]
    live = [d for d in states if model.feature_is_live(d)]
    working = [d for d in live if model.open_blocker(d) is None]
    if working:
        for data in working:
            line = f"- **{data.get('feature_id')}** — fase `{data.get('phase')}`"
            if model.feature_is_stale(data):
                line += f" — ⚠️ estancada hace {model.stale_days(data)} días"
            lines.append(line)
    else:
        lines.append("- _ninguna feature activa_")

    lines += ["", "## Qué falta", ""]
    pending_any = False
    for data in live:
        # AC-03 (F-01 repair, tope de dos menciones): a feature already headlined above in
        # "## Necesita tu decisión" repeats its `⛔ bloqueo:` bit here verbatim -- same text,
        # same truncation, zero new information (3rd mention). Every OTHER bit
        # (`_pending_bits` also renders open findings / pending tasks) is new information
        # and stays: only the literal blocker-duplicate line is dropped, never the feature.
        # 028/N3a, same principle: `describe_next_step` on a BLOCKED feature is
        # "corresponde tu decisión (ver Blocker)" -- zero information beyond the headline
        # this feature is already under, so it gets the same treatment as `⛔ bloqueo:`.
        headlined = model.open_blocker(data) is not None
        for bit in _pending_bits(data):
            if headlined and (bit.startswith("⛔ bloqueo:") or bit.startswith("→ corresponde tu decisión")):
                continue
            lines.append(f"- **{data.get('feature_id')}** {bit}")
            pending_any = True
    if not pending_any:
        lines.append("- _nada pendiente_ ✅")

    # AC-22 (019/PKG-3, ADR-0036): module_impacts recorded in the window, across every
    # package of every feature -- same "derived from state, never hand-maintained" posture
    # as every other section here.
    module_changes = []
    for data in states:
        for package in data.get("packages", []) or []:
            if not isinstance(package, dict):
                continue
            for impact in package.get("module_impacts", []) or []:
                if isinstance(impact, dict) and impact.get("at", "") >= since:
                    module_changes.append({**impact, "feature_id": impact.get("feature_id") or data.get("feature_id")})
    lines += ["", "## Qué cambió en el software", ""]
    if module_changes:
        # F-03 repair evidence (P3 review): this reads module_impacts straight out of raw
        # state (not schema-validated), so module/feature_id/package_id -- like every other
        # state-sourced field this digest renders -- must pass through `_short` before
        # landing in a file merge_note protects, or a crafted value can inject a fake
        # heading/arbitrary content into BUENOS-DIAS.md's machine block.
        for entry in sorted(module_changes, key=lambda e: e.get("at", "")):
            lines.append(
                f"- **{_short(entry.get('module', '?'), 80)}** — {_short(entry.get('cambio', ''), 200)} "
                f"({_short(entry.get('feature_id', '?'), 80)}/{_short(entry.get('package_id', '?'), 80)})"
            )
    else:
        lines.append("- _sin cambios de módulo registrados en la ventana_")

    from feature_state_lib.render_bitacora import read_jsonl as _read
    from feature_state_lib.render_notes import DECISIONS_LOG as _DECISIONS
    decisions = [e for e in _read(out_dir / _DECISIONS) if e.get("at", "") >= since]
    if decisions:
        lines += ["", "## Decisiones nuevas", ""]
        for entry in decisions:
            # AC-13 (028/N3a): "Decisiones nuevas" — the 18-of-18 case the spec measured
            # (`_short(..., 200)`). D-4d: a decision's "por qué" is conventionally
            # written LAST, so a head-truncation at 200 chars is not a neutral cut, it is
            # specifically the part this feature exists to stop losing. Full text.
            lines.append(f"- **{entry.get('title', '')}** — {_short(entry.get('decision', ''), None)}")

    quickfixes = [e for e in _read(out_dir / "quickfix-log.jsonl") if e.get("at", "") >= since]
    if quickfixes:
        lines += ["", "## Quick-fixes", ""]
        for entry in quickfixes:
            lines.append(f"- {_short(entry.get('summary', ''), 200)} ({entry.get('result', '')})")

    notes_dir = Path(args.notes_dir) if args.notes_dir else notes_root(anchor, None)
    if notes_dir is None:
        print_json({"ok": False, "error": "notes root unresolved (state dir is not ai/state)"})
        return 2
    target = notes_dir / "BUENOS-DIAS.md"
    # One-time migration: the hand-written predecessor has no notas:auto markers, and
    # merge_note would otherwise DISCARD it. Move it whole under "Notas propias" so the
    # human text survives exactly like in every other living note.
    from feature_state_lib.render_notes import NOTES_AUTO_BEGIN, NOTES_AUTO_END
    if target.exists():
        existing = target.read_text(encoding="utf-8")
        if NOTES_AUTO_BEGIN not in existing:
            target.write_text(
                "# Buenos días — digest del proyecto\n\n"
                f"{NOTES_AUTO_BEGIN}\n{NOTES_AUTO_END}\n\n"
                "## Notas propias (contenido manual previo, preservado)\n\n" + existing,
                encoding="utf-8",
            )
    write_note(target, "Buenos días — digest del proyecto", "\n".join(lines))
    print(f"DIGEST_WRITTEN file={target} since={since}")
    print_json({"ok": True, "file": str(target), "since": since,
                "finished": len(finished), "decisions": len(decisions), "quickfixes": len(quickfixes)})
    return 0


def run_dry_workflow(feature_id: str) -> dict[str, Any]:
    data = base_state(feature_id, "docs/specs/example/spec.md", "dry-run")
    data["acceptance_criteria"] = ["AC-1", "AC-2", "AC-3"]

    def direct(event: str, from_phase: str, to_phase: str, actor: str, package_id: str | None = None, metadata: dict[str, Any] | None = None) -> None:
        if data["phase"] != from_phase:
            raise StateError(f"dry-run expected {from_phase}, found {data['phase']}")
        check_transition(data, to_phase, package_id, actor)
        data["phase"] = to_phase
        model.record_event(data, event, from_phase, to_phase, actor, package_id, metadata)

    package = compact_package("PKG-01", "Deliver one observable vertical slice")
    package.update({
        "acceptance_criteria": ["AC-1", "AC-2", "AC-3"],
        "tasks": [
            {"id": "T-001", "status": "planned", "local_validations": [], "blockers": []},
            {"id": "T-002", "status": "planned", "local_validations": [], "blockers": []},
            {"id": "T-003", "status": "planned", "local_validations": [], "blockers": []},
        ],
        "owned_paths": ["src/**", "tests/**"],
        "complexity": "medium",
        "selected_role": "implementer",
        "selected_model": "terra",
        "routing_reason": "three related tasks across implementation and tests",
    })
    data["packages"].append(package)
    data["current_package_id"] = "PKG-01"
    model.record_event(data, "create-package", "PACKAGE_PLANNING", "PACKAGE_PLANNING", "package-planner", "PKG-01")
    direct("transition", "PACKAGE_PLANNING", "PACKAGE_IMPLEMENTATION", "orchestrator", "PKG-01")
    for task in package["tasks"]:
        task["status"] = "completed"
        task["local_validations"] = ["typecheck", "lint", "focused-unit-test"]
        model.record_event(data, "complete-task", "PACKAGE_IMPLEMENTATION", "PACKAGE_IMPLEMENTATION", "implementer", "PKG-01", {"task_id": task["id"]})
    direct("transition", "PACKAGE_IMPLEMENTATION", "PACKAGE_GATES", "orchestrator", "PKG-01")
    package["integrated"] = True
    package["diff_ref"] = "dry-run-diff"
    package["gates"].append({"name": "package verify", "status": "pass", "required": True, "evidence": "dry-run", "at": now()})
    direct("transition", "PACKAGE_GATES", "PACKAGE_REVIEW", "orchestrator", "PKG-01")
    package["reviews"].append({"verdict": "repair_required", "findings": ["F-001", "F-002"], "at": now(), "evidence": "dry-run consolidated review"})
    package["findings"] = [
        {"id": "F-001", "severity": "high", "category": "correctness", "status": "open"},
        {"id": "F-002", "severity": "medium", "category": "testing", "status": "open"},
    ]
    package["attempts"]["deep_review_cycles"] = 1
    data["metrics"]["package_reviews"] = 1
    data["phase"] = "PACKAGE_REPAIR"
    model.record_event(data, "record-review", "PACKAGE_REVIEW", "PACKAGE_REPAIR", "package-reviewer", "PKG-01", {"finding_count": 2})
    # The bundle carries a high finding, so ADR-0009 D4 requires the verifier: the
    # self-demonstration must show the node, refutation shape included.
    refuted = package["findings"][1]
    refuted.update({
        "status": "refuted",
        "verified_by": "finding-verifier",
        "verified_at": now(),
        "verified_verdict": "refuted",
        "verdict_reason": "an existing regression test already covers the cited path",
        "verdict_evidence": "$ pytest tests/test_example.py -k interleaving\n1 passed, 0 failed",
    })
    upheld = package["findings"][0]
    upheld.update({"verified_by": "finding-verifier", "verified_at": now(), "verified_verdict": "upheld"})
    package["verifications"].append({"refuted": ["F-002"], "upheld": ["F-001"], "at": now(), "evidence": "dry-run refutation pass"})
    package["attempts"]["verifications"] = 1
    data["metrics"]["verifications"] = 1
    model.record_event(data, "record-verification", "PACKAGE_REPAIR", "PACKAGE_REPAIR", "finding-verifier", "PKG-01", {"refuted": 1, "upheld": 1})
    for finding in package["findings"]:
        if finding["status"] == "refuted":
            continue
        finding["status"] = "closed"
        finding["repair_attempts"] = 1
    package["repairs"].append({"finding_ids": ["F-001"], "changed_files": ["src/example.py"], "verification": ["focused-unit-test"], "at": now()})
    package["attempts"]["repair_batches"] = 1
    data["metrics"]["repair_batches"] = 1
    data["phase"] = "DELTA_REVIEW"
    model.record_event(data, "record-repair", "PACKAGE_REPAIR", "DELTA_REVIEW", "repair-agent", "PKG-01", {"finding_ids": ["F-001"]})
    package["delta_reviews"].append({"verdict": "pass", "closed_findings": ["F-001"], "new_or_reopened_findings": [], "requires_full_review": False, "reason": "dry-run", "at": now()})
    data["metrics"]["delta_reviews"] = 1
    data["phase"] = "PACKAGE_TESTING"
    model.record_event(data, "record-delta-review", "DELTA_REVIEW", "PACKAGE_TESTING", "delta-reviewer", "PKG-01", {"verdict": "pass"})
    package["testing"].append({"status": "pass", "commands": ["verify", "integration"], "evidence": "dry-run tests", "at": now()})
    data["phase"] = "PACKAGE_RUNTIME_QA"
    model.record_event(data, "record-testing", "PACKAGE_TESTING", "PACKAGE_RUNTIME_QA", "gate-runner", "PKG-01", {"status": "pass"})
    package["runtime_qa"].append({
        "status": "pass",
        "url": "http://localhost:3000",
        "browser": "playwright",
        "screenshots": ["dry-run-home.png"],
        "checks": ["flow renders", "save works", "no visible secret"],
        "evidence": "dry-run browser QA",
        "at": now(),
    })
    model.record_event(data, "record-runtime-qa", "PACKAGE_RUNTIME_QA", "PACKAGE_RUNTIME_QA", "runtime-verifier", "PKG-01", {"status": "pass"})
    errors = package_accept_ready(data, package, "orchestrator")
    if errors:
        raise StateError("; ".join(errors))
    package["status"] = "accepted"
    data["phase"] = "PACKAGE_ACCEPTED"
    model.record_event(data, "accept-package", "PACKAGE_RUNTIME_QA", "PACKAGE_ACCEPTED", "orchestrator", "PKG-01")
    # ADR-0036: entering INTEGRATION requires module-impact coverage per accepted package.
    # This synthetic run demonstrates the waiver path -- record-module-impact is the CLI's
    # own dedicated verb, exercised for real by tests/test_module_docs.py.
    package["module_impact_waiver"] = {"reason": "dry-run demonstration", "at": now(), "actor": "orchestrator"}
    direct("transition", "PACKAGE_ACCEPTED", "INTEGRATION", "orchestrator", "PKG-01")
    data["global_gates"].append({"name": "global verify", "status": "pass", "required": True, "evidence": "dry-run", "at": now()})
    direct("transition", "INTEGRATION", "DONE", "orchestrator", "PKG-01")
    data["final_state"] = "DONE"
    fail_if_invalid(data)
    return data


def cmd_spawns(args: argparse.Namespace) -> int:
    """ADR-0031: read-only listing of a feature's spawns with their routing decision
    (model/provider/effort/route_id) when the record carries one. Never mutates state;
    legacy spawns without the structured fields list with those keys absent."""
    from feature_state_lib.cli_lifecycle import state_file_arg  # deferred: see module docstring
    from feature_state_lib.model import load_state
    from feature_state_lib.render_notes import _note_packages
    path = state_file_arg(args)
    data = load_state(path)
    spawns = []
    for package in _note_packages(data):
        if args.package_id and package.get("package_id") != args.package_id:
            continue
        for spawn in package.get("spawns", []) or []:
            if not isinstance(spawn, dict):
                continue
            row = {"package_id": package.get("package_id")}
            for key in ("spawn_id", "role", "purpose", "model", "provider", "effort", "route_id", "at"):
                if spawn.get(key):
                    row[key] = spawn[key]
            spawns.append(row)
    print_json({"ok": True, "feature_id": data.get("feature_id"), "spawns": spawns})
    return 0


def cmd_dry_run(args: argparse.Namespace) -> int:
    data = run_dry_workflow(args.feature_id)
    evidence = {
        "deep_reviews_per_task": data["metrics"]["task_deep_reviews"],
        "package_reviews": data["metrics"]["package_reviews"],
        "repair_batches": data["metrics"]["repair_batches"],
        "delta_reviews": data["metrics"]["delta_reviews"],
        "testing_runs": len(data["packages"][0]["testing"]),
        "runtime_qa_runs": len(data["packages"][0]["runtime_qa"]),
        "human_questions_after_approval": data["metrics"]["human_questions_after_approval"],
        "final_state": data["phase"],
    }
    print_json({"ok": True, "evidence": evidence, "state": data})
    print("DRY_RUN_PASS")
    return 0
