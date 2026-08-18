#!/usr/bin/env python3
"""Pure policy gate used before a package's INTEGRATION transition (docs/adr/0020-*.md).

Mirrors release_gate.py's shape and role exactly: a pure function the wrapper
(integration_action.py) calls before running anything real. `freeze-candidate`/
`record-receipt` are narrowed to this wrapper for Bash-surface reasons, but their
own correctness is already enforced by the CLI commands themselves (phase guards,
package_accept_ready, live re-derivation inside record-receipt) -- this gate does
not duplicate that logic. `transition` is the one action this gate actually checks
against, via the same `integration_ready` the state machine itself now requires.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from feature_state_lib.model import StateError, package_by_id  # noqa: E402
from feature_state_lib.candidate_identity import integration_ready  # noqa: E402


def fail(message):
    print(message, file=sys.stderr)
    raise SystemExit(2)


def check(state_path, package_id, action):
    if action not in {"freeze-candidate", "record-receipt", "transition"}:
        fail("invalid integration action")
    if action in {"freeze-candidate", "record-receipt"}:
        return True
    try:
        data = json.loads(Path(state_path).read_text(encoding="utf-8"))
        package = package_by_id(data, package_id)
    except (OSError, json.JSONDecodeError, StateError) as exc:
        fail(f"integration blocked: cannot read package state: {exc}")
    errors = integration_ready(package)
    if errors:
        fail("integration blocked: " + "; ".join(errors))
    return True


if __name__ == "__main__":
    if len(sys.argv) != 4:
        fail("usage: integration_gate.py STATE.json PACKAGE_ID freeze-candidate|record-receipt|transition")
    check(sys.argv[1], sys.argv[2], sys.argv[3])
    print("INTEGRATION_ALLOWED")
