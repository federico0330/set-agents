# B3 repair — ventana y rollup

Estado de entrada: seis hallazgos, todos `upheld` por el finding-verifier. El diff en el
working tree ya traía, al arrancar este repair-agent, los cinco primeros hallazgos resueltos
por un repair-agent anterior de este mismo ciclo (relanzado en otro proveedor por límite de
sesión, según `bitacora.md`); este repair cierra el resto: valida cada arreglo heredado con
reproducción antes/después, corrige un resto de F06 que había quedado sin tocar, y repara F03
(que sólo podía escribirse bien después de F01).

## Tabla hallazgo → cambio → verificación

| Hallazgo | Archivo:línea | Qué cierra | Verificación |
| --- | --- | --- | --- |
| B3-F01 (critical) | `store.py:836-842` (rama sin replacement) y el mismo call cubre la rama con replacement | `close_exhausted_and_authorize_replacement` llama `_rollup_usage_in(c, now, original_identity, "failure", usage_row)` en la MISMA transacción que escribe las columnas de usage, antes de cualquier branch | Reproducción antes/después (abajo): sin el call, el run se borra sin que su propio consumo quede en ningún agregado; con el call, se borra sólo cuando su consumo YA está agregado |
| B3-F02 (critical) | `store.py:250-251` (`_RECENT_WRITERS_LIMIT`, `_RECENT_WRITERS_ORDER_BY`), usadas en `recent_writers` (`:1030`) y en `_compact_dispatches_in`'s protected clause (`:1113`) | Un solo order/limit nombrado y compartido — ya no hay una segunda copia que pueda desalinearse | Reproducción antes/después (abajo): con el order-by desalineado (`recent_writers` ASC, guarda DESC), la fila que `recent_writers()` ofrece es exactamente la que la retención borra → `REVIEW_IDENTITY_INVALID`; con el order-by compartido, nunca coinciden |
| B3-F03 (high) | `tests/test_routing.py:2360-2407` (`test_b3_dispatch_retention_keeps_replacement_parents_and_current_reviewer_candidates`) | El test escrito por el implementer sobrevivía por el mecanismo equivocado (falta de rollup propio de `original`, no por la cláusula `NOT EXISTS(successor)`) porque F01 aún no estaba arreglado cuando se escribió. Con F01 ya arreglado, `original` ahora SÍ tiene su propio rollup, así que `SUM(run_count)` pasa de 2 a 3 y la supervivencia de `original` depende exclusivamente de esa cláusula | Mordida documentada abajo: quitar `NOT EXISTS(successor...)` → rojo (`FOREIGN KEY constraint failed` / `ROUTING_UNAVAILABLE`); restaurar → verde |
| B3-F04 (medium) | `store.py:64-76` (`CHECK(typeof(x)='integer')` en cada acumulador de `usage_rollups`) | Ya estaba en el diff heredado; verificado con reproducción (abajo) que efectivamente detecta el desborde a REAL y hace `ROLLBACK` de todo el cierre, no sólo del rollup | Reproducción abajo: dos cierres de `usage_input=2**62` sobre la misma clave → el segundo lanza `ROUTING_UNAVAILABLE`, el rollup queda sin corromper, el segundo run queda `dispatched` (no a medias) |
| B3-F05 (medium) | `store.py:754-761` (`_event(..., compact=True)` + `compact=False` en los dos eventos extra de `close_exhausted_and_authorize_replacement`, `:860-861`) | Ya estaba en el diff heredado; verificado que CADA transacción de escritura (grep de los 10 call-sites de `self._event(c,...)`) emite compactación exactamente UNA vez, nunca cero ni dos | Grep exhaustivo abajo: de los 10 call-sites, sólo `close_exhausted_and_authorize_replacement` emite 3 eventos en una transacción, y 2 de esos 3 llevan `compact=False` |
| B3-F06 (low) | `store.py:234-251` (constantes nombradas) + `store.py:634` (resto sin tocar: `_migrate_7_to_8` seguía con `86400000` literal dos veces) | Constantes de retención de un solo origen (`_DAY_MS`, `_RETENTION_DAYS`, `_RETENTION_CUTOFF_MS`, `_RETENTION_ROW_LIMIT`, `_RECENT_WRITERS_LIMIT`, `_RECENT_WRITERS_ORDER_BY`) y docstrings de `_compact_in`/`recent_writers` corregidos — ya estaban en el diff heredado. Lo que arreglé yo: el único `86400000` que quedaba fuera de `_DAY_MS`, en `_migrate_7_to_8` | Grep abajo: un solo literal `86400000` en todo el archivo (la definición de `_DAY_MS`); el resto son referencias a la constante |

## `terminal()` y `abandon()`: decisión

**No los toqué.** Grep repo-wide (`grep -rn "\.terminal(\|\.abandon("` fuera de
`tests/test_routing.py` y `routing_core/store.py`) no encuentra NINGÚN llamador de producción
hoy — sólo `close_run` está cableado desde `claude_code_spawn.py`/`opencode_spawn.py`/CLI, tal
como dice su propio docstring ("This replaces the CLI's former ... two-transaction pattern").
A diferencia de `close_exhausted_and_authorize_replacement`, ninguna de las dos escribe
`_USAGE_SET_CLAUSE`: no tocan ninguna columna `usage_*`/`cost_micros`/`usage_status` de
`dispatches`, así que una fila cerrada por cualquiera de las dos queda con `usage_status` NULL.
La guarda de retención lee eso como `COALESCE(usage_status,'unknown')`, y nada escribe jamás un
rollup con `usage_status='unknown'` salvo la migración 7→8 (una sola vez, sobre filas
preexistentes). Consecuencia: una fila cerrada por `terminal()`/`abandon()` nunca puede probar
un rollup que la cubra, así que la retención la retiene para siempre — falla del lado seguro
(disco de más, nunca evidencia perdida), exactamente la dirección que "ante la duda, no borres"
ya exige. Agregué un comentario en `store.py:914` documentando este razonamiento para el
próximo que lea el código, en vez de agregar una llamada a rollup inalcanzable en código muerto.

