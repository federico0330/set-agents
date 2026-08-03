#!/usr/bin/env python3
"""Executable package-workflow state machine.

The state file is compact, atomic, and deterministic. It is intentionally not a
conversation log: agents record decisions, gates, findings, repairs, and a small
event history that lets the orchestrator resume without re-running prior steps.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Loaded both as a normal script (python3 feature-state.py ...) and via
# importlib.util.spec_from_file_location by tests/test_harness.py -- the latter does
# NOT add this file's own directory to sys.path, so `import feature_state_lib` would
# fail under that loading path without this.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from feature_state_lib import model
from feature_state_lib.model import (
    StateError, now, state_path, print_json, parse_json_object, parse_bool, base_state,
    compact_package, load_state, atomic_write, validate_state, fail_if_invalid, package_by_id,
    task_by_id, has_open_findings, required_gates, failing_required_gates, tasks_complete,
    package_review_ready, package_accept_ready, done_ready,
    PHASES, LEGAL_TRANSITIONS, TERMINAL, MUTATING_COMMANDS, NON_ACCEPTING_ACTORS, REFUTING_ACTORS,
    DEFAULT_MAX_VERIFICATIONS, MODE_BUDGETS, TERMINAL_FINDING_STATUSES,
)
from feature_state_lib.transitions import check_transition, next_transition
from feature_state_lib.render_status import status_root, summarize_feature, render_status
from feature_state_lib.render_bitacora import (
    read_jsonl, collect_narrative, format_narrative, bitacora_path, render_bitacora, NARRATIVE_LOG,
)
from feature_state_lib.render_notes import (
    slugify, notes_root, merge_note, write_note, _short, _decision_name, _unique_decisions,
    _dicts, _snake_key, _normalize_note_state, _note_packages, _pending_bits,
    _package_body, _decision_body, _log_render_failure,
    NOTES_AUTO_BEGIN, NOTES_AUTO_END, DECISIONS_LOG, RENDER_FAILURE_LOG, RENDER_FAILURE_LOG_CAP,
)
from feature_state_lib.graph import (
    _norm, _mermaid_escape, _GraphState, _review_label, _add_package_findings,
    _add_package_spawns, _add_feature_to_graph, build_execution_graph, validate_mermaid_structure,
    render_mermaid, GRAPH_NODE_TYPES, GRAPH_EDGE_TYPES, MERMAID_RESERVED_WORDS,
)
from feature_state_lib.cli_lifecycle import (
    output_state, state_file_arg, verify_spec_hash, cmd_init, cmd_validate, cmd_status, cmd_next,
    cmd_transition, cmd_create_package, cmd_update_package, cmd_start_task, cmd_complete_task,
    cmd_fail_task, cmd_resume, cmd_reopen, cmd_block, block_with_reason,
)
from feature_state_lib.cli_review import (
    cmd_record_review, panel_roles, cmd_record_subreview, cmd_finalize_review_panel,
    _verdict_text, normalize_verdicts, _repair_entered_from_review, merge_finding,
    require_verified,
    EVIDENCE_SHAPES, MAX_VERDICT_FIELD, MIN_EVIDENCE_LEN, VERIFICATION_AXIS,
)
from feature_state_lib.cli_repair import (
    normalize_findings, cmd_record_gate, _git_answer, validate_commit_ref, cmd_record_repair,
    cmd_record_delta_review, cmd_record_testing, cmd_record_runtime_qa, cmd_accept_package,
    FINDING_BOOKKEEPING, COMMIT_SHA_RE, GIT_TIMEOUT_SECONDS,
)
from feature_state_lib.cli_reporting import (
    cmd_render_status, cmd_log_quickfix, cmd_log_narrative, cmd_log_decision, cmd_sync_notes,
    run_dry_workflow, cmd_dry_run,
)
from feature_state_lib.parser import add_common_state_args


# `replayed`/`record_event`/`mutate` stay physically defined in this file (see
# tests.test_harness.HarnessTests.test_replay_detection_has_exactly_one_definition):
# every other command that needs them reaches them through the `model.record_event`/
# `model.mutate` slots injected right after they are defined below. The five commands
# that call `replayed(` directly (cmd_record_spawn, cmd_start_review_panel,
# cmd_extend_review_panel, cmd_record_late_review, cmd_record_verification) stay here
# too, for the same reason.
#
# `render_notes`/`_hub_body`/`_feature_body`, `cmd_graph`, and
# `_apply_verification_waiver`/`_apply_verdicts` ALSO stay here (rather than in
# feature_state_lib/render_notes.py, graph.py, and cli_review.py respectively, as
# the original split plan had them) for a second, independent reason: several
# tests in tests/test_harness.py load this file as a module, monkeypatch one of
# its private helpers (e.g. `module._mermaid_escape`, `module._feature_body`,
# `module.now`, `module.record_event`), and then call a SIBLING public function
# on that same loaded module expecting the patch to be observed. Python resolves
# a bare name inside a function via that function's OWN defining module's
# globals, never via whichever module happens to import/re-export the same
# object under the same name -- so the patched name and the function reading it
# must share one file for the patch to have any effect. `render_notes` calls
# `_hub_body`/`_feature_body` directly; `cmd_graph` calls `_mermaid_escape`
# directly; `_apply_verification_waiver`/`_apply_verdicts` are unit-tested by
# direct call and read `now`/`record_event` directly -- all bare-name reads that
# would otherwise silently stop seeing a test's patch.


def replayed(data: dict[str, Any], event: str, event_id: str | None) -> bool:
    """Has *this exact call* already run?

    Keyed on the command as well as the id, because "already applied" is a claim about a
    call and not about a string.  Scoping it by `event_id` alone made an id reused across
    two different commands read as a replay of the second one: the caller got
    `{"ok": true, "changed": false}` and nothing happened — the silent success-shaped
    no-op this feature exists to abolish, and on `record-late-review` it meant a verified
    critical finding disappearing with exit 0.  Every guard that asks the question asks it
    here, so the updaters and `record_event` can never disagree about the answer: if they
    did, a call could pass its own guard and then have its history entry silently dropped.
    """
    if not event_id:
        return False
    return any(item.get("event_id") == event_id and item.get("event") == event
               for item in data.get("history", []))

def record_event(
    data: dict[str, Any],
    event: str,
    from_phase: str,
    to_phase: str,
    actor: str,
    package_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    event_id: str | None = None,
) -> bool:
    if replayed(data, event, event_id):
        return False
    entry = {
        "timestamp": now(),
        "event": event,
        "from": from_phase,
        "to": to_phase,
        "actor": actor,
        "package_id": package_id,
        "metadata": metadata or {},
    }
    if event_id:
        entry["event_id"] = event_id
    data.setdefault("history", []).append(entry)
    return True

def mutate(
    path: Path,
    args: argparse.Namespace,
    operation: str,
    updater,
) -> tuple[dict[str, Any], bool]:
    data = load_state(path)
    fail_if_invalid(data)
    expected = getattr(args, "expect_revision", None)
    if expected is not None and data.get("revision") != expected:
        raise StateError(f"stale revision: expected {expected}, found {data.get('revision')}")
    before = deepcopy(data)
    changed = updater(data)
    if changed:
        data["revision"] = int(data.get("revision", 0)) + 1
        data["updated_at"] = now()
        fail_if_invalid(data)
        atomic_write(path, data)
        only = data.get("feature_id")
        render_status(path)
        render_bitacora(path, only_feature=only)
        render_notes(path, only_feature=only)
    return data, before != data


model.record_event = record_event
model.mutate = mutate


def _hub_body(states: list[dict[str, Any]], out_dir: Path, decisions: list[dict[str, Any]]) -> str:
    lines = ["## Features", ""]
    if not states:
        lines.append("- _todavía no hay features en el state_")
    for data in states:
        fid = data.get("feature_id", "?")
        packages = _note_packages(data)
        accepted = sum(1 for p in packages if p.get("status") == "accepted")
        tail = f" · **{data['final_state']}**" if data.get("final_state") else ""
        lines.append(
            f"- [[features/{fid}|{fid}]] — fase `{data.get('phase')}` · paquetes {accepted}/{len(packages)}{tail}"
        )
    lines += ["", "## Qué falta", ""]
    pending_any = False
    for data in states:
        for bit in _pending_bits(data):
            lines.append(f"- **{data.get('feature_id')}** {bit}")
            pending_any = True
    if not pending_any:
        lines.append("- _nada pendiente en features activas_ ✅")
    quickfixes = read_jsonl(out_dir / "quickfix-log.jsonl")
    if quickfixes:
        lines += ["", "## Quick-fixes recientes", ""]
        for entry in quickfixes[-5:][::-1]:
            lines.append(f"- {entry.get('at', '')[:16]} — {_short(entry.get('summary', ''))} ({entry.get('result', '')})")
    if decisions:
        lines += ["", "## Decisiones", ""]
        for entry in decisions[-8:][::-1]:
            lines.append(f"- [[decisiones/{_decision_name(entry)}|{entry.get('title', '')}]]")
    updated = max((data.get("updated_at", "") for data in states), default="-")
    lines += [
        "", "## Referencias", "",
        "- `ai/state/STATUS.md` — dashboard técnico",
        "- `docs/adr/` — decisiones formales de arquitectura",
        "", f"_Actualizado: {updated}_",
    ]
    return "\n".join(lines)


def _feature_body(
    data: dict[str, Any], out_dir: Path,
    narrative: list[dict[str, Any]], decisions: list[dict[str, Any]],
) -> str:
    fid = data.get("feature_id", "?")
    lines = ["## Estado", "", f"- fase: `{data.get('phase')}` · modo: {data.get('mode') or 'feature'} · revisión {data.get('revision', 0)}"]
    if data.get("final_state"):
        lines.append(f"- estado final: **{data['final_state']}**")
    spec = data.get("approved_spec") or {}
    if spec.get("path"):
        lines.append(f"- spec: `{spec['path']}` (hash `{str(spec.get('hash', ''))[:12]}`)")
    criteria = data.get("acceptance_criteria", [])
    if criteria:
        lines += ["", "## Criterios de aceptación", ""] + [f"- {item}" for item in criteria]
    packages = _note_packages(data)
    if packages:
        lines += ["", "## Paquetes", ""]
        for package in packages:
            pid = package.get("package_id", "?")
            lines.append(f"- [[features/{fid}/{pid}|{pid}]] — {package.get('status')} · {_short(package.get('objective', ''), 90)}")
    approach = []
    for package in packages:
        if package.get("routing_reason"):
            approach.append(f"- ruteo {package.get('package_id')}: {_short(package['routing_reason'])}")
    for entry in [e for e in narrative if e.get("feature_id") == fid and e.get("tech")][-6:]:
        approach.append(f"- [{entry.get('at', '')[:10]}] {entry.get('role', '-')}: {_short(entry.get('tech', ''), 180)}")
    for entry in decisions:
        if entry.get("feature_id") == fid:
            approach.append(f"- decisión: [[decisiones/{_decision_name(entry)}|{entry.get('title', '')}]]")
    if approach:
        lines += ["", "## Approach y decisiones", ""] + approach
    pending = _pending_bits(data)
    lines += ["", "## Qué falta", ""] + ([f"- {bit}" for bit in pending] or ["- _nada pendiente_ ✅"])
    budgets = data.get("budgets", {})
    spawns = sum(p.get("attempts", {}).get("spawns", 0) for p in packages)
    lines += [
        "", "## Presupuestos", "",
        f"- spawns: {spawns} (máx {budgets.get('max_spawns_per_package', '?')}/paquete) · "
        f"deep review máx {budgets.get('max_deep_review_cycles', '?')} ciclos",
        "", f"[[00 - Proyecto|⌂ Proyecto]] · [[features/{fid}/grafo|grafo]] · bitácora: `{bitacora_path(out_dir, fid)}`",
        "", f"_Actualizado: {data.get('updated_at', '-')}_",
    ]
    return "\n".join(lines)


def render_notes(
    state_file: Path,
    notes_dir: str | None = None,
    project_name: str | None = None,
    only_feature: str | None = None,
    force: bool = False,
) -> list[str]:
    """Rebuild the living docs. Never raises: a broken note must not block state.

    only_feature keeps the hub fresh but regenerates feature/package notes for
    that feature alone and skips decision notes (they only change on
    log-decision). force ignores --no-render: sync-notes is the consolidation
    point and must always render everything.
    """
    written: list[str] = []
    if model.RENDER_SKIP and not force:
        return written
    try:
        fallback_out_dir = status_root(state_file)[1]
    except Exception:
        fallback_out_dir = None
    try:
        notes = notes_root(state_file, notes_dir)
        if notes is None:
            return written
        features_dir, out_dir = status_root(state_file)
        states = []
        for path in sorted(features_dir.glob("*.json")):
            try:
                states.append(_normalize_note_state(json.loads(path.read_text(encoding="utf-8"))))
            except (OSError, json.JSONDecodeError):
                continue
        narrative = collect_narrative(features_dir, out_dir)
        decisions = _unique_decisions(read_jsonl(out_dir / DECISIONS_LOG))
        project = project_name or notes.resolve().parent.parent.name
        if write_note(notes / "00 - Proyecto.md", f"{project} — notas", _hub_body(states, out_dir, decisions)):
            written.append("00 - Proyecto.md")
        for data in states:
            try:
                fid = data.get("feature_id", "?")
                if only_feature and fid != only_feature:
                    continue
                if write_note(notes / "features" / f"{fid}.md", fid, _feature_body(data, out_dir, narrative, decisions)):
                    written.append(f"features/{fid}.md")
                for package in _note_packages(data):
                    pid = package.get("package_id", "?")
                    if write_note(notes / "features" / fid / f"{pid}.md", f"{fid} · {pid}", _package_body(fid, package)):
                        written.append(f"features/{fid}/{pid}.md")
                # AC-24: same construction the `graph` subcommand uses (build_execution_graph
                # + render_mermaid), never a second copy of the join logic. Best-effort on
                # the same terms as every other note above -- a broken graph render lands in
                # the `except` below with the rest of this feature's notes, never raises.
                # PR-05: `features_dir` is THIS function's own, from `status_root()` above --
                # passed straight through rather than re-derived from `out_dir.parent.parent`
                # a second time by convention-chasing a DIFFERENT path.
                graph_state, graph_missing = build_execution_graph(
                    out_dir.parent.parent, [fid], features_dir=features_dir)
                grafo_body = "```mermaid\n" + render_mermaid(graph_state, graph_missing) + "```\n"
                if write_note(notes / "features" / fid / "grafo.md", f"{fid} · grafo", grafo_body):
                    written.append(f"features/{fid}/grafo.md")
            except Exception as exc:  # one malformed feature must not block the rest
                _log_render_failure(out_dir, f"feature={data.get('feature_id', '?')}", exc)
                continue
        if not only_feature:
            for entry in decisions:
                name = _decision_name(entry)
                if write_note(notes / "decisiones" / f"{name}.md", entry.get("title", "Decisión"), _decision_body(entry)):
                    written.append(f"decisiones/{name}.md")
    except Exception as exc:  # the living docs are best-effort by contract
        if fallback_out_dir is not None:
            _log_render_failure(fallback_out_dir, "render_notes", exc)
    return written


model.render_notes = render_notes


def cmd_graph(args: argparse.Namespace) -> int:
    root = Path(args.root) if args.root else Path.cwd()
    explicit_feature_ids = args.feature_id or None
    state, missing = build_execution_graph(root, explicit_feature_ids)
    text = render_mermaid(state, missing)
    if not explicit_feature_ids and not (root / "ai" / "state" / "features").is_dir():
        # PR-06: whole-repo mode (no --feature-id) against a root with no state
        # directory at all used to degrade silently to the bare `flowchart TD`
        # skeleton with exit 0 -- indistinguishable from a real project that
        # legitimately has zero features yet. AC-23 already sets the precedent for
        # this exact "nothing to read" case: `cmd_context`'s CONTEXT_VAULT_NOT_FOUND
        # announces it instead of staying silent. `root` is escaped like every other
        # interpolated value in this document (SEC-002); the line's shape is part of
        # `_MERMAID_MISSING_COMMENT_RE`'s closed vocabulary, so this stays a
        # structurally valid comment rather than an unchecked special case.
        text += "%% no state directory at " + _mermaid_escape(str(root)) + "\n"
        # D-03: this append happens AFTER `render_mermaid` already ran its own
        # self-check, so without a second check here the appended line would be the
        # one piece of this command's output the oracle never actually validates.
        # Same defense-in-depth posture as `render_mermaid`'s own check: this
        # module's own output failing its own oracle is a real bug, surfaced loudly.
        problems = validate_mermaid_structure(text)
        if problems:
            raise StateError("generated an invalid mermaid document: " + "; ".join(problems))
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def cmd_record_spawn(args: argparse.Namespace) -> int:
    path = state_file_arg(args)

    def update(data: dict[str, Any]) -> bool:
        if replayed(data, "record-spawn", args.event_id):
            # AC-01 (010-spawn-provenance): FIRST, before the phase gate and the budget
            # check -- a retried --event-id that arrives after the spawn already minted
            # its id must not re-spend the spawn budget or mint a second SPAWN-NNN. Same
            # guard, same position, same reason as cmd_start_review_panel's replayed()
            # guard: between the phase gate and the mint sits the budget check, which
            # could BLOCK the whole feature a second time on a pure retry.
            return False
        if data["phase"] in TERMINAL:
            raise StateError(f"cannot record spawn from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        attempts = package.setdefault("attempts", {})
        budget = data.get("budgets", {}).get("max_spawns_per_package", 12)
        if attempts.get("spawns", 0) >= budget:
            return block_with_reason(data, args.actor, args.package_id, "spawn budget exhausted")
        attempts["spawns"] = attempts.get("spawns", 0) + 1
        # AC-01: the id is always derived from the counter, never from
        # len(package["spawns"]) -- a package that already had spawns recorded before
        # this feature existed (e.g. attempts.spawns=8, no spawns[] key at all, the
        # exact shape of 006's own P3 package) continues the SAME counter: its next
        # spawn is SPAWN-009, not SPAWN-001.
        spawn_id = f"SPAWN-{attempts['spawns']:03d}"
        spawns = package.setdefault("spawns", [])
        if any(item.get("spawn_id") == spawn_id for item in spawns):
            # Defense in depth against a desynced counter. Reachable only by a
            # hand-corrupted fixture -- no real caller ever provides spawn_id, only
            # this command mints it.
            raise StateError(f"spawn {spawn_id} already exists on {args.package_id}: counter out of sync")
        spawns.append({
            "spawn_id": spawn_id,
            "role": args.role,
            "purpose": args.purpose,
            "client": args.client,
            "tech": args.tech,
            "at": now(),
        })
        metadata = {"role": args.role, "purpose": args.purpose, "spawns": attempts["spawns"], "spawn_id": spawn_id}
        # The two registers of the opening narration block. Optional so older
        # callers keep working, but the orchestrator doctrine requires them:
        # they are what render_bitacora turns into the durable story.
        if args.client:
            metadata["client"] = args.client
        if args.tech:
            metadata["tech"] = args.tech
        record_event(
            data,
            "record-spawn",
            data["phase"],
            data["phase"],
            args.actor,
            args.package_id,
            metadata,
            args.event_id,
        )
        return True

    data, changed = mutate(path, args, "record-spawn", update)
    return output_state(data, changed, path)


def cmd_start_review_panel(args: argparse.Namespace) -> int:
    path = state_file_arg(args)
    # Outside the updater: validating an argument should not need a loadable state file.
    roles = panel_roles(args.role)

    def update(data: dict[str, Any]) -> bool:
        if replayed(data, "start-review-panel", args.event_id):
            # FIRST, before the phase gate: a replayed open legitimately arrives after the
            # panel it created has already closed, and `cannot start review panel from
            # phase PACKAGE_REPAIR` is indistinguishable from a real precondition failure.
            # Same guard, same position, same reason as cmd_record_verification, and the
            # same shared `replayed()` as record_event — which is what stops the updater
            # and the history from disagreeing about whether this call is a retry.
            return False
        if data["phase"] != "PACKAGE_REVIEW":
            raise StateError(f"cannot start review panel from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        errors = package_review_ready(package)
        if errors:
            raise StateError("cannot start review panel: " + "; ".join(errors))
        attempts = package.setdefault("attempts", {})
        if attempts.get("deep_review_cycles", 0) >= data["budgets"]["max_deep_review_cycles"]:
            return block_with_reason(data, args.actor, args.package_id, "deep review budget exhausted")
        panel_id = args.panel_id or f"RP-{attempts.get('deep_review_cycles', 0) + 1:02d}"
        if any(panel.get("panel_id") == panel_id for panel in package.get("review_panels", [])):
            # Not a no-op: a second open against a live panel_id is either a lost update
            # or an attempt to grow the panel, and both have to say so.  Measured before
            # this existed: with an auto-generated id the silence was worse than silent,
            # because the id derives from the counter this command bumps — the retry
            # minted RP-02, spent the last deep-review cycle, stranded RP-01 in_progress
            # where record-subreview would never reach it again, and left the next
            # legitimate open to BLOCK the feature on `deep review budget exhausted`.
            raise StateError(
                f"review panel {panel_id} already exists on {package['package_id']}; to add a member "
                "to an open panel use extend-review-panel, and to retry a timed-out call pass the "
                "original --event-id"
            )
        panel = {
            "panel_id": panel_id,
            "status": "in_progress",
            "roles": roles,
            "subreviews": [],
            "started_at": now(),
            "completed_at": None,
        }
        package.setdefault("review_panels", []).append(panel)
        attempts["deep_review_cycles"] = attempts.get("deep_review_cycles", 0) + 1
        data["metrics"]["package_reviews"] += 1
        record_event(data, "start-review-panel", "PACKAGE_REVIEW", "PACKAGE_REVIEW", args.actor, args.package_id, {"panel_id": panel_id, "roles": panel["roles"]}, args.event_id)
        return True

    data, changed = mutate(path, args, "start-review-panel", update)
    return output_state(data, changed, path)


def cmd_extend_review_panel(args: argparse.Namespace) -> int:
    """Add a member to an OPEN panel instead of opening a second one.

    `orchestrator.md` already orders a specialist that becomes necessary mid-panel to be
    recorded "as a subreview of the same bounded panel" — impossible unless it was named
    at open time, and AC-08 makes that dead end permanent.  This is that verb.  It never
    touches `deep_review_cycles`, `metrics.package_reviews` or the deep-review budget: the
    panel is ONE cycle no matter how it grows, which is the whole reason it exists.
    """
    path = state_file_arg(args)
    roles = panel_roles(args.role)
    if not (args.reason or "").strip():
        # Without this, a grown panel is indistinguishable in the record from one that
        # named all its members up front — precisely what AC-08 exists to prevent.
        # Extending is the sanctioned loophole, so it has to document itself.
        raise StateError(
            "extend-review-panel requires --reason: why this member became necessary mid-panel"
        )

    def update(data: dict[str, Any]) -> bool:
        if replayed(data, "extend-review-panel", args.event_id):
            return False
        if data["phase"] != "PACKAGE_REVIEW":
            raise StateError(f"cannot extend review panel from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        panels = package.get("review_panels", [])
        if args.panel_id:
            panel = next((item for item in panels if item.get("panel_id") == args.panel_id), None)
            if panel is None:
                raise StateError(f"unknown panel_id: {args.panel_id}")
            if panel.get("status") != "in_progress":
                raise StateError(
                    f"panel {args.panel_id} is {panel.get('status')}; a review that returns after its "
                    "panel closed is recorded with record-late-review"
                )
        else:
            panel = next((item for item in reversed(panels) if item.get("status") == "in_progress"), None)
            if not panel:
                raise StateError("no active review panel")
        existing = panel.setdefault("roles", [])
        already = [role for role in roles if role in existing]
        if already:
            # Silence would let a retry look like a successful extension while the member
            # it named was never added: the same failure shape AC-09 closes one command up.
            raise StateError(f"already on panel {panel['panel_id']}: {', '.join(already)}")
        existing.extend(roles)
        panel.setdefault("extensions", []).append(
            {"roles": roles, "reason": args.reason.strip(), "at": now()}
        )
        record_event(
            data, "extend-review-panel", "PACKAGE_REVIEW", "PACKAGE_REVIEW", args.actor, args.package_id,
            {"panel_id": panel["panel_id"], "added_roles": roles}, args.event_id,
        )
        return True

    data, changed = mutate(path, args, "extend-review-panel", update)
    return output_state(data, changed, path)


def cmd_record_late_review(args: argparse.Namespace) -> int:
    """An independent review that returned after its panel closed (AC-10).

    Phase-agnostic on purpose: `cmd_record_review` and `cmd_record_subreview` both
    hard-gate on `PACKAGE_REVIEW` and `LEGAL_TRANSITIONS["PACKAGE_REPAIR"]` has no edge
    back, so a reviewer that returns late has no door at all — five verified architect
    findings ended up in `decisions-log.jsonl`, where a reader looking at the package will
    never find them.  It consumes NO deep-review cycle: the concurrent panel is one cycle
    by rule, and counting a straggler as a second one would misrepresent the process in
    the opposite direction.  What makes it safe without a new phase is that its findings
    land on `package["findings"]`, which `package_accept_ready` already reads through
    `has_open_findings` — a blocking late finding stops acceptance with no new machinery.
    """
    path = state_file_arg(args)
    role = (args.role or "").strip()
    if not role:
        raise StateError("record-late-review requires a non-empty role")
    evidence = (args.evidence or "").strip()
    if len(evidence) < MIN_EVIDENCE_LEN:
        # This is the one record in the harness that no panel witnessed and no phase gate
        # guarded, so its evidence IS the audit trail — required here even though
        # `record-subreview --evidence` defaults to empty.  The EVIDENCE_SHAPES burden
        # stays where it belongs: on the verb that RETIRES findings, not the one that
        # files them.
        raise StateError(
            f"record-late-review requires --evidence of at least {MIN_EVIDENCE_LEN} characters: "
            "nothing else witnessed this review"
        )

    def update(data: dict[str, Any]) -> bool:
        if replayed(data, "record-late-review", args.event_id):
            return False
        package = package_by_id(data, args.package_id)
        if package.get("status") == "accepted":
            # `package_accept_ready` has already run, so a finding recorded here would be
            # read by nobody, ever: PACKAGE_ACCEPTED has no edge to PACKAGE_REPAIR and
            # `reopen` only applies from BLOCKED.  Recording it anyway would produce a
            # package showing an open blocking finding and an `accepted` status at the
            # same time, which is a worse lie than the refusal.  The gap is registered as
            # debt rather than simulated closed.
            raise StateError(
                f"{package['package_id']} is already accepted and has no path back to repair "
                "(PACKAGE_ACCEPTED has no edge to PACKAGE_REPAIR, and reopen only applies from "
                "BLOCKED); raise this against the integration or block the feature"
            )
        open_panel = next((item for item in package.get("review_panels", [])
                           if item.get("status") == "in_progress"), None)
        if open_panel:
            # While a panel is live the sanctioned channel is the panel; without this the
            # late verb is simply a way around its membership gate.  Checked before the
            # "no closed review" guard below because both fire on an open first panel and
            # this is the one that names what to do instead.
            raise StateError(
                f"panel {open_panel.get('panel_id')} is still open; use record-subreview, or "
                "extend-review-panel first if this role is not yet a member"
            )
        if not package.get("reviews"):
            # Otherwise this is a back door that files findings on a package that never
            # passed package_review_ready and never entered PACKAGE_REVIEW at all.
            raise StateError(
                f"{package['package_id']} has no closed review to be late to"
            )
        if args.panel_id and not any(item.get("panel_id") == args.panel_id
                                     for item in package.get("review_panels", [])):
            raise StateError(f"unknown panel_id: {args.panel_id}")
        findings = normalize_findings(args.finding or [])
        for finding in findings:
            # The same attribution record-subreview stamps.  Without it,
            # cmd_record_verification has nothing to compare and a late reviewer can file
            # a finding and then refute its own.
            finding.setdefault("source_role", role)
        package.setdefault("late_reviews", []).append({
            "role": role,
            "findings": [item["id"] for item in findings],
            "panel_id": args.panel_id,
            "evidence": evidence,
            "at": now(),
        })
        for finding in findings:
            # merge_finding, never a blind append: re-raising a finding the verifier
            # refuted is legitimate here — half the point of a late reviewer — and merging
            # archives the stale verdict so the finding re-enters unjudged.
            merge_finding(package, finding)
        # from == to on purpose: this moves no phase, and saying so keeps the event out of
        # every reader that looks for an entry INTO a phase.
        record_event(
            data, "record-late-review", data["phase"], data["phase"], args.actor, args.package_id,
            {"role": role, "finding_count": len(findings)}, args.event_id,
        )
        return True

    data, changed = mutate(path, args, "record-late-review", update)
    return output_state(data, changed, path)


def _apply_verification_waiver(data: dict[str, Any], package: dict[str, Any], attempts: dict[str, Any],
                                verdicts: list[dict[str, Any]], budget: int, args: argparse.Namespace) -> bool:
    """The `--skip-reason` branch of `record-verification`: waive instead of verdicting."""
    if verdicts:
        raise StateError("--skip-reason cannot be combined with --verdict")
    # Waivers keep their own counter so the cheap path stays reachable once the
    # verification budget is spent — but they are still a loop, and this harness
    # caps every loop.  Same ceiling, separate dimension, no second key to drift.
    if attempts.get("verification_waivers", 0) >= budget:
        return block_with_reason(data, args.actor, args.package_id,
                                 f"verification waiver budget exhausted for {args.package_id}")
    # Physical waiver, not a prose one: skipping verification is legal only
    # when nothing above `low` is open, where the spawn costs more than the
    # repairs it would prevent.
    if has_open_findings(package, {"critical", "high", "medium"}):
        raise StateError("--skip-reason requires all open findings to be low severity")
    if len(args.skip_reason) > MAX_VERDICT_FIELD or len(args.evidence or "") > MAX_VERDICT_FIELD:
        raise StateError(f"waiver fields exceed {MAX_VERDICT_FIELD} chars")
    record = {"skipped": True, "reason": args.skip_reason, "at": now(), "evidence": args.evidence}
    package.setdefault("verifications", []).append(record)
    # Its own counter, not the budgeted one: a waiver is the declaration that no
    # pass was needed, so it must be VISIBLE without consuming the runaway
    # backstop — otherwise the cheap path becomes unreachable at the ceiling.
    attempts["verification_waivers"] = attempts.get("verification_waivers", 0) + 1
    data["metrics"]["verifications"] = data["metrics"].get("verifications", 0) + 1
    record_event(data, "record-verification", "PACKAGE_REPAIR", data["phase"], args.actor,
                 args.package_id, {"skipped": True, "reason": args.skip_reason}, args.event_id)
    return True


def _apply_verdicts(data: dict[str, Any], package: dict[str, Any], attempts: dict[str, Any],
                     verdicts: list[dict[str, Any]], budget: int, args: argparse.Namespace) -> bool:
    """The `--verdict` branch of `record-verification`: refute/uphold each finding."""
    if not verdicts:
        raise StateError("record-verification requires --verdict or --skip-reason")

    # Checked after the waiver branch on purpose: the two counters are separate
    # dimensions, so spending the verification budget never makes the cheap path
    # unreachable.
    if attempts.get("verifications", 0) >= budget:
        return block_with_reason(data, args.actor, args.package_id,
                                 f"verification budget exhausted for {args.package_id}")

    if any(item["verdict"] == "refuted" for item in verdicts) and args.actor not in REFUTING_ACTORS:
        # Retiring a blocking finding with no code change is the verifier's verb
        # alone.  Without this the implementer can clear the findings against its
        # own diff and the package accepts with no repair and no delta review.
        raise StateError(f"{args.actor} cannot refute findings; only {'/'.join(sorted(REFUTING_ACTORS))} may")

    refuted, upheld = [], []
    for verdict in verdicts:
        finding = next((item for item in package.get("findings", []) if item.get("id") == verdict["id"]), None)
        if not finding:
            raise StateError(f"unknown finding: {verdict['id']}")
        if finding.get("status", "open") in TERMINAL_FINDING_STATUSES:
            raise StateError(f"finding is not open: {verdict['id']} ({finding.get('status')})")
        if finding.get("verified_verdict") == "upheld":
            # `upheld` is terminal for verification even though the finding stays
            # open for repair.  Otherwise re-verifying is a retry-until-you-win loop
            # in a harness that caps every other loop.
            raise StateError(f"finding was already upheld and cannot be re-verified: {verdict['id']}")
        if verdict["verdict"] == "refuted" and finding.get("source_role") == args.actor:
            raise StateError(f"{args.actor} raised {verdict['id']} and cannot refute it")
        finding["verified_by"] = args.actor
        finding["verified_at"] = now()
        finding["verified_verdict"] = verdict["verdict"]
        if verdict["verdict"] == "refuted":
            # The finding is never deleted: it keeps its verdict and evidence so the
            # package record shows what was killed and on what grounds.
            finding["status"] = "refuted"
            finding["verdict_reason"] = verdict["reason"]
            finding["verdict_evidence"] = verdict["evidence"]
            refuted.append(finding["id"])
        else:
            upheld.append(finding["id"])

    package.setdefault("verifications", []).append({
        "refuted": refuted, "upheld": upheld, "at": now(), "evidence": args.evidence,
    })
    attempts["verifications"] = attempts.get("verifications", 0) + 1
    data["metrics"]["verifications"] = data["metrics"].get("verifications", 0) + 1

    if not has_open_findings(package) and _repair_entered_from_review(data, args.package_id):
        # Every finding was refuted: there is nothing left to repair, so the repair
        # pass and its delta review are skipped entirely.  That is the whole point.
        # Gated on WHY the package is in PACKAGE_REPAIR: a red test or a failed
        # runtime QA put it here for a reason the finding set knows nothing about.
        data["phase"] = "PACKAGE_TESTING"
        package["status"] = "testing_required"
    record_event(data, "record-verification", "PACKAGE_REPAIR", data["phase"], args.actor, args.package_id,
                 {"refuted": len(refuted), "upheld": len(upheld)}, args.event_id)
    return True


def cmd_record_verification(args: argparse.Namespace) -> int:
    """Adversarial refutation pass between the review panel and repair.

    This is NOT a review cycle: it never touches `deep_review_cycles`.  It is an
    edge inside the cycle the panel already counted.  Dispatches to
    `_apply_verification_waiver` (`--skip-reason`) or `_apply_verdicts` (`--verdict`)
    after the guards shared by both branches.
    """
    path = state_file_arg(args)

    if not args.actor:
        raise StateError("record-verification requires an explicit --actor")

    def update(data: dict[str, Any]) -> bool:
        if replayed(data, "record-verification", args.event_id):
            # Replay of a timed-out call is a no-op, like start-review-panel and
            # record-subreview.  Without this the per-finding guards below fire first and
            # a retry cannot tell "already applied" from "state corrupt".
            return False
        if data["phase"] != "PACKAGE_REPAIR":
            raise StateError(f"cannot record verification from phase {data['phase']}")
        package = package_by_id(data, args.package_id)
        attempts = package.setdefault("attempts", {})
        verdicts = normalize_verdicts(args.verdict or [])
        budget = data.get("budgets", {}).get("max_verifications_per_package", DEFAULT_MAX_VERIFICATIONS)

        if args.skip_reason:
            return _apply_verification_waiver(data, package, attempts, verdicts, budget, args)
        return _apply_verdicts(data, package, attempts, verdicts, budget, args)

    data, changed = mutate(path, args, "record-verification", update)
    return output_state(data, changed, path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("feature_id")
    init.add_argument("spec_path")
    init.add_argument("spec_hash")
    init.add_argument("--state-file")
    init.add_argument("--force", action="store_true")
    # Required, like `reopen --authorized-by`: an assertion that defaults to a value
    # nobody chose is exactly the assertion this command used to make for free.
    init.add_argument("--approved-by", required=True)
    init.add_argument("--actor", default="orchestrator")
    init.add_argument("--ac", action="append")
    init.add_argument("--max-deep-review-cycles", type=int)
    init.add_argument("--max-repairs-per-finding", type=int)
    init.add_argument("--max-package-subdivisions", type=int)
    init.add_argument("--max-spawns-per-package", type=int)
    # A feature that reaches init already carries a risk signal (quick-fixes
    # close via log-quickfix, no state file), so scoped budgets are the floor;
    # full feature/SDD budgets stay opt-in via explicit --mode feature.
    init.add_argument("--mode", choices=sorted(MODE_BUDGETS), default="scoped")
    init.set_defaults(func=cmd_init)

    for name, func in (("status", cmd_status), ("next", cmd_next), ("resume", cmd_resume), ("validate", cmd_validate)):
        item = sub.add_parser(name)
        item.add_argument("feature_id", nargs="?")
        item.add_argument("--state-file")
        item.set_defaults(func=func)

    transition = sub.add_parser("transition")
    add_common_state_args(transition)
    transition.add_argument("to_phase")
    transition.add_argument("--feature-id")
    transition.add_argument("--package-id")
    transition.add_argument("--reason", default="")
    transition.set_defaults(func=cmd_transition)

    create = sub.add_parser("create-package")
    add_common_state_args(create)
    create.add_argument("package_id")
    create.add_argument("objective")
    create.add_argument("--feature-id")
    create.add_argument("--ac", action="append")
    create.add_argument("--task", action="append")
    create.add_argument("--depends-on", action="append")
    create.add_argument("--owned-path", action="append")
    create.add_argument("--read-only-path", action="append")
    create.add_argument("--shared-path", action="append")
    create.add_argument("--risk", action="append")
    create.add_argument("--complexity", choices=["small", "medium", "high"])
    create.add_argument("--selected-role")
    create.add_argument("--selected-model")
    create.add_argument("--routing-reason")
    create.add_argument("--context-pack")
    create.add_argument("--runtime-surface")
    create.set_defaults(func=cmd_create_package)

    update = sub.add_parser("update-package")
    add_common_state_args(update)
    update.add_argument("package_id")
    update.add_argument("--feature-id")
    update.add_argument("--integrated")
    update.add_argument("--runtime-surface")
    update.add_argument("--diff-ref")
    update.add_argument("--complexity", choices=["small", "medium", "high"])
    update.add_argument("--selected-role")
    update.add_argument("--selected-model")
    update.add_argument("--routing-reason")
    update.add_argument("--context-pack")
    update.add_argument("--exception", action="append")
    update.set_defaults(func=cmd_update_package)

    for name, func in (("start-task", cmd_start_task), ("complete-task", cmd_complete_task), ("fail-task", cmd_fail_task)):
        item = sub.add_parser(name)
        add_common_state_args(item)
        item.add_argument("package_id")
        item.add_argument("task_id")
        item.add_argument("--feature-id")
        if name == "complete-task":
            item.add_argument("--validation", action="append")
        if name == "fail-task":
            item.add_argument("--reason", required=True)
        item.set_defaults(func=func)

    gate = sub.add_parser("record-gate")
    add_common_state_args(gate)
    gate.add_argument("name")
    gate.add_argument("status", choices=["pass", "fail", "blocked"])
    gate.add_argument("--feature-id")
    gate.add_argument("--package-id")
    gate.add_argument("--global-gate", action="store_true")
    gate.add_argument("--optional", action="store_true")
    gate.add_argument("--evidence", default="")
    gate.set_defaults(func=cmd_record_gate)

    spawn = sub.add_parser("record-spawn")
    add_common_state_args(spawn)
    spawn.add_argument("package_id")
    spawn.add_argument("role")
    spawn.add_argument("--feature-id")
    spawn.add_argument("--purpose", default="")
    spawn.add_argument("--client", default="")
    spawn.add_argument("--tech", default="")
    spawn.set_defaults(func=cmd_record_spawn)

    review = sub.add_parser("record-review")
    add_common_state_args(review)
    review.add_argument("package_id")
    review.add_argument("verdict", choices=["pass", "repair_required", "blocked"])
    review.add_argument("--feature-id")
    review.add_argument("--finding", action="append")
    review.add_argument("--evidence", default="")
    review.set_defaults(func=cmd_record_review)

    panel = sub.add_parser("start-review-panel")
    add_common_state_args(panel)
    panel.add_argument("package_id")
    panel.add_argument("--feature-id")
    panel.add_argument("--panel-id")
    panel.add_argument("--role", action="append")
    panel.set_defaults(func=cmd_start_review_panel)

    subreview = sub.add_parser("record-subreview")
    add_common_state_args(subreview)
    subreview.add_argument("package_id")
    subreview.add_argument("role")
    subreview.add_argument("verdict", choices=["pass", "repair_required", "blocked"])
    subreview.add_argument("--feature-id")
    subreview.add_argument("--finding", action="append")
    subreview.add_argument("--evidence", default="")
    subreview.set_defaults(func=cmd_record_subreview)

    finalize = sub.add_parser("finalize-review-panel")
    add_common_state_args(finalize)
    finalize.add_argument("package_id")
    finalize.add_argument("verdict", choices=["pass", "repair_required", "blocked"])
    finalize.add_argument("--feature-id")
    finalize.add_argument("--allow-missing", action="store_true")
    finalize.add_argument("--evidence", default="")
    finalize.set_defaults(func=cmd_finalize_review_panel)

    extend = sub.add_parser("extend-review-panel")
    add_common_state_args(extend)
    extend.add_argument("package_id")
    extend.add_argument("--feature-id")
    extend.add_argument("--panel-id")
    extend.add_argument("--role", action="append")
    extend.add_argument("--reason")
    extend.set_defaults(func=cmd_extend_review_panel)

    late = sub.add_parser("record-late-review")
    add_common_state_args(late)
    late.add_argument("package_id")
    late.add_argument("role")
    late.add_argument("--feature-id")
    late.add_argument("--panel-id")
    late.add_argument("--finding", action="append")
    # No `verdict` positional, unlike every other review verb: a verdict in this CLI is a
    # token that drives a phase, and this command drives none.  Offering `blocked` without
    # blocking would be a lie, and `pass` would invite the readers of `reviews[-1]` to
    # trust a record that is deliberately not one of them.
    late.add_argument("--evidence", default="")
    late.set_defaults(func=cmd_record_late_review)

    verification = sub.add_parser("record-verification")
    add_common_state_args(verification)
    verification.add_argument("package_id")
    verification.add_argument("--feature-id")
    verification.add_argument("--verdict", action="append")
    verification.add_argument("--skip-reason", default="")
    verification.add_argument("--evidence", default="")
    # `verified_by` IS the independence attribution; silently recording the coordinator's
    # default would erase the one thing the field exists for.  Drop the inherited default
    # so the command can demand an explicit actor.
    verification.set_defaults(func=cmd_record_verification, actor=None)

    repair = sub.add_parser("record-repair")
    add_common_state_args(repair)
    repair.add_argument("package_id")
    repair.add_argument("--feature-id")
    repair.add_argument("--finding-id", action="append")
    repair.add_argument("--changed-file", action="append")
    repair.add_argument("--verification", action="append")
    repair.add_argument("--skip-delta", action="store_true")
    repair.add_argument("--commit", help="AC-21: sha of the commit that repaired this finding (7-40 hex)")
    repair.set_defaults(func=cmd_record_repair)

    delta = sub.add_parser("record-delta-review")
    add_common_state_args(delta)
    delta.add_argument("package_id")
    delta.add_argument("verdict", choices=["pass", "repair_required", "blocked"])
    delta.add_argument("--feature-id")
    delta.add_argument("--closed-finding", action="append")
    delta.add_argument("--new-finding", action="append")
    delta.add_argument("--requires-full-review", action="store_true")
    delta.add_argument("--reason", default="")
    delta.set_defaults(func=cmd_record_delta_review)

    testing = sub.add_parser("record-testing")
    add_common_state_args(testing)
    testing.add_argument("package_id")
    testing.add_argument("status", choices=["pass", "fail", "blocked"])
    testing.add_argument("--feature-id")
    testing.add_argument("--command", action="append")
    testing.add_argument("--evidence", default="")
    testing.set_defaults(func=cmd_record_testing)

    runtime = sub.add_parser("record-runtime-qa")
    add_common_state_args(runtime)
    runtime.add_argument("package_id")
    runtime.add_argument("status", choices=["pass", "fail", "blocked"])
    runtime.add_argument("--feature-id")
    runtime.add_argument("--url", default="")
    runtime.add_argument("--browser", default="")
    runtime.add_argument("--screenshot", action="append")
    runtime.add_argument("--check", action="append")
    runtime.add_argument("--evidence", default="")
    runtime.set_defaults(func=cmd_record_runtime_qa)

    accept = sub.add_parser("accept-package")
    add_common_state_args(accept)
    accept.add_argument("package_id")
    accept.add_argument("--feature-id")
    accept.set_defaults(func=cmd_accept_package)

    block = sub.add_parser("block")
    add_common_state_args(block)
    block.add_argument("reason")
    block.add_argument("--feature-id")
    block.add_argument("--package-id")
    block.set_defaults(func=cmd_block)

    reopen = sub.add_parser("reopen")
    add_common_state_args(reopen)
    reopen.add_argument("--feature-id")
    reopen.add_argument("--package-id")
    reopen.add_argument("--reason", required=True)
    reopen.add_argument("--authorized-by", required=True)
    reopen.set_defaults(func=cmd_reopen)

    render = sub.add_parser("render-status")
    render.add_argument("--state-dir")
    render.set_defaults(func=cmd_render_status)

    quickfix = sub.add_parser("log-quickfix")
    quickfix.add_argument("--summary", required=True)
    quickfix.add_argument("--result", required=True, choices=["done", "reverted", "blocked"])
    quickfix.add_argument("--file", action="append")
    quickfix.add_argument("--gate")
    quickfix.add_argument("--actor", default="orchestrator")
    quickfix.add_argument("--log-file")
    quickfix.set_defaults(func=cmd_log_quickfix)

    narrative = sub.add_parser("log-narrative")
    narrative.add_argument("--client", required=True)
    narrative.add_argument("--tech", required=True)
    narrative.add_argument("--result", default="done", choices=["started", "done", "blocked"])
    narrative.add_argument("--role")
    narrative.add_argument("--package-id")
    narrative.add_argument("--feature-id")
    narrative.add_argument("--actor", default="orchestrator")
    narrative.add_argument("--log-file")
    narrative.set_defaults(func=cmd_log_narrative)

    decision = sub.add_parser("log-decision")
    decision.add_argument("--title", required=True)
    decision.add_argument("--context", required=True)
    decision.add_argument("--decision", required=True)
    decision.add_argument("--consequences")
    decision.add_argument("--feature-id")
    decision.add_argument("--package-id")
    decision.add_argument("--slug")
    decision.add_argument("--actor", default="orchestrator")
    decision.add_argument("--log-file")
    decision.set_defaults(func=cmd_log_decision)

    notes = sub.add_parser("sync-notes")
    notes.add_argument("--state-dir")
    notes.add_argument("--notes-dir")
    notes.add_argument("--project-name")
    notes.set_defaults(func=cmd_sync_notes)

    dry = sub.add_parser("dry-run")
    dry.add_argument("feature_id")
    dry.set_defaults(func=cmd_dry_run)

    graph = sub.add_parser("graph")
    graph.add_argument("--feature-id", action="append")
    graph.add_argument("--root")
    graph.add_argument("--out")
    graph.set_defaults(func=cmd_graph)

    # Available on every subcommand: defer STATUS/bitacora/notes regeneration
    # for high-frequency intra-phase writes; sync-notes always renders anyway.
    for item in sub.choices.values():
        item.add_argument("--no-render", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    global RENDER_SKIP
    RENDER_SKIP = bool(getattr(args, "no_render", False))
    try:
        return args.func(args)
    except (OSError, json.JSONDecodeError, StateError) as exc:
        print_json({"ok": False, "error": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
