#!/usr/bin/env python3
"""Claude PreToolUse guard for the project-local P001 gate runner."""

import json
import shlex
import sys


SCRIPTS = {"ai/scripts/feature-state.py", "ai/scripts/check-owned-paths.py"}
STATE_PREFIX = "ai/state/features/"


def blocked() -> None:
    print("Blocked: local-gate-runner may only execute its P001 commands", file=sys.stderr)
    raise SystemExit(2)


def is_feature_state(values: list[str]) -> bool:
    # The sole write target is a flat feature state file under ai/state/features/, generic across
    # projects. Reject nested paths and traversal so the lockdown stays as tight as a fixed filename.
    if len(values) != 1:
        return False
    path = values[0]
    return (
        path.startswith(STATE_PREFIX)
        and path.endswith(".json")
        and ".." not in path
        and "/" not in path[len(STATE_PREFIX):]
    )


try:
    command = json.load(sys.stdin).get("tool_input", {}).get("command", "").strip()
    argv = shlex.split(command)
except (json.JSONDecodeError, AttributeError, ValueError):
    blocked()

if not command or "\n" in command or any(token.startswith(".env") or ".env" in token for token in argv):
    blocked()

allowed = (
    len(argv) == 4
    and argv[:3] == ["python3", "-m", "py_compile"]
    and argv[3] in SCRIPTS
) or (
    len(argv) == 3
    and argv[0] == "python3"
    and argv[1] in SCRIPTS
    and argv[2] == "--help"
) or (
    len(argv) == 7
    and argv[:2] == ["python3", "ai/scripts/check-owned-paths.py"]
    and argv[2::2] == ["--state-file", "--package-id", "--baseline"]
) or argv == ["git", "diff", "--check"] or (
    len(argv) >= 5
    and argv[:3] == ["python3", "ai/scripts/feature-state.py", "record-gate"]
    and argv.count("--state-file") == 1
    and is_feature_state(argv[argv.index("--state-file") + 1:argv.index("--state-file") + 2])
)

if not allowed:
    blocked()
