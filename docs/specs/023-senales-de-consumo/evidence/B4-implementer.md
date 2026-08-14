# B4-estimado-nunca-dato-del-proveedor — evidencia del implementer

Último paquete de 023-senales-de-consumo. Depende de B3 (schema 9, `usage_rollups` con el par
suma/`reported_count`, ya aceptado). No se tocó `_usage_row`, `service.py` (sort key) ni
`reason_codes` — verificado por grep, cero resultados nuevos ahí.

## Tabla AC → cambio → prueba

| AC | Cambio | Prueba |
|---|---|---|
| AC-08 (ningún estimado viaja solo) | `ai/scripts/cost-report.py:499-527` (`format_metric_estimate`, la única función que compone una línea de "restante": consumido crudo, cobertura `reported/run_count`, ventana ISO exacta, y — sólo con budget — `ESTIMADO`/`provider_reported: false`/`basis`) + `:436-454` (`window_bounds`/`window_label`, ventana nombrada por su rango exacto, no relativa) + `:456-497` (`collect_estimate`, lee `usage_rollups` sin promediar sobre lo no reportado) | `tests/test_harness.py:7911` (`test_estimate_reports_measured_consumption_with_named_window_and_coverage`) — cobertura 12/40 y ventana ISO exacta en la salida real; `tests/test_harness.py:7941` (`test_estimate_shows_remaining_only_with_declared_budget_labeled_estimado`) — las cuatro piezas en la MISMA línea |
| AC-09 (guard test, ratchet estructural) | `ai/scripts/cost-report.py:499-527` (un único call site que arma el literal `"  restante estimado: "`) | `tests/test_harness.py:7987` (`test_cost_report_restante_has_exactly_one_render_site`) — cuenta el marcador en el código fuente, exige exactamente 1 |
| AC-10 (sin presupuesto no hay "restante") | `ai/scripts/cost-report.py:508-518` (el `if budget is not None:` es la ÚNICA rama que agrega la línea de restante) + `:413-434` (`parse_budgets`, valida `FIELD=N` explícito, dies loudly ante FIELD desconocido o N no entero, nunca infiere) + `:627-634` (validado ANTES de imprimir nada, en `main`) | `tests/test_harness.py:7964` (`test_estimate_never_shows_remaining_without_declared_budget`) — sin `--budget`, el marcador de VALOR (`"restante estimado:"`) no aparece en ningún campo, sólo "consumido en la ventana" |
| — (pin de la ventana) | `ai/scripts/cost-report.py:70` (`_DAY_MS = 86400000`, duplicado de `routing_core/store.py` porque `cost-report.py` no importa código del repo, AC-16) | `tests/test_routing.py:1623` (`test_cost_report_day_ms_matches_store`) — pinnea contra `routing_store._DAY_MS` |
| ADR-0046 | `docs/adr/0046-estimado-es-estimado.md` (nuevo), indexado en `docs/adr/README.md` | `tests/test_harness.py::test_every_adr_on_disk_has_a_row_in_the_index` / `test_the_adr_index_never_lists_a_file_that_is_not_there` (ya existentes, corridas contra el ADR nuevo) |

`ai/scripts/set_agents_app.py` fue inspeccionado (`grep -n "restante\|remaining_quota\|ESTIMADO"` →
cero resultados antes y después) y no tiene ninguna superficie de "restante"/cuota hoy — la única
superficie de este paquete es `cost-report.py`. No se tocó.

## Diseño de la superficie

`cost-report.py` gana una Section 3 ("ESTIMADO"), separada de las Secciones 1/2 (B2, AC-04/AC-05
sin tocar — el disclaimer "never summed" de esas dos sigue intacto y sin modificar una palabra).
Lee `usage_rollups` (schema 9) para la ventana UTC-día vigente (`--window-start` para tests
deterministas, oculto de `--help`, igual que `--home`), por cada uno de los cinco campos de token
(`FIELDS` — **tokens únicamente**, misma doctrina "what matters is quota" que el propio docstring
del módulo ya declaraba para las Secciones 1/2; `cost_micros` queda fuera de esta superficie,
consistente con esa decisión previa, no reabierta aquí).

