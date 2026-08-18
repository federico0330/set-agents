# 031-registro-correctivo · P1-verbos-correctivos

<!-- notas:auto -->
## Motivo

- objetivo: Implementar reopen --from-done y amend-package en feature-state.py
- ruteo: cambio quirúrgico en un solo módulo Python → implementer (claude-sonnet-4.6)
- complejidad: small
- paths: `ai/scripts/feature_state_lib/cli_lifecycle.py`, `PROYECTO/ai/scripts/feature_state_lib/cli_lifecycle.py`, `ai/scripts/feature-state.py`, `PROYECTO/ai/scripts/feature-state.py`

## Tareas

- [x] extend-reopen (completed) · tests verdes: AC-01 AC-02 AC-03 reopen-from-done todos pasan
- [x] add-amend-package (completed) · tests verdes: AC-07 AC-08 AC-10 amend-package todos pasan
- [x] register-subparsers (completed) · amend-package y --from-done registrados en feature-state.py argparse
- [x] build-mirror (completed) · ./build.sh --check: SELF_SCAFFOLD_SYNC_OK GLOBAL_TREE_SYNC_OK BUILD_CHECK_PASS
- [x] tests-bite (completed) · 6 tests 031 verdes; suite completa 1266 tests OK skipped=4; VERIFY_PASS

## Recorrido

- review: pass (0 hallazgos)
- testing: pass
- runtime QA: pass
- gate `verify`: pass

## Spawns

- SPAWN-001 package-reviewer · modelo anthropic/claude-sonnet-4.6

↩ [[features/031-registro-correctivo|031-registro-correctivo]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
