#!/usr/bin/env python3
"""Claude PreToolUse hook for app-runner. Exit 2 blocks a Bash command.

Allows read-only inspection (coord policy), launching the project via its own
scripts, managing browser MCP only for runtime QA, and probing local health
endpoints. Never permits edits, installs, commits, or arbitrary mutation.
"""

import json
import re
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from coord_policy import FORBIDDEN_OPTIONS, FORBIDDEN_SYNTAX, allowed as coord_allowed  # noqa: E402

RUN = [
    re.compile(r"\./ai/scripts/run\.sh(\s|$)"),
    re.compile(r"\./ai/scripts/verify\.sh(\s|$)"),
    re.compile(r"\./ai/scripts/e2e\.sh(\s|$)"),
    re.compile(r"\./ai/scripts/mcp\.sh\s+(?:browser-gate|ensure-brave-cdp|status)(?:\s|$)"),
    re.compile(r"\./ai/scripts/mcp\.sh\s+(?:on|off)\s+(?:playwright|brave-cdp)(?:\s|$)"),
    re.compile(r"curl\s+(?:-[A-Za-z]+\s+)*(?:http://)?(?:localhost|127\.0\.0\.1)(?::\d+)?(?:/|\s|$)"),
]


def allowed(command: str) -> bool:
    command = command.strip()
    if not command or "\n" in command:
        return False
    if coord_allowed(command):
        return True
    if FORBIDDEN_SYNTAX.search(command) or FORBIDDEN_OPTIONS.search(command):
        return False
    try:
        shlex.split(command)
    except ValueError:
        return False
    return any(pattern.match(command) for pattern in RUN)


if __name__ == "__main__":
    try:
        payload = json.load(sys.stdin)
        command = payload.get("tool_input", {}).get("command", "")
    except (json.JSONDecodeError, AttributeError):
        command = ""
    if not allowed(command):
        print("Blocked: run-ro may only inspect, run ./ai/scripts/{run,verify,e2e}.sh, manage browser MCP for runtime QA, and probe localhost", file=sys.stderr)
        raise SystemExit(2)
