"""Append-only inter-agent bus under ai/state/bus/ (ADR-0077).

No relay agent: producers ``bus-post``, consumers ``bus-list``. Messages are
JSONL lines; topics are closed to ``[a-z0-9][a-z0-9._-]{0,63}``.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from feature_state_lib.model import StateError, now, print_json
from feature_state_lib.render_bitacora import read_jsonl

_TOPIC_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
BUS_DIRNAME = "bus"


def bus_root(state_dir: Path | None = None) -> Path:
    root = Path(state_dir) if state_dir else Path("ai/state")
    return root / BUS_DIRNAME


def _topic_path(root: Path, topic: str) -> Path:
    if not _TOPIC_RE.match(topic):
        raise StateError(
            f"BUS_TOPIC_INVALID: {topic!r} — use [a-z0-9][a-z0-9._-]{{0,63}}"
        )
    return root / f"{topic}.jsonl"


def bus_post(
    *,
    topic: str,
    from_role: str,
    to_role: str,
    body: str,
    feature_id: str = "",
    package_id: str = "",
    state_dir: Path | None = None,
) -> dict[str, Any]:
    if not from_role or not to_role or not body.strip():
        raise StateError("BUS_POST_INVALID: --from, --to and --body are required")
    root = bus_root(state_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = _topic_path(root, topic)
    entry = {
        "at": now(),
        "topic": topic,
        "from": from_role,
        "to": to_role,
        "body": body.strip(),
        "feature_id": feature_id or "",
        "package_id": package_id or "",
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")
    return {"ok": True, "path": str(path), "entry": entry}


def bus_list(
    *,
    topic: str,
    to_role: str | None = None,
    limit: int = 50,
    state_dir: Path | None = None,
) -> dict[str, Any]:
    root = bus_root(state_dir)
    path = _topic_path(root, topic)
    if not path.is_file():
        return {"ok": True, "path": str(path), "entries": []}
    entries = read_jsonl(path)
    if to_role:
        entries = [e for e in entries if e.get("to") == to_role]
    if limit > 0:
        entries = entries[-limit:]
    return {"ok": True, "path": str(path), "entries": entries}


def cmd_bus_post(args: argparse.Namespace) -> int:
    result = bus_post(
        topic=args.topic,
        from_role=args.from_role,
        to_role=args.to_role,
        body=args.body,
        feature_id=args.feature_id or "",
        package_id=args.package_id or "",
        state_dir=Path(args.state_dir) if args.state_dir else None,
    )
    print_json(result)
    return 0


def cmd_bus_list(args: argparse.Namespace) -> int:
    result = bus_list(
        topic=args.topic,
        to_role=args.to_role,
        limit=int(args.limit),
        state_dir=Path(args.state_dir) if args.state_dir else None,
    )
    print_json(result)
    return 0
