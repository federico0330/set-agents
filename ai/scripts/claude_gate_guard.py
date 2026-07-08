#!/usr/bin/env python3
"""Claude PreToolUse guard for deterministic gate commands."""

import json
import re
import shlex
import sys

SAFE = re.compile(
    r"(?:\./ai/scripts/verify\.sh|npm (?:test|run (?:test|lint|typecheck|build))|"
    r"dotnet test|go test|cargo test|python -m pytest)(?:\s|$)"
)
FORBIDDEN = re.compile(r"(?:>|>>|<|<<|\|\||&&|;|\|)|`|\$\(")

try:
    command = json.load(sys.stdin).get("tool_input", {}).get("command", "").strip()
except (json.JSONDecodeError, AttributeError):
    command = ""

try:
    argv = shlex.split(command)
except ValueError:
    argv = []

dangerous = ("-exec", "-toolexec", "--exec", "--runner", "--config")
if not command or "\n" in command or FORBIDDEN.search(command) or not SAFE.match(command) or any(
    token.startswith(prefix) for token in argv for prefix in dangerous
):
    print("Blocked: gate-runner may only execute deterministic gates", file=sys.stderr)
    raise SystemExit(2)
