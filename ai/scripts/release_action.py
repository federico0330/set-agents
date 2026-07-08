#!/usr/bin/env python3
"""Execute one tightly-scoped release command after checking recorded gates."""

import json
import subprocess
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from release_gate import check  # noqa: E402

FORBIDDEN_SYNTAX = re.compile(r"(?:>|>>|<|<<|\|\||&&|;|\|)|`|\$\(")
PROTECTED_BRANCHES = {"main", "master", "release", "develop"}

# Approval actions record the human's explicit "ok" into the STATE file so the
# gate can see it. The agent runs them through this same sanctioned wrapper, so
# no Write capability is needed. They set only the confirmation flags — never the
# gate results — so a human ok can never fake verify/audits/judge.
if len(sys.argv) >= 3 and sys.argv[2] in {"confirm-publish", "confirm-merge"}:
    state_path, action = sys.argv[1], sys.argv[2]
    check(state_path, action)
    path = Path(state_path)
    state = json.loads(path.read_text()) if path.exists() else {}
    state["publish_confirmed" if action == "confirm-publish" else "merge_confirmed"] = True
    path.write_text(json.dumps(state, indent=2) + "\n")
    print(f"RELEASE_{action.upper().replace('-', '_')}_RECORDED")
    raise SystemExit(0)

if "--" not in sys.argv:
    raise SystemExit("release action requires -- COMMAND")
separator = sys.argv.index("--")
action = sys.argv[2]
command = sys.argv[separator + 1:]
check(sys.argv[1], action)

allowed = {
    "commit": [("git", "switch", "-c"), ("git", "add"), ("git", "commit")],
    "publish": [("git", "push"), ("gh", "pr", "create"), ("gh", "pr", "edit")],
    "merge": [("gh", "pr", "merge")],
}
if not command or not any(tuple(command[:len(prefix)]) == prefix for prefix in allowed[action]):
    raise SystemExit("command is not allowed for this release phase")
if any(FORBIDDEN_SYNTAX.search(part) for part in command):
    raise SystemExit("unsafe shell syntax blocked")
blocked = {"--force", "-f", "--admin", "--delete-branch", "--repo", "--mirror", "--delete"}
if blocked.intersection(command):
    raise SystemExit("unsafe release option blocked")
if action == "publish" and command[0:2] == ["git", "push"]:
    if len(command) != 4 or command[2].startswith("-") or command[3].startswith("-") or ":" in command[2] or ":" in command[3]:
        raise SystemExit("publish must be a plain branch push")
    if command[3] in PROTECTED_BRANCHES:
        raise SystemExit("push to a protected branch requires a human; agent auto-push is blocked")
if action == "merge" and "--squash" not in command:
    raise SystemExit("merge must use --squash")

raise SystemExit(subprocess.run(command, check=False).returncode)
