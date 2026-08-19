"""Extracted from ai/scripts/feature-state.py by a behavior-preserving refactor
(mechanical reorganization only -- no logic changes). See feature-state.py's own
module docstring and the package-level notes for the split rationale.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from feature_state_lib import model
from feature_state_lib.model import now


NARRATIVE_LOG = "narrative-log.jsonl"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if not path.exists():
        return entries
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            entries.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return entries


def collect_narrative(features_dir: Path, out_dir: Path) -> list[dict[str, Any]]:
    """Merge the two sources of narration into one chronological list.

    The opening block of a delegation rides on `record-spawn` metadata, so it
    stays attached to the budget it consumed. Every other block — closings,
    consult, quick-fix — lands in narrative-log.jsonl. Reading both is what
    makes the story hole-free.
    """
    entries: list[dict[str, Any]] = []
    for entry in read_jsonl(out_dir / NARRATIVE_LOG):
        if entry.get("client") or entry.get("tech"):
            entries.append(entry)
    for path in sorted(features_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for event in data.get("history", []):
            meta = event.get("metadata") or {}
            if not (meta.get("client") or meta.get("tech")):
                continue
            entries.append({
                "at": event.get("timestamp", ""),
                "feature_id": data.get("feature_id", path.stem),
                "package_id": event.get("package_id") or "-",
                "role": meta.get("role") or event.get("event", "-"),
                "result": "started",
                "client": meta.get("client", ""),
                "tech": meta.get("tech", ""),
                "actor": event.get("actor", "-"),
                # ADR-0031: the structured routing decision record-spawn now carries.
                "model": meta.get("model", ""),
                "provider": meta.get("provider", ""),
                "effort": meta.get("effort", ""),
                "spawn_budget": meta.get("spawn_budget", ""),
                "spawn_budget_warn": meta.get("spawn_budget_warn", False),
            })
    # Timestamps have second resolution, so an opening and its closing block can
    # tie. Break the tie on result so a delegation never reads as having finished
    # before it started.
    entries.sort(key=lambda item: (
        item.get("at", ""),
        item.get("feature_id", ""),
        0 if item.get("result") == "started" else 1,
    ))
    return entries


# AC-15 / hallazgo N3b-F01: UN solo tope para los campos de narración. Antes había dos
# números en desacuerdo -- `narration_lint.LONG_FIELD_LIMIT = 400` decidía qué se puede
# ESCRIBIR (AC-05) y este render cortaba en 300, así que un `tech` de 350 caracteres era
# perfectamente legal al escribirlo y salía SIEMPRE mutilado al leerlo. No se alinea
# bajando el tope de escritura: AC-05 concede 400 explícitamente. `tests/test_digest.py`
# afirma que este número y `LONG_FIELD_LIMIT` son iguales, así que no pueden volver a
# separarse en silencio. El marcador `_(truncado al render)_` sigue existiendo para todo
# lo que sí exceda: el corte es ruidoso, nunca callado.
NARRATION_FIELD_LIMIT = 400


def format_narrative(entry: dict[str, Any]) -> list[str]:
    """One narration block: a header line plus the two labelled registers."""
    from feature_state_lib.render_notes import _short  # deferred: see module docstring
    def _render_field(label: str, value: Any, limit: int = NARRATION_FIELD_LIMIT) -> str:
        normalized = " ".join(str(value or "").split()).replace("<!--", "‹!--").replace("-->", "--›")
        text = _short(value, limit) or "-"
        if normalized and len(normalized) > limit:
            text += " _(truncado al render)_"
        return f"{label}: {text}"

    parts = [
        part for part in (entry.get("package_id"), entry.get("role"), entry.get("result"))
        if part and part != "-"
    ]
    # ADR-0031: agent-authored fields headed for a generated file go through _short,
    # like every register below — never raw into the notas:auto surface.
    model = entry.get("model")
    if model:
        provider = entry.get("provider")
        parts.append("modelo " + _short(f"{provider}/{model}" if provider else model, 80))
    if entry.get("effort"):
        parts.append("effort " + _short(entry["effort"], 20))
    if entry.get("spawn_budget"):
        budget_bit = "spawns " + _short(entry["spawn_budget"], 40)
        if entry.get("spawn_budget_warn"):
            budget_bit += " WARN 80%"
        parts.append(budget_bit)
    tail = " · ".join(parts)
    lines = [
        f"[{entry.get('at', '?')}] {tail}".rstrip(),
        _render_field("Cliente", entry.get("client")),
        _render_field("Ingeniería", entry.get("tech")),
    ]
    if entry.get("learned"):
        lines.append(_render_field("Aprendimos", entry.get("learned")))
    if entry.get("next"):
        lines.append(_render_field("Conviene ahora", entry.get("next")))
    if entry.get("why"):
        lines.append(_render_field("Por qué ahora", entry.get("why")))
    if entry.get("alternative"):
        lines.append(_render_field("Alternativa", entry.get("alternative")))
    lines.append("")
    return lines


def bitacora_path(out_dir: Path, feature_id: str) -> Path:
    """Prefer the client-facing delivery folder; fall back to internal state.

    docs/specs/<feature_id>/ is what a client actually receives (sibling of
    evidence/), so the narration belongs there when the feature has one.
    """
    root = out_dir.parent.parent
    delivery = root / "docs" / "specs" / feature_id
    if delivery.is_dir():
        return delivery / "bitacora.md"
    return out_dir / "bitacora" / f"{feature_id}.md"


def render_bitacora(state_file: Path, only_feature: str | None = None) -> None:
    """Rebuild the cumulative per-feature narration log.

    STATUS.md keeps only the tail; this file keeps the whole story in the
    language the user can hand to a client. Fully regenerated from state
    history plus narrative-log.jsonl, so it is never hand-edited and never
    drifts. Never raises: narration must not block a state mutation.

    only_feature limits the rebuild to that feature's bitacora — mutations
    touch one feature, so rewriting every other feature's log is waste.
    """
    if model.RENDER_SKIP:
        return
    try:
        from feature_state_lib.render_status import status_root  # deferred: see module docstring
        features_dir, out_dir = status_root(state_file)
        by_feature: dict[str, list[dict[str, Any]]] = {}
        for entry in collect_narrative(features_dir, out_dir):
            by_feature.setdefault(entry.get("feature_id") or "sin-feature", []).append(entry)
        for feature_id, items in by_feature.items():
            if only_feature and feature_id != only_feature:
                continue
            lines = [
                f"# Bitácora — {feature_id}",
                "",
                "_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la "
                "justificación de ingeniería. No editar a mano._",
                "",
                f"Actualizado: {now()}",
                "",
            ]
            for entry in items:
                lines += format_narrative(entry)
            target = bitacora_path(out_dir, feature_id)
            target.parent.mkdir(parents=True, exist_ok=True)
            payload = "\n".join(lines).rstrip() + "\n"
            with tempfile.NamedTemporaryFile(
                "w", dir=str(target.parent), delete=False, encoding="utf-8"
            ) as handle:
                handle.write(payload)
                tmp_name = handle.name
            os.replace(tmp_name, target)
    except Exception:  # narration is best-effort by contract, never blocks state
        pass
