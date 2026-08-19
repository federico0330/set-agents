"""Extracted from ai/scripts/feature-state.py by a behavior-preserving refactor
(mechanical reorganization only -- no logic changes). See feature-state.py's own
module docstring and the package-level notes for the split rationale.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from feature_state_lib.model import now, package_by_id, TERMINAL_FINDING_STATUSES, spawn_budget_counts, spawn_budget_warns, spawn_budget_label
from feature_state_lib.render_status import status_root, describe_next_step


# ------------------------------------------------------------ living notes ---
# Obsidian-friendly living docs under docs/notas/: a project hub, one note per
# feature, one per package, and one per logged decision, all wired with
# [[wikilinks]]. Same contract as STATUS.md/bitacora: fully regenerated from
# state on every mutation, atomic writes, never raises. Opt-in by directory:
# a repo without docs/notas/ never gets notes written.

NOTES_AUTO_BEGIN = "<!-- notas:auto -->"
NOTES_AUTO_END = "<!-- /notas:auto -->"
DECISIONS_LOG = "decisions-log.jsonl"


def slugify(text: str) -> str:
    slug = "".join(ch if ch.isalnum() else "-" for ch in text.lower())
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "decision"


def notes_root(state_file: Path, notes_dir: str | None = None) -> Path | None:
    """Notes are mandatory for any harness-managed project (ADR-0012/AC-13): the marker is
    `ai/state/` existing, never an arbitrary or third-party directory someone merely changed
    into, and never "does docs/notas already exist" (that opt-in-by-directory rule is what let
    a project silently go without notes forever). `write_note` creates the directory tree.
    """
    if notes_dir:
        return Path(notes_dir)
    _, out_dir = status_root(state_file)
    if not (out_dir.is_dir() and out_dir.name == "state" and out_dir.parent.name == "ai"):
        return None
    return out_dir.parent.parent / "docs" / "notas"


def merge_note(existing: str | None, title: str, body: str) -> str:
    """Regenerate only the machine-owned block; everything else is the human's."""
    # Defense in depth behind `_short`: the split below uses maxsplit=1, so a body
    # carrying either marker would silently redefine the block boundary.
    body = body.replace(NOTES_AUTO_END, "--›").replace(NOTES_AUTO_BEGIN, "‹!--")
    generated = f"{NOTES_AUTO_BEGIN}\n{body.rstrip()}\n{NOTES_AUTO_END}"
    if existing and NOTES_AUTO_BEGIN in existing and NOTES_AUTO_END in existing:
        prefix, rest = existing.split(NOTES_AUTO_BEGIN, 1)
        _, suffix = rest.split(NOTES_AUTO_END, 1)
        return prefix + generated + suffix
    return (
        f"# {title}\n\n{generated}\n\n"
        "## Notas propias\n\n_Lo que escribas fuera del bloque auto se preserva en cada regeneración._\n"
    )


def write_note(path: Path, title: str, body: str) -> bool:
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    payload = merge_note(existing, title, body)
    if existing == payload:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=str(path.parent), delete=False, encoding="utf-8") as handle:
        handle.write(payload)
        tmp_name = handle.name
    os.replace(tmp_name, path)
    return True


def _short(text: Any, limit: int | None = 120) -> str:
    """`limit=None` means "render the full text, never a mid-sentence cut" — AC-13
    (028/N3a): the digest's three truncation points (blockers, closes, decisions) must
    stop emitting a trailing `…` that eats the "why" (D-4d: a `why` is conventionally
    written last, so a head-truncation keeps the "what" and throws away exactly the part
    this whole feature exists to surface). Every OTHER caller keeps its numeric limit
    unchanged — this is additive, not a relaxation of the existing truncation contract.
    """
    text = " ".join(str(text or "").split())
    # `merge_note` splits on the FIRST NOTES_AUTO_END, so a generated body able to emit
    # that terminator moves the machine/human boundary permanently: the text below it is
    # promoted into the human-owned region and re-promoted on every regeneration.  Every
    # agent-authored field rendered from state passes through here — neutralize once.
    text = text.replace("<!--", "‹!--").replace("-->", "--›")
    if limit is None or len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _decision_name(entry: dict[str, Any]) -> str:
    return f"{entry.get('at', '')[:10]} {entry.get('slug', 'decision')}".strip()


