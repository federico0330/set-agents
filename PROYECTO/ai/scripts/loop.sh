#!/usr/bin/env bash
# loop.sh — Loop controlado: implement → verify → audit → repair → re-verify, con cortes duros.
# Uso: ./ai/scripts/loop.sh <TASK_ID> [MAX_ITER]
# Cortes: MAX_ITER, mismo estado repetido (hash), HUMAN_DECISION_REQUIRED, audit+verify PASS.
set -uo pipefail

TASK_ID="${1:?Uso: ai/scripts/loop.sh <TASK_ID> [MAX_ITER]}"
MAX_ITER="${2:-4}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT"; mkdir -p ai/state

# Modelos (OpenCode por defecto; baratos para implementar, capaces para auditar)
IMPL_MODEL="${IMPL_MODEL:-opencode/deepseek-v4-flash-free}"
AUDIT_MODEL="${AUDIT_MODEL:-opencode-go/deepseek-v4-pro}"
DEBUG_MODEL="${DEBUG_MODEL:-opencode-go/kimi-k2.7-code}"
SCRIBE_MODEL="${SCRIBE_MODEL:-opencode/north-mini-code-free}"

PREV_HASH=""
state_hash() { { cat ai/state/verify.log ai/state/audit-findings.md 2>/dev/null; } | sha256sum | awk '{print $1}'; }
human_stop() {
  if rg -l "HUMAN_DECISION_REQUIRED" ai/state docs/specs 2>/dev/null | grep -q .; then
    echo "⛔ Loop detenido: se requiere decisión humana."; exit 2
  fi
}
run_oc() { command -v opencode >/dev/null 2>&1 && opencode run --agent "$1" --model "$2" "$3"; }

for ITER in $(seq 1 "$MAX_ITER"); do
  echo "===== ITERACIÓN $ITER/$MAX_ITER — $TASK_ID ====="

  run_oc implementer "$IMPL_MODEL" "Implement task ${TASK_ID}. Read AGENTS.md and docs/specs. Use
safe-implementation + TDD. Smallest diff only. Do NOT audit your own work." | tee "ai/state/impl-${TASK_ID}-${ITER}.log"
  human_stop

  if ./ai/scripts/verify.sh; then VERIFY_OK=1; else VERIFY_OK=0; fi
  if [ "$VERIFY_OK" -eq 0 ]; then
    run_oc debugger "$DEBUG_MODEL" "Debug the failure for ${TASK_ID}. Read ai/state/verify.log. Fix the root
cause minimally. Stop with HUMAN_DECISION_REQUIRED if it repeats or is ambiguous." | tee "ai/state/debug-${TASK_ID}-${ITER}.log"
  fi

  run_oc auditor "$AUDIT_MODEL" "Read-only audit for ${TASK_ID}. Inspect AGENTS.md, spec/tasks/acceptance,
git diff, ai/state/verify.log. Return AUDIT_PASS or concrete findings only." | tee ai/state/audit-findings.md
  human_stop

  if grep -q "AUDIT_PASS" ai/state/audit-findings.md && grep -q "VERIFY_PASS" ai/state/verify.log; then
    run_oc memory-scribe "$SCRIBE_MODEL" "Save durable memory for verified task ${TASK_ID}: decisions, files,
verification, gotchas. No secrets, no raw logs." || true
    echo "✅ LOOP_PASS: ${TASK_ID} verificado y auditado."; exit 0
  fi

  CUR_HASH="$(state_hash)"
  if [ "$CUR_HASH" = "$PREV_HASH" ]; then
    echo "⛔ Loop detenido: mismo estado de falla/audit repetido."
    run_oc memory-scribe "$SCRIBE_MODEL" "Save memory: ${TASK_ID} loop stalled (estado repetido). Resumir falla
estable y archivos. No secrets." || true
    exit 3
  fi
  PREV_HASH="$CUR_HASH"

  run_oc implementer "$IMPL_MODEL" "Repair ONLY the concrete findings in ai/state/audit-findings.md for
${TASK_ID}. Use repair-loop. Do not change acceptance criteria or weaken tests. Minimal patch." | tee "ai/state/repair-${TASK_ID}-${ITER}.log"
done

echo "⛔ Loop detenido: MAX_ITER alcanzado sin converger."; exit 4
