"""Extracted from ai/scripts/feature-state.py by a behavior-preserving refactor
(mechanical reorganization only -- no logic changes). See feature-state.py's own
module docstring and the package-level notes for the split rationale.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from feature_state_lib import model
from feature_state_lib.model import StateError, now, load_state, package_by_id, TERMINAL_FINDING_STATUSES
from feature_state_lib.transitions import next_transition
from feature_state_lib.render_bitacora import read_jsonl, collect_narrative, format_narrative


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
        "next": (next_transition(data).get("next") or "-"),
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
        with tempfile.NamedTemporaryFile("w", dir=str(out_dir), delete=False) as handle:
            handle.write(payload)
            tmp_name = handle.name
        os.replace(tmp_name, out_dir / "STATUS.md")
    except Exception:  # the dashboard is best-effort by contract, never blocks state
        pass
