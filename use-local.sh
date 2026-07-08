#!/usr/bin/env bash
# Switch to the `local` profile: hosted judgment roles use openai/* directly instead of the
# go-zen/zen routers. Code-writing and mechanical roles run on cheap hosted models here too
# (openai/gpt-5.4-mini) — Ollama is NOT the default in any profile (it proved too slow and
# unreliable on CPU); it remains only as a manual opt-in fallback if you edit a cell in roles.tsv.
# Judgment, audit, judge, test-writer (end-stage regression net) and vision roles stay on capable models everywhere.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
printf 'local\n' > "$ROOT/active-profile"
exec "$ROOT/build.sh" --install "$@"