## Reproducción B3-F01 (antes/después)

Escenario: `original` se cierra por `quota_exhausted` sin fallback disponible (la rama SIN
reemplazo, la más peligrosa — sin esa rama, `original` siempre tiene un sucesor que la protege
igual, sin depender del rollup) con `usage_input=1000`; un sibling no relacionado, con la MISMA
identidad/outcome/status, cierra con `usage_input=1`. Se envejecen 91 días y se compacta.

**Antes** (con la línea de F01 neutralizada temporalmente vía `cp`/edit/`cp`, restaurada
después — nunca se tocó git):

```
F01 REPRO: usage_rollups.usage_input_sum for this key/outcome/status BEFORE compact=1 (original's own 1000 tokens are NOT in it) | run A (original) survives=False | recoverable dispatches.usage_input SUM: before compact=1001 after compact=1
```

El propio consumo de `original` (1000) nunca queda en NINGÚN agregado, y aun así su fila se
borra porque el sibling "prueba" la clave. Recuperable total: 1001 antes, 1 después — 1000
tokens perdidos sin dejar rastro.

**Después** (código real, sin modificar):

```
F01 REPRO: usage_rollups.usage_input_sum for this key/outcome/status BEFORE compact=1001 (original's own 1000 tokens ARE in it) | run A (original) survives=False | recoverable dispatches.usage_input SUM: before compact=1001 after compact=1
```

La fila de `dispatches` se sigue borrando (retención sigue podando), pero el agregado YA tiene
los 1000 tokens de `original` antes de que eso pueda pasar: el total recuperable vía
`usage_rollups` es 1001, nunca se pierde nada — sólo se muda de la fila cruda al agregado, que
es el punto de AC-06/AC-07.

## Reproducción B3-F02 (antes/después)

Escenario: 19 filas writer/`terminal_success` estrictamente más nuevas (rank 1-19 bajo
cualquier desempate) más un par empatado en el mismo `terminal_at` (`row_low`=`run1_555...5`,
`row_high`=`run1_fff...f`) compitiendo por el rank 20, con un rollup propio cubriendo a ambas.

**Antes** (con `recent_writers` revertido temporalmente a `ORDER BY terminal_at DESC,run_id`
—ASC en el empate—, la guarda de retención sin tocar en `run_id DESC`; restaurado después vía
`cp`/edit/`cp`):

```
F02 REPRO: recent_writers() offered row_low=True row_high=False | AFTER compact: row_low survives=False row_high survives=True | reviewer would get REVIEW_IDENTITY_INVALID on the offered candidate=True
```

`recent_writers()` ofrece `row_low` como candidato válido; la retención (con el desempate
opuesto) borra exactamente esa fila. La aserción `assertRaisesRegex(RoutingError,
"REVIEW_IDENTITY_INVALID")` sobre `implementation_identity(row_low)` PASA — confirma el bloqueo
de independencia de revisión que describe el hallazgo.

**Después** (código real, sin modificar):

```
F02 REPRO: recent_writers() offered row_low=False row_high=True | AFTER compact: row_low survives=False row_high survives=True | reviewer would get REVIEW_IDENTITY_INVALID on the offered candidate=False
```

`recent_writers()` y la guarda de retención concuerdan siempre: la fila ofrecida (`row_high`)
es exactamente la que sobrevive.

## Reproducción B3-F04

Dos cierres de `usage_input=2**62` sobre la misma identidad/outcome/status (código real, sin
modificar):

```
F04 REPRO: after first close (2**62) rollup row=(4611686018427387904, 'integer') | second close of another 2**62 raised=ROUTING_UNAVAILABLE | rollup row AFTER second attempt=(4611686018427387904, 'integer') (unchanged=True) | second run's dispatch state=('dispatched',) (rolled back if not terminal_success)
```

El segundo cierre, que hubiera desbordado el acumulador a REAL, lanza `ROUTING_UNAVAILABLE`; el
rollup queda EXACTAMENTE como estaba tras el primer cierre (`typeof='integer'`, sin corromper);
el segundo run queda `dispatched` — el `ROLLBACK` deshizo el cierre completo, no sólo el
rollup, cumpliendo la misma disciplina transaccional que AC-06 exige para fallas de SQLite.

(Las tres reproducciones de arriba se hicieron con métodos de test temporales, agregados,
corridos y ELIMINADOS antes de este commit — no quedan en el diff final. `git diff --check` y
`grep -n "test__repro_scratch" tests/test_routing.py` (sin salida) lo confirman.)

## Mordida de B3-F03

Sobre `test_b3_dispatch_retention_keeps_replacement_parents_and_current_reviewer_candidates`,
quitando `NOT EXISTS (SELECT 1 FROM dispatches AS successor WHERE
successor.replacement_of_run_id=dispatches.run_id) AND` de `_compact_dispatches_in`'s
`protected` (vía `cp`/edit; restaurado con `cp` desde el backup, nunca `git checkout`):

Rojo (bloque literal, recortado a la traza relevante):

