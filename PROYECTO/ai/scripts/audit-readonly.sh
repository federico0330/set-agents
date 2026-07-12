#!/usr/bin/env bash
# audit-readonly.sh — Corre una revisión read-only sobre el paquete actual y guarda findings.
# Uso: ./ai/scripts/audit-readonly.sh [FEATURE_ID|PACKAGE_ID|scope]
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT"; mkdir -p ai/state
SCOPE="${1:-current-package}"
OUT="ai/state/audit-findings.md"
AUDITOR_MODEL="${AUDITOR_MODEL:-openai/gpt-5.6-sol}"

PROMPT="Read-only PACKAGE review for ${SCOPE}. Inspect AGENTS.md, the approved spec/acceptance, package state \
under ai/state/features when present, the output of \`git diff\`, and ai/state/verify.log. Do not edit files. \
Return a consolidated package verdict: pass, repair_required, or blocked. Findings must include id, severity, \
category, acceptance_criterion, file/line, evidence, reproduction, required_outcome, and suggested_scope."

if command -v opencode >/dev/null 2>&1; then
  opencode run --agent package-reviewer --model "$AUDITOR_MODEL" "$PROMPT" 2>&1 | tee "$OUT"
else
  echo "opencode no encontrado; corré el agente auditor manualmente." | tee "$OUT"
fi