`--budget FIELD=N` (repetible) es la ÚNICA fuente de un presupuesto — nunca inferido, nunca un
horario de reset asumido. Un campo sin `--budget` sólo muestra lo medido + su cobertura.

## Salida literal — CON presupuesto declarado (`--budget input=1000000`)

Fixture: `usage_rollups` con `run_count=40`, `usage_input_sum=120000`,
`usage_input_reported_count=12` (el ejemplo exacto del context pack, 12 de 40).

```
Section 3 -- ESTIMADO (source: routing.db usage_rollups, window 2023-08-14T00:00:00+00:00 to 2023-08-15T00:00:00+00:00 (UTC calendar day, usage_rollups.window_start))
======================================================================================================================================================================
input: consumido en la ventana = 120000 (medido, no proyectado)
  ventana: 2023-08-14T00:00:00+00:00 to 2023-08-15T00:00:00+00:00 (UTC calendar day, usage_rollups.window_start)
  cobertura: 12/40 runs reportaron input en esta ventana
  restante estimado: 880000 -- ESTIMADO, provider_reported: false, basis: presupuesto declarado (1000000) menos input consumido y medido en la ventana (120000); cobertura 12/40 runs reportaron input en esta ventana; nunca proyectado sobre los runs que no reportaron
output: consumido en la ventana = 45000 (medido, no proyectado)
  ventana: 2023-08-14T00:00:00+00:00 to 2023-08-15T00:00:00+00:00 (UTC calendar day, usage_rollups.window_start)
  cobertura: 12/40 runs reportaron output en esta ventana
cache_read: consumido en la ventana = 8000 (medido, no proyectado)
  ventana: 2023-08-14T00:00:00+00:00 to 2023-08-15T00:00:00+00:00 (UTC calendar day, usage_rollups.window_start)
  cobertura: 10/40 runs reportaron cache_read en esta ventana
cache_write: consumido en la ventana = 500 (medido, no proyectado)
  ventana: 2023-08-14T00:00:00+00:00 to 2023-08-15T00:00:00+00:00 (UTC calendar day, usage_rollups.window_start)
  cobertura: 10/40 runs reportaron cache_write en esta ventana
reasoning: consumido en la ventana = 2000 (medido, no proyectado)
  ventana: 2023-08-14T00:00:00+00:00 to 2023-08-15T00:00:00+00:00 (UTC calendar day, usage_rollups.window_start)
  cobertura: 6/40 runs reportaron reasoning en esta ventana

No provider exposes remaining quota (measured -- the permitted commands answer authenticated yes/no and which models list, nothing about quota). Every "restante" line above is an ESTIMATE computed from this harness's OWN measured consumption against a budget YOU declared with --budget FIELD=N -- never data the provider reported (ADR-0046). A field with no --budget shows only what was measured, never a guessed remainder (AC-10).
```

Nótese: `input` (con `--budget input=1000000`) es el ÚNICO campo con línea de "restante" — los
otros cuatro (`output`, `cache_read`, `cache_write`, `reasoning`) muestran únicamente lo medido +
cobertura, exactamente AC-10.

## Salida literal — SIN presupuesto declarado (mismo fixture, sin `--budget`)

