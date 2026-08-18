"""Extracted from ai/scripts/feature-state.py by a behavior-preserving refactor
(mechanical reorganization only -- no logic changes). See feature-state.py's own
module docstring and the package-level notes for the split rationale.
"""

from __future__ import annotations

import contextlib
import os
import tempfile
from pathlib import Path
from typing import Any

from feature_state_lib import model
from feature_state_lib.model import StateError, now, load_state, package_by_id, TERMINAL_FINDING_STATUSES
from feature_state_lib.transitions import next_transition
from feature_state_lib.render_bitacora import read_jsonl, collect_narrative, format_narrative


# --------------------------------------------------------- human-readable next step ---
# 028/N3a, AC-11 x AC-12 (spec's own conflict resolution, "AC-12 manda"): `next_transition`
# (transitions.py) is the MACHINE advisor `feature-state.py next` consults -- its `reason`
# is code-controlled vocabulary, and some branches interpolate raw flags verbatim
# (`model.module_impacts_ready`, via transitions.py:123-125: "record-module-impact",
# "--module-impact-waived"). Pasting that string into STATUS.md would satisfy AC-11's
# letter (show the reason) while breaking AC-12 (no flags/commands/phase-names in a
# surface a human reads). This section re-derives the SAME states in Spanish prose
# instead, and is shared by STATUS.md's "Próximo paso" (this module, `describe_next_step`)
# and the digest's "Qué falta" bit (`render_notes._pending_bits`) -- one function feeding
# two surfaces, so they can never say two different things about the same state.
#
# The reason vocabulary is enumerated by hand against transitions.py:54-129 and
# model.py's `package_review_ready`/`module_impacts_ready` (both closed, code-controlled
# strings -- never agent narration, so a literal-lookup translation is safe here in a way
# it would not be for `client`/`tech`). A reason this repo starts emitting later that
# isn't in the table below still never leaks raw (see the fallback in `translate_reason`);
# it degrades to a generic phrase instead. Declared as a known risk in the package
# evidence, not hidden.

PHASE_LABEL_ES: dict[str, str] = {
    "PACKAGE_PLANNING": "planificación del próximo paquete",
    "PACKAGE_IMPLEMENTATION": "implementación",
    "PACKAGE_GATES": "gates del paquete",
    "PACKAGE_REVIEW": "revisión del paquete",
    "PACKAGE_REPAIR": "reparación",
    "DELTA_REVIEW": "revisión delta",
    "PACKAGE_TESTING": "pruebas de integración",
    "PACKAGE_RUNTIME_QA": "QA en vivo",
    "PACKAGE_ACCEPTED": "aceptación del paquete",
    "INTEGRATION": "integración final",
    "DONE": "cerrado",
    "BLOCKED": "bloqueado",
}

_VERDICT_ES = {"pass": "aprobó", "fail": "no aprobó", "repair_required": "pidió reparación"}


def _es_verdict(word: str) -> str:
    return _VERDICT_ES.get(word, word)


# Exact-match reasons: the constant strings every non-dynamic branch of
# `next_transition` returns (transitions.py:54-129), quoted verbatim as dict keys so a
# change to either side breaks loudly instead of silently falling back.
_STATIC_REASON_ES = {
    "plan next coherent package": "toca planificar el próximo paquete",
    "all package tasks completed": "las tareas del paquete están completas; sigue evaluar los gates",
    "continue local implementation": "sigue la implementación local del paquete",
    "package ready for deep review": "el paquete está listo para la revisión profunda",
    "review panel in progress": "el panel de revisión sigue en curso",
    "record-verification is required before repair": "hace falta verificar los hallazgos antes de reparar",
    "repair batch recorded": "la reparación quedó registrada; sigue la revisión delta",
    "delta review requires full review": "la revisión delta pide una revisión completa nueva",
    "a blocking finding is open; repair or refute it before testing can advance":
        "hay un hallazgo bloqueante abierto; hace falta repararlo o refutarlo antes de seguir con las pruebas",
    "run regression/integration tests": "toca correr las pruebas de regresión e integración",
    "a blocking finding is open; acceptance refuses until it is repaired or refuted":
        "hay un hallazgo bloqueante abierto; la aceptación se niega hasta repararlo o refutarlo",
    "run app/browser QA": "toca correr la QA de la app en el navegador",
    "remaining packages exist": "quedan paquetes del plan sin aceptar",
    "all packages accepted": "todos los paquetes están aceptados; sigue la integración",
    "run final global gates first": "faltan correr los gates globales finales",
    # AC-17, "rama sin paquete": transitions.py:129, the catch-all fallback. Translated,
    # never published raw.
    "record required event before continuing": "hace falta registrar el evento pendiente antes de seguir",
}

