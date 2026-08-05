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


def format_narrative(entry: dict[str, Any]) -> list[str]:
    """One narration block: a header line plus the two labelled registers."""
    from feature_state_lib.render_notes import _short  # deferred: see module docstring
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
    tail = " · ".join(parts)
    return [
        f"[{entry.get('at', '?')}] {tail}".rstrip(),
        f"Cliente: {_short(entry.get('client'), 400) or '-'}",
        f"Ingeniería: {_short(entry.get('tech'), 400) or '-'}",
        "",
    ]


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
