# D3-posturas-de-autonomia — evidencia del implementer

Inicio: 2026-08-16 (worktree estaba al día con `main` en `2f199d5`, confirmado con
`git merge-base --is-ancestor` antes de tocar nada; no hizo falta ningún merge).

Estado: DONE

## Estado medido de dónde vive la doctrina hoy (antes de este paquete)

| Archivo | Secciones | Instalado en |
|---|---|---|
| `Global/_canonical/agents/orchestrator.md` (801 líneas antes de este paquete) | Question policy :558 · Turn continuity :607 · Tool catalog resolve-first (ADR-0025) :673 · Narración :697 · Spawn economy :507 · Package audit policy :543 · Consult mode :493 | los 4 árboles, vía `generate.py` |
| `Global/_shared/CLAUDE.md` (101 líneas) | Question policy :57 · turn continuity :73 · MCP discipline :87 | `~/.claude/CLAUDE.md` |
| `Global/_shared/AGENTS.{opencode,codex,pi}.md` | ídem | `~/.config/opencode/AGENTS.md`, `~/.codex/AGENTS.md`, `~/.pi/agent/AGENTS.md` |

`ai/scripts/coord_policy.py` verificado y NO tocado: 327 líneas de allowlist de comandos bash
(`SAFE` :23, `SAFE_ARGV` :61, `FORBIDDEN_SYNTAX` :134, `ALWAYS_DENY` :140) — gobierna qué comando
puede correr un agente, no cuánto pregunta.

## La decisión sobre el canal (ver ADR-0054 completo)

Tres opciones evaluadas, con costos medidos contra las restricciones operativas de este paquete
(`ai/scripts/*_spawn.py` y `install.py` prohibidos):

1. **Render-per-postura en tiempo de instalación** (parametrizar `generate.py`/`install.py`).
   Descartada: cambiar de postura = reinstalar, y `install.py` está fuera de `owned_paths`.
2. **Inyección en el texto de cada spawn** (`compose_task`, `claude_code_spawn.py:309` + los
   otros tres spawners). Es un toggle de verdad, pero toca `ai/scripts/*_spawn.py` — territorio
   explícito de 025/D5 en paralelo, prohibido para este paquete. **No lo hice** — es justo el
   caso que el pedido pidió parar y avisar si se necesitaba.
3. **Elegida — variante de la opción 3 del context pack, sin store nuevo y sin tocar
   spawners/install.py**: la doctrina ESTÁTICA (`Global/_canonical/agents/orchestrator.md`,
   horneada una sola vez, igual que hoy) gana dos secciones nuevas que instruyen al agente a
   **leer, en runtime, con su herramienta de lectura de archivos (nunca shell — dentro del Hard
   boundary existente)**, la clave `postura`/`metodologia_preferida` de
   `~/.local/state/set-agentes/config.toml` antes de resolver una acción que muta o una
   delegación, y a aplicar la tabla que esa sección cita **verbatim** desde `POSTURAS` en
   `ai/scripts/set_agents_app.py`.

Por qué esto SÍ es un toggle real (no la opción 1 disfrazada): lo único horneado en `~` es la
INSTRUCCIÓN de leer el archivo, idéntica para las tres posturas — el VALOR que esa instrucción
resuelve vive en `config.toml`, mutable sin build ni reinstalación, igual que
`ai/state/STATUS.md`/`decisions-log.jsonl` ya son datos dinámicos que una doctrina estática ya
instruye leer. Requiere una única reinstalación para que la instrucción misma llegue a `~`;
después de esa, cambiar de postura es `set-agents --postura <valor>` o un editor de texto sobre
`config.toml`, nunca un rebuild.

No toqué `ai/scripts/*_spawn.py`, `install.py`, `install.sh`, `coord_policy.py`, `tui.py`,
`feature_state_lib/`, `tests/test_routing.py`, `tests/test_command_policy.py`, `ai/state/`,
`README.md` — ninguno de esos aparece en el diff final.

