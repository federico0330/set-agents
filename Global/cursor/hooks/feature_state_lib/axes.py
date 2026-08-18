"""Axes intake helpers for 029/conventions-before-code."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from feature_state_lib.model import StateError

AXES = (
    "data-store",
    "api-gateway",
    "deploy-platform",
    "audience",
    "embeddings",
    "realtime",
    "mobile",
    "auth",
    "cost",
    "legal",
)

FIRST_CLASS_AXES = {"data-store", "api-gateway", "deploy-platform"}
VALID_ORIGINS = {"request", "notas", "decisions-log", "adr", "user", "assumed", "n/a"}
CONTENT_DENYLIST = {"n/a", "na", "none", "ninguno", "ninguna", "-", "--", "tbd", "todo", "por definir", "a definir", "ok"}


def axes_log_path(state_file: Path, axes_log: str | None = None) -> Path:
    if axes_log:
        return Path(axes_log)
    state_file = state_file.resolve()
    if state_file.parent.name == "features":
        return state_file.parent.parent / "axes-log.jsonl"
    return state_file.parent / "axes-log.jsonl"


def read_axes_log(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def append_axes_row(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def validate_row(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    axis = row.get("axis")
    if row.get("feature_id") in {None, ""}:
        errors.append("missing feature_id")
    if axis not in AXES:
        errors.append("invalid axis")
    if not row.get("stance") or str(row.get("stance")).strip().lower() in CONTENT_DENYLIST:
        errors.append("invalid stance")
    origin = row.get("origin")
    if origin not in VALID_ORIGINS:
        errors.append("invalid origin")
    if origin == "n/a":
        if not row.get("reason") or str(row.get("reason")).strip().lower() in CONTENT_DENYLIST:
            errors.append("origin n/a requires reason")
    elif not row.get("source"):
        errors.append("source required")
    if origin == "assumed":
        for key in ("threshold", "next_stance", "revisit"):
            if not row.get(key) or str(row.get(key)).strip().lower() in CONTENT_DENYLIST:
                errors.append(f"assumed requires {key}")
    if origin == "user" and axis in FIRST_CLASS_AXES and not row.get("asked_at"):
        errors.append("first-class user axis requires asked_at")
    return errors


def latest_rows(rows: list[dict[str, Any]], feature_id: str) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("feature_id") != feature_id:
            continue
        axis = row.get("axis")
        if axis in AXES:
            latest[axis] = row
    return latest


def _exists_source(source: str) -> bool:
    path = Path(source.split(":", 1)[0])
    return path.is_file()


def validate_rows(rows: list[dict[str, Any]], feature_id: str) -> list[str]:
    errors: list[str] = []
    latest = latest_rows(rows, feature_id)
    missing = [axis for axis in AXES if axis not in latest]
    if missing:
        errors.append("missing axes: " + ", ".join(missing))
    for axis, row in latest.items():
        if row.get("feature_id") != feature_id:
            errors.append(f"{axis}: wrong feature_id")
        if row.get("axis") not in AXES:
            errors.append(f"{axis}: invalid axis")
        if not row.get("stance") or str(row.get("stance")).strip().lower() in CONTENT_DENYLIST:
            errors.append(f"{axis}: invalid stance")
        origin = row.get("origin")
        if origin not in VALID_ORIGINS:
            errors.append(f"{axis}: invalid origin")
            continue
        source = row.get("source")
        threshold = row.get("threshold")
        next_stance = row.get("next_stance")
        revisit = row.get("revisit")
        reason = row.get("reason")
        if origin == "n/a":
            if not reason or str(reason).strip().lower() in CONTENT_DENYLIST:
                errors.append(f"{axis}: origin n/a requires reason")
            continue
        if not source:
            errors.append(f"{axis}: source required")
        elif origin in {"request", "notas", "decisions-log", "adr"} and not _exists_source(str(source)):
            errors.append(f"{axis}: source not resolvable")
        if origin == "assumed":
            if not threshold or str(threshold).strip().lower() in CONTENT_DENYLIST:
                errors.append(f"{axis}: assumed requires threshold")
            if not next_stance or str(next_stance).strip().lower() in CONTENT_DENYLIST:
                errors.append(f"{axis}: assumed requires next_stance")
            if not revisit or str(revisit).strip().lower() in CONTENT_DENYLIST:
                errors.append(f"{axis}: assumed requires revisit")
        if origin == "user" and axis in FIRST_CLASS_AXES and not row.get("asked_at"):
            errors.append(f"{axis}: first-class user axis requires asked_at")
        if threshold and str(threshold).strip().lower() in CONTENT_DENYLIST:
            errors.append(f"{axis}: threshold is placeholder")
        if next_stance and str(next_stance).strip().lower() in CONTENT_DENYLIST:
            errors.append(f"{axis}: next_stance is placeholder")
        if revisit and str(revisit).strip().lower() in CONTENT_DENYLIST:
            errors.append(f"{axis}: revisit is placeholder")
    return errors


def render_table(rows: list[dict[str, Any]], feature_id: str) -> str:
    latest = latest_rows(rows, feature_id)
    lines = ["## Convenciones", "", "| Eje | Origen | Stance | Umbral | Siguiente | Revisit |", "|---|---|---|---|---|---|"]
    for axis in AXES:
        row = latest.get(axis)
        if not row:
            lines.append(f"| {axis} | - | - | - | - | - |")
            continue
        lines.append(
            f"| {axis} | {row.get('origin', '-')} | {row.get('stance', '-')} | "
            f"{row.get('threshold', '-')} | {row.get('next_stance', '-')} | {row.get('revisit', '-')} |"
        )
    return "\n".join(lines)


def render_hub_table(rows: list[dict[str, Any]]) -> str:
    by_feature: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        fid = row.get("feature_id")
        if not fid:
            continue
        by_feature.setdefault(str(fid), []).append(row)
    lines = ["## Convenciones", "", "| Feature | Cobertura | Orígenes |", "|---|---|---|"]
    for fid in sorted(by_feature):
        latest = latest_rows(by_feature[fid], fid)
        covered = sum(1 for axis in AXES if axis in latest)
        origins = ", ".join(sorted({str(row.get("origin", "-")) for row in latest.values()})) or "-"
        lines.append(f"| {fid} | {covered}/{len(AXES)} | {origins} |")
    if len(lines) == 4:
        lines.append("| - | 0/10 | - |")
    return "\n".join(lines)
