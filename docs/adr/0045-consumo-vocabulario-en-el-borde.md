# ADR-0045 — Un vocabulario de consumo, traducido en el borde

- Estado: Accepted (2026-08-13). Feature 023-senales-de-consumo, PKG-B1
  (`B1-registro-que-no-miente`, AC-01..AC-03). No supersede nada. **Extendido por PKG-B2**
  (`B2-el-reporte-dice-de-donde-sale`, AC-04a/AC-04/AC-05, mismo día) — ver §§4-5 y la
  actualización de Consecuencias al final de este documento.

## Contexto

El plan original de 023 diagnosticaba que `opencode`/`claude-code` "mentían": cerraban runs con
`usage_status='ok'` y todas las columnas en NULL. **Ese diagnóstico era falso** y se re-midió antes
de implementar. Medido el 2026-08-13 en `~/.local/state/set-agentes/routing-v2/routing.db`, tabla
`dispatches`, 80 filas: **1** con números reales, **54** `absent` (claude-code 10, opencode 14, pi
30), **25** `NULL` (runs cerrados sin pasar uso en absoluto). `absent` no es un defecto —
`store.py:140-152` (ahora con la extensión de este ADR) lo documenta explícitamente: significa "el
proveedor no reportó nada", una respuesta legítima, no una mentira.

El defecto real es más simple y más grave: **nadie manda el uso nunca**. La flag existe
(`--usage JSON`, `set_agents_app.py:3641`, *"con --route-terminal: uso/costo del spawn"*), pero la
doctrina canónica no la menciona una sola vez (`grep -rn '\-\-usage' Global/_canonical/` → cero
resultados antes de este paquete) y el propio orquestador cerró unos veinte runs en la sesión del
2026-08-12/13 con `--route-terminal <id> success`, sin `--usage`, teniendo los tokens de cada
subagente a la vista en el resultado del spawn.

**Hallazgo adicional, medido durante la implementación de este paquete, no en el plan original**:
`claude_code_spawn.py:602-605` y `opencode_spawn.py:318-321` sí intentan adjuntar `--usage`
automáticamente en sus rutas de dispatch — pero en una forma que `_usage_row` (`store.py`) no
reconoce (`{"total_cost_usd":..., "modelUsage":{...}}` y `{"tokens":{...}}` respectivamente, ninguna
con las claves planas `input`/`output`/`cache_read`/`cache_write`/`reasoning`/`cost` que
`_usage_row` valida). Hoy esto no se manifestó como filas "ok con todo NULL" porque ambos
wrappers sólo adjuntan `--usage` cuando su propio campo (`modelUsage`/`tokens`) vino no-vacío, y
eso no ocurrió en los runs medidos — pero es un defecto latente, distinto del que este paquete
corrige, y **fuera de `ALCANCE`** de B1 (`claude_code_spawn.py`/`opencode_spawn.py`/
`codex_spawn.py` no están en la lista de archivos tocables). Queda nombrado aquí para que un futuro
paquete (candidato natural: B2, que ya toca los stores de los CLIs) lo repare importando
`ai/scripts/routing_core/usage.py` en vez de re-derivar el mapeo.

## Decisión

### 1. Un solo vocabulario plano, en `_usage_row` — sigue siendo el validador cerrado

`store.py`'s `_usage_row` sigue siendo la única función que decide `ok`/`absent`/`invalid`, y
**no se relaja**: cada caso ya-correcto (campo reconocido pero parcial, `{}`/`None` → `absent`,
valor con tipo/rango inválido → `invalid`) queda exactamente igual. La única adición es un
**endurecimiento**, nunca una relajación: un dict no vacío que no coincide con NINGÚN campo del
vocabulario (ni token conocido, ni `totalTokens`, ni `cost`) ahora es `invalid`, no `ok`. Antes de
este paquete, `{"campo_no_reconocido": 1}` devolvía silenciosamente la fila `ok` con todas las
columnas NULL — indistinguible de `{"cost": {"total": 0}}` (un `ok` disperso pero legítimo, AC-11)
y, en cualquier vista que sólo mira "¿las columnas son NULL?", indistinguible de `absent`. Ese es
precisamente el defecto que el paquete nombra: *"que se note la diferencia entre 'no reportó' y
'reportó basura'"*.

