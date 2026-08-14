# B3 implementer — ventana y rollup

Estado: implementación terminada; gates globales sin veredicto limpio por fallas ajenas al
diff bajo el sandbox (detalladas abajo). No es una aprobación propia.

| AC | Cambio (archivo:línea) | Prueba |
| --- | --- | --- |
| AC-06 | `store.py:16,50-63,587-609,920-945,984-1011,1120` | Fixture schema 7 con datos migra a 8, conserva el dispatch y agrega su rollup; fallo SQLite del rollup revierte el cierre completo; uso basura cierra como `invalid` y sí entra al rollup. |
| AC-07 | `store.py:63,1013-1051` | Fixture mantiene el padre de `replacement_of_run_id` y el writer consultable; borra sólo un terminal ordinario ya agregado. |
| Docstring B2 | `usage.py:21-22` | Corrección de texto: claude-code/opencode están conectados desde B2; codex sigue fuera. |

## Conciliación AC-06

Las dos reglas operan sobre fallas distintas. `_usage_row` ya es total: una forma inválida
del proveedor se convierte antes de escribir en la categoría `invalid`, de modo que el uso no
aborta el cierre. Un error real al escribir SQLite el rollup sí hace rollback de la única
transacción, por lo que no queda un dispatch terminal sin rollup ni un rollup sin dispatch.

El rollup es UTC-diario y conserva suma **y** cantidad reportada por campo: un cero informado no
se vuelve indistinguible de ausente. La migración clasifica el `usage_status` NULL histórico como
`unknown`, no como `absent`, para no fabricar una observación de proveedor.

## ROJO por prueba nueva

Los tests se escribieron antes de implementar el cambio (equivalente a neutralizarlo: schema 7,
sin tabla/método B3). No se tocó la base real del usuario.

### `test_b3_migrates_a_populated_schema_seven_into_usage_rollups_without_losing_the_run`

Bloque recortado (fragmento literal):

```text
ERROR: test_b3_migrates_a_populated_schema_seven_into_usage_rollups_without_losing_the_run
...
routing_core.domain.RoutingError: ROUTING_UNAVAILABLE
```

### `test_b3_rollup_write_failure_rolls_back_the_close_instead_of_leaving_a_half_closed_run`

Bloque recortado (fragmento literal):

```text
ERROR: test_b3_rollup_write_failure_rolls_back_the_close_instead_of_leaving_a_half_closed_run
...
AttributeError: <routing_core.store.RoutingStore object ...> does not have the attribute '_rollup_usage_in'
```

### `test_b3_dispatch_retention_keeps_replacement_parents_and_current_reviewer_candidates`

Bloque recortado (fragmento literal):

```text
ERROR: test_b3_dispatch_retention_keeps_replacement_parents_and_current_reviewer_candidates
...
sqlite3.OperationalError: no such table: usage_rollups
```

## VERDE focal

Migración 7→8 con fixture poblado: el fixture inserta un `terminal_success` con
`input=13`, `output=5`, `cost_micros=1800`, `usage_status=ok`; después de migrar afirma que el
dispatch conserva exactamente esos cinco valores y que `usage_rollups` contiene
`(run_count=1,input_sum=13,input_reported=1,output_sum=5,output_reported=1,cost_sum=1800,cost_reported=1,status=ok)`.

Bloque recortado (fragmento literal):

```text
$ python3 -m unittest tests.test_routing.RoutingTests.test_b3_migrates_a_populated_schema_seven_into_usage_rollups_without_losing_the_run tests.test_routing.RoutingTests.test_b3_rollup_write_failure_rolls_back_the_close_instead_of_leaving_a_half_closed_run tests.test_routing.RoutingTests.test_b3_dispatch_retention_keeps_replacement_parents_and_current_reviewer_candidates
...
----------------------------------------------------------------------
Ran 3 tests in 0.454s

OK
```

El tercero usa sólo fixture para los dos negativos exigidos: la base medida tenía 0 filas con
`replacement_of_run_id`, así que no se afirma una validación en vivo. Prueba que se conservan
el padre enlazado y el writer que `recent_writers()` todavía expone; también prueba que un
terminal ordinario de 91 días se borra únicamente después de verificar su rollup.

Compatibilidad adicional de schema/migración y cierres existentes:

Bloque literal:

```text
........
----------------------------------------------------------------------
Ran 8 tests in 2.864s

OK
```

Pendiente. Los bloques de comandos se incorporarán literales, o explícitamente marcados como recortados.

## Gates

### Suite requerida

`ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests` — **sin verificar
hasta final**: el runner de esta sesión devolvió control antes de informar exit status; su salida
literal parcial ya mostraba `E`. Diagnóstico determinista sin pipeline:

Bloque literal:

```text
$ python3 -m unittest -f tests.test_routing
.....................................................................E
======================================================================
ERROR: test_ac04a_verified_review_shape_dispatches_via_ac02_cross_lane_with_diff_payload_reaching_stdin (...)
...
subprocess.CalledProcessError: Command '['./build.sh']' returned non-zero exit status 1.
...
Ran 70 tests in 1.060s

FAILED (errors=1)
```

La causa observada al ejecutar ese `./build.sh` directo es ajena al diff y al schema:

Bloque literal:

```text
CHECK_PASS: generated and validated profile go-zen
Generated tracked artifacts for go-zen.
./build.sh: line 66: /home/federico/SET-AGENTES/.git/hooks/post-commit: Read-only file system
```

### Verificación requerida

`ai/scripts/heartbeat-run.py --interval 20 -- ./ai/scripts/verify.sh` — **sin verificar hasta final**:
el runner devolvió control durante su suite y mostró errores de `test_harness` ajenos a estos
archivos, sin línea final `VERIFY_PASS`/exit status. No se corrigieron por estar fuera de alcance.

### Build requerido

Bloque literal:

```text
$ ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```

### Diff requerido

`git diff --check` — exit 0, sin salida.
