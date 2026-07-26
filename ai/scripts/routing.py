#!/usr/bin/env python3
"""Compatibility composition facade for trusted routing-v2."""
from __future__ import annotations
import json
import os
import re
import stat
from pathlib import Path
from routing_core.catalog import build_snapshot
from routing_core.domain import CRITICAL, TASK_CLASSES, RouteDecision, RoutingError, TaskRequest
from routing_core.gates import GateSpec, gate_specs, run_gate
from routing_core.service import RoutingService
from routing_core.store import RoutingStore

SCHEMA_VERSION=2
ROOT=Path(__file__).resolve().parents[2]

def compose(config, roster, *, simulate=False):
    """Production composition: snapshot, inventory, and root are never caller-provided.

    RoutingService seals its own composition: it builds the snapshot from the
    on-disk catalog and probes the pair inventory internally.
    """
    return RoutingService(ROOT/"ai/catalogs/routes.v1.toml", roster, config,
                          None if simulate else RoutingStore(), simulate=simulate)

def _compose_for_tests(config, roster, inventory, root=None, simulate=False):
    """Private hermetic seam; not exported and never used by app composition."""
    store = None if simulate else (RoutingStore() if root is None else RoutingStore._for_tests(root))
    return RoutingService._for_tests(build_snapshot(ROOT/"ai/catalogs/routes.v1.toml", roster, config), roster, inventory, store, simulate=simulate)

def cli_envelope(ok, command, data, warnings=(), reason_codes=()):
    return {"schema_version":2,"ok":bool(ok),"command":command,"data":data if isinstance(data,dict) else {},"warnings":list(warnings),"reason_codes":list(reason_codes)}

def legacy_warnings(state_dir: Path):
    """No-follow legacy presence detector; it never opens legacy routing data."""
    legacy = Path(state_dir) / "routing"
    exact = {"routing-decisions.json", "routing-decisions.lock", "routing-events.jsonl", "routing-metadata.json", "routing.salt", "routing.lock"}
    rotated = re.compile(r"^routing-events-[0-9]+-[0-9]+\.jsonl$")
    warnings = set()
    try:
        root_mode = legacy.lstat().st_mode
    except FileNotFoundError:
        return ()
    except OSError:
        return ("LEGACY_ROUTING_STATE_UNSAFE",)
    if stat.S_ISLNK(root_mode) or not stat.S_ISDIR(root_mode):
        return ("LEGACY_ROUTING_STATE_UNSAFE",)
    try:
        names = os.listdir(legacy)
    except OSError:
        return ("LEGACY_ROUTING_STATE_UNSAFE",)
    for name in names:
        if name not in exact and not rotated.fullmatch(name): continue
        entry = legacy / name
        try: mode = entry.lstat().st_mode
        except OSError: warnings.add("LEGACY_ROUTING_STATE_UNSAFE"); continue
        warnings.add("LEGACY_ROUTING_STATE_PRESENT")
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode): warnings.add("LEGACY_ROUTING_STATE_UNSAFE")
    return tuple(sorted(warnings))

def route_task(task, catalog=None, config=None, observed=None):
    """Deprecated v1 helper: callers must use RoutingService.route with facts."""
    raise RoutingError("TRUSTED_ROUTING_SERVICE_REQUIRED")

__all__=["RouteDecision","RoutingError","TaskRequest","RoutingStore","RoutingService","GateSpec","compose","cli_envelope","gate_specs","run_gate","SCHEMA_VERSION","TASK_CLASSES","CRITICAL"]
