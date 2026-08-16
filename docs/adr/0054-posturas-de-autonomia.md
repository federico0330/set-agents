# ADR-0054 — Posturas de autonomía: un parámetro leído en runtime, no un rebuild

- Estado: Accepted (2026-08-16). Feature 025-consola-minima-y-flexible, PKG-3
  (`D3-posturas-de-autonomia`). AC-06, AC-07, AC-08.

## Contexto

La doctrina de "cuánto actúa el harness por su cuenta" (ADR-0025 resolve-first, ADR-0037 resolvé
antes de preguntar, MCP enable→use→disable) es hoy una **constante**: prosa horneada en `~` en
tiempo de instalación, duplicada en cinco archivos fuente
(`Global/_canonical/agents/orchestrator.md:558,607,673,697,507,543,493`,
`Global/_shared/CLAUDE.md:57,73,87` y los tres `AGENTS.{opencode,codex,pi}.md` equivalentes). El
usuario pidió tres posturas elegibles (Autónoma / Consultiva / Todo consultado, AC-06) más los
toggles de metodología TDD estricto/RDD/SDD (AC-07/AC-08).

`ai/scripts/coord_policy.py` (327 líneas de allowlist de comandos bash) **no** es donde vive la
constante — gobierna qué comando puede correr un agente, no cuánto pregunta — y quedó fuera de
alcance de este paquete (acaba de recibir una reparación de seguridad crítica, ADR-0059).

## El problema real: el canal

Un valor en `config.toml` no cambia sola la conducta de un agente si nada lo lee. Tres canales
posibles, cada uno con costo distinto:

1. **Renderizar la doctrina según la postura en tiempo de instalación** (parametrizar
   `generate.py`/`install.py`). Simple de escribir, pero **cambiar de postura exige reinstalar**
   — deja de ser un toggle y pasa a ser una variante de build. Además `install.py` está fuera de
   alcance de este paquete.
2. **Inyectar la postura en el texto de cada spawn** (`compose_task`,
   `claude_code_spawn.py:309` y los spawners de los otros tres runtimes). Es un toggle de verdad
   — cambiar `config.toml` cambia la conducta del próximo spawn sin reinstalar — pero toca los
   cuatro spawners, territorio de 025/D5 (`vault-en-todo-spawn`) en paralelo. Fuera de alcance:
   `ai/scripts/*_spawn.py` están explícitamente prohibidos para este paquete.
3. **Un archivo de postura que los agentes leen.** Correcto en el fondo, pero como estaba
   planteado en el context pack ("necesita que algo se lo diga al agente") reabre el problema 2:
   si nadie apunta al agente hacia ese archivo, es letra muerta.

## Decisión

**Variante de la opción 3, sin tocar spawners ni `install.py`**: la doctrina **estática**
(`Global/_canonical/agents/orchestrator.md`, horneada una sola vez por instalación, exactamente
como hoy) gana dos secciones nuevas — "Postura de autonomía" y "Metodología preferida" — que
instruyen al agente a **leer, en runtime, con su herramienta de lectura de archivos (no shell)**,
la clave `postura`/`metodologia_preferida` de `~/.local/state/set-agentes/config.toml` antes de
resolver una acción que muta o una delegación, y aplicar la tabla que esa misma sección cita
verbatim.

Por qué esto SÍ es un toggle real y no la opción 1 disfrazada: lo único horneado en `~` es la
*instrucción de leer el archivo* (idéntica para las tres posturas). El *valor* que esa instrucción
resuelve vive en `config.toml`, mutable en cualquier momento sin build ni reinstalación —
exactamente el mismo patrón que `ai/state/STATUS.md`/`decisions-log.jsonl` ya usan para que un
agente lea estado dinámico desde una doctrina estática. Requiere UNA sola reinstalación (para que
la instrucción misma llegue a `~`), y después de esa, cambiar de postura es editar `config.toml` —
nunca más un rebuild.

