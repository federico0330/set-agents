#!/usr/bin/env bash
# audit-readonly.sh — Corre el auditor read-only sobre el diff actual y guarda findings.
# Uso: ./ai/scripts/audit-readonly.sh [TASK_ID]
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT"; mkdir -p ai/state
TASK="${1:-current}"
OUT="ai/state/audit-findings.md"
AUDITOR_MODEL="${AUDITOR_MODEL:-opencode-go/deepseek-v4-pro}"

PROMPT="Read-only audit for task ${TASK}. Inspect AGENTS.md, the active spec/tasks/acceptance, the output of \
\`git diff\`, and ai/state/verify.log. Return exactly 'AUDIT_PASS: no concrete findings against the provided \
scope.' or findings using the schema (id, severity, file:line, evidence, impact, minimal_fix, verification). \
Do not edit files."

if command -v opencode >/dev/null 2>&1; then
  opencode run --agent auditor --model "$AUDITOR_MODEL" "$PROMPT" 2>&1 | tee "$OUT"
else
  echo "opencode no encontrado; corré el agente auditor manualmente." | tee "$OUT"
fi