def _unique_decisions(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keyed: dict[str, dict[str, Any]] = {}
    for entry in entries:
        keyed[_decision_name(entry)] = entry  # last write wins per (date, slug)
    return list(keyed.values())


def _dicts(seq: Any) -> list[dict[str, Any]]:
    return [item for item in (seq or []) if isinstance(item, dict)]


def _snake_key(key: str) -> str:
    if not key.isidentifier() or key[0].isupper() or not any(ch.isupper() for ch in key):
        return key
    return "".join(f"_{ch.lower()}" if ch.isupper() else ch for ch in key)


def _normalize_note_state(node: Any) -> Any:
    """Best-effort camelCase→snake_case for legacy state files. Rendering only —
    the state on disk is never written back through this."""
    if isinstance(node, dict):
        return {(_snake_key(key) if isinstance(key, str) else key): _normalize_note_state(value)
                for key, value in node.items()}
    if isinstance(node, list):
        return [_normalize_note_state(item) for item in node]
    return node


def _note_packages(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize packages for the notes renderer: legacy states keyed them by id
    (dict) or named fields in camelCase (id/ownershipPaths)."""
    packages = data.get("packages", [])
    if isinstance(packages, dict):
        packages = [
            {**value, "package_id": value.get("package_id", key)} if isinstance(value, dict) else {"package_id": key}
            for key, value in packages.items()
        ]
    normalized = []
    for package in packages:
        if not isinstance(package, dict):
            continue
        if "package_id" not in package and package.get("id"):
            package = {**package, "package_id": package["id"]}
        if "owned_paths" not in package and package.get("ownership_paths"):
            package = {**package, "owned_paths": package["ownership_paths"]}
        normalized.append(package)
    return normalized


def _pending_bits(data: dict[str, Any]) -> list[str]:
    bits = []
    try:
        # AC-12 (028/N3a): never the raw `next` phase name nor the raw `reason` string
        # (D-4b: `reason` can carry literal flags, e.g. "record-module-impact",
        # "--module-impact-waived"). `describe_next_step` re-derives the same state in
        # Spanish prose and is the SAME function STATUS.md's "Próximo paso" column uses
        # (AC-11 x AC-12's own conflict resolution: one function, two surfaces).
        # mark_stale=False: this digest surface already marks staleness once, in "Qué
        # se está haciendo" -- see `describe_next_step`'s own docstring.
        step_text = describe_next_step(data, mark_stale=False)
    except Exception:  # legacy states may predate the transition schema
        step_text = None
    if step_text and step_text != "—":
        bits.append(f"→ {step_text}")
    for blocker in data.get("blockers", []):
        if isinstance(blocker, dict):
            if not blocker.get("resolved_at"):
                bits.append(f"⛔ bloqueo: {_short(blocker.get('reason', ''))}")
        elif blocker:
            bits.append(f"⛔ bloqueo: {_short(blocker)}")
    open_findings = sum(
        1
        for package in _note_packages(data)
        for finding in package.get("findings", [])
        if finding.get("status", "open") not in TERMINAL_FINDING_STATUSES
    )
    if open_findings:
        bits.append(f"{open_findings} hallazgos abiertos")
    try:
        package = package_by_id(data)
    except Exception:
        package = None
    if package:
        pending = [t.get("id", "?") for t in package.get("tasks", []) if t.get("status") != "completed"]
        if pending:
            # AC-12 (028/N3a, D-4c): `task["id"]` has held free-form English task titles
            # in real history (`render_notes.py`, pre-fix), not short codes — dumping them
            # raw here is exactly the "IDs de tarea en inglés" the digest must stop
            # publishing. The count plus the package id (evidence, AC-04b's carve-out in
            # the sibling narration-guard spec) says what's needed without the English
            # blob; the full list still lives in the package note itself (`_package_body`).
            n = len(pending)
            noun = "tarea" if n == 1 else "tareas"
            bits.append(f"{n} {noun} pendientes en {package.get('package_id')}")
    used, ceiling = spawn_budget_counts(data, package)
    if spawn_budget_warns(used, ceiling):
        bits.append(f"WARN spawns {spawn_budget_label(used, ceiling)}")
    return bits



def _package_body(fid: str, package: dict[str, Any]) -> str:
    lines = ["## Motivo", "", f"- objetivo: {package.get('objective', '-')}"]
    if package.get("routing_reason"):
        lines.append(f"- ruteo: {_short(package['routing_reason'])} → {package.get('selected_role', '?')} ({package.get('selected_model', '?')})")
    if package.get("complexity"):
        lines.append(f"- complejidad: {package['complexity']}")
    for risk in package.get("risks", []):
        lines.append(f"- riesgo: {_short(risk)}")
    if package.get("owned_paths"):
        lines.append("- paths: `" + "`, `".join(package["owned_paths"]) + "`")
    if package.get("dependencies"):
        lines.append(f"- depende de: {', '.join(package['dependencies'])}")
    tasks = package.get("tasks", [])
    if tasks:
        lines += ["", "## Tareas", ""]
        for task in tasks:
            if not isinstance(task, dict):  # legacy states listed tasks as plain strings
                task = {"id": task, "status": "planned"}
            mark = "x" if task.get("status") == "completed" else " "
            extra = f" · {', '.join(task.get('local_validations', []))}" if task.get("local_validations") else ""
            lines.append(f"- [{mark}] {task.get('id')} ({task.get('status')}){extra}")
    findings = [f for f in package.get("findings", []) if isinstance(f, dict)]
    if findings:
        lines += ["", "## Hallazgos", ""]
        for finding in findings:
            label = _short(finding.get("category") or finding.get("summary") or "")
            line = f"- {finding.get('id')} [{finding.get('severity')}] {finding.get('status', 'open')}"
            if label:
                line += f" — {label}"
            if finding.get("status") == "refuted":
                # The grounds AND the proof belong in the record, not in a chat log: a
                # reason without its evidence is the claim without the burden.
                line += (
                    f" · refutado por {finding.get('verified_by', '?')}:"
                    f" {_short(finding.get('verdict_reason', ''))}"
                    f" [{_short(finding.get('verdict_evidence', ''), 80)}]"
                )
            lines.append(line)
    trail = []
    for review in _dicts(package.get("reviews")):
        trail.append(f"- review: {review.get('verdict')} ({len(review.get('findings', []))} hallazgos)")
    for late in _dicts(package.get("late_reviews")):
        # Listed as its own kind, not folded into `review`: the note is where a human
        # looks to see that a finding arrived after the panel had already closed.
        trail.append(
            f"- review tardía ({late.get('role', '?')}): {len(late.get('findings', []))} hallazgos"
        )
    for verification in _dicts(package.get("verifications")):
        if verification.get("skipped"):
            trail.append(f"- verificación: salteada ({_short(verification.get('reason', ''))})")
        else:
            trail.append(
                f"- verificación: {len(verification.get('refuted', []))} refutados, "
                f"{len(verification.get('upheld', []))} sostenidos"
            )
    for repair in _dicts(package.get("repairs")):
        trail.append(f"- repair: {', '.join(repair.get('finding_ids', []))} → {len(repair.get('changed_files', []))} archivos")
    for delta in _dicts(package.get("delta_reviews")):
        trail.append(f"- delta review: {delta.get('verdict')}")
    for testing in _dicts(package.get("testing")):
        trail.append(f"- testing: {testing.get('status')}")
    for qa in _dicts(package.get("runtime_qa")):
        trail.append(f"- runtime QA: {qa.get('status')}{' (waived)' if qa.get('waived') else ''}")
    for gate in _dicts(package.get("gates")):
        trail.append(f"- gate `{gate.get('name')}`: {gate.get('status')}")
    if trail:
        lines += ["", "## Recorrido", ""] + trail
    # ADR-0031: only spawns that carry a structured routing decision are listed —
    # packages written before the fields existed render byte-identical.
    routed = [
        s for s in package.get("spawns", []) or []
        if isinstance(s, dict) and any(s.get(k) for k in ("model", "provider", "effort", "route_id"))
    ]
    if routed:
        lines += ["", "## Spawns", ""]
        for spawn in routed:
            bits = [f"- {spawn.get('spawn_id', '?')} {_short(spawn.get('role', '?'), 40)}"]
            if spawn.get("model"):
                model_txt = f"{spawn['provider']}/{spawn['model']}" if spawn.get("provider") else spawn["model"]
                bits.append("modelo " + _short(model_txt, 80))
            if spawn.get("effort"):
                bits.append("effort " + _short(spawn["effort"], 20))
            if spawn.get("route_id"):
                bits.append("route " + _short(spawn["route_id"], 60))
            lines.append(" · ".join(bits))
    if package.get("context_pack"):
        lines += ["", f"context pack: `{package['context_pack']}`"]
    lines += ["", f"↩ [[features/{fid}|{fid}]]"]
    return "\n".join(lines)


def _decision_body(entry: dict[str, Any]) -> str:
    lines = [f"- fecha: {entry.get('at', '')[:10]} · actor: {entry.get('actor', '-')}"]
    links = []
    if entry.get("feature_id"):
        links.append(f"[[features/{entry['feature_id']}|{entry['feature_id']}]]")
        if entry.get("package_id"):
            links.append(f"[[features/{entry['feature_id']}/{entry['package_id']}|{entry['package_id']}]]")
    if links:
        lines.append("- alcance: " + " · ".join(links))
    lines += ["", "## Contexto", "", entry.get("context", "-"), "", "## Decisión", "", entry.get("decision", "-")]
    if entry.get("consequences"):
        lines += ["", "## Consecuencias", "", entry["consequences"]]
    return "\n".join(lines)


RENDER_FAILURE_LOG = "render-failures.log"
RENDER_FAILURE_LOG_CAP = 200_000  # bytes; single-generation rotation past this


def _log_render_failure(out_dir: Path, context: str, exc: BaseException) -> None:
    """Best-effort, PER-PROJECT (out_dir is this project's own ai/state/, per AC-20's
    cross-project isolation requirement — a render failure in project Y's ai/state/ can never
    land in project X's log because each project's out_dir is its own directory). Never raises:
    a broken logger must not break render_notes's own never-raises invariant.
    """
    try:
        path = out_dir / RENDER_FAILURE_LOG
        if path.exists() and path.stat().st_size > RENDER_FAILURE_LOG_CAP:
            path.replace(path.with_name(path.name + ".1"))
        # SEC-004: `context` carries a caller-supplied `feature_id` and `str(exc)` can
        # carry arbitrary exception text (which, in turn, can embed a caller-supplied
        # value) -- neither is bounded or newline-safe. `_short()` collapses whitespace
        # (so a `\n` inside either can never forge a second, fake log entry with its own
        # timestamp) and truncates, exactly like every other agent-authored field that
        # lands in a generated file elsewhere in this module.
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"{now()} {_short(context)}: {type(exc).__name__}: {_short(str(exc))}\n")
    except OSError:
        pass