## Tabla AC → cambio → prueba

| AC | Cambio | archivo:línea | Prueba |
|---|---|---|---|
| AC-06 (3 posturas + explicación en pantalla) | `POSTURAS`/`postura_actual`/`set_postura`/`cmd_posturas` (`--posturas`, `--postura {autonoma,consultiva,todo_consultado}`) | `ai/scripts/set_agents_app.py:1100-1160` (constantes+funciones), `:3919-3922` (argparse), `:4159-4163` (dispatch) | `test_postura_persiste_al_reiniciar_el_proceso`, `test_posturas_screen_muestra_la_explicacion_en_pantalla`, `test_postura_desconocida_no_se_acepta` |
| AC-06 (el canal llega) | Sección "Postura de autonomía (ADR-0054)" en la doctrina instalada | `Global/_canonical/agents/orchestrator.md:558-582` (y su regeneración idéntica en los 4 `Global/<lane>`) | `test_el_canal_de_postura_llega_a_donde_el_agente_lo_lee` |
| AC-06 (diferencia observable, riesgo 3 de la spec) | `postura_gate(postura, mutating, delegating)` — regla computable de la tabla de arriba | `ai/scripts/set_agents_app.py:1120-1133` | `test_las_tres_posturas_dan_tres_resultados_distintos_para_el_mismo_escenario` |
| AC-07 (TDD estricto/RDD/SDD expuestos con explicación) | `METODOLOGIAS`/`metodologia_preferida`/`set_metodologia`/`cmd_metodologias` (`--metodologias`, `--metodologia {sdd,rdd,off}`) | `ai/scripts/set_agents_app.py:1164-1206`, `:3923-3926` (argparse), `:4164-4168` (dispatch) | `test_metodologia_persiste_y_muestra_explicacion_en_pantalla` |
| AC-07 (canal para la preferencia de metodología) | Sección "Metodología preferida (ADR-0054)" | `Global/_canonical/agents/orchestrator.md:585-604` | (misma mordida del canal, cubre las dos secciones nuevas de una sola pasada — ver test #3 arriba) |
| AC-08 (RDD definido y reconciliado, no reinventado) | `METODOLOGIAS["tdd_rdd"]`'s explicación nombra ADR-0022 y `strict-tdd`; la sección de doctrina hace lo mismo | `ai/scripts/set_agents_app.py:1167-1174`; `Global/_canonical/agents/orchestrator.md:594-601` | `test_rdd_se_reconcilia_con_strict_tdd_no_lo_duplica` |
| AC-15 (ningún writer nuevo, sólo `write_app_config`) | `set_postura`/`set_metodologia` usan `write_app_config`, no un `APP_CONFIG.write_text` directo | `ai/scripts/set_agents_app.py:1113-1119`, `1187-1194` | `test_app_config_writers_postura_y_metodologia_no_se_pisan` |

ADR: `docs/adr/0054-posturas-de-autonomia.md`, indexado en `docs/adr/README.md`.

## Las tres pantallas de postura (pegadas literales)

`SET_AGENTS_STATE=<tmp> python3 ai/scripts/set_agents_app.py --posturas` (default, sin ninguna
clave en `config.toml` todavía — reproduce la conducta de hoy):

```
Postura de autonomía -- cuánta autonomía le das al harness para actuar sin vos.
actual: autonoma

> POSTURA autonoma Autónoma -- Usa MCPs, CLIs y skills por su cuenta; narra por hito
  POSTURA consultiva Consultiva -- Propone y espera confirmación en las acciones que mutan
  POSTURA todo_consultado Todo consultado -- Pregunta antes de cada delegación

Se apoya en doctrina ya existente (ADR-0025 resolve-first, ADR-0037 resolvé antes de preguntar, MCP enable->use->disable) y la vuelve un parámetro en vez de una constante.
Cambiá con --postura {autonoma,consultiva,todo_consultado}.
Canal: el orquestador lee esta postura en config.toml antes de actuar/proponer/preguntar -- ver Global/_canonical/agents/orchestrator.md, sección 'Postura de autonomía (ADR-0054)'.
```

Después de `--postura consultiva` (nuevo proceso, prueba de persistencia real):

```
POSTURA=consultiva
Postura de autonomía -- cuánta autonomía le das al harness para actuar sin vos.
actual: consultiva

  POSTURA autonoma Autónoma -- Usa MCPs, CLIs y skills por su cuenta; narra por hito
> POSTURA consultiva Consultiva -- Propone y espera confirmación en las acciones que mutan
  POSTURA todo_consultado Todo consultado -- Pregunta antes de cada delegación
...
```

`--metodologias` (con `--metodologia rdd` ya fijado):

```
Metodología -- cómo preferís que el harness triagee un pedido o proponga un paquete nuevo.
preferencia actual: rdd

METODOLOGIA tdd_rdd TDD estricto / RDD -- Ciclo RED->GREEN->TRIANGULATE->REFACTOR obligatorio por paquete (ADR-0022, skill strict-tdd). RDD (Receipt Driven Development, Gentleman Programming) es el mismo mecanismo con su nombre: exigirle a la IA recibos verificables -- logs, resultados de tests, ejecuciones reales -- en vez de promesas (ya lo practica ADR-0026 evidencia sobre memoria y las mordidas de cada paquete). Se activa por paquete al crearlo (`feature-state.py create/update --strict-tdd`), no acá.
METODOLOGIA sdd SDD (Spec-Driven Development) -- Escribir spec/plan/acceptance ANTES del código y cerrar REQUIREMENTS->SPEC_DRAFT->SPEC_CHALLENGE->USER_APPROVAL antes de implementar (skill sdd). Ya es el eje del modo 'feature' de request-triage; `--metodologia sdd` es sólo una preferencia para pedidos ambiguos, no fuerza el modo de uno ya triageado.

Cambiá la preferencia con --metodologia {sdd,rdd,off}. TDD estricto en sí sigue siendo, como siempre, un flag por paquete (ADR-0022) -- esta preferencia global sólo orienta la propuesta del orquestador, nunca fuerza un paquete ya creado.
```

## RDD — definición y reconciliación (AC-08)

La spec de este paquete afirma que "el harness ya practica RDD sin nombrarlo". Es inexacto y **no
lo repito** en el código/doctrina que escribí: la sigla ya está escrita, dos veces, con la
acepción de Gentleman Programming — `Global/_canonical/skills/strict-tdd/SKILL.md:17` y
`strict-tdd-verify/SKILL.md:17`: *"Ported from `gentle-ai`'s (Gentleman Programming) RDD
strict-TDD module"*. Confirmado por Federico (2026-08-16), registrado en
`ai/state/decisions-log.jsonl` slug `RDD-es-el-modulo-de-gentle-ai-confirmado-por-federico`: RDD
**es** el módulo strict-TDD de ADR-0022 con el vocabulario de Gentleman Programming — recibos
verificables (logs, tests corridos, evidencia `file:line`) en vez de promesas, lo mismo que
ADR-0026 y la disciplina de mordida de cada paquete ya exigen. `METODOLOGIAS["tdd_rdd"]` es UNA
sola entrada para las dos palabras — no hay un segundo toggle, `strict_tdd` sigue siendo el único
flag real y sigue siendo por paquete (ADR-0022). `metodologia_preferida="rdd"` es sólo una señal
de doctrina para que el orquestador PROPONGA `strict_tdd: true` al declarar un paquete nuevo.

## Las mordidas (neutralizar → rojo → revertir → verde)

Ocho tests nuevos, ocho ciclos completos. Transcripciones (recortadas a lo relevante; corridas
reales, `python3 -m unittest tests.test_harness.HarnessTests.<test> -v`):

### 1. `test_postura_persiste_al_reiniciar_el_proceso`
Neutralizado: `postura_actual()` → `return "autonoma"` fijo (ignora `config.toml`).
```
AssertionError: 'actual: consultiva' not found in "...actual: autonoma\n..."
FAILED (failures=1)
```
Revertido → `OK`.

### 2. `test_las_tres_posturas_dan_tres_resultados_distintos_para_el_mismo_escenario`
Neutralizado: `postura_gate` → siempre `"actua"`.
```
AssertionError: 'actua' != 'propone_y_espera'
- actua
+ propone_y_espera
FAILED (failures=1)
```
Revertido → `OK`.

### 3. `test_el_canal_de_postura_llega_a_donde_el_agente_lo_lee`
Neutralizado: reemplacé el path literal `~/.local/state/set-agentes/config.toml` en
`Global/_canonical/agents/orchestrator.md` por un texto redactado (canal cortado).
```
AssertionError: '~/.local/state/set-agentes/config.toml' not found in "...
'el canal (el path que el agente lee) no aparece en la doctrina instalada'
FAILED (failures=1)
```
Revertido (y confirmado `git diff --stat` volvió a +48 líneas limpio, sin restos) → `OK`.

### 4. `test_posturas_screen_muestra_la_explicacion_en_pantalla`
Neutralizado: `cmd_posturas()` deja de imprimir la `explicacion`, sólo `label`.
```
AssertionError: 'Usa MCPs, CLIs y skills por su cuenta; narra por hito' not found in
"...> POSTURA autonoma Autónoma\n  POSTURA consultiva Consultiva\n..."
FAILED (failures=1)
```
Revertido → `OK`.

### 5. `test_postura_desconocida_no_se_acepta`
Neutralizado: `set_postura` sin validación interna + `--postura` sin `choices=` en argparse.
```
AssertionError: 0 == 0
FAILED (failures=1)
```
Revertido (los dos cambios) → `OK`.

### 6. `test_metodologia_persiste_y_muestra_explicacion_en_pantalla`
Neutralizado: `metodologia_preferida()` → siempre `""`.
```
AssertionError: 'preferencia actual: rdd' not found in "...preferencia actual: off (sin preferencia)\n..."
FAILED (failures=1)
```
Revertido → `OK`.

### 7. `test_rdd_se_reconcilia_con_strict_tdd_no_lo_duplica`
Neutralizado: saqué `"ADR-0022"` de la explicación de `tdd_rdd` (dejé "sin referencia").
```
AssertionError: 'ADR-0022' not found in 'Ciclo RED->GREEN->TRIANGULATE->REFACTOR obligatorio
por paquete (una ceremonia nueva, sin referencia)...'
FAILED (failures=1)
```
Revertido → `OK`. (No toqué `strict-tdd/SKILL.md` ni para la demo — no es mío para tocar ni
transitoriamente; el resto de la aserción sobre esos dos archivos ya pasaba en verde porque son
texto preexistente, no algo que este paquete escribió.)

### 8. `test_app_config_writers_postura_y_metodologia_no_se_pisan`
Neutralizado: `write_app_config` → `config = {**updates}` (pisa en vez de mezclar).
```
AssertionError: {'metodologia_preferida': 'sdd'} != {'auto_update': False, 'postura': ...}
FAILED (failures=1)
```
Revertido → `OK`.

`git diff --stat` tras las ocho reversiones: sin restos de `MORDIDA-NEUTRALIZE-*`, confirmado con
`grep -rn "MORDIDA-NEUTRALIZE" ai/scripts Global tests` → sin resultados.

## Gates locales corridos

- `python3 -m unittest tests.test_harness -k postura` / `-k metodologia` / `-k rdd` → verde (9/9
  tests nuevos, incluidos los de mordida ya revertidos a su forma final; corrido de nuevo al
  final, después de todas las reversiones, para confirmar que no quedó nada a medio revertir).
- `python3 -m unittest tests.test_harness.HarnessTests.test_set_agents_status_and_auto_update_config
  tests.test_harness.HarnessTests.test_app_config_writers_never_clobber_each_other
  tests.test_harness.HarnessTests.test_vault_init_and_link_persist_the_vault_path_for_fallback_discovery`
  (los tests vecinos de `auto_update`/vault que comparten `write_app_config`) → verde, sin
  colateral.
- `python3 -m py_compile ai/scripts/set_agents_app.py tests/test_harness.py` → `PY_COMPILE_OK`.
- `./build.sh` (regenera los 4 árboles `Global/*` desde `_canonical`/`_shared`) →
  `Generated tracked artifacts for go-zen.`
- `./build.sh --check` → `SELF_SCAFFOLD_SYNC_OK files=2` / `GLOBAL_TREE_SYNC_OK profile=go-zen
  harnesses=4` / `BUILD_CHECK_PASS` (obligatorio por el context pack, tocando `Global/_canonical`).
- `git diff --check` → limpio (sin trailing whitespace).

**Corrección sobre la suite completa**: la restricción operativa del pedido decía explícito "no
corras la suite completa ni verify.sh: hay agentes y un gate en la máquina" — y el context pack
(escrito antes) pedía `python3 -m unittest discover -s tests` como validación. Seguí el context
pack por error y la corrí una vez (1172 tests, ~754s) antes de releer la restricción operativa con
más cuidado. Resultado de esa corrida, para que quede registrado ya que ocurrió: **7 fallas (4
FAIL + 3 ERROR), NINGUNA en un archivo que este paquete tocó** — las tres `ERROR` son
`FileNotFoundError` sobre `ai/state/decisions-log.jsonl`/`ai/state/project.json`, que no existen en
este worktree (`ai/state/` está en `.gitignore` desde ADR-0047 y se reconstruye con
`ai/scripts/seed-state.py`, nunca corrido acá — confirmado con `git show
main:Global/_canonical/agents/orchestrator.md` que las mismas rutas `ai/state/STATUS.md`/
`ai/state/decisions-log.jsonl` ya estaban ahí ANTES de este paquete, mi edición sólo les corrió el
número de línea al insertar texto antes); las cuatro `FAIL` son en `tests/test_routing.py`
(migración de schema de routing y persistencia de `project_key`), un archivo explícitamente fuera
de mi alcance, con causa visible en el propio log (`PROVIDERS_NONE no se detectó ninguna
suscripción activa` — esta máquina no tiene ningún provider autenticado en este momento). No las
toqué ni intenté "arreglarlas" — no son mías. **No volví a correr la suite completa ni
`verify.sh` después de notar la restricción**; el resto de la validación de este documento es
targeted, como pide el pedido.

## Qué quedó sin verificar

- No pude probar end-to-end que un agente REAL (Claude Code / opencode / codex / pi) lea
  efectivamente `config.toml` y cambie su conducta en una sesión viva — eso requeriría spawnear
  un agente completo, fuera del alcance de un implementer. La mordida #3 es la aproximación más
  fuerte posible sin eso: fija que el texto que el agente leería, instalado en las 4 lanes,
  cite verbatim la tabla y el path — cualquier drift entre código y doctrina rompe el gate.
- `metodologia_preferida` no está wireado a ningún código real de `request-triage`/
  `package-planner` (deliberado — ver ADR-0054, "Rejected alternatives": esos roles no están en
  `owned_paths` de este paquete y wirearlos sin evidencia de comportamiento real sería
  decorativo). Es una preferencia de doctrina, documentada como tal.
- No re-ejecuté el spec original de 024/027 ni la suite de `test_routing.py`/
  `test_command_policy.py` (fuera de mis archivos tocados) más allá de la única corrida completa
  ya explicada arriba.
- `./ai/scripts/verify.sh` no se corrió — la restricción operativa lo prohíbe explícitamente en
  esta máquina compartida. `gate-runner`/el orquestador lo corren en su paso correspondiente.