# Sub-reasons `package_review_ready` (model.py:485-495) joins with "; " into the
# PACKAGE_GATES branch's `reason` (transitions.py:71).
_SUBREASON_ES = {
    "tasks are not all completed": "quedan tareas del paquete sin completar",
    "required gates are missing or failing": "falta correr o falló algún gate obligatorio",
    "diff_ref is required": "falta registrar la referencia del diff integrado",
    "package must be integrated locally": "el paquete todavía no está integrado localmente",
}

_DYNAMIC_PREFIXES = (
    ("latest review verdict=", "la última revisión dio"),
    ("latest delta verdict=", "la última revisión delta dio"),
    ("latest testing status=", "las últimas pruebas dieron"),
    ("latest runtime QA status=", "la última QA en vivo dio"),
)


def _translate_dynamic(reason: str) -> str | None:
    for prefix, label in _DYNAMIC_PREFIXES:
        if reason.startswith(prefix):
            return f"{label}: {_es_verdict(reason[len(prefix):])}"
    return None


def _translate_join(reason: str) -> str | None:
    """`package_review_ready`/`module_impacts_ready` (model.py) join their own errors
    with '; ' before `next_transition` hands them back as `reason`
    (transitions.py:71,:125). Each part is closed, code-controlled vocabulary -- unlike
    `client`/`tech`, never agent narration -- so a literal per-part lookup is safe here.
    Returns None (never a partial/raw mix) when any part isn't recognized, so the caller
    falls back instead of ever publishing a mystery fragment raw.
    """
    parts = [p.strip() for p in reason.split("; ") if p.strip()]
    if not parts:
        return None
    translated = []
    for part in parts:
        if part in _SUBREASON_ES:
            translated.append(_SUBREASON_ES[part])
        elif "module impact required" in part and ":" in part:
            # model.py:546-549 (`module_impacts_ready`): carries the raw command names
            # AC-12 forbids ("record-module-impact", "--module-impact-waived") — this is
            # D-4b's own cited example. The package id is evidence (AC-04b's carve-out
            # in the sibling narration-guard spec applies the same way here), so it stays;
            # the flags never do.
            pkg = part.split(":", 1)[0].strip()
            translated.append(f"{pkg}: falta declarar el impacto de módulo o marcarlo como exento")
        else:
            return None
    return "; ".join(translated)


def translate_reason(reason: str) -> str:
    """Spanish rendering of a `next_transition` reason string. AC-12 forbids ever
    publishing the machine string verbatim in a human-facing surface, including for a
    shape this function doesn't recognize -- the fallback below is generic, never raw."""
    if not reason:
        return "sin motivo registrado"
    if reason in _STATIC_REASON_ES:
        return _STATIC_REASON_ES[reason]
    dynamic = _translate_dynamic(reason)
    if dynamic is not None:
        return dynamic
    joined = _translate_join(reason)
    if joined is not None:
        return joined
    return "hace falta resolver un paso previo antes de seguir"