```
sqlite3.IntegrityError: FOREIGN KEY constraint failed

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File ".../tests/test_routing.py", line 2392, in test_b3_dispatch_retention_keeps_replacement_parents_and_current_reviewer_candidates
    svc.store.compact(now_ms=old + 91 * 86400 * 1000 + 1)
  File ".../ai/scripts/routing_core/store.py", line 1126, in compact
    raise RoutingError("ROUTING_UNAVAILABLE") from exc
routing_core.domain.RoutingError: ROUTING_UNAVAILABLE

Ran 1 test in 0.296s

FAILED (errors=1)
```

(La base SQLite se niega a borrar `original` sin borrar antes su sucesor —
`replacement_of_run_id` es una FK— exactamente porque, sin esa cláusula, `original` ahora
cumple `terminal AND rollup AND protected` y entra al `DELETE`. Es una falla incluso más dura
que un simple `assertEqual`: el motor mismo objeta.)

Restaurado:

```
$ python3 -m unittest tests.test_routing.RoutingTests.test_b3_dispatch_retention_keeps_replacement_parents_and_current_reviewer_candidates -v
test_b3_dispatch_retention_keeps_replacement_parents_and_current_reviewer_candidates (...) ... ok

Ran 1 test in 0.325s

OK
```

Además: la aserción heredada `SUM(run_count) == 2` estaba desactualizada por el propio arreglo
de F01 (ahora `original` aporta su propio rollup) y fallaba realmente contra el código ya
arreglado:

```
AssertionError: Tuples differ: (3,) != (2,)
```

Corregida a `3`, con un comentario explicando por qué (F01 hace que `original` aporte su propio
`run_count`), más una aserción adicional de que existe al menos una fila de rollup
`outcome='failure'` con `run_count=1` (la contribución aislada de `original` antes de fusionarse
con cualquier otra). Ésta es ahora la SEXTA guarda de esta familia en el proyecto que se probó
con el protocolo rojo→restaurar→verde, no la sexta hueca.

## Grep de verificación F05 (una compactación por transacción)

```
$ grep -n "self\._event(c" ai/scripts/routing_core/store.py
781:            self._event(c,"authorized",identity,fallback=fallback is not None); c.execute("COMMIT")
846:                self._event(c,"terminal",original_identity,"failure",reason="quota_exhausted",latency=latency_ms)
859:            self._event(c,"terminal",original_identity,"failure",reason="quota_exhausted",latency=latency_ms)
860:            self._event(c,"authorized",fallback,compact=False)
861:            self._event(c,"dispatched",fallback,compact=False)
883:            c=self._connect(); c.execute("BEGIN IMMEDIATE"); self._event(c,"rejected",identity,"failure",reason); c.execute("COMMIT")
898:            self._event(c,event,tuple(row[:6] if all(row[:6]) else row[6:12]),outcome,latency=latency,via_fallback=bool(row[12])); c.execute("COMMIT")
936:            self._event(c,"fallback",tuple(row[:6])); c.execute("COMMIT"); return tuple(row[:6])
949:            self._event(c,"abandoned",tuple(row),"failure"); c.execute("COMMIT")
995:                self._event(c,"terminal",identity,outcome,latency=latency_ms,via_fallback=bool(row[13])); c.execute("COMMIT")
1006:                self._event(c,"abandoned",tuple(row[7:13]),"failure"); c.execute("COMMIT")
```

Diez call-sites, uno por transacción excepto `close_exhausted_and_authorize_replacement`
(líneas 846 XOR 859-861, según la rama): la única transacción con más de un evento lleva
`compact=False` en dos de los tres, dejando exactamente una compactación. Los benchmarks de
milisegundos citados en el comentario de `:854-858` (228ms/664ms a 20k/40k filas) son los que
trajo el reviewer en el hallazgo original — **sin verificar** por este repair-agent (no se
re-corrió el benchmark; la corrección estructural sí se confirmó por grep exhaustivo arriba).

## Grep de verificación F06 (constantes de un solo origen)

```
$ grep -n "_DAY_MS = 86400000\|_RETENTION_DAYS = 90\|_RETENTION_ROW_LIMIT = 10000\|_RECENT_WRITERS_LIMIT = 20\|_RECENT_WRITERS_ORDER_BY =" ai/scripts/routing_core/store.py
241:_DAY_MS = 86400000
242:_RETENTION_DAYS = 90
244:_RETENTION_ROW_LIMIT = 10000
250:_RECENT_WRITERS_LIMIT = 20
251:_RECENT_WRITERS_ORDER_BY = "terminal_at DESC,run_id DESC"

$ grep -n "86400000" ai/scripts/routing_core/store.py
241:_DAY_MS = 86400000
```

Un solo literal `86400000` en todo el archivo — la definición de `_DAY_MS`. Antes de este
repair, `_migrate_7_to_8` (`store.py:634`, ahora `f"...{_DAY_MS}...{_DAY_MS}..."`) todavía
tenía el literal duplicado dos veces; ese resto es lo único que yo arreglé de F06, el resto ya
venía resuelto.

## Gates

### `python3 -m unittest discover -s tests`

```
Ran 1098 tests in 706.518s

OK (skipped=3)
```

Corrida completa final, contra el diff exacto de este commit (sin los tests temporales de
reproducción, ya eliminados antes de esta corrida).

### `./ai/scripts/verify.sh`

