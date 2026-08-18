#!/usr/bin/env python3
"""Pure policy gate used by github-release-manager before mutations."""

import json
import sys
from pathlib import Path


def fail(message):
    print(message, file=sys.stderr)
    raise SystemExit(2)


# Which auditors MUST have run for each touched surface. Ties JUDGE_PASS to real coverage
# instead of trusting a single free-text audits="pass" attestation.
SURFACE_AUDITORS = {
    "auth": {"security-auditor"},
    "money": {"security-auditor", "package-reviewer"},
    "pii": {"security-auditor"},
    "data": {"package-reviewer"},
    "ui": {"ux-ui-designer"},
}


def check_coverage(state):
    """Deterministic audit-coverage gate: every touched surface must have its mandatory auditors recorded."""
    surfaces = state.get("surfaces")
    if surfaces is None:
        fail("release blocked: audit surface coverage not declared (state.surfaces missing)")
    ran = set(state.get("audits_ran") or [])
    if "package-reviewer" not in ran:
        fail("release blocked: base reviewer did not run (audits_ran missing 'package-reviewer')")
    for surface in surfaces:
        missing = SURFACE_AUDITORS.get(surface, set()) - ran
        if missing:
            fail(f"release blocked: surface '{surface}' requires {sorted(missing)} which did not run")


def check(state_path, action):
    if action not in {"commit", "publish", "merge", "confirm-publish", "confirm-merge"}:
        fail("invalid release action")
    if action in {"confirm-publish", "confirm-merge"}:
        # Recording the human's explicit approval. The publish/merge gate below
        # still independently enforces green verify/audits/judge, so an approval
        # can never substitute for a real gate result.
        return True
    state = json.loads(Path(state_path).read_text(encoding="utf-8"))
    if (state.get("verify"), state.get("audits"), state.get("judge")) != ("pass", "pass", "JUDGE_PASS"):
        fail("release blocked: local gates are not green")
    check_coverage(state)
    if action in {"publish", "merge"} and state.get("publish_confirmed") is not True:
        fail("release blocked: publication confirmation required")
    if action == "merge" and (state.get("remote_checks") != "pass" or state.get("merge_confirmed") is not True):
        fail("release blocked: green remote checks and merge confirmation required")
    return True


if __name__ == "__main__":
    if len(sys.argv) != 3:
        fail("usage: release_gate.py STATE.json commit|publish|merge")
    check(sys.argv[1], sys.argv[2])
    print(f"RELEASE_{sys.argv[2].upper()}_ALLOWED")
