# Los dos hallazgos abiertos dentro de features cerradas ya estaban reparados

<!-- notas:auto -->
- fecha: 2026-08-18 · actor: orchestrator

## Contexto

016-audit-debt-repayment/P1-harness-debt/P1F-01 (low) y 020-honest-dashboard/P2-anclas-verificables/F-04 (low) figuraban open dentro de features en DONE. Verificado el 2026-08-18 sobre el arbol real, no sobre memoria.

## Decisión

Los dos estan reparados en el codigo. P1F-01 ('el pop de repair_entry anidado bajo if args.package_id'): ai/scripts/feature_state_lib/cli_lifecycle.py:277-285 resuelve por package_by_id con fallback a current_package_id y nombra el hallazgo en el comentario; el test que el suggested_fix pedia existe, tests/test_harness.py:8650 test_cmd_transition_pops_stale_repair_entry_without_package_id. F-04 ('CHECK_PASS y SELF_SCAFFOLD_SYNC_OK no comparan contra el estado real de Global/'): build.sh:117-127 ahora corre diff -ruN de los cuatro arboles contra una generacion fresca y emite GLOBAL_TREE_SYNC_OK o falla, que es la implementacion del punto 1 de ADR-0041. Ademas SELF_SCAFFOLD_SYNC_OK paso de dos archivos nombrados a mano a los 23 del espejo completo.

## Consecuencias

Los registros de hallazgo siguen diciendo open porque ningun verbo cierra un hallazgo sobre una feature en DONE sin un reopen --from-done completo, y hacer ese recorrido entero para dos hallazgos low sobre features correctas arriesga mas de lo que corrige. La correccion vive aca, con file:line, no en memoria. Si se quiere el registro literalmente limpio, es un reopen deliberado y es decision de Federico.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