```
...
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

(Incluye, más arriba en el mismo log, la corrida completa de la suite con `OK (skipped=3)`.)

### `./build.sh --check`

```
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```

### `git diff --check`

Exit 0, sin salida.

## Alcance

Todo el cambio quedó dentro de `ai/scripts/routing_core/store.py`,
`tests/test_routing.py` y `docs/adr/0045-consumo-vocabulario-en-el-borde.md` — el
alcance declarado para este paquete. No se tocó `ai/scripts/routing_core/usage.py` en este
pase (ya venía arreglado el docstring de B2 en el diff heredado); no se tocó la base real del
usuario (`~/.local/state/set-agentes/routing-v2/routing.db`) en ningún momento — todas las
reproducciones usaron `tempfile.TemporaryDirectory()`.

**No aprueba su propio trabajo.** Corresponde un delta review independiente.

## Repair puntual — la red que faltaba para B3-F02 (post-batch)

El RESULTADO REQUERIDO de B3-F02 pedía un test permanente, no sólo la reproducción manual de
arriba (que se corrió y se borró antes del commit, según la nota bajo "Reproducción B3-F02").
Ese test no se había escrito. Este repair agrega exactamente eso — sin tocar producción; el
arreglo de F02 (`_RECENT_WRITERS_ORDER_BY`/`_RECENT_WRITERS_LIMIT` compartidas, `store.py:250-251`)
ya estaba.

### El test nuevo

`tests/test_routing.py:2409-2455` —
`test_b3_retention_guard_protects_every_row_recent_writers_would_return_on_a_terminal_at_tie`.

21 cierres `writer`/`terminal_success` (uno más que `_RECENT_WRITERS_LIMIT=20`) se fuerzan al
MISMO `terminal_at`, se envejecen 91 días. `recent_writers()` se lee ANTES de `compact()` — esa
foto es exactamente lo que la consulta de un reviewer devolvería — y la aserción
(`tests/test_routing.py:2455`) exige que ese conjunto de `run_id` siga vivo después de
`compact()`:

```python
recent_before = {row["run_id"] for row in svc.store.recent_writers()}
self.assertEqual(len(recent_before), 20)
svc.store.compact(now_ms=old + 91 * 86400 * 1000 + 1)
...
live = {row[0] for row in c.execute("SELECT run_id FROM dispatches")}
self.assertTrue(recent_before.issubset(live), recent_before - live)
```

Es determinístico, no probabilístico: con N>=21 filas empatadas, "los 20 `run_id` más grandes"
(`terminal_at DESC,run_id DESC`, lo que devuelve `recent_writers`) y "los 20 más chicos"
(`terminal_at DESC,run_id ASC`, el desempate opuesto que tenía B3-F02) nunca pueden ser el mismo
conjunto — el `run_id` más grande de los 21 está siempre en el primero y nunca en el segundo.

### Mordida — dirección 1: reintroducir la divergencia SOLO en la guarda

Backup con `cp` (no `git checkout`) y edición de `_compact_dispatches_in`'s `protected`
(`store.py:1121-1123`), reemplazando `ORDER BY {_RECENT_WRITERS_ORDER_BY} LIMIT
{_RECENT_WRITERS_LIMIT}` por `ORDER BY review.terminal_at DESC,review.run_id ASC LIMIT 20` —
la guarda desalineada del hallazgo original; `recent_writers` (`store.py:1040`) queda intacta.

```
$ cp ai/scripts/routing_core/store.py <scratchpad>/store.py.bak
$ # edit: protected's ORDER BY -> "review.terminal_at DESC,review.run_id ASC LIMIT 20"
$ python3 -m unittest tests.test_routing.RoutingTests.test_b3_retention_guard_protects_every_row_recent_writers_would_return_on_a_terminal_at_tie -v
test_b3_retention_guard_protects_every_row_recent_writers_would_return_on_a_terminal_at_tie (tests.test_routing.RoutingTests.test_b3_retention_guard_protects_every_row_recent_writers_would_return_on_a_terminal_at_tie)
B3-F02 regression: the guard and `recent_writers` MUST share one tie-break. ... FAIL

======================================================================
FAIL: test_b3_retention_guard_protects_every_row_recent_writers_would_return_on_a_terminal_at_tie (tests.test_routing.RoutingTests.test_b3_retention_guard_protects_every_row_recent_writers_would_return_on_a_terminal_at_tie)
B3-F02 regression: the guard and `recent_writers` MUST share one tie-break.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/federico/SET-AGENTES/tests/test_routing.py", line 2455, in test_b3_retention_guard_protects_every_row_recent_writers_would_return_on_a_terminal_at_tie
    self.assertTrue(recent_before.issubset(live), recent_before - live)
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: False is not true : {'run1_f7ddc5a58b0e35f479f665bd7564e3b1'}

----------------------------------------------------------------------
Ran 1 test in 1.239s

FAILED (failures=1)
```

Rojo: el `run_id` más grande de los 21 (`run1_f7ddc5a58b0e35f479f665bd7564e3b1`), presente en la
foto de `recent_writers()` tomada antes de `compact()`, quedó borrado por la guarda desalineada.
Exactamente el hueco que describe B3-F02.

### Mordida — dirección 2: restaurar con `cp`

```
$ cp <scratchpad>/store.py.bak ai/scripts/routing_core/store.py
$ python3 -m unittest tests.test_routing.RoutingTests.test_b3_retention_guard_protects_every_row_recent_writers_would_return_on_a_terminal_at_tie -v
test_b3_retention_guard_protects_every_row_recent_writers_would_return_on_a_terminal_at_tie (tests.test_routing.RoutingTests.test_b3_retention_guard_protects_every_row_recent_writers_would_return_on_a_terminal_at_tie)
B3-F02 regression: the guard and `recent_writers` MUST share one tie-break. ... ok

