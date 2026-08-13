# Context pack — B3-ventana-y-rollup

Spec: `docs/specs/023-senales-de-consumo/spec.md`, **AC-06, AC-07**. Depende de **B2**, ya aceptada.

## Estado medido de la base

`~/.local/state/set-agentes/routing-v2/routing.db`, hoy:

| | |
|---|---|
| `schema_version` en `meta` | **7** |
| `dispatches` | 82 filas |
| `events` | 200 filas |
| `metric_rollups` | 20 filas |
| con `replacement_of_run_id` | **0** |

Ya existe precedente de retención **para `events`**: índices `events_retention` y
`events_route_retention` (`store.py:426`), y un `DELETE FROM events WHERE …` (`:946`) cuya
compactación **comparte la transacción del escritor** (`:682`: *"Compaction shares the writer's
transaction: the retention bound holds"*). **Copiá esa forma; no inventes otra.**

`dispatches` **no tiene retención**: crece sin límite.

## TAREA

**AC-06** — Schema **8** con `usage_rollups`, escrito **en la misma transacción** que `close_run`
(`store.py:857`). Si el rollup no entra, el run tampoco: no puede haber un run cerrado sin su
rollup, ni un rollup sin su run.

`close_run` ya documenta su propia disciplina transaccional (`:857-870`: *"Close ANY run_id in one
transaction"*, y *"`usage` never aborts the close"*). **Esa segunda regla no se rompe**: el rollup
tampoco puede abortar el cierre. Resolvelo dentro de la transacción, no relajándola.

Hay tres migraciones de precedente para copiar la forma: `_migrate_4_to_5:550`,
`_migrate_5_to_6:557`, `_migrate_6_to_7:566`.

**AC-07** — Retención de `dispatches`. Dos reglas duras:

1. **Nunca** borra una fila referenciada por `replacement_of_run_id` — hay un índice único
   dedicado (`dispatches_one_replacement`, `:426`) que existe justamente porque esa relación
   importa.
2. **Nunca** borra una fila que un reviewer todavía pueda consultar. El índice `dispatches_review`
   (`project_key, role, state, terminal_at`) te dice cuál es la vía de consulta que hay que
   respetar.

**Hoy hay 0 filas con `replacement_of_run_id`**, así que ese caso **no lo podés validar contra el
estado real**: construilo con fixture y decilo así en la evidencia en vez de sugerir que lo
verificaste en vivo.

## La trampa

Una retención que borra de más es **pérdida de evidencia silenciosa** — y este harness usa
`dispatches` como registro de procedencia de cada spawn. Si borrás una fila que un review necesita,
el defecto aparece meses después y no hay forma de reconstruirlo.

**Ante la duda, no borres.** Un `dispatches` grande es un problema de disco; uno podado de más es
un problema de auditoría.

## Restricciones

- **Extendé ADR-0045**, no crees uno nuevo.
- **No toques `_usage_row`** ni los normalizadores de B1/B2.
- **No estimes nada**: eso es B4.
- **No toques el sort key.**
- **No uses `git checkout`, `git restore` ni `git stash`.** Para morder y restaurar: `cp` y `cp`.
- **No toques la base real del usuario.** Stores temporales y fixtures. Una migración mal probada
  sobre su base le rompe el historial de ruteo.
- **Arreglá de paso el docstring de `usage.py:21-24`**, que dice que el módulo "no se conecta a
  ningún punto de dispatch": desde B2 eso es falso para claude-code y opencode, y sigue siendo
  cierto sólo para `codex_spawn.py`. Es una línea y lo flageó el implementer de B2.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**; base **1095 OK / 3 skips**)
· `./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → `GLOBAL_TREE_SYNC_OK` +
`BUILD_CHECK_PASS` · `git diff --check` limpio.

**Corré los comandos largos así:** `ai/scripts/heartbeat-run.py --interval 20 -- <comando>`
(ADR-0041).

## Evidencia

`docs/specs/023-senales-de-consumo/evidence/B3-implementer.md`, escrito **en el primer minuto**:
tabla AC → cambio (`archivo:línea`) → prueba; **la migración 7→8 corrida sobre un store de fixture
con datos**, mostrando que no pierde nada; la prueba de que un fallo del rollup **no** deja un run
cerrado a medias; los dos casos de retención que **no** deben borrar, con fixture; y los gates.

**Por cada test nuevo: neutralizá el cambio, confirmá el rojo, revertí, pegá la prueba.** En 022
aparecieron cuatro guardas falsas; en B1 y B2 ninguna. Mantené la racha.

**Cada bloque literal, o marcado como recortado.** Si no lo corriste, "sin verificar".

## Fuera de alcance

La estimación y las etiquetas `ESTIMADO` (B4) · el sort key · `context_window` · la etiqueta `"pi"`
por fila de `cost-report.py` (cosmética, registrada) · el aislamiento roto de los módulos de test
(preexistente, registrado).