Por qué no la opción 2: tocar `*_spawn.py` mientras D5 trabaja ahí es el conflicto de merge que
el propio pedido pidió evitar explícitamente ("si concluís que la opción correcta toca los
spawners... parenlo"). La opción elegida no necesita tocarlos porque el rol que decide "¿pregunto o
actúo?" (Question policy, Tool catalog, Turn continuity) ya vive en `orchestrator.md`, el mismo
archivo que ahora lee la postura — no hace falta que el TEXTO DE LA TAREA de un spawn cargue el
valor, alcanza con que el propio orquestador lo consulte antes de decidir.

Store: **ninguno nuevo** (regla explícita del paquete) — `postura`/`metodologia_preferida` son dos
claves más del `config.toml` existente (`APP_CONFIG`, `write_app_config`, el mismo lector
read-merge-write que ya usa `auto_update`/`vault`, AC-15). Superficie:
`ai/scripts/set_agents_app.py` — `POSTURAS`/`postura_actual()`/`set_postura()`/`cmd_posturas()`
(`--posturas`, `--postura {autonoma,consultiva,todo_consultado}`) y el mismo molde para
`METODOLOGIAS`/`metodologia_preferida()`/`set_metodologia()`/`cmd_metodologias()`
(`--metodologias`, `--metodologia {sdd,rdd,off}`).

**Default = conducta de hoy, byte por byte**: `postura_actual()` sin clave devuelve `"autonoma"`
— exactamente ADR-0025/ADR-0037 sin cambios — y `metodologia_preferida()` sin clave devuelve
`""` — ninguna preferencia forzada, exactamente el comportamiento actual de `request-triage`/
`package-planner`.

### RDD (AC-08) — reconciliación, no invención

La spec de este paquete decía que el harness "practica RDD sin nombrarlo". Es inexacto: la sigla
ya vive instalada en `Global/_canonical/skills/strict-tdd/SKILL.md:17` y
`strict-tdd-verify/SKILL.md:17` — *"Ported from `gentle-ai`'s (Gentleman Programming) RDD
strict-TDD module"*. Confirmado por Federico el 2026-08-16
(`decisions-log.jsonl`, slug `RDD-es-el-modulo-de-gentle-ai-confirmado-por-federico`): RDD **es**
el módulo strict-TDD de ADR-0022, con el vocabulario de Gentleman Programming (Receipt Driven
Development: recibos verificables — logs, tests corridos, evidencia `file:line` — en vez de
promesas, lo mismo que ADR-0026 y la disciplina de mordida ya exigen). Este ADR **no** crea un
segundo toggle: `METODOLOGIAS["tdd_rdd"]` es una sola entrada, un solo texto, que nombra las dos
palabras para el mismo mecanismo — `metodologia_preferida="rdd"` es sólo una señal para que el
orquestador proponga `strict_tdd: true` al declarar un paquete nuevo (ADR-0022 sigue siendo la
única fuente del flag real, por paquete).

## Rejected alternatives

- **Render-per-postura en `generate.py`/`install.py`** (opción 1 completa). Rechazada: convierte
  "cambiar de postura" en "reinstalar", y el pedido fue explícito en que eso no cuenta como
  toggle. También tocaría `install.py`, fuera de `owned_paths` de este paquete.
- **Inyección en `compose_task` de los cuatro spawners** (opción 2 completa). Rechazada para este
  paquete: territorio de 025/D5 en paralelo, prohibido explícitamente
  (`ai/scripts/*_spawn.py`). Queda documentada como la vía a considerar si en el futuro se necesita
  que la postura viaje también en el TEXTO de la tarea (por ejemplo, para lanes sin acceso nativo
  a herramientas de lectura de archivos) — decisión diferida, no descartada para siempre.
- **Un store nuevo separado de `config.toml`.** Rechazada explícitamente por el paquete
  (`write_app_config` o nada) — un segundo archivo de estado sólo para posturas fragmentaría el
  único writer que ya evita que los toggles se pisen entre sí (AC-15).
- **Un toggle global nuevo para TDD estricto/SDD, además del que ya existe por paquete.**
  Rechazada: `strict_tdd` es y sigue siendo un flag POR PAQUETE (ADR-0022); duplicarlo a nivel
  global crearía dos fuentes de verdad divergentes. `metodologia_preferida` es una preferencia
  ADEMÁS de eso, nunca en su lugar.

## Consecuencias

- Postura y metodología preferida son datos, no código: cambiarlas es `set-agents --postura
  <valor>` (o editar `config.toml`), nunca un build.
- Requiere que el usuario reinstale UNA vez (`./build.sh --install`) para que la instrucción de
  leer `config.toml` llegue a `~/.claude/agents/orchestrator.md` y sus tres equivalentes — después
  de esa instalación, todo cambio de postura es en caliente.
- El canal elegido no cubre (todavía) los lanes que despachan por subprocess sin herramienta
  nativa de lectura de archivos si alguna vez existieran — hoy los cuatro (`claude-code`,
  `opencode`, `codex`, `pi`) leen su propio `agents/orchestrator.md` como prompt/persona
  instalado, así que esto no es una limitación medida, es una nota para cuando eso deje de ser
  cierto.
- `tests/test_harness.py` fija con una mordida específica que la postura/explicación EN CÓDIGO
  (`POSTURAS`, `set_agents_app.py`) y la doctrina INSTALADA (`Global/_canonical` +
  `Global/claude-code/agents/orchestrator.md`, ambos generados por `./build.sh`) nunca diverjan —
  un cambio a una sin la otra rompe el gate, no sólo el review.

## Fuente de RDD

`Receipt-Driven Development` no es una glosa nuestra: es el nombre que usa el propio
upstream. Verificado el 2026-08-16 contra el README de
[`Gentleman-Programming/gentle-ai`](https://github.com/Gentleman-Programming/gentle-ai),
cita textual: *"**Receipt-Driven Development (RDD) is the supported stable path.**"*, y
*"Receipt-Driven Development (RDD) started in `gentle-ai` `v1.47.0` on 2026-07-10"*.

Se cita acá porque la spec afirmaba la expansión sin fuente y el texto llegó hasta la
pantalla que ve el usuario. ADR-0026 exige fuente para afirmaciones sobre blancos móviles,
y el vocabulario de un proyecto de terceros lo es.
