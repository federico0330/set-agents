# 006 evidencia de consistencia whole-repo registrada, fase se queda en PACKAGE_ACCEPTED

<!-- notas:auto -->
- fecha: 2026-07-30 · actor: orchestrator
- alcance: [[features/006-execution-graph|006-execution-graph]]

## Contexto

La integración de 005-portable-harness esta noche motivó correr verify.sh/build.sh --check también contra el trabajo aceptado de 006 (P3-graph-view), en el mismo árbol de trabajo sin commitear.

## Decisión

Evidencia registrada en docs/specs/006-execution-graph/evidence/whole-repo-consistency.md (457 tests OK, VERIFY_PASS, SELF_SCAFFOLD_SYNC_OK, AC-20..AC-29 sostenidos). No se llamó transition de ningún tipo -- 006 se queda en PACKAGE_ACCEPTED para siempre, tal como ya lo declara el contrato 1.2.0 del propio spec (init solo declaró AC-20..AC-29, sin backfillear P1/P2).

## Consecuencias

006 nunca va a mostrar INTEGRATION ni DONE en STATUS.md -- es intencional y ya estaba documentado antes de esta noche, no una feature estancada.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
