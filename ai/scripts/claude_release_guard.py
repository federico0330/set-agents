#!/usr/bin/env python3
"""Allow Claude release Bash only through the gated wrapper."""

import json
import shlex
import sys
from pathlib import Path

# Add ai/scripts to path to import coord_policy.
# SEC-030-R1: the import is fail-CLOSED on purpose.  A PreToolUse hook only blocks with
# exit 2; ANY other exit lets the command proceed.  So an ImportError here -- a moved
# file, a symlinked hook dir, a broken install -- used to turn this guard OFF silently,
# which is the worst possible failure for a control whose whole job is denying.  And it
# is reachable: a command that deletes or renames coord_policy.py disables every guard
# that imports it.  `.resolve()` matters for the same reason: without it, a hook invoked
# through a symlink looks for coord_policy next to the LINK, not next to the real file.
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from coord_policy import FORBIDDEN_SYNTAX
except Exception as exc:  # noqa: BLE001 -- deny on ANY import failure, never proceed
    print(f"Blocked: command policy unavailable ({exc.__class__.__name__}): {exc}", file=sys.stderr)
    raise SystemExit(2)

try:
    command = json.load(sys.stdin).get("tool_input", {}).get("command", "")
    argv = shlex.split(command)
except (json.JSONDecodeError, AttributeError, ValueError):
    argv = []

base_ok = argv[:2] == ["python3", "~/.claude/hooks/release_action.py"]
# Approval actions: `release_action.py STATE confirm-publish|confirm-merge` (no `-- COMMAND`).
confirm_ok = base_ok and len(argv) == 4 and argv[3] in ("confirm-publish", "confirm-merge")
# Full gated mutation: `release_action.py STATE ACTION -- COMMAND`.
full_ok = base_ok and len(argv) >= 6 and "--" in argv

if "\n" in command or FORBIDDEN_SYNTAX.search(command) or not (confirm_ok or full_ok):
    print("Blocked: release actions must use the gated wrapper", file=sys.stderr)
    raise SystemExit(2)