### 2. `ai/scripts/routing_core/usage.py` — el traductor, en el borde, nunca en el validador

Cada runtime tiene su propio formato de cable, genuinamente distinto (medido en vivo esta sesión,
2026-08-13, con el modelo más barato alcanzable y un prompt de una palabra — nunca inventado):

| Runtime | Comando medido | Forma real capturada |
|---|---|---|
| pi | ya medido y citado en `store.py:111-118` (spawn real, 2026-07-29) | `{"input":3321,"output":5,"reasoning":0,"totalTokens":3326,"cacheRead":0,"cacheWrite":0,"cost":{...}}` |
| claude-code | `claude --print --model haiku --output-format json --no-session-persistence "..."` | `{"total_cost_usd":0.0271811,"modelUsage":{"claude-haiku-4-5-...":{"inputTokens":10,"outputTokens":43,"cacheReadInputTokens":18101,"cacheCreationInputTokens":12573,"costUSD":0.0271811,...}}}` |
| opencode | `opencode run -m opencode/nemotron-3.5-lightning-free --format json "..."` | `{"tokens":{"total":30493,"input":30322,"output":0,"reasoning":197,"cache":{"write":0,"read":0}},"cost":0}` |
| codex | `codex exec --ephemeral --sandbox read-only -m gpt-5.6-luna -c model_reasoning_effort=low --json "..."` | `{"input_tokens":16057,"cached_input_tokens":8960,"cache_write_input_tokens":0,"output_tokens":5,"reasoning_output_tokens":0}` |

`ai/scripts/routing_core/usage.py` (nuevo) traduce cada una a la vocabulario plana de `_usage_row`,
con la muestra real pegada en el docstring de cada función/módulo. Donde la semántica de un campo
no se pudo verificar (ninguna referencia de esquema consultada, y la única muestra en vivo no lo
desambigua), queda **sin mapear, marcado UNVERIFIED en el docstring**, nunca supuesto:

- **claude-code**: `reasoning` no se mapea — esta forma no trae ningún campo de tokens de
  razonamiento, y no hay un total independiente contra el cual verificar una suma derivada.
- **opencode**: `tokens.total` NO se mapea a `totalTokens` — medido en vivo, `30493 !=
  30322+0+197+0+0` (`30519`): el "total" de opencode no suma los mismos cinco componentes que este
  vocabulario rastrea. Pasarlo como `totalTokens` haría que `_usage_row` descartara un reporte
  legítimo como `invalid` por el chequeo de suma.
- **codex**: `cached_input_tokens`/`cache_write_input_tokens` no se mapean — sin verificar si son
  aditivos o si ya están incluidos dentro de `input_tokens`; no hay `cost` en absoluto en este
  stream.

Este módulo **no se conecta a ningún punto de dispatch en este paquete** (deliberado: `ALCANCE` de
B1 no incluye `claude_code_spawn.py`/`opencode_spawn.py`/`codex_spawn.py`). Su consumidor en este
paquete es la doctrina del orquestador (§3 abajo) y sus propios tests — queda listo para que una
futura reparación de los wrappers lo importe en vez de re-derivar el mapeo.

### 3. La doctrina exige `--usage`, con el comando exacto, no un menú

`Global/_canonical/agents/orchestrator.md` gana un paso 8 explícito en el protocolo de tiered
dispatch: **imperativo**, con el comando `--route-terminal ... --usage '...'` pegado literalmente
por runtime, derivado mecánicamente de la tabla de arriba — nunca "podés pasar `--usage`". La
lección de ADR-0041 es literal: *"una regla escrita como menú es una regla que alguien va a elegir
no seguir"*. El caso que NO necesita `--usage` (el cierre de un worker perdido/muerto, paso 5; el
abandono antes de dispatch, 3a) se nombra explícitamente como excluido, porque `close_run` fuerza
`absent` en esa rama sin importar qué se pase — pedir `--usage` ahí sería ruido, no señal.

