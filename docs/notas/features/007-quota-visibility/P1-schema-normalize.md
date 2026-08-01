# 007-quota-visibility · P1-schema-normalize

<!-- notas:auto -->
## Motivo

- objetivo: Que la comparacion de DDL compare estructura y no prosa, y que una base que genuinamente no se puede migrar lo diga nombrando el objeto que diverge en vez de fallar mudo
- complejidad: medium
- riesgo: Redefine que significa 'correcto' para toda base en disco: _canonical_schema_sql define la referencia de los otros dos …
- paths: `ai/scripts/routing_core/store.py`, `docs/adr/0005-trusted-routing-sqlite-lifecycle.md`, `docs/specs/007-quota-visibility/**`, `ai/state/features/007-quota-visibility.json`, `ai/state/STATUS.md`, `ai/state/decisions-log.jsonl`, `ai/state/narrative-log.jsonl`, `docs/notas/**`

## Tareas

- [x] Fixture congelado parametrizado (comentarios / CHECK N03 / version) reemplazando el literal inline, byte-identico con las perillas por default (completed) · frozen_dispatches_script() con las perillas por default es byte-identico (3913 chars) al literal borrado de tests/test_routing.py:1118-1141, comparado fuera de la suite antes de borrarlo, test_routing_migrate_uses_harness_identity_and_test_store pasa sin tocar ninguna de sus aserciones: es el portero del refactor, python3 -m unittest de los tres tests de schema (migrate, drift byte-identico, warning schema-4): OK en 0.240s
- [x] _normalize_ddl() delimiter-aware sobre las cuatro formas de comillas, comentarios antes del colapso de espacios (completed) · Los tres tests mostrados en rojo antes de escribir la funcion (AttributeError: module routing_core.store has no attribute _normalize_ddl), verdes despues, Mutacion 'bracket-opens-inside-quote' cazada por test_normalize_ddl_strips_the_canonical_comment_block; mutacion 'collapse-before-strip' cazada por los dos. Ningun guard queda solo demostrado en verde, La funcion todavia no esta cableada: la conducta del store es bit-identica en este paso
- [x] Cablear los tres sitios de normalizacion y colapsar la query de sqlite_master triplicada (AC-01) (completed) · test_comment_only_divergence_migrates_and_opens y test_comment_free_schema_five_database_opens mostrados rojos antes (ROUTING_MIGRATE_FAILED rc 2), verdes despues, test_normalize_ddl_is_the_only_normalizer rojo antes (4 != 1), verde despues: la expresion inline y la query de sqlite_master quedan en 1 ocurrencia cada una, test_altered_check_is_still_rejected verde antes y despues: la reparacion no aflojo el control, python3 -m unittest tests.test_routing: Ran 82 tests, OK
- [x] SchemaDivergence: str() sigue siendo ROUTING_UNAVAILABLE, el detalle viaja en atributos, nombres canonicos se imprimen y los del archivo se cuentan (AC-05) (completed) · Tres tests rojos antes (SchemaDivergence inexistente; 'altered=dispatches' ausente de stderr), verdes despues, Mutacion 'unexpected-name-echoed' cazada por test_diagnostic_never_echoes_a_file_supplied_name; mutacion 'narrow-isinstance-exit-removed' cazada por ese y por test_missing_check_names_the_diverged_object, test_schema_drift_fails_closed_byte_identically pasa sin tocar una sola de sus aserciones: assertRaisesRegex(RoutingError, ROUTING_UNAVAILABLE) sigue cierto sobre la subclase, Corregi una asercion propia que estaba mal (el alfabeto del diagnostico excluia mayusculas y SCHEMA_DIVERGED las tiene); se arreglo el test, no el codigo, python3 -m unittest tests.test_routing: Ran 86 tests, OK (base 75)
- [x] Enmienda en ADR-0005 con el modelo de amenaza real (AC-07) (completed) · Enmienda inline en el bullet Security, con el mismo idioma que la enmienda R3 que ya vivia en el archivo (linea con fecha + decision referenciada), Referencia routing-ddl-validation-blind-to-triggers y dice por que ese hueco NO se cierra: cerrarlo no cambia el alcance del adversario, La fila del indice de ADRs no cambia (el estado sigue Accepted), asi que el guard de 009-P3 sobre docs/adr/README.md sigue pasando

## Hallazgos

- F-01 [medium] refuted —  · refutado por finding-verifier: El sujeto de la frase disputada es la COMPARACION de DDL, y la propia reproduccion del hallazgo la prueba cierta: la ba… [ai/scripts/routing_core/store.py:302-304 es la comparacion, que pasa; el rechaz…]

## Recorrido

- review: repair_required (1 hallazgos)
- verificación: 1 refutados, 0 sostenidos
- testing: pass
- runtime QA: pass (waived)
- gate `package verify`: pass
- gate `self-scaffold-sync`: pass
- gate `whitespace`: pass
- gate `ownership`: pass
- gate `adversarial-proof`: pass
- gate `live-diagnosis`: pass
- gate `package verify (post-panel)`: pass

context pack: `docs/specs/007-quota-visibility/context/P1-schema-normalize.md`

↩ [[features/007-quota-visibility|007-quota-visibility]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