def describe_next_step(data: dict[str, Any], mark_stale: bool = True) -> str:
    """AC-11/AC-17 (028/N3a): the four states without prior contract, defined here.

    - **Fase terminal (DONE)**: "—", no motive to show (AC-17: a raw `terminal` on the
      17 `DONE` rows would be worse than the dash it replaces).
    - **`BLOCKED` de decisión humana**: the next step belongs to the human, named as
      such; no alternative is required of it (mirrors AC-03 of the sibling 028/N1
      package, which exempts `HUMAN_DECISION_REQUIRED` from needing one).
    - **Rama sin paquete** (`transitions.py:129`'s catch-all): translated via
      `translate_reason`, never the raw fallback string.
    - **Muerte por cuota a mitad de camino**: there is no explicit "the instance died"
      flag in state, so this uses the closest existing, already-tested proxy —
      `model.feature_is_stale` (a live, unblocked feature whose `updated_at` is past
      `STALE_THRESHOLD_DAYS`) — and says so as "interrumpido", never silently reading
      the stale reason as if work were actively continuing. Declared limitation: a
      feature that died of quota exhaustion TODAY reads as "in progress" until it
      crosses the same staleness threshold the digest already uses elsewhere.

    `mark_stale=False` for the digest's "Qué falta" bit (`render_notes._pending_bits`):
    that surface already marks staleness once, in "Qué se está haciendo"
    (`⚠️ estancada hace N días`, cli_reporting.cmd_digest) -- appending it again here
    would be the same "3rd mention" SC-06 already forbids for a blocked feature's
    headline. STATUS.md has no other staleness column, so it keeps the marker.
    """
    phase = data.get("phase")
    if phase == "DONE":
        return "—"
    if phase == "BLOCKED":
        return "corresponde tu decisión (ver Blocker)"
    step = next_transition(data)
    text = translate_reason(step.get("reason") or "")
    if mark_stale and model.feature_is_stale(data):
        days = model.stale_days(data)
        text += f" — sin novedades hace {days} días, revisar si quedó interrumpido"
    return text


def status_root(state_file: Path) -> tuple[Path, Path]:
    """Return (features_dir, status_dir) for a given state file.

    Canonical layout is ai/state/features/<id>.json with STATUS.md one level up
    in ai/state/. Arbitrary --state-file locations (tests, ad-hoc runs) keep
    everything in the state file's own directory.
    """
    parent = state_file.resolve().parent
    if parent.name == "features":
        return parent, parent.parent
    return parent, parent


def summarize_feature(data: dict[str, Any]) -> dict[str, Any]:
    from feature_state_lib.render_notes import _short  # deferred: see module docstring
    budgets = data.get("budgets", {})
    packages = data.get("packages", [])
    current = None
    try:
        current = package_by_id(data)
    except StateError:
        pass
    spawns = sum(p.get("attempts", {}).get("spawns", 0) for p in packages)
    cycles = current.get("attempts", {}).get("deep_review_cycles", 0) if current else 0
    open_findings = sum(
        1
        for p in packages
        for f in p.get("findings", [])
        if f.get("status", "open") not in TERMINAL_FINDING_STATUSES
    )
    blockers = [b for b in data.get("blockers", []) if not b.get("resolved_at")]
    history = data.get("history", [])
    last = history[-1] if history else {}
    return {
        "feature_id": data.get("feature_id", "?"),
        "mode": data.get("mode") or "feature",
        "phase": data.get("phase", "?"),
        "package": f"{current.get('package_id')} ({current.get('status')})" if current else "-",
        "accepted": f"{sum(1 for p in packages if p.get('status') == 'accepted')}/{len(packages)}",
        "spawns": f"{spawns}/{budgets.get('max_spawns_per_package', '?')}",
        "reviews": f"{cycles}/{budgets.get('max_deep_review_cycles', '?')}",
        "open_findings": open_findings,
        # Raw here would put agent-authored newlines and pipes into a markdown TABLE in
        # a file memory-scribe and adversarial-judge read.  `_short` collapses the
        # whitespace; the pipe escape keeps the row a row.
        "blocker": _short(blockers[-1].get("reason", ""), 160).replace("|", "\\|") if blockers else "-",
        # AC-11 (028/N3a): the reason `next_transition` already computes, in Spanish
        # prose (`describe_next_step`) -- never `next_transition(data).get("next")` alone,
        # which is a bare phase name (AC-12) and discards the "why" that was sitting
        # right there in the same dict (D-4a). Pipe-escaped like `blocker` above: this
        # cell is agent-adjacent generated text landing in a markdown TABLE row.
        "next": describe_next_step(data).replace("|", "\\|"),
        "last_event": f"{last.get('timestamp', '')} {last.get('event', '')}".strip() or "-",
    }


