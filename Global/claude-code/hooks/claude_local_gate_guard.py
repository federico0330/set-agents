#!/usr/bin/env python3
"""Claude PreToolUse guard for the project-local P001 gate runner."""

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


SCRIPTS = {"ai/scripts/feature-state.py", "ai/scripts/check-owned-paths.py"}
STATE_FILE = "ai/state/002-local-uat-identities-and-feature-state.json"


def blocked() -> None:
    print("Blocked: local-gate-runner may only execute its P001 commands", file=sys.stderr)
    raise SystemExit(2)


try:
    command = json.load(sys.stdin).get("tool_input", {}).get("command", "").strip()
    argv = shlex.split(command)
except (json.JSONDecodeError, AttributeError, ValueError):
    blocked()

if not command or "\n" in command or FORBIDDEN_SYNTAX.search(command) or any(token.startswith(".env") or ".env" in token for token in argv):
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
    and argv[argv.index("--state-file") + 1:argv.index("--state-file") + 2] == [STATE_FILE]
)

if not allowed:
    blocked()