```
Section 3 -- ESTIMADO (source: routing.db usage_rollups, window 2023-08-14T00:00:00+00:00 to 2023-08-15T00:00:00+00:00 (UTC calendar day, usage_rollups.window_start))
======================================================================================================================================================================
input: consumido en la ventana = 120000 (medido, no proyectado)
  ventana: 2023-08-14T00:00:00+00:00 to 2023-08-15T00:00:00+00:00 (UTC calendar day, usage_rollups.window_start)
  cobertura: 12/40 runs reportaron input en esta ventana
output: consumido en la ventana = 45000 (medido, no proyectado)
  ventana: 2023-08-14T00:00:00+00:00 to 2023-08-15T00:00:00+00:00 (UTC calendar day, usage_rollups.window_start)
  cobertura: 12/40 runs reportaron output en esta ventana
cache_read: consumido en la ventana = 8000 (medido, no proyectado)
  ventana: 2023-08-14T00:00:00+00:00 to 2023-08-15T00:00:00+00:00 (UTC calendar day, usage_rollups.window_start)
  cobertura: 10/40 runs reportaron cache_read en esta ventana
cache_write: consumido en la ventana = 500 (medido, no proyectado)
  ventana: 2023-08-14T00:00:00+00:00 to 2023-08-15T00:00:00+00:00 (UTC calendar day, usage_rollups.window_start)
  cobertura: 10/40 runs reportaron cache_write en esta ventana
reasoning: consumido en la ventana = 2000 (medido, no proyectado)
  ventana: 2023-08-14T00:00:00+00:00 to 2023-08-15T00:00:00+00:00 (UTC calendar day, usage_rollups.window_start)
  cobertura: 6/40 runs reportaron reasoning en esta ventana

No provider exposes remaining quota (measured -- the permitted commands answer authenticated yes/no and which models list, nothing about quota). Every "restante" line above is an ESTIMATE computed from this harness's OWN measured consumption against a budget YOU declared with --budget FIELD=N -- never data the provider reported (ADR-0046). A field with no --budget shows only what was measured, never a guessed remainder (AC-10).
```

**Cero apariciones de `"restante estimado:"` en esta salida** (grep confirmado, y es exactamente
lo que `test_estimate_never_shows_remaining_without_declared_budget` pinnea contra el proceso
real, no contra un mock).

Ambas salidas: corridas reales de `python3 ai/scripts/cost-report.py` contra una fixture SQLite
armada a mano en `/var/tmp` (nunca la base real del usuario), capturadas literalmente, no
recortadas.

## `--budget` inválido falla fuerte, antes de imprimir nada

```
$ python3 ai/scripts/cost-report.py --home /tmp --budget bogus=5
cost-report.py: --budget 'bogus=5' -- FIELD must be one of input, output, cache_read, cache_write, reasoning, given as FIELD=N
$ echo $?
1
$ python3 ai/scripts/cost-report.py --home /tmp --budget input=notanumber
cost-report.py: --budget 'input=notanumber' -- N must be an integer
$ echo $?
1
```

Corrido sin pipe a `tail` (para no perder el exit code real por el de `tail`); nada se imprime
antes del error -- `parse_budgets` se valida al principio de `main()`, antes de las Secciones 1/2.

## Guard test AC-09 — mordida en las dos direcciones, cada test neutralizado y revertido

Para cada uno de los 4 tests nuevos de comportamiento/estructura, se corrió la secuencia
neutralizar → confirmar rojo → revertir → confirmar verde, contra el archivo real (`cp` de
respaldo, nunca `git checkout`/`stash`). Las 4 mutaciones y sus rojos exactos:

1. **`test_estimate_reports_measured_consumption_with_named_window_and_coverage`** — mutación:
   `coverage` hardcodeado a `f"{run_count}/{run_count}"` (el bug de la trampa: fingir cobertura
   completa). Rojo:
   ```
   AssertionError: '12/40 runs reportaron input' not found in '...cobertura: 40/40 runs reportaron input en esta ventana...'
   ```
2. **`test_estimate_shows_remaining_only_with_declared_budget_labeled_estimado`** — mutación: se
   quita `provider_reported: false` del f-string de la línea de restante. Rojo:
   ```
   AssertionError: 'ESTIMADO' not found in '  restante estimado: 880000 -- basis: presupuesto declarado (1000000) menos input consumido y medido en la ventana (120000); cobertura 12/40 runs reportaron input en esta ventana; nunca proyectado sobre los runs que no reportaron'
   ```
