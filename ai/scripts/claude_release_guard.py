#!/usr/bin/env python3
"""Allow Claude release Bash only through the gated wrapper."""

import json
import shlex
import sys
from pathlib import Path

# Add ai/scripts to path to import coord_policy
sys.path.insert(0, str(Path(__file__).parent))
from coord_policy import FORBIDDEN_SYNTAX

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
