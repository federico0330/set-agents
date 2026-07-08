#!/usr/bin/env bash
# loop.sh — Autonomous spine: SDD → implement⇄audit loop → regression tests → verify → [panel] → judge → E2E → memory.
# Uso: ./ai/scripts/loop.sh <TASK_ID> [MAX_ITER]
# Cortes duros (anti-bucle): timeout por paso, MAX_ITER, mismo estado repetido (hash),
#   HUMAN_DECISION_REQUIRED, y (AUDIT_PASS + VERIFY_PASS + panel + JUDGE_PASS + RUNTIME_PASS).
# El "ímpetu" y el orden SDD/implementar⇄auditar los pone ESTE script — no la fuerza de voluntad del modelo.
# Los tests NO son guardarraíl: un test verde no prueba correctitud. El guardarraíl es el auditor read-only
# contra spec/diseño/acceptance. Los tests de regresión se escriben AL FINAL, cuando el auditor ya dio AUDIT_PASS.
# Rigor alineado con el orquestador interactivo: si la spec toca superficie sensible (auth/plata/PII) la
#   implementación va a un modelo HOSTED (no el leaf local) y corre el panel de seguridad (security-auditor +
#   red-team, y db/performance si toca datos) ANTES del judge.
set -uo pipefail

TASK_ID="${1:?Uso: ai/scripts/loop.sh <TASK_ID> [MAX_ITER]}"
MAX_ITER="${2:-3}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT"; mkdir -p ai/state
SPEC_DIR="docs/specs/${TASK_ID}"

# Timeout por paso (segundos). Mata el cuelgue de un modelo que "no para de pensar".
STEP_TIMEOUT="${STEP_TIMEOUT:-600}"
SCRIBE_TIMEOUT="${SCRIBE_TIMEOUT:-120}"
# Modelo hosted para lógica dura (override del leaf local en tareas sensibles).
HOSTED_IMPL_MODEL="${HOSTED_IMPL_MODEL:-openai/gpt-5.4}"

# ── Reset de estado transitorio ───────────────────────────────────────────────────────────────
# Un HUMAN_DECISION_REQUIRED o findings viejos de una corrida anterior NO deben envenenar esta.
# Las specs durables en docs/specs quedan intactas.
rm -f ai/state/verify.log ai/state/audit-findings.md ai/state/judge.md \
      ai/state/audit-security.md ai/state/audit-redteam.md ai/state/audit-db.md ai/state/audit-perf.md \
      "ai/state/tests-${TASK_ID}.log" "ai/state/regr-${TASK_ID}.done" ai/state/impl-"${TASK_ID}"-*.log \
      ai/state/repair-"${TASK_ID}"-*.log \
      ai/state/debug-"${TASK_ID}"-*.log "ai/state/e2e-${TASK_ID}.log" 2>/dev/null || true

# Corre un agente con SU modelo de perfil, o con un modelo forzado (4º arg), y con timeout duro.
run_oc() {
  local agent="$1" prompt="$2" tmo="${3:-$STEP_TIMEOUT}" model="${4:-}" rc
  if ! command -v opencode >/dev/null 2>&1; then echo "⛔ opencode CLI no encontrado."; return 127; fi
  if [ -n "$model" ]; then
    timeout "$tmo" opencode run --agent "$agent" --model "$model" "$prompt"; rc=$?
  else
    timeout "$tmo" opencode run --agent "$agent" "$prompt"; rc=$?
  fi
  if [ "$rc" -eq 124 ]; then echo "⏱️  ${agent} excedió ${tmo}s — paso cortado por timeout (anti-cuelgue)."; fi
  return $rc
}

