#!/usr/bin/env python3
"""Execute one tightly-scoped integration command after checking recorded gates
(docs/adr/0020-*.md). Mirrors release_action.py's shape, with one extra
positional (PACKAGE_ID) since integration authority is package-scoped, never
feature-scoped.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from integration_gate import check  # noqa: E402
from feature_state_lib.model import package_by_id  # noqa: E402

FORBIDDEN_SYNTAX = re.compile(r"(?:>|>>|<|<<|\|\||&&|;|\|)|`|\$\(")
WRAPPER = Path(__file__).resolve()
TRUSTED_FEATURE_STATE = WRAPPER.parent / "feature-state.py"
WRAPPER_WORKTREE = WRAPPER.parent.parent.parent
TRANSITION_VALUE_FLAGS = frozenset({
    "--feature-id", "--package-id", "--reason", "--state-file",
    "--expect-revision", "--actor", "--event-id",
})

if len(sys.argv) < 4 or "--" not in sys.argv:
    raise SystemExit("usage: integration_action.py STATE PACKAGE_ID ACTION -- COMMAND")
state_path, package_id, action = sys.argv[1], sys.argv[2], sys.argv[3]
separator = sys.argv.index("--")
command = sys.argv[separator + 1:]
check(state_path, package_id, action)

try:
    canonical_state = Path(state_path).resolve()
except OSError:
    raise SystemExit("state path is not canonical")


def _feature_state_script_allowed(script: str) -> bool:
    if script == "ai/scripts/feature-state.py":
        try:
            cwd = Path.cwd().resolve()
            sibling = (cwd / "ai/scripts/feature-state.py").resolve()
        except OSError:
            return False
        return cwd == WRAPPER_WORKTREE.resolve() and sibling == TRUSTED_FEATURE_STATE.resolve()
    try:
        return Path(script).resolve() == TRUSTED_FEATURE_STATE.resolve()
    except OSError:
        return False


def _state_file_tokens(cmd: list[str]) -> list[str]:
    tokens: list[str] = []
    idx = 0
    while idx < len(cmd):
        if cmd[idx] == "--state-file":
            if idx + 1 >= len(cmd):
                return tokens
            tokens.append(cmd[idx + 1])
            idx += 2
            continue
        idx += 1
    return tokens


def _state_file_matches(cmd: list[str]) -> bool:
    tokens = _state_file_tokens(cmd)
    if len(tokens) != 1:
        return False
    try:
        return Path(tokens[0]).resolve() == canonical_state
    except OSError:
        return False


def _transition_to_phase(cmd: list[str]) -> str | None:
    if len(cmd) < 3 or cmd[2] != "transition":
        return None
    idx = 3
    while idx < len(cmd):
        token = cmd[idx]
        if token.startswith("--"):
            if token not in TRANSITION_VALUE_FLAGS:
                return None
            if idx + 1 >= len(cmd):
                return None
            if cmd[idx + 1] == "INTEGRATION":
                return None
            idx += 2
            continue
        return token
    return None


allowed_actions = {
    "freeze-candidate": [("python3", "ai/scripts/feature-state.py", "freeze-candidate")],
    "record-receipt": [("python3", "ai/scripts/feature-state.py", "record-receipt")],
    "transition": [("python3", "ai/scripts/feature-state.py", "transition")],
}
if not command or command[0] != "python3" or len(command) < 3:
    raise SystemExit("command is not allowed for this integration action")
if not _feature_state_script_allowed(command[1]):
    raise SystemExit("command is not allowed for this integration action")
if command[2] != allowed_actions[action][0][2]:
    raise SystemExit("command is not allowed for this integration action")
if not _state_file_matches(command):
    raise SystemExit("command --state-file must match wrapper STATE exactly")
if any(FORBIDDEN_SYNTAX.search(part) for part in command):
    raise SystemExit("unsafe shell syntax blocked")

if action in {"freeze-candidate", "record-receipt"}:
    # These take package_id as their first positional (argv[3] of the underlying
    # command) -- must match the package this wrapper's Bash-layer check named,
    # never a different one smuggled into the command past the gate check.
    if len(command) < 4 or command[3] != package_id:
        raise SystemExit(f"{action} command must target the checked package_id as its first positional")
    if action == "freeze-candidate":
        try:
            data = json.loads(canonical_state.read_text(encoding="utf-8"))
            package = package_by_id(data, package_id)
        except Exception as exc:
            raise SystemExit(f"cannot inspect package for HCE guard: {exc}") from exc
        if package.get("convergence_exception"):
            raise SystemExit("HCE parent forbids freeze-candidate through integration wrapper")
if action == "transition":
    to_phase = _transition_to_phase(command)
    if to_phase != "INTEGRATION":
        raise SystemExit("only the INTEGRATION transition is allowed through this wrapper")
    try:
        pkg_flag_index = command.index("--package-id")
    except ValueError:
        raise SystemExit("transition command must explicitly pass --package-id")
    if pkg_flag_index + 1 >= len(command) or command[pkg_flag_index + 1] != package_id:
        raise SystemExit("transition command's --package-id must match the checked package_id")

raise SystemExit(subprocess.run(command, check=False).returncode)
