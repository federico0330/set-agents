#!/usr/bin/env python3
"""Claude PreToolUse guard shared by read-only review, gate, and run-ro roles.

Fails open: only the short, irreducible list of always-dangerous commands
(sudo, recursive force-delete, force-push, repo deletion) is hard-blocked.
Everything else falls through (exit 0) to Claude Code's own interactive
permission prompt instead of a silent deny, so a subagent can ask a human for
an uncommon command instead of getting stuck with no way to proceed.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from coord_policy import always_denied  # noqa: E402

try:
    command = json.load(sys.stdin).get("tool_input", {}).get("command", "")
except (json.JSONDecodeError, AttributeError):
    command = ""

if always_denied(command):
    print("Blocked: destructive command is never allowed, even with confirmation", file=sys.stderr)
    raise SystemExit(2)
