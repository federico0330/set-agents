#!/usr/bin/env python3
"""Claude PreToolUse hook. Exit 2 blocks a Bash command."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from coord_policy import allowed  # noqa: E402

try:
    payload = json.load(sys.stdin)
    command = payload.get("tool_input", {}).get("command", "")
except (json.JSONDecodeError, AttributeError):
    command = ""

if not allowed(command):
    print("Blocked: coordinator Bash is read-only and deny-by-default", file=sys.stderr)
    raise SystemExit(2)