----------------------------------------------------------------------
Ran 1 test in 1.208s

OK
```

Verde. `git diff ai/scripts/routing_core/store.py` después de la restauración sigue mostrando
`ORDER BY {_RECENT_WRITERS_ORDER_BY} LIMIT {_RECENT_WRITERS_LIMIT}` en `protected` — ningún
resto de la mordida quedó en el árbol; nunca se usó `git checkout`/`git restore`/`git stash`.

### Gates (con el test nuevo, código de producción sin tocar)

```
$ ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests
...
Ran 1099 tests in 488.699s

OK (skipped=3)
$ echo $?
0
```

(1099 = los 1098 de la base más el test nuevo. `pytest` no está instalado, no se usó; la salida
no se pipeó a `tail`, ADR-0041 — se redirigió a archivo y se leyó completo con `Read`.)

```
$ git diff --check
$ echo $?
0
```

### Alcance de esta pasada

Único archivo tocado: `tests/test_routing.py` (el test nuevo) más este archivo de evidencia.
`ai/scripts/routing_core/store.py` volvió, tras la mordida, byte a byte al estado que traía al
empezar (verificado por grep arriba) — el arreglo de producción de B3-F02 no se tocó. No se tocó
`~/.local/state/set-agentes/routing-v2/routing.db` ni ningún fixture bajo `~`.

## Reparación urgente — B3-F04 rompió el ruteo en la máquina real (SCHEMA sin bumpear)

Estado de entrada de ESTA pasada: el árbol de trabajo, al arrancar este repair-agent, YA traía
`SCHEMA = 9`, `_migrate_8_to_9`, su entrada en `_MIGRATION_STEPS`, el fixture de schema 8 real
(`frozen_dispatches_script(version=8)`, con el CHECK sin tipar) y el test-candado
`test_canonical_ddl_is_pinned_to_schema` — sin commitear, y sin la sección de evidencia
correspondiente. Este repair verificó cada pieza (lectura completa, tests dirigidos, mordida en
las dos direcciones sobre el candado, y la recuperación real), no volvió a escribir código que ya
estaba correcto, y agrega esta sección más la recuperación de la base real, que faltaba.

### El defecto: diff exacto, confirmado contra el backup real del usuario

`_USAGE_ROLLUPS_DDL` (`ai/scripts/routing_core/store.py:64-76`) agregó
`CHECK(typeof(x)='integer')` a las seis columnas de suma sin bumpear `SCHEMA` (se había quedado
en 8). Diff mínimo, las seis columnas son todas iguales salvo el nombre:

```
-usage_input_sum INTEGER NOT NULL CHECK(usage_input_sum >= 0)
+usage_input_sum INTEGER NOT NULL CHECK(usage_input_sum >= 0) CHECK(typeof(usage_input_sum)='integer')
```

No es un diff reconstruido: es literalmente lo que tenía en disco la base real del usuario ANTES
de esta reparación (`sqlite_master.sql`, backup pre-migración tomado por `migrate()` más abajo)
contra lo que exige el DDL canónico vivo:

```
$ sqlite3 ~/.local/state/set-agentes/routing-v2/backups/routing-v8-20260814T034003Z.db \
  "SELECT sql FROM sqlite_master WHERE name='usage_rollups';"
CREATE TABLE usage_rollups (
 window_start INTEGER NOT NULL, project_key TEXT NOT NULL, route_key TEXT NOT NULL,
 runtime TEXT NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL, family TEXT NOT NULL,
 outcome TEXT NOT NULL CHECK(outcome IN ('success','failure')),
 usage_status TEXT NOT NULL CHECK(usage_status IN ('ok','absent','invalid','unknown')),
 run_count INTEGER NOT NULL CHECK(run_count >= 0),
 usage_input_sum INTEGER NOT NULL CHECK(usage_input_sum >= 0), usage_input_reported_count INTEGER NOT NULL CHECK(usage_input_reported_count >= 0),
 usage_output_sum INTEGER NOT NULL CHECK(usage_output_sum >= 0), usage_output_reported_count INTEGER NOT NULL CHECK(usage_output_reported_count >= 0),
 usage_cache_read_sum INTEGER NOT NULL CHECK(usage_cache_read_sum >= 0), usage_cache_read_reported_count INTEGER NOT NULL CHECK(usage_cache_read_reported_count >= 0),
 usage_cache_write_sum INTEGER NOT NULL CHECK(usage_cache_write_sum >= 0), usage_cache_write_reported_count INTEGER NOT NULL CHECK(usage_cache_write_reported_count >= 0),
 usage_reasoning_sum INTEGER NOT NULL CHECK(usage_reasoning_sum >= 0), usage_reasoning_reported_count INTEGER NOT NULL CHECK(usage_reasoning_reported_count >= 0),
 cost_micros_sum INTEGER NOT NULL CHECK(cost_micros_sum >= 0), cost_micros_reported_count INTEGER NOT NULL CHECK(cost_micros_reported_count >= 0),
 PRIMARY KEY(window_start,project_key,route_key,runtime,provider,model,family,outcome,usage_status))