3. **`test_estimate_never_shows_remaining_without_declared_budget`** — mutación: se borra el
   `if budget is not None:` (el "restante" se imprime SIEMPRE, budget default 0 — la violación
   exacta de AC-10). Rojo:
   ```
   AssertionError: 'restante estimado:' unexpectedly found in '...restante estimado: -120000 -- ESTIMADO, provider_reported: false, basis: presupuesto declarado (None) menos input consumido...'
   ```
4. **`test_cost_report_restante_has_exactly_one_render_site`** — mutación: se agrega un segundo
   `print("  restante estimado: " + "999")` al principio de `render_estimate` (un bypass del
   formateador guardado). Rojo:
   ```
   AssertionError: 2 != 1 : a new site writes "restante" text outside format_metric_estimate -- AC-09's whole point is that this is caught here, not discovered later on a live surface missing its label/basis
   ```

Las 4 mutaciones se revirtieron con `cp` desde el respaldo (`diff` byte-a-byte confirmado
idéntico al original), y las 4 pruebas + el pin de `_DAY_MS` volvieron a pasar en verde:

```
test_estimate_reports_measured_consumption_with_named_window_and_coverage ... ok
test_estimate_shows_remaining_only_with_declared_budget_labeled_estimado ... ok
test_estimate_never_shows_remaining_without_declared_budget ... ok
test_cost_report_restante_has_exactly_one_render_site ... ok
test_cost_report_day_ms_matches_store ... ok
----------------------------------------------------------------------
Ran 5 tests in 0.310s

OK
```

Ningún test viejo de `cost-report.py` (Section 1/2, `collect_pi`, project-identity) se tocó ni
cambió de comportamiento — corridos junto a los nuevos, 15/15 OK (ver arriba).

## Gates

Los cuatro corridos reales, en orden, contra el árbol con los cambios de este paquete
(`ai/scripts/heartbeat-run.py --interval 20 -- <comando>` para los dos largos, ADR-0041 --
nunca pipeados a `tail`, lección aprendida en el camino: un primer intento sí lo hizo, se
mató y se corrió de nuevo limpio).

### `python3 -m unittest discover -s tests`

```
----------------------------------------------------------------------
Ran 1107 tests in 872.472s

OK (skipped=3)
```
Base declarada por el context pack: **1102 OK / 3 skips**. Este paquete agregó 5 tests
(4 en `tests/test_harness.py`, 1 en `tests/test_routing.py`) → 1107, 3 skips intactos, **cero
fallas**. Sin `pytest` (no está instalado, confirmado antes de empezar).

### `./ai/scripts/verify.sh`

```
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
...
Ran 1107 tests in 817.455s

OK (skipped=3)
...
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```
(salida completa: 1408 líneas, incluye ejecución completa de la suite otra vez dentro del
script + los chequeos de portabilidad/paths/feature-state; recortado acá a los marcadores de
paso — el archivo íntegro quedó en el output del proceso en background durante la corrida,
sin fallas ni tracebacks, grep confirmado: cero `FAILED`/`ERROR:`/`Traceback`).

### `./build.sh --check`

```
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```

### `git diff --check`

```
$ git diff --check
$ echo $?
0
```
Limpio.

## Alcance final

Tocado: `ai/scripts/cost-report.py`, `tests/test_harness.py`, `tests/test_routing.py`,
`docs/adr/0046-estimado-es-estimado.md` (nuevo), `docs/adr/README.md`, este archivo de
evidencia. `ai/scripts/set_agents_app.py` fue inspeccionado y no requirió cambios (sin
superficie de "restante" propia). No se tocó `service.py`, `reason_codes`, `_usage_row`, el
esquema de B3, ni la base real del usuario.

Estado: **COMPLETO** — AC-08/AC-09/AC-10 implementados y probados, los 4 gates en verde.
