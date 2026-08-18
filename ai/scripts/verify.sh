#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

./build.sh --check
# ADR-0047: a fresh clone has no ai/state/ at all; seed it so tests that
# assert canonical harness decisions (e.g. decisions-log.jsonl) find their
# data.  On a machine with real history this is a no-op (seed refuses to
# overwrite an existing ai/state/).
python3 ai/scripts/seed-state.py "$ROOT" >/dev/null
# The guest portability regression already exercises scaffold, install, and
# routing before it calls this script.  Re-running the whole suite from that
# copied checkout exceeds the bounded E2E budget without adding coverage; run
# the portable script/build checks there instead.  Normal verification always
# retains the complete suite.
if [[ "${SET_AGENTS_GUEST_VERIFY:-}" == "1" ]]; then
  python3 -m unittest -v \
    tests.test_harness.HarnessTests.test_check_and_native_codex_agents \
    tests.test_harness.HarnessTests.test_shell_scripts_parse
else
  python3 "$ROOT/ai/scripts/verify_reporter.py"  # python3 -m unittest discover -s tests -v
fi
python3 -m py_compile ai/scripts/*.py ai/scripts/routing_core/*.py ai/scripts/feature_state_lib/*.py \
  PROYECTO/ai/scripts/feature_state_lib/*.py tests/*.py
git diff --check

STAGING="$(mktemp -d "${TMPDIR:-/tmp}/set-agentes-verify.XXXXXX")"
trap 'rm -rf "$STAGING"' EXIT
./build.sh --output "$STAGING" >/dev/null
for harness in opencode claude-code codex pi cursor; do
  diff -ruN "Global/$harness" "$STAGING/$harness"
done
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1])
global_root = root / "Global"
legacy = {
    "_canonical/opencode-agents/package-gate-runner.md",
    "opencode/agents/package-gate-runner.md",
}
for path in global_root.rglob("*"):
    if not path.is_file():
        continue
    raw = path.read_bytes()
    rel = str(path.relative_to(global_root))
    if b"ai/scripts/set_agents_app.py" in raw:
        if b"__SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py" not in raw:
            raise SystemExit(f"GLOBAL_PLACEHOLDER_MISSING file={rel}")
        if raw.count(b"ai/scripts/set_agents_app.py") != raw.count(b"__SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py"):
            raise SystemExit(f"GLOBAL_BARE_APP_CLI file={rel}")
    if str(root).encode() in raw:
        raise SystemExit(f"GLOBAL_BUILDER_PATH file={rel}")
    if (b"/home/" in raw or b"/Users/" in raw) and rel not in legacy:
        raise SystemExit(f"GLOBAL_ABSOLUTE_PATH_RATCHET file={rel}")
print("GLOBAL_PORTABILITY_OK")
PY
# Lives in its own script rather than a heredoc so a test can drive it against a
# fixture tree: a guard whose failing path nothing exercises decays unnoticed.
python3 "$ROOT/ai/scripts/check-canonical-paths.py" "$ROOT"
# The only enforcement point the whole world sees: CI runs this on Linux and macOS,
# a fresh clone runs this, a guest runs this.  A pre-commit hook would block sooner
# and be invisible to all three, because .git/hooks is not versioned.
python3 "$ROOT/ai/scripts/check-feature-state.py" "$ROOT"
echo "VERIFY_PASS"
