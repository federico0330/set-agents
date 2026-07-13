#!/usr/bin/env bash
# e2e.sh — Runtime E2E gate: launch app → enable browser MCP → run runtime-verifier → ALWAYS clean up.
# Uso: ./ai/scripts/e2e.sh <TASK_ID> [playwright|brave-cdp|auto]
# Excepción MCP: prende el browser MCP SOLO durante el gate y lo apaga en el trap EXIT.
set -uo pipefail

TASK_ID="${1:?Uso: ai/scripts/e2e.sh <TASK_ID>}"
BROWSER_MODE="${2:-${BROWSER_MODE:-auto}}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT"; mkdir -p ai/state
E2E_TIMEOUT="${E2E_TIMEOUT:-600}"

cleanup() {
  ./ai/scripts/mcp.sh off playwright >/dev/null 2>&1 || true
  ./ai/scripts/mcp.sh off brave-cdp >/dev/null 2>&1 || true
  ./ai/scripts/run.sh down          >/dev/null 2>&1 || true
}
trap cleanup EXIT

if ! command -v opencode >/dev/null 2>&1; then echo "⛔ E2E: opencode CLI no encontrado."; exit 127; fi
if [ ! -f ./ai/scripts/run.sh ]; then echo "⛔ E2E: falta ai/scripts/run.sh — el proyecto no define arranque."; exit 2; fi

# 1. Levantar backend + frontend.
if ! ./ai/scripts/run.sh up; then echo "⛔ E2E: run.sh up falló — no hay app que probar."; exit 2; fi

# 2. Prender el browser MCP solo para este gate (se apaga en cleanup pase lo que pase).
if [ -x ./ai/scripts/mcp.sh ]; then
  ./ai/scripts/mcp.sh browser-gate "$BROWSER_MODE" || { echo "⛔ E2E: no pude habilitar un browser MCP."; exit 2; }
else
  echo "⛔ E2E: falta ai/scripts/mcp.sh para gestionar el MCP."; exit 2
fi

# 3. Probar la app corriendo con el runtime-verifier (usa su modelo de perfil; timeout duro anti-cuelgue).
timeout "$E2E_TIMEOUT" opencode run --agent runtime-verifier \
  "Verify task ${TASK_ID} in the RUNNING app. Read docs/specs/${TASK_ID}/acceptance.md. Drive the UI via the
available browser MCP (${BROWSER_MODE}), read screenshots, and check endpoint status codes (e.g. 200 vs 409). Exercise only the flows the
task names. Return RUNTIME_PASS or concrete problems (where / expected vs actual / evidence)."
rc=$?
[ "$rc" -eq 124 ] && echo "⏱️  runtime-verifier excedió ${E2E_TIMEOUT}s — E2E cortado por timeout."
exit $rc
