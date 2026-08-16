#!/usr/bin/env python3
"""Claude PreToolUse hook. Exit 2 blocks a Bash command."""

import json
import sys
from pathlib import Path

# SEC-030-R1: fail CLOSED if the policy cannot be imported.  A PreToolUse hook only
# blocks with exit 2; any other exit lets the command through, so an ImportError used to
# disable this guard silently.
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from coord_policy import allowed  # noqa: E402
except Exception as exc:  # noqa: BLE001 -- deny on ANY import failure, never proceed
    print(f"Blocked: command policy unavailable ({exc.__class__.__name__}): {exc}", file=sys.stderr)
    raise SystemExit(2)

try:
    payload = json.load(sys.stdin)
    command = payload.get("tool_input", {}).get("command", "")
except (json.JSONDecodeError, AttributeError):
    command = ""

if not allowed(command):
    print("Blocked: coordinator Bash is read-only and deny-by-default", file=sys.stderr)
    raise SystemExit(2)
