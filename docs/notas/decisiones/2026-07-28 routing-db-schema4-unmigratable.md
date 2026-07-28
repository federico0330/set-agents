# La DB de routing local no se puede migrar de schema 4 a 5 por el path sancionado

<!-- notas:auto -->
- fecha: 2026-07-28 · actor: orchestrator

## Contexto

El adaptive routing (feature 004) esta APAGADO en esta maquina: --route-decide devuelve ROUTING_UNAVAILABLE con warning ROUTING_SCHEMA_MIGRATION_REQUIRED, porque ~/.local/state/set-agentes/routing-v2/routing.db esta en schema 4 y la feature 005-P1 introdujo la columna project_key (schema 5). El comando sancionado --routing-migrate falla con ROUTING_MIGRATE_FAILED y hace rollback correctamente (la DB queda intacta, verificado). Causa raiz diagnosticada: store.py:281 compara el DDL post-migracion contra _canonical_schema_sql() exigiendo igualdad byte-exacta, pero ALTER TABLE ADD COLUMN conserva el TEXTO ORIGINAL del CREATE TABLE guardado en sqlite_master. Esta DB se creo con una version del codigo cuyo CREATE TABLE no tenia los comentarios SQL '-- n03: abandoned is a never-dispatched close', que el DDL canonico actual SI tiene. El desvio arranca en el caracter 2082. Por construccion, NINGUNA DB creada antes de que se agregaran esos comentarios puede pasar esa comparacion. La via rebuild+rename ya fue descartada en el ADR-0008 D8 porque produce CREATE TABLE con comillas, que tambien rompe la igualdad byte-exacta.

## Decisión

No se borra ni se toca la DB sin decision humana. Contenido real: 2 filas en dispatches (una terminal_success, una abandoned) y 7 en metric_rollups. Copia de seguridad tomada en el scratchpad de la sesion. El harness sigue funcionando degradado a agentes base con modelos estaticos por rol, que es la doctrina de degrade honesto de la 004.

## Consecuencias

Dos caminos para el humano: (a) borrar ~/.local/state/set-agentes/routing-v2/routing.db y dejar que el store la recree en schema 5 -- se pierden 2 dispatches y 7 rollups, historial despreciable, y el routing adaptativo se enciende en el acto; (b) abrir un paquete de reparacion en la feature 005 que arregle migrate_from_v4 para que normalice el DDL en vez de exigir igualdad byte-exacta contra un texto que ALTER no puede reescribir. La opcion (b) es la correcta a nivel producto porque el bug afecta a CUALQUIER instalacion previa, no solo a esta maquina.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
