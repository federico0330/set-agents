# 019-harness-evolution · P2-billing-aware-ordering

<!-- notas:auto -->
## Motivo

- objetivo: Ordenamiento consciente del costo (suscripcion/free antes que metered a igual tier) y superficie de consola: --route-doctor, panel y wizard declarando el inventario vivo (ADR-0035)
- complejidad: medium
- riesgo: el sort key es contrato pineado; insertar rank sin mover exclusiones duras
- paths: `docs/adr/0035-billing-aware-ordering.md`, `ai/scripts/setup_models.py`
- depende de: P1-provider-auto-adoption

## Tareas

- [x] PROVIDER_BILLING_KIND completo + billing_rank puro (free por sufijo -free) (completed) · implementer P2: ADR-0035 + billing_rank + --route-doctor + panel/wizard; 831 tests OK (subio de 819), verify.sh VERIFY_PASS, build.sh --check CHECK_PASS+SELF_SCAFFOLD_SYNC_OK, git diff --check limpio
- [x] Insercion en el sort key tras TIER_ORDER y antes de _bias_rank; exclusiones duras intactas (completed) · implementer P2: ADR-0035 + billing_rank + --route-doctor + panel/wizard; 831 tests OK (subio de 819), verify.sh VERIFY_PASS, build.sh --check CHECK_PASS+SELF_SCAFFOLD_SYNC_OK, git diff --check limpio
- [x] Reason code aditivo observable en decisions-v1.jsonl (completed) · implementer P2: ADR-0035 + billing_rank + --route-doctor + panel/wizard; 831 tests OK (subio de 819), verify.sh VERIFY_PASS, build.sh --check CHECK_PASS+SELF_SCAFFOLD_SYNC_OK, git diff --check limpio
- [x] set-agents --route-doctor con probes frescos: auth, modelos, billing, diagnostico de cache (completed) · implementer P2: ADR-0035 + billing_rank + --route-doctor + panel/wizard; 831 tests OK (subio de 819), verify.sh VERIFY_PASS, build.sh --check CHECK_PASS+SELF_SCAFFOLD_SYNC_OK, git diff --check limpio
- [x] Panel de modelos y wizard: proveedores descubiertos rutables, rotulo y politica citando ADR-0034/0035 (completed) · implementer P2: ADR-0035 + billing_rank + --route-doctor + panel/wizard; 831 tests OK (subio de 819), verify.sh VERIFY_PASS, build.sh --check CHECK_PASS+SELF_SCAFFOLD_SYNC_OK, git diff --check limpio

## Hallazgos

- F-01 [high] closed — testing
- F-02 [low] closed — readability
- F-03 [low] closed — correctness

## Recorrido

- review: repair_required (3 hallazgos)
- verificación: 0 refutados, 1 sostenidos
- repair: F-01, F-02, F-03 → 3 archivos
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `unit-suite`: pass

## Spawns

- SPAWN-001 implementer · modelo openai-codex/gpt-5.6-terra · effort high · route run1_7557c4c0d8554e71783d257f1aac30da

context pack: `docs/specs/019-harness-evolution/context/P2-billing-aware-ordering.md`

↩ [[features/019-harness-evolution|019-harness-evolution]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
