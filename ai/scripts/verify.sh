#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

./build.sh --check
python3 -m unittest discover -s tests -v
python3 -m py_compile ai/scripts/*.py tests/*.py
git diff --check

STAGING="$(mktemp -d "${TMPDIR:-/tmp}/set-agentes-verify.XXXXXX")"
trap 'rm -rf "$STAGING"' EXIT
./build.sh --output "$STAGING" >/dev/null
for harness in opencode claude-code codex; do
  diff -ruN "Global/$harness" "$STAGING/$harness"
done
echo "VERIFY_PASS"