```

Ni un `typeof(...)='integer'` en las seis columnas — exactamente el "altered" que
`_ddl_divergence` detecta (`store.py:498-516`) y que `_validate_existing_readonly`
(`store.py:518-539`) convierte en `SchemaDivergence` → `ROUTING_UNAVAILABLE` en cada apertura,
con la base ya migrada a schema 8 antes del cambio.

### El bump: `SCHEMA = 9` y `_migrate_8_to_9`

`ai/scripts/routing_core/store.py:16` — `SCHEMA = 9` (antes 8).

`ai/scripts/routing_core/store.py:644-679` — `_migrate_8_to_9`: reconstruye `usage_rollups`
(`ALTER TABLE ... RENAME TO usage_rollups_v8`, recrea con el `_USAGE_ROLLUPS_DDL` actual —ya
tipado—, `INSERT INTO usage_rollups SELECT * FROM usage_rollups_v8`, `DROP TABLE
usage_rollups_v8`), copiando cada fila sin lista de columnas hecha a mano porque nombres y orden
son idénticos entre ambos DDL (sólo se agregó un CHECK).

`ai/scripts/routing_core/store.py:1230-1235` — `_MIGRATION_STEPS` incluye `8:
RoutingStore._migrate_8_to_9`, así que `migrate()` (que ya camina la cadena hasta `SCHEMA`,
`store.py:681-768`) atraviesa 7→8→9 en una sola transacción cuando corresponde.

**Decisión explícita sobre filas ya corrompidas a REAL** (docstring completo en
`store.py:644-675`, párrafo "DECISION, not left implicit"): si una fila YA tiene un acumulador en
REAL (el desborde que F-04 previene hacia adelante, no repara hacia atrás), el `INSERT` viola el
CHECK nuevo y `_migrate_8_to_9` deja que `sqlite3.IntegrityError` se propague. `migrate()` corre
toda la cadena dentro de un solo `BEGIN EXCLUSIVE` y hace `ROLLBACK` completo ante cualquier
excepción (`store.py:758-761`), así que el archivo en disco queda EXACTAMENTE en schema 8 — nunca
un downgrade de confianza silencioso — y el backup pre-migración, ya tomado y verificado antes de
correr cualquier paso, queda intacto. Redondear, descartar o re-derivar la fila corrupta en
silencio destruiría la única evidencia de qué fila y qué cifra perdió precisión; el operador que
choque con esto tiene el backup para inspeccionar a mano y decidir con los números reales
delante, que es exactamente lo que un arreglo silencioso borraría.

### La migración sobre fixtures CON datos (no una base vacía)

Tres tests, cada uno corrido individualmente (ver salida abajo) y dentro de la corrida completa:

- `tests/test_routing.py:2374`
  `test_b3_migrates_a_populated_schema_seven_into_usage_rollups_without_losing_the_run` — un
  fixture real de schema 7 (sin tabla `usage_rollups`) con UNA fila de `dispatches`
  (`usage_input=13, usage_output=5, cost_micros=1800`) migra 7→…→`SCHEMA` actual (no un `8`
  hardcodeado) y termina con esa fila intacta y su rollup agregado
  (`run_count=1,usage_input_sum=13,...`).
- `tests/test_routing.py:2414`
  `test_b3f04_migrates_a_populated_schema_eight_into_the_typed_usage_rollups_check_without_losing_the_row`
  — el fixture es la forma REAL de schema 8 (`frozen_dispatches_script(version=8)`, CHECK SIN
  tipar — la misma forma que el backup real de arriba), con DOS filas de `usage_rollups`
  precargadas (una normal, otra con `run_count=1` y sumas en 0). Tras `migrate()`: ambas filas
  sobreviven byte a byte en sus columnas de negocio, `schema_version` queda en el `SCHEMA`
  vigente, y un `UPDATE` directo que fuerce un acumulador a REAL post-migración es rechazado por
  `sqlite3.IntegrityError` — el CHECK nuevo está realmente vivo, no sólo la tabla existe.
- `tests/test_routing.py:2476`
  `test_b3f04_migration_refuses_loudly_when_a_stored_sum_is_already_real_typed` — prueba, no sólo
  narra, la decisión documentada arriba: una fila con `usage_input_sum` ya en REAL
  (`9223372036854775808.0`) hace que `migrate()` lance `ROUTING_UNAVAILABLE`, el archivo en disco
  queda byte a byte igual (`before_bytes == after`), `schema_version` sigue en `"8"`, y el backup
  ya tomado (`routing-v8-*.db`) pasa `PRAGMA integrity_check` y conserva la fila corrupta intacta
  para inspección manual.

Corrida dirigida de los tres más el candado (sección siguiente), aisladas del resto de la suite:

```
$ python3 -m unittest tests.test_routing.RoutingTests.test_canonical_ddl_is_pinned_to_schema tests.test_routing.RoutingTests.test_b3_migrates_a_populated_schema_seven_into_usage_rollups_without_losing_the_run tests.test_routing.RoutingTests.test_b3f04_migrates_a_populated_schema_eight_into_the_typed_usage_rollups_check_without_losing_the_row tests.test_routing.RoutingTests.test_b3f04_migration_refuses_loudly_when_a_stored_sum_is_already_real_typed -v
test_canonical_ddl_is_pinned_to_schema (tests.test_routing.RoutingTests.test_canonical_ddl_is_pinned_to_schema)
The regression, made structurally impossible to repeat silently. ... ok
test_b3_migrates_a_populated_schema_seven_into_usage_rollups_without_losing_the_run (tests.test_routing.RoutingTests.test_b3_migrates_a_populated_schema_seven_into_usage_rollups_without_losing_the_run)
AC-06: a real schema-7-shaped fixture gets one schema-8 rollup and keeps its row. ... ok
test_b3f04_migrates_a_populated_schema_eight_into_the_typed_usage_rollups_check_without_losing_the_row (tests.test_routing.RoutingTests.test_b3f04_migrates_a_populated_schema_eight_into_the_typed_usage_rollups_check_without_losing_the_row)
023 B3-F04 follow-up (AC: the bump this repair adds): a real schema-8-shaped ... ok
test_b3f04_migration_refuses_loudly_when_a_stored_sum_is_already_real_typed (tests.test_routing.RoutingTests.test_b3f04_migration_refuses_loudly_when_a_stored_sum_is_already_real_typed)
023 B3-F04 follow-up: the documented decision in `_migrate_8_to_9`'s docstring, ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.302s

