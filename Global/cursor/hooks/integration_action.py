#!/usr/bin/env python3
"""Execute one tightly-scoped integration command after checking recorded gates
(docs/adr/0020-*.md). Mirrors release_action.py's shape, with one extra
positional (PACKAGE_ID) since integration authority is package-scoped, never
feature-scoped.
"""

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from integration_gate import check  # noqa: E402

FORBIDDEN_SYNTAX = re.compile(r"(?:>|>>|<|<<|\|\||&&|;|\|)|`|\$\(")

if len(sys.argv) < 4 or "--" not in sys.argv:
    raise SystemExit("usage: integration_action.py STATE PACKAGE_ID ACTION -- COMMAND")
state_path, package_id, action = sys.argv[1], sys.argv[2], sys.argv[3]
separator = sys.argv.index("--")
command = sys.argv[separator + 1:]
check(state_path, package_id, action)

allowed = {
    "freeze-candidate": [("python3", "ai/scripts/feature-state.py", "freeze-candidate")],
    "record-receipt": [("python3", "ai/scripts/feature-state.py", "record-receipt")],
    "transition": [("python3", "ai/scripts/feature-state.py", "transition")],
}
if not command or not any(tuple(command[:len(prefix)]) == prefix for prefix in allowed[action]):
    raise SystemExit("command is not allowed for this integration action")
if any(FORBIDDEN_SYNTAX.search(part) for part in command):
    raise SystemExit("unsafe shell syntax blocked")

if action in {"freeze-candidate", "record-receipt"}:
    # These take package_id as their first positional (argv[3] of the underlying
    # command) -- must match the package this wrapper's Bash-layer check named,
    # never a different one smuggled into the command past the gate check.
    if len(command) < 4 or command[3] != package_id:
        raise SystemExit(f"{action} command must target the checked package_id as its first positional")
if action == "transition":
    # The one shape this wrapper exists to gate: the command must actually BE the
    # INTEGRATION transition for this exact package -- never a free-form transition
    # to some other phase smuggled through the one wrapper allowed to bypass
    # coord_policy's direct-call denial for `transition ... INTEGRATION`.
    if "INTEGRATION" not in command:
        raise SystemExit("only the INTEGRATION transition is allowed through this wrapper")
    try:
        pkg_flag_index = command.index("--package-id")
    except ValueError:
        raise SystemExit("transition command must explicitly pass --package-id")
    if pkg_flag_index + 1 >= len(command) or command[pkg_flag_index + 1] != package_id:
        raise SystemExit("transition command's --package-id must match the checked package_id")

raise SystemExit(subprocess.run(command, check=False).returncode)