# Corte por decisión humana: SOLO mira los artefactos de ESTA tarea + los compartidos de esta corrida +
# la spec de esta tarea. Logs viejos de OTRAS tareas no lo disparan (evita contaminación cruzada).
human_stop() {
  if rg -l "HUMAN_DECISION_REQUIRED" \
       "$SPEC_DIR" ai/state/verify.log ai/state/audit-findings.md ai/state/judge.md \
       ai/state/*"${TASK_ID}"* 2>/dev/null | grep -q .; then
    echo "⛔ Loop detenido: se requiere decisión humana."; exit 2
  fi
}
state_hash() { { cat ai/state/verify.log ai/state/audit-findings.md 2>/dev/null; } | sha256sum | awk '{print $1}'; }

# Veredicto ESTRICTO: el token debe ser la última línea NO vacía (no una mención suelta en prosa) y sin
# *_FAIL en esa línea. Fail-closed: si no hay línea de veredicto → falla. Cierra el agujero del grep de substring.
verdict_pass() { # <file> <PASS_TOKEN> <FAIL_TOKEN>
  local last; last="$(grep -v '^[[:space:]]*$' "$1" 2>/dev/null | tail -n1)"
  case "$last" in
    *"$3"*) return 1 ;;   # FAIL explícito en la última línea
    *"$2"*) return 0 ;;   # PASS explícito en la última línea
    *)      return 1 ;;   # sin veredicto → fail-closed
  esac
}
VERDICT_RULE="End your ENTIRE output with a FINAL line that is EXACTLY the verdict token and nothing after it."

# ── SDD gate: no se implementa sin spec/tasks/acceptance reales (no se inventan) ──────────────
if [ ! -f "$SPEC_DIR/spec.md" ] || [ ! -f "$SPEC_DIR/tasks.md" ] || [ ! -f "$SPEC_DIR/acceptance.md" ]; then
  echo "⛔ SDD gate: falta $SPEC_DIR/{spec,tasks,acceptance}.md."
  echo "   Delegá la spec a product-analyst (interactivo) antes de correr el loop. No se fabrica una spec vacía."
  exit 2
fi

# ── Sensibilidad de la superficie: dispara implementación HOSTED + panel de seguridad/datos ────
SENSITIVE=0; DATA=0
if rg -qiE '(auth|login|logout|password|contrase|token|session|jwt|oauth|credential|payment|pago|money|dinero|saldo|precio|\bprice\b|billing|checkout|invoice|\bpii\b|personal data|datos personales)' "$SPEC_DIR" 2>/dev/null; then SENSITIVE=1; fi
if rg -qiE '(migration|migrac|schema|transaction|transacc|concurren|optimistic|\bsql\b|\bquery\b|\bindex\b|rowversion)' "$SPEC_DIR" 2>/dev/null; then DATA=1; fi
IMPL_MODEL=""
if [ "$SENSITIVE" -eq 1 ]; then IMPL_MODEL="$HOSTED_IMPL_MODEL"; echo "🔒 Superficie sensible → implementación HOSTED (${HOSTED_IMPL_MODEL}) + panel de seguridad antes del judge."; fi
[ "$DATA" -eq 1 ] && echo "🗄️  Superficie de datos → db-auditor + performance-auditor antes del judge."

# Panel de seguridad/datos antes del judge (alinea el loop autónomo con el contrato del orquestador interactivo).
# Escribe el output de cada auditor; agrega los que FALLAN a audit-findings.md. Devuelve 0 si TODO pasa.
run_panel() {
  local ok=1
  if [ "$SENSITIVE" -eq 1 ]; then
    run_oc security-auditor "Read-only security audit for ${TASK_ID} (authz/object-level access, input validation, secrets, PII, tenant scoping). Inspect ${SPEC_DIR}, git diff. Concrete blocking problems only, binary. ${VERDICT_RULE} 'AUDIT_PASS' or 'AUDIT_FAIL'." | tee ai/state/audit-security.md
    verdict_pass ai/state/audit-security.md AUDIT_PASS AUDIT_FAIL || { ok=0; cat ai/state/audit-security.md >> ai/state/audit-findings.md; }
    human_stop
    run_oc red-team "Authorized read-only offensive review for ${TASK_ID} (authz bypass/IDOR, parameter tampering, injection, race conditions, token replay, mass assignment). Inspect ${SPEC_DIR}, git diff. Concrete exploitable problems only. ${VERDICT_RULE} 'AUDIT_PASS' or 'AUDIT_FAIL'." | tee ai/state/audit-redteam.md
    verdict_pass ai/state/audit-redteam.md AUDIT_PASS AUDIT_FAIL || { ok=0; cat ai/state/audit-redteam.md >> ai/state/audit-findings.md; }
    human_stop
  fi
  if [ "$DATA" -eq 1 ]; then
    run_oc db-auditor "Read-only data-integrity audit for ${TASK_ID} (atomic transactions, optimistic concurrency that actually fires, validate-before-mutate, money types, safe migrations, audited failed attempts). Inspect ${SPEC_DIR}, git diff. ${VERDICT_RULE} 'AUDIT_PASS' or 'AUDIT_FAIL'." | tee ai/state/audit-db.md
    verdict_pass ai/state/audit-db.md AUDIT_PASS AUDIT_FAIL || { ok=0; cat ai/state/audit-db.md >> ai/state/audit-findings.md; }
    human_stop
    run_oc performance-auditor "Read-only scalability audit for ${TASK_ID} (pagination in SQL not memory, no N+1, column projection, indexes on filters, bounded work). Inspect ${SPEC_DIR}, git diff. ${VERDICT_RULE} 'AUDIT_PASS' or 'AUDIT_FAIL'." | tee ai/state/audit-perf.md
    verdict_pass ai/state/audit-perf.md AUDIT_PASS AUDIT_FAIL || { ok=0; cat ai/state/audit-perf.md >> ai/state/audit-findings.md; }
    human_stop
  fi
  [ "$ok" -eq 1 ]
}

# ── Sin gate de tests-antes-de-implementar: el guardarraíl es el auditor, no un test verde. ────
# Los tests de regresión se escriben recién cuando el loop implementar⇄auditar convergió (AUDIT_PASS), más abajo.

PREV_HASH=""
for ITER in $(seq 1 "$MAX_ITER"); do
  echo "===== ITERACIÓN $ITER/$MAX_ITER — $TASK_ID ====="

  if [ "$ITER" -eq 1 ]; then
    run_oc implementer "Implement task ${TASK_ID} to satisfy ${SPEC_DIR}/acceptance.md and the design. Read
AGENTS.md and ${SPEC_DIR}. safe-implementation + smallest diff. There are no tests to make pass — you are audited
against the spec/design right after. Do NOT audit your own work." \
      "$STEP_TIMEOUT" "$IMPL_MODEL" | tee "ai/state/impl-${TASK_ID}-${ITER}.log"
  else
    run_oc implementer "Repair ONLY the concrete findings in ai/state/audit-findings.md for ${TASK_ID}.
repair-loop. Do not change acceptance criteria or weaken tests. Minimal patch." \
      "$STEP_TIMEOUT" "$IMPL_MODEL" | tee "ai/state/repair-${TASK_ID}-${ITER}.log"
  fi
  human_stop

  if ./ai/scripts/verify.sh > ai/state/verify.log 2>&1; then VERIFY_OK=1; else VERIFY_OK=0; fi
  if [ "$VERIFY_OK" -eq 0 ]; then
    run_oc debugger "Debug the failure for ${TASK_ID}. Read ai/state/verify.log. Fix the root cause minimally.
Stop with HUMAN_DECISION_REQUIRED if it repeats or is ambiguous." | tee "ai/state/debug-${TASK_ID}-${ITER}.log"
    human_stop
    ./ai/scripts/verify.sh > ai/state/verify.log 2>&1 && VERIFY_OK=1 || VERIFY_OK=0
  fi

  run_oc auditor "Read-only audit for ${TASK_ID}. Inspect AGENTS.md, ${SPEC_DIR}, git diff, ai/state/verify.log.
You are the GUARDRAIL: judge the implementation against the spec/design/acceptance (does it actually return what
the spec expects?) — NOT against a test suite. Check scope AND SOLID/clean-architecture best practices (a
best-practices violation is blocking). Binary, no severity. ${VERDICT_RULE} 'AUDIT_PASS' or 'AUDIT_FAIL'." | tee ai/state/audit-findings.md
  human_stop

  if verdict_pass ai/state/audit-findings.md AUDIT_PASS AUDIT_FAIL && [ "$VERIFY_OK" -eq 1 ]; then
    # ── Convergió: el auditor confirma que la implementación cumple el diseño. RECIÉN AHORA, tests de
    #    regresión (no antes, no como gate de implementación). Se escriben una sola vez por corrida. ──
    if [ ! -f "ai/state/regr-${TASK_ID}.done" ]; then
      echo "===== REGRESSION TESTS — $TASK_ID ====="
      run_oc test-writer "The implement⇄audit loop for ${TASK_ID} converged (AUDIT_PASS). Write regression tests
from ${SPEC_DIR}/acceptance.md that PROVE the already-correct behavior. Use the regression-tests skill. Assert the
real expected values from the spec, never weaken. Do NOT modify production code." | tee "ai/state/tests-${TASK_ID}.log"
      touch "ai/state/regr-${TASK_ID}.done"
      human_stop
      if ./ai/scripts/verify.sh > ai/state/verify.log 2>&1; then VERIFY_OK=1; else VERIFY_OK=0; fi
      if [ "$VERIFY_OK" -eq 0 ]; then
        echo "↩️  Los tests de regresión fallan — regresión real detectada, a reparar."
        cp ai/state/verify.log ai/state/audit-findings.md
      fi
    fi
    # ── Panel de seguridad/datos (si aplica) ANTES del judge — sólo si los tests de regresión pasan ──
    if [ "$VERIFY_OK" -eq 1 ] && run_panel; then
      # ── Final gate 1: adversarial judge (mandatory) ──
      run_oc adversarial-judge "Judge the complete evidence for ${TASK_ID}: ${SPEC_DIR}, git diff, tests,
ai/state/verify.log, ai/state/audit-findings.md, and (if present) ai/state/audit-{security,redteam,db,perf}.md.
${VERDICT_RULE} 'JUDGE_PASS' or 'JUDGE_FAIL'." | tee ai/state/judge.md
      human_stop
      if ! verdict_pass ai/state/judge.md JUDGE_PASS JUDGE_FAIL; then
        cp ai/state/judge.md ai/state/audit-findings.md   # route judge findings into the repair loop
        echo "↩️  Judge devolvió problemas — a reparar."
      else
        # ── Final gate 2: E2E runtime (si el proyecto tiene run.sh + e2e.sh) ──
        if [ -x ./ai/scripts/e2e.sh ] && [ -f ./ai/scripts/run.sh ]; then
          echo "===== E2E — $TASK_ID ====="
          if ./ai/scripts/e2e.sh "$TASK_ID" | tee ai/state/e2e-${TASK_ID}.log; then
            RUNTIME_OK=$(grep -q "RUNTIME_PASS" ai/state/e2e-${TASK_ID}.log && echo 1 || echo 0)
          else RUNTIME_OK=0; fi
          human_stop
          if [ "$RUNTIME_OK" -eq 0 ]; then
            cp ai/state/e2e-${TASK_ID}.log ai/state/audit-findings.md
            echo "↩️  E2E encontró problemas de runtime — a reparar."
          else
            run_oc memory-scribe "Save durable memory for verified task ${TASK_ID}: decisions, files, verification,
E2E result, gotchas. No secrets, no raw logs." "$SCRIBE_TIMEOUT" || true
            echo "✅ LOOP_PASS: ${TASK_ID} verificado, auditado, juzgado y probado en runtime."; exit 0
          fi
        else
          echo "ℹ️  E2E salteado (falta run.sh/e2e.sh — el proyecto no define arranque)."
          run_oc memory-scribe "Save durable memory for verified task ${TASK_ID}: decisions, files, verification,
gotchas. No secrets, no raw logs." "$SCRIBE_TIMEOUT" || true
          echo "✅ LOOP_PASS: ${TASK_ID} verificado, auditado y juzgado (sin E2E)."; exit 0
        fi
      fi
    else
      echo "↩️  Tests de regresión o panel (seguridad/datos) encontraron problemas — a reparar."
      # los findings ya quedaron en ai/state/audit-findings.md (regresión: cp verify.log; panel: run_panel)
    fi
  fi

  # ── Corte anti-bucle: mismo estado de falla/audit dos veces seguidas ──
  CUR_HASH="$(state_hash)"
  if [ "$CUR_HASH" = "$PREV_HASH" ]; then
    echo "⛔ Loop detenido: mismo estado de falla/audit repetido (no converge)."
    run_oc memory-scribe "Save memory: ${TASK_ID} loop stalled (estado repetido). Resumir falla estable y
archivos. No secrets." "$SCRIBE_TIMEOUT" || true
    exit 3
  fi
  PREV_HASH="$CUR_HASH"
done

echo "⛔ Loop detenido: MAX_ITER (${MAX_ITER}) alcanzado sin converger. Requiere decisión humana."; exit 4