OK
```

### El test-candado: `test_canonical_ddl_is_pinned_to_schema`, mordido en las DOS direcciones

`tests/test_routing.py:1424` (`_ddl_fingerprint` en `:179`, `_CANONICAL_DDL_FINGERPRINTS` en
`:207`). Un SHA-256 sobre el DDL canónico completo (`RoutingStore._canonical_schema_sql()`),
pineado por valor de `SCHEMA` en un dict mantenido a mano; el test recalcula el digest del DDL
canónico ACTUAL y lo busca por el `SCHEMA` ACTUAL — sin fallback ni valor por defecto. Muerde en
dos direcciones independientes:

**Dirección 1 — un DDL cambia sin bumpear `SCHEMA`** (la regresión real de B3-F04, reproducida):
backup con `cp` (nunca `git checkout`), agregado un CHECK inocuo a `run_count` sin tocar
`SCHEMA`:

```
$ cp ai/scripts/routing_core/store.py <scratchpad>/store.py.bak
$ # edit: "run_count INTEGER NOT NULL CHECK(run_count >= 0)," ->
$ #       "run_count INTEGER NOT NULL CHECK(run_count >= 0) CHECK(run_count < 999999999),"
$ python3 -m unittest tests.test_routing.RoutingTests.test_canonical_ddl_is_pinned_to_schema -v
test_canonical_ddl_is_pinned_to_schema (tests.test_routing.RoutingTests.test_canonical_ddl_is_pinned_to_schema)
The regression, made structurally impossible to repeat silently. ... FAIL

======================================================================
FAIL: test_canonical_ddl_is_pinned_to_schema (tests.test_routing.RoutingTests.test_canonical_ddl_is_pinned_to_schema)
----------------------------------------------------------------------
Traceback (most recent call last):
  ...
AssertionError: '4c187bbd5ec281159896fa6e74d9fc64e20e72da9c1aec9dd5025ceb8a40aaf7' != 'a397159792ed60f3d7d607da49014a2ca58d354dbe0a14445a88e0cbb497e61a'
- 4c187bbd5ec281159896fa6e74d9fc64e20e72da9c1aec9dd5025ceb8a40aaf7
+ a397159792ed60f3d7d607da49014a2ca58d354dbe0a14445a88e0cbb497e61a
 : canonical DDL changed without a SCHEMA bump (or a migration step is missing for it) -- see routing_core/store.py's SCHEMA constant and _MIGRATION_STEPS; this is exactly the B3-F04 regression.

----------------------------------------------------------------------
Ran 1 test in 0.007s

FAILED (failures=1)
$ cp <scratchpad>/store.py.bak ai/scripts/routing_core/store.py
$ python3 -m unittest tests.test_routing.RoutingTests.test_canonical_ddl_is_pinned_to_schema -v
test_canonical_ddl_is_pinned_to_schema ... ok

Ran 1 test in 0.004s

OK
```

**Dirección 2 — `SCHEMA` se bumpea sin agregar la entrada nueva al fingerprint** (el otro medio
hueco: alguien podría "arreglar" la dirección 1 sólo copiando el digest viejo bajo la clave
nueva, que este assertIn impide):

```
$ cp ai/scripts/routing_core/store.py <scratchpad>/store.py.bak
$ # edit: "SCHEMA = 9" -> "SCHEMA = 10"
$ python3 -m unittest tests.test_routing.RoutingTests.test_canonical_ddl_is_pinned_to_schema -v
test_canonical_ddl_is_pinned_to_schema ... FAIL

======================================================================
FAIL: test_canonical_ddl_is_pinned_to_schema
----------------------------------------------------------------------
Traceback (most recent call last):
  ...
AssertionError: 10 not found in {9: 'a397159792ed60f3d7d607da49014a2ca58d354dbe0a14445a88e0cbb497e61a'} : SCHEMA bumped without a new _CANONICAL_DDL_FINGERPRINTS entry in tests/test_routing.py -- add one deliberately (never copy the previous value forward), after confirming the DDL change it accompanies is real.

----------------------------------------------------------------------
Ran 1 test in 0.006s

FAILED (failures=1)
$ cp <scratchpad>/store.py.bak ai/scripts/routing_core/store.py
$ python3 -m unittest tests.test_routing.RoutingTests.test_canonical_ddl_is_pinned_to_schema -v
test_canonical_ddl_is_pinned_to_schema ... ok

Ran 1 test in 0.004s

