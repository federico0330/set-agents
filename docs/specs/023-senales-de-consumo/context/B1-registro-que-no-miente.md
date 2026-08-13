# Context pack — B1-registro-que-no-miente

Spec: `docs/specs/023-senales-de-consumo/spec.md`, **AC-01, AC-02, AC-03**. Primer paquete de 023 y
**bloqueante**: ningún otro arranca hasta que haya datos por runtime.

## Leé esto primero: el diagnóstico del plan era falso y se re-midió

El plan A→B→C decía que `opencode` y `claude-code` persisten `usage_status='ok'` con todo en NULL,
o sea que **mienten**. **Es falso.** Medido el 2026-08-13 en
`~/.local/state/set-agentes/routing-v2/routing.db`, tabla `dispatches`, 80 filas:

| `usage_status` | filas | detalle |
|---|---|---|
| con números reales | **1** | `usage_input=3321, usage_output=5, cost_micros=3351` |
| `absent` | 54 | claude-code 10, opencode 14, pi 30 |
| `NULL` | 25 | runs cerrados sin pasar uso |

**`absent` no es un defecto.** `_usage_row` lo documenta explícitamente (`store.py:140-152`):
significa "el proveedor no reportó nada", y NULL significa "no reportado" mientras 0 significa
"reportado como cero". Esa distinción **es la que este paquete tiene que preservar**, no borrar.

## El defecto real, y es más simple

**Nadie manda el uso nunca.**

- La flag existe: `set_agents_app.py:3641`, `--usage JSON`, *"con --route-terminal: uso/costo del
  spawn"*.
- La doctrina canónica **no la menciona una sola vez**: `grep -rn '\-\-usage' Global/_canonical/`
  da **cero**.
- El propio orquestador cerró **unos veinte runs** en la sesión del 2026-08-12/13 con
  `--route-terminal <id> success`, **sin `--usage`**, teniendo los tokens de cada subagente a la
  vista en el resultado del spawn.

O sea: no hay un normalizador roto procesando datos malos. **No llegan datos.**

## TAREA

**AC-01 — que el uso efectivamente llegue.** Es lo primero y lo que desbloquea todo.

`Global/_canonical/agents/orchestrator.md` pasa a exigir `--usage` al cerrar un run, con el formato
exacto por runtime. **Imperativo, no un menú** — la lección de ADR-0041 es literal: *"una regla
escrita como menú es una regla que alguien va a elegir no seguir"*, y ahí murieron ocho agentes por
un `tail`. Escribí **el comando exacto pegado**, no "podés pasar `--usage`".

Después de tocar `Global/_canonical/`: **`./build.sh` y luego `./build.sh --check`**. Si te da
`GLOBAL_TREE_DRIFT`, te faltó el `build.sh`.

**AC-02 — el normalizador.** `ai/scripts/routing_core/usage.py`, con **la muestra real del cable por
runtime pegada en el docstring**, no un esquema inventado. Si no podés medir la forma real de algún
runtime, **decilo "sin verificar"** en vez de suponerla.

`_usage_row` sigue siendo el validador cerrado y **no se relaja**. En particular: `absent` sigue
significando lo que significa hoy. Si tu cambio hace que un `absent` legítimo pase a `invalid`,
rompiste algo que funcionaba.

**AC-03 — la prueba.** Por runtime: las columnas quedan **no-NULL** cuando el uso se manda. Y un
dict **no vacío** sin ningún campo reconocido se cuenta como `'invalid'`, no pasa por bueno.
Evidenciado con `status_counts` **antes y después**, no con una afirmación.

## Lo que NO es este paquete

- **No inventes números.** Si un runtime no reporta, `absent` es la respuesta correcta.
- **No toques el sort key**: el consumo no es factor de ruteo, es información para el humano.
- No estimes nada: eso es B4.
- No toques `cost-report.py`: es B2.

## Restricciones

- **ADR-0045** (`ls docs/adr/` para confirmar que está libre, indexalo en `docs/adr/README.md`): un
  vocabulario de consumo, traducido en el borde.
- **No uses `git checkout`, `git restore` ni `git stash`.** Para morder y restaurar: `cp` y `cp`.
- **No toques la base real del usuario** (`~/.local/state/set-agentes/routing-v2/routing.db`).
  Fixtures y stores temporales.
- `tests/test_harness.py` assertea frases doctrinales por grep: `grep -n` antes de mover texto en
  `Global/_canonical/`.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**; base **1080 OK / 3 skips**)
· `./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh && ./build.sh --check` →
`GLOBAL_TREE_SYNC_OK` + `BUILD_CHECK_PASS` · `git diff --check` limpio.

**Corré los comandos largos así:** `ai/scripts/heartbeat-run.py --interval 20 -- <comando>`. La
suite tarda ~10 min; sin `-f`, `tail` no emite un byte hasta EOF y el watchdog te mata a los 600 s.

## Evidencia

`docs/specs/023-senales-de-consumo/evidence/B1-implementer.md`, escrito **en el primer minuto**:
tabla AC → cambio (`archivo:línea`) → prueba; **la muestra real del cable por runtime, o "sin
verificar" donde no la tengas**; `status_counts` antes y después sobre un store de fixture; la
prueba de que un `absent` legítimo sigue siendo `absent`; y los gates.

**Por cada test nuevo: neutralizá el cambio, confirmá el rojo, revertí, pegá la prueba.** En 022
aparecieron **cuatro** guardas que decían cubrir algo que no miraban.

**Cada bloque literal, o marcado como recortado.** Si no lo corriste, "sin verificar".

## Fuera de alcance

El doble conteo con los stores de los CLIs (B2) · rollups y retención (B3) · estimación (B4) · el
sort key · `context_window` · el aislamiento roto de los módulos de test (preexistente, registrado).