def render_status(state_file: Path) -> None:
    """Rebuild the multi-feature STATUS.md dashboard next to the state files.

    Called after every successful mutation so the dashboard is always fresh
    without any extra orchestration step. Never raises: a broken dashboard must
    not block a state mutation.
    """
    if model.RENDER_SKIP:
        return
    try:
        features_dir, out_dir = status_root(state_file)
        rows = []
        for path in sorted(features_dir.glob("*.json")):
            try:
                rows.append(summarize_feature(load_state(path)))
            except Exception:  # legacy/malformed schemas degrade to a row, never a crash
                rows.append({"feature_id": path.stem, "mode": "?", "phase": "INVALID_STATE",
                             "package": "-", "accepted": "-", "spawns": "-", "reviews": "-",
                             "open_findings": "-", "blocker": "state file failed to parse",
                             "next": "-", "last_event": "-"})
        lines = [
            "# Estado del desarrollo",
            "",
            "_Generado por `feature-state.py` en cada mutación de estado. No editar a mano._",
            "",
            f"Actualizado: {now()}",
            "",
            "## Features",
            "",
            "| Feature | Modo | Fase | Paquete | Aceptados | Spawns | Reviews | Findings abiertos | Blocker | Próximo paso | Último evento |",
            "|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        if rows:
            for row in rows:
                lines.append(
                    "| {feature_id} | {mode} | {phase} | {package} | {accepted} | {spawns} | {reviews} "
                    "| {open_findings} | {blocker} | {next} | {last_event} |".format(**row)
                )
        else:
            lines.append("| _sin features registradas_ | | | | | | | | | | |")
        lines += ["", "## Quick-fixes recientes", ""]
        entries = read_jsonl(out_dir / "quickfix-log.jsonl")
        if entries:
            for entry in entries[-10:][::-1]:
                files = ", ".join(entry.get("files", [])) or "-"
                lines.append(
                    f"- [{entry.get('at', '?')}] {entry.get('summary', '?')} — archivos: {files} "
                    f"— gate: {entry.get('gate', '-')} — resultado: {entry.get('result', '-')}"
                )
        else:
            lines.append("- _sin quick-fixes registrados_")
        lines += ["", "## Bitácora (últimos 15)", ""]
        narrative = collect_narrative(features_dir, out_dir)
        if narrative:
            for entry in narrative[-15:][::-1]:
                lines += format_narrative(entry)
        else:
            lines.append("- _sin narración registrada_")
        out_dir.mkdir(parents=True, exist_ok=True)
        payload = "\n".join(lines) + "\n"
        # encoding="utf-8" is NOT decoration. Without it Python picks the machine's
        # locale encoding, and every heading here is Spanish ("Bitácora", "Próximo
        # paso"). Measured on 2026-08-18: under `PYTHONCOERCECLOCALE=0 LC_ALL=C` the
        # write raised UnicodeEncodeError, the bare `except: pass` below swallowed it,
        # `render-status` still exited 0, STATUS.md was NEVER written, and the partial
        # temp file stayed behind in ai/state/. A silently stale dashboard reporting
        # success is the exact false-green this harness exists to kill. Windows CI hit
        # the mirror image: cp1252 bytes written here, then read back as UTF-8.
        tmp_name = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", dir=str(out_dir), delete=False, encoding="utf-8"
            ) as handle:
                handle.write(payload)
                tmp_name = handle.name
            os.replace(tmp_name, out_dir / "STATUS.md")
        except Exception:
            # Never leave the partial file behind: `ai/state/` is the durable record,
            # not a scratch directory, and the turds accumulate one per failed render.
            if tmp_name:
                with contextlib.suppress(OSError):
                    os.unlink(tmp_name)
            raise
    except Exception as exc:  # the dashboard is best-effort by contract, never blocks state
        # ...but "best-effort" is not "invisible". render_notes and render_modules both
        # route their failures to this log; STATUS.md -- the one artifact contracted to
        # be "always fresh" -- was the only renderer that swallowed them into nothing.
        with contextlib.suppress(Exception):
            from feature_state_lib.render_notes import _log_render_failure
            _log_render_failure(status_root(state_file)[1], "render_status", exc)