OK
$ diff <scratchpad>/store.py.bak ai/scripts/routing_core/store.py && echo IDENTICAL
IDENTICAL
```

Restaurado byte a byte las dos veces (`diff` sin salida, `IDENTICAL` impreso); nunca se usó `git
checkout`/`git restore`/`git stash`. `git diff ai/scripts/routing_core/store.py` en este repair
no muestra ningún resto de ninguna de las dos mordidas.

### Recuperación de la base real

Antes de tocar nada: snapshot independiente por `cp` (además de los dos backups que ya había
tomado el orquestador), y estado de partida confirmado:

```
$ sqlite3 ~/.local/state/set-agentes/routing-v2/routing.db "SELECT key,value FROM meta;"
schema_version|8
installation_hmac_salt|2beff1d82fbe4a4e04c1c51fe91d085130ce6c2a567484f9f33bdada0f1d97da
$ sqlite3 ~/.local/state/set-agentes/routing-v2/routing.db "SELECT COUNT(*) FROM dispatches;"
85
```

Migración real:

```
$ python3 ai/scripts/set_agents_app.py --routing-migrate
ROUTING_MIGRATE_OK from=8 to=9 rows=85 backup=/home/federico/.local/state/set-agentes/routing-v2/backups/routing-v8-20260814T034003Z.db
$ echo $?
0
```

Verificación posterior (base real, no un fixture):

```
$ sqlite3 ~/.local/state/set-agentes/routing-v2/routing.db "SELECT key,value FROM meta;"
schema_version|9
installation_hmac_salt|2beff1d82fbe4a4e04c1c51fe91d085130ce6c2a567484f9f33bdada0f1d97da
$ sqlite3 ~/.local/state/set-agentes/routing-v2/routing.db "SELECT COUNT(*) FROM dispatches;"
85
$ sqlite3 ~/.local/state/set-agentes/routing-v2/routing.db "PRAGMA integrity_check;"
ok
$ sqlite3 ~/.local/state/set-agentes/routing-v2/backups/routing-v8-20260814T034003Z.db "PRAGMA integrity_check;"
ok
```

Las 85 filas de `dispatches` sobreviven sin pérdida; el backup pre-migración (schema 8, tal como
estaba) pasa su propio `integrity_check`.

Ruteo real, post-migración — un `--route-decide` real contra la base de producción (rol
`product-analyst`/`docs-rw`, `role_class="other"`: ejercita `provider_exhausted` →
`self._connect()` → `_validate_existing_readonly` igual que cualquier rol, pero NUNCA llama
`_authorize_issued`/escribe `dispatches`, así que la verificación no deja un run colgado en la
base real):

```
$ echo '{"role":"product-analyst","task_class":"documentation","selected_runtime":"claude-code"}' \
  | python3 ai/scripts/set_agents_app.py --route-decide - --json
{"command": "route-decide", "data": {"bias_class": "decision", ... "execution_enabled": false,
 "family": "haiku", "model": "haiku", "provider": "anthropic", "role_class": "other",
 "route_id": "rt1_e9ddd428c6fad4fb", "run_id": null, "runtime": "claude-code",
 "reason_codes": ["BILLING_RANK provider=anthropic rank=0"], ... }, "ok": true,
 "reason_codes": ["BILLING_RANK provider=anthropic rank=0"], "schema_version": 2, "warnings": []}
$ echo $?
0
```

(`"data": {...}` recortado: la lista completa de 78 `exclusions` con `"RUNTIME_UNAVAILABLE"` —
runtimes efectivamente no probados en esta sesión de reparación— no aporta señal adicional; el
campo que importa es `"ok": true` con una decisión real, `route_id`/`model`/`provider` concretos,
y `run_id: null` confirmando que no se autorizó ningún dispatch.)

`ok:true` con una decisión concreta — **ya no `ROUTING_UNAVAILABLE`**. Confirmado además que
`dispatches` sigue en 85 filas después de esta llamada (sin escritura) y que
`sqlite_master.sql` de `usage_rollups` en la base real ya lleva el CHECK tipado en las seis
columnas.

**No se tocó ningún otro archivo bajo `~`** — sólo `~/.local/state/set-agentes/routing-v2/routing.db`
vía `--routing-migrate` (que hace su propio backup) y la lectura de `--route-decide`, exactamente
la única excepción autorizada para este repair.

### Gates de esta pasada

```
$ ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests
Ran 1102 tests in 516.223s
OK (skipped=3)
$ echo $?
0
```

(Una primera corrida completa, en paralelo con la recuperación de la base real de arriba, dio
`FAILED (failures=1, skipped=3)` con un único fallo en
`test_model_request.ModelRequestCliTests.test_model_request_does_not_bias_a_later_decide_call_without_it`
— fuera del alcance de este repair, `tests/test_model_request.py`, no `test_routing.py`. Aislado,
pasa solo (`OK`, 8.4s); la corrida completa repetida arriba, sin nada corriendo en paralelo, da
`OK` limpio — confirma flake por contención de recursos durante la corrida concurrente con la
migración real, no una regresión de este repair. `store.py`/`test_routing.py` no cambiaron entre
ambas corridas.)

```
$ ai/scripts/heartbeat-run.py --interval 20 -- ./ai/scripts/verify.sh
...
VERIFY_PASS
```

```
$ ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```

```
$ git diff --check
$ echo $?
0
```

### Alcance de esta pasada (la de recuperación urgente)

`ai/scripts/routing_core/store.py` y `tests/test_routing.py`: **cero cambios netos** — el bump,
la migración y el test-candado ya estaban correctos en el árbol de trabajo al empezar; este
repair los verificó (lectura completa + 4 tests dirigidos + mordida en dos direcciones,
restaurada byte a byte cada vez) en vez de reescribirlos. Único archivo modificado por este
repair: este archivo de evidencia. Único archivo tocado fuera del repo:
`~/.local/state/set-agentes/routing-v2/routing.db`, vía el único comando autorizado
(`--routing-migrate`), que hizo su propio backup — verificado íntegro arriba.

**No aprueba su propio trabajo.** Corresponde revisión independiente.