## Extensión — PKG-B2 (2026-08-13): el cableado que B1 dejó nombrado, y el doble conteo

B1 dejó dos cosas nombradas a propósito, no reparadas (§2 "no se conecta a ningún punto de
dispatch" y la nota "el hallazgo adicional... fuera de `ALCANCE`" en el Contexto de arriba):
que `claude_code_spawn.py:602-605`/`opencode_spawn.py:318-321` YA intentaban `--usage`, en
una forma que `_usage_row` no reconocía; y el riesgo de doble conteo entre `dispatches` (el
registro propio del harness) y los stores propios de cada CLI que `cost-report.py` lee. Este
paquete cierra ambos, dentro de su propio `ALCANCE` (`claude_code_spawn.py`/
`opencode_spawn.py`/`cost-report.py`/`tests/`).

### 4. El cableado: `routing_core/usage.py` importado en el borde real, no sólo citado en la doctrina

`claude_code_spawn.py:605-617` y `opencode_spawn.py:321-333` ahora importan y llaman
`normalize_claude_code`/`normalize_opencode` (de `routing_core.usage`, sin re-derivar el
mapeo) sobre la MISMA forma que ya extraían (`total_cost_usd`+`modelUsage` /
`{"tokens": {...}}`), justo antes de componer `--usage`. `_usage_row` no se toca: la
traducción sigue ocurriendo estrictamente en el borde, tal como este ADR ya decidía en su
§2 — la wiring es la única novedad, el mapeo mismo es el que B1 ya midió y no se re-deriva.

Medido con un dispatch real por lane (store real en disco, ciclo `--route-decide ->
--route-dispatched -> --route-terminal` real vía subproceso contra `set_agents_app.py`;
sólo el spawn del hijo LLM —`claude`/`opencode` mismos— está mockeado, con la muestra que
B1 ya midió en vivo, nunca inventada): `status_counts` pasa de `{}` a `{"ok": 1}` en vez de
`{"invalid": 1}` para los dos lanes (confirmado en rojo con el cableado revertido, y en
verde restaurado — `docs/specs/023-senales-de-consumo/evidence/B2-implementer.md`).

### 5. El doble conteo: dos secciones, nombradas por su fuente, nunca sumadas

`cost-report.py` arma DOS diccionarios de reporte separados y llama a `render()` dos veces
— nunca uno solo combinado:
- **Sección 1 — CLI-native stores**: `collect_opencode`+`collect_claude`+`collect_codex`,
  exactamente como antes de este paquete.
- **Sección 2 — harness dispatch registry**: `collect_pi` (que en realidad lee `dispatches`
  para TODO runtime que el harness despache — pi, y ahora también claude-code-lane/
  opencode-lane una vez que §4 los hace `ok` — no sólo el CLI `pi`; la etiqueta de fila
  `"pi"` sigue siendo cosmética, deliberadamente sin tocar, tal como el context pack de
  este paquete la nombra explícitamente fuera de alcance).

Cada `render()` imprime su propio título+fuente y su propio `TOTAL (..., this section
only)`; `main()` nunca suma los dos diccionarios entre sí — no hay ningún `report` dict que
contenga las dos fuentes a la vez — y el módulo imprime un disclaimer explícito al final:
las dos secciones miden el MISMO gasto solapado desde dos vantage points distintos (un
dispatch por el lane claude-code/opencode cuenta en las dos secciones a la vez desde que §4
existe), sumarlas duplicaría esa plata.

### 6. PKG-B3: el agregado es transaccional y la poda conserva procedencia

Schema 8 agrega `usage_rollups`: un agregado por ventana UTC, proyecto, identidad efectiva,
resultado y estado de uso. Cada campo numérico conserva además su cantidad de reportes; por eso
un cero informado no se confunde con un campo ausente al compactar. `close_run` actualiza el
dispatch y ese agregado en la misma transacción: datos de uso inválidos ya se vuelven la categoría
`invalid` antes de escribir, por lo que no impiden cerrar; un error real de SQLite revierte ambos,
sin dejar un cierre sin rollup ni un rollup sin cierre.

La compactación de `dispatches` comparte la transacción del escritor como la de `events`, y sólo
borra terminales que ya tienen su rollup. Conserva siempre un padre referenciado por
`replacement_of_run_id` y los 20 writers exitosos más recientes por proyecto que un reviewer
puede consultar. Si no puede demostrar esas condiciones, retiene la fila: el costo de disco es
preferible a perder evidencia de procedencia.

## Alternativas rechazadas

- **Relajar `_usage_row` para aceptar cualquier forma cruda de runtime directamente** (que el
  validador mismo intentara reconocer los cuatro formatos): rechazado — el paquete pide
  explícitamente que `_usage_row` "siga siendo el validador cerrado", y mezclar la traducción
  dentro del validador es exactamente la clase de acoplamiento que ADR-0045 nombra en el título:
  el vocabulario se traduce EN EL BORDE, se valida en un solo lugar cerrado.
- **Adivinar la forma de `codex`'s campos de cache o el `totalTokens` de `opencode`**: rechazado
  explícitamente por la instrucción del paquete ("si no podés medir la forma real de algún runtime,
  escribí 'sin verificar' en vez de suponerla") — un campo mal mapeado que pasa validación en
  silencio es peor que un campo ausente que se nota.
- **Conectar `usage.py` a `claude_code_spawn.py`/`opencode_spawn.py` en este mismo paquete para
  cerrar también el defecto latente hallado**: fuera de `ALCANCE` de B1 — nombrado como hallazgo
  para un paquete futuro, no reparado aquí, para no ensanchar el diff de un paquete ya delimitado.

## Consecuencias

- `_usage_row` distingue ahora tres casos reales, no dos: "no reportó" (`absent`), "reportó algo
  que entendimos" (`ok`, aunque sea disperso), y "reportó algo que no reconocemos" (`invalid`,
  nuevo). Ningún caso previamente `ok`/`absent` cambia de valor.
- La doctrina da al orquestador el mapeo exacto por runtime, listo para copiar, con la fuente de
  verdad (`usage.py`) nombrada explícitamente para que un cambio de formato futuro se corrija ahí
  primero, nunca sólo en el prosa de la doctrina.
- El defecto latente en `claude_code_spawn.py`/`opencode_spawn.py` (usage adjuntado en una forma
  que `_usage_row` no reconoce) quedó documentado en PKG-B1 y **se cerró en PKG-B2** (§4 arriba):
  ambos lanes ahora traducen antes de componer `--usage`, reusando el mismo traductor.
- `cost-report.py` (PKG-B2, §5 arriba) ya no puede producir un total que sume dos mediciones del
  mismo gasto — estructuralmente, no por convención: no existe ningún `report` dict que contenga
  las dos fuentes a la vez, y cada sección imprime su propio total con su propio nombre.
- El label `"pi"` por fila en la Sección 2 de `cost-report.py` sigue siendo impreciso para
  dispatches claude-code/opencode-lane cerrados por el harness — nombrado, deliberadamente sin
  reparar (cosmético, ver el context pack de PKG-B2).
- Rollups/retención (B3) y estimación (B4) quedan fuera de este ADR, tal como los nombra el
  context pack de B1 (y el de B2, que tampoco los toca).

## Evidencia

`docs/specs/023-senales-de-consumo/evidence/B1-implementer.md` (PKG-B1) y
`docs/specs/023-senales-de-consumo/evidence/B2-implementer.md` (PKG-B2).
