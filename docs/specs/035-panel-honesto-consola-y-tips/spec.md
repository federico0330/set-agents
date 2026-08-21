# 035 — Panel honesto, consola partida y TIPS al día

> Este spec está escrito para que lo implemente **Cursor** (runtime anfitrión, 032).
> Cada criterio nombra archivos y líneas del árbol **medidos el 2026-08-20** con
> `rg`/`wc -l`/lectura directa. Donde no pude medir, digo **sin verificar**.
> 032/033/034 no se reabren como producto.

**Estado del contrato:** Draft (SPEC_DRAFT, sin state file — `init` no corrió).
**Origen:** pedido de Federico del 2026-08-20, "Si, hagamos esas 3" — las tres piezas
diferidas en `docs/notas/decisiones/2026-08-20 035-consult-como-funciona-no-refactor.md:12`
y enumeradas en `docs/COMO-FUNCIONA.md:439-448` (§11).
**Runtime:** Cursor. `--route-decide` sigue prohibido en el anfitrión. Engram no entra.
**Ejes de arquitectura (store / API Gateway / deploy):** **n/a**. El pedido no introduce
persistencia nueva, ni superficie de red, ni cambio de despliegue: es CLI de estado,
reorganización de un módulo Python y documentación. No se redacta ADR de deploy.
**Eje que sí existe (corregido — F-035-001):** el rechazo nuevo de `record-review` **es**
un cambio de contrato público del CLI de estado, porque la doctrina vigente todavía
presenta `record-review` como la vía default y el panel como opcional
(`Global/_canonical/agents/orchestrator.md:103-108`, medido). Por eso el **ADR de enmienda
de contrato entra EN ALCANCE** (AC-A.9) y lo redacta `architect` — producto no lo escribe,
pero deja de declararlo fuera de alcance.

**Revisión post-challenge (2026-08-20).** Este contrato incorpora los siete hallazgos de
`spec-challenger` (verdict `revision_required`). Cada AC corregido cita el `F-035-00N` que
cierra. Dos decisiones **no** se relitigan: **DEC-DOOR** (el verbo se rechaza, no se
endurece) y el recorte de `record-repair --skip-delta`, resuelto por el orquestador en
`docs/notas/decisiones/2026-08-20 035-skip-delta-fuera-del-slice.md`.

---

## Problema

Las tres piezas quedaron diferidas con razón (no había alcance ni aceptación), y cada
una es una mentira medible del árbol de hoy:

**1) El panel de review se puede saltear con el verbo viejo.**
`start-review-panel` enforcea la membresía obligatoria: calcula
`required_reviewers` (`ai/scripts/feature-state.py:569`), rechaza escritores
(`:570-575`), rechaza un panel que le falte un rol requerido (`:576-583`) y rechaza uno
inflado cuando el requerido es uno solo (`:584-587`). La regla vive en
`required_reviewers_for` (`ai/scripts/feature_state_lib/model.py:565-575`): `small`+`low`
→ `SINGLE_REVIEW_PANEL = ["package-reviewer"]` (`:95`); cualquier eje `medium`/`high` →
`FULL_REVIEW_PANEL = ["package-reviewer", "security-auditor"]` (`:96`).
`cmd_record_review` (`ai/scripts/feature_state_lib/cli_review.py:21-63`) **no consulta
`required_reviewers` en ningún punto**: acepta un verdict `pass` de un solo actor y pone
la feature en `PACKAGE_TESTING` (`:54-56`). Y `package_accept_ready`
(`model.py:819-822`) solo pide que `reviews` no esté vacío y que el último verdict sea
`pass` o `repair_required` — nunca pregunta quién revisó. Resultado observable: un
paquete `medium`/`high` llega a `DONE` con `security-auditor` nunca instanciado.

Y la doctrina lo respalda, que es lo que vuelve esto un cambio de contrato y no un bugfix
(**F-035-001**): `Global/_canonical/agents/orchestrator.md:103` lista `record-review` entre
los verbos del ciclo normal, y `:105-108` presenta `start-review-panel` /
`record-subreview` / `finalize-review-panel` como lo que se usa "when multiple specialist
reviewers **are useful**" — opcional, a criterio del orquestador. Cerrar el verbo sin
enmendar esa frase deja al harness rechazando lo que su propia doctrina recomienda.

**2) La deuda hermana ya está escrita en el árbol.** El comentario de
`ai/scripts/feature_state_lib/transitions.py:102-107` lo dice con nombre y apellido:
`cmd_record_review` pone `PACKAGE_TESTING` en `pass` **sin chequear
`has_open_findings`**, a diferencia de `finalize-review-panel`
(`cli_review.py:158-160`, que levanta `StateError`) y de `record-delta-review`. El
comentario cierra con "record-review is outside this package's criteria and every
package in flight uses it" — o sea: deuda registrada, no reparada. El test
`test_next_does_not_blame_a_late_review_that_never_happened`
(`tests/test_harness.py:9024-9039`) documenta la puerta y hoy **pasa** afirmando
`data["phase"] == "PACKAGE_TESTING"` con un finding `high` abierto.

**3) La consola es un módulo de 4399 líneas y la mitad del corte ya se hizo.**
`wc -l ai/scripts/set_agents_app.py` = **4399**. Pero **la extracción no está en cero**:
`ai/scripts/routing_cli.py` (277 líneas) y `ai/scripts/vault_ops.py` (455 líneas) ya
existen, y sus docstrings enumeran exactamente qué **no** se pudo mover y por qué
(`routing_cli.py:1-31`, `vault_ops.py:1-23`): globals mutables que solo
`set_agents_app.main()` reasigna (`PROJECT_KEY`, `PROJECT_ROOT`, `ROOT`,
`ROUTING_WARNINGS`), `app_config`/`write_app_config`, y sobre todo el helper de tests
`_import()` (`tests/test_harness.py:663-684`) que carga `set_agents_app.py` con
`spec_from_file_location` **sin registrarlo en `sys.modules`**, de modo que un import
inverso arranca un segundo exec top-level del módulo desde disco. Eso significa que
"extraer routing y vault" **no es trabajo virgen**: es una segunda pasada cuyo bloqueo
está medido y documentado, y cuyo riesgo real es agregar un tercer docstring de
"documented deviation" sin bajar una línea.

**4) `TIPS-USO.md` afirma un control plane que ya no existe.** `TIPS-USO.md:7-14`:
"**OpenCode is the orchestration control plane**", Claude Code = "review/debug lane",
Codex = "second-opinion lane", "The other two harnesses are single-task lanes, not
orchestrators". Contra eso, medido hoy:

| afirmación de TIPS-USO | medición 2026-08-20 |
|---|---|
| `:3` "versioned source for OpenCode, Claude Code, and Codex" | `ls Global/` → `claude-code`, `codex`, `cursor`, `opencode`, `pi` (cinco árboles) |
| `:9` "the other two harnesses are single-task lanes, not orchestrators" | Cursor es anfitrión desde 032; Claude tiene el roster completo. `docs/COMO-FUNCIONA.md:219-230` ya documenta que los tres orquestan |
| `:45` `Global/{opencode,claude-code,codex}` | falta `cursor` y `pi` |
| `:127-129` "Native agents" (tres bullets) | falta Cursor (`~/.cursor/agents/*.md`, 032/ADR-0063) y `pi` |
| `:133-134` "the three harnesses' own session stores ... plus a fourth `pi` lane" | `ai/scripts/cost-report.py:20-23`, `:836-843` cubre Cursor explícitamente ("every runtime including Cursor") |

Y hay un lazo: `docs/COMO-FUNCIONA.md:227-230` dice "`TIPS-USO.md` todavía dice
'OpenCode es el control plane'". Arreglar TIPS sin tocar esa frase deja al repo
contradiciéndose en la dirección opuesta.

---

## Usuarios

- **Federico**, operando el harness en Cursor y leyendo `TIPS-USO.md` como el "cómo se
  usa esto" de nivel repo.
- **El orquestador** de cualquier runtime, que hoy puede elegir `record-review` y
  saltear el panel sin que nada lo frene.
- **Quien audita un paquete cerrado** y necesita saber si `security-auditor` corrió de
  verdad o si el registro solo dice "un review pasó".
- **Quien vaya a tocar la consola** y necesita saber si el corte pendiente es trabajo o
  un techo ya medido.

---

## Invariantes (no se relajan)

1. **`MODE_BUDGETS.scoped.max_spawns_per_package == 8`** (`model.py:125`). No se sube.
   Un panel FULL exigido por PKG-A consume despachos del mismo techo; si un paquete
   choca el techo, eso es `HUMAN_DECISION_REQUIRED`, no un presupuesto más grande.
2. **`RISK_SIGNAL_REQUIRED` / ADR-0064** siguen intactos. Este spec no toca la
   selección de modo ni el default quick-fix de 1–3 archivos.
3. **`NON_ACCEPTING_ACTORS`** (`model.py:90`) y **`REFUTING_ACTORS`** (`model.py:109`)
   no cambian de contenido ni de semántica. PKG-A agrega una obligación de membresía;
   no reabre quién puede aceptar ni quién puede refutar.
4. **Cursor fuera de `RUNTIMES`**; `inherit` en un reviewer Cursor sigue prohibido
   (034/ADR-0063). `--route-decide` sigue prohibido en el anfitrión.
5. **`tests/test_harness.py` no se parte.** Es el contrato golden (~15 025 líneas,
   `wc -l`). Partirlo no es objetivo de esta feature y es no-goal nombrado abajo.
6. **Los tests no se aflojan.** Los **siete** sitios que este spec pone en rojo (enumerados
   uno por uno en `acceptance.md` § Mordida de PKG-A, corregido por F-035-004) se
   **reescriben** conservando su invariante vivo y con el comentario explicando la razón
   nueva — el patrón que 034 AC-B.2 ya usó con el test `-fast`. Ningún `skip`, ningún
   borrado, ninguna aserción bajada de tono, y **ningún `--complexity medium` degradado a
   `small`** para esquivar el guarda.
7. **Paridad de copias.** `ai/scripts` ↔ `PROYECTO/ai/scripts` está gateado por
   `build.sh:69-79` (`SELF_SCAFFOLD_DRIFT`), y `Global/*/hooks/feature_state_lib` se
   **genera** por `copytree` en `ai/scripts/generate.py:667` (cuatro árboles:
   `claude-code`, `codex`, `cursor`, `opencode`), verificado por `build.sh --check`.
   Dato crítico para PKG-A: el golden suite corre el CLI **del template** —
   `tests/test_harness.py:32` apunta a `PROYECTO/ai/scripts/feature-state.py`. Un
   cambio que viva solo en `ai/scripts/` no lo ve ningún test.
8. **El vault Obsidian es mandatory** (ADR-0012, ADR-0056) y `routing_core/` no se
   rediseña. PKG-B mueve código, no semántica.
9. **`feature-state.py` sigue siendo el único escritor** de `ai/state/features/*.json`.

---

## Decisiones de producto (tomadas acá — el planner no las relitiga)

| id | decisión |
|---|---|
| **DEC-DOOR** | `record-review` **se rechaza**, no se endurece, cuando el panel resuelto del paquete pide más de un rol. Sigue siendo la puerta legítima del paquete de un solo reviewer. Razón medida: cada llamada a `record-review` incrementa `attempts.deep_review_cycles` (`cli_review.py:46`) y el techo es `max_deep_review_cycles = 2` (`model.py:123-127`) — cubrir dos roles con dos llamadas gastaría el presupuesto entero de review en un solo panel. La simetría también existe ya: el CLI hoy rechaza un panel **inflado** para `small+low` (`feature-state.py:584-587`) y acepta un review **encogido** para `medium`/`high`. Esa asimetría es el defecto. |
| **DEC-ABSENCE** | `required_reviewers` **ausente**, `null` explícito, o presente-pero-inservible **no** significa "sin requisito". Se re-deriva de `complexity` + riesgo resuelto (`required_reviewers_for`, `model.py:565-575`, que ya hace fail-safe a `medium` cuando `complexity` es `None`, `:571`). **Medición corregida (F-035-005)** — la anterior ("30 de 31 null") contaba archivos y confundía ausencia con `null`. Re-medido el 2026-08-20 sobre **76 paquetes** en 31 archivos de `ai/state/features/`: `required_reviewers` **ausente en 71**, **poblado en 5**, **`null` explícito en 0**. `complexity`: `high` 25, `medium` 34, `small` 13, **ausente en 4**. Comando: `python3 -c` recorriendo `ai/state/features/*.json` y clasificando `"required_reviewers" not in pkg` vs `is None` vs poblado (corrido 2026-08-20). Consecuencia dura: la forma real de los datos es **la clave ausente**, no `null`, así que un predicado escrito contra `pkg["required_reviewers"] is None` no toca ni un paquete real; y el fail-safe FULL por `complexity` ausente tiene 4 clientes medidos, no cero. |
| **DEC-LEGACY** | La negativa nueva dispara en el **verbo que muta**, no al validar un registro histórico. Un paquete `accepted`/`superseded` y una feature `DONE` no se re-juzgan. Medido: 27 features en `DONE` de 31 archivos (el resto: 2 `BLOCKED`, 1 `PACKAGE_GATES`, 1 `INTEGRATION`), y de los paquetes vivos hay tres que sí caen bajo la regla nueva — 032 `C1` (`complexity=medium`, 0 reviews, feature en `PACKAGE_GATES`), 011 `P1-quota-failover` (`high`, 0 reviews, `BLOCKED`), 002 `P1-routing-core` (`high`, `repair_required`, `BLOCKED`). Esos tres son el universo real del cambio. **Los 4 paquetes sin `complexity`** (F-035-005) quedan cubiertos por esta misma decisión: están todos en features `accepted`/`DONE`, así que el fail-safe FULL nunca se les aplica retroactivamente — pero el predicado igual tiene que manejarlos, porque un paquete futuro sin `complexity` sí llega al verbo. |
| **DEC-SIBLING-IN** | La deuda hermana (`record-review pass` con finding bloqueante abierto) **entra** en este slice, en dos ACs (AC-A.4, AC-A.5), **limitada al verbo `record-review`** — no a "todas las puertas hacia `PACKAGE_TESTING`". Cabe: la simetría ya está escrita en `finalize-review-panel` (`cli_review.py:158-160`) y el costo medido en el golden suite son **dos** sitios (`tests/test_harness.py:9032` y `:11048`), no una barrida. Dejarla afuera obligaría a reescribir el mismo comentario de `transitions.py:102-107` dos veces. |
| **DEC-SKIP-DELTA-OUT** | `record-repair --skip-delta` **no entra** (F-035-002). Está medido que es la otra puerta viva: `cli_repair.py:274-282` pone `data["phase"] = "PACKAGE_TESTING"` directo, y su guarda de `:246-253` exige "all **repaired** findings <= medium" — solo los `--finding-id` de esa llamada —, así que un finding abierto que no se reparó viaja igual. Cerrarla es un slice propio; decisión del orquestador registrada en `docs/notas/decisiones/2026-08-20 035-skip-delta-fuera-del-slice.md`. Consecuencia útil y no cosmética: la rama advisora de `transitions.py:96-109` **sigue siendo alcanzable** por esta puerta, así que se conserva y su comentario la nombra (AC-A.5) — no hay que declarar inalcanzable algo que no lo es. |
| **DEC-TOKENS** | Los rechazos son errores **nombrados**, como `RISK_SIGNAL_REQUIRED` de 034: `REVIEW_PANEL_REQUIRED` (membresía) y `BLOCKING_FINDING_OPEN` (finding abierto). El texto nombra el verbo correcto (`start-review-panel`, `extend-review-panel`) para que el agente que lo lee sepa qué hacer, no solo que falló. |
| **DEC-EXTRACT-TWO-OUTCOMES** | PKG-B tiene **dos cierres legales**, y los dos son un `pass`: (a) el residuo se movió, o (b) se probó que el residuo restante está anclado a un global mutable / al helper `_import()` y se registró con una razón por comando. Lo que **no** es un cierre legal es una mudanza parcial que agregue un tercer docstring de "documented deviation" sin bajar líneas ni enumerar el residuo. Esto es lo que impide que "extraer" se vuelva un refactor sin techo. |
| **DEC-TIPS-POINTER** | `TIPS-USO.md` se corrige **y** `docs/COMO-FUNCIONA.md:227-230` deja de afirmar que TIPS está atrasado. Las dos superficies se mueven en el mismo paquete o el repo se autocontradice. |

---

## Alcance

### PKG-A — Panel honesto (CLI de estado)

**Objetivo.** Un paquete cuyo panel resuelto incluye `security-auditor` no puede llegar a
`PACKAGE_TESTING` ni quedar `accept_ready` sin evidencia registrada de que
`security-auditor` corrió. `small`+`low` sigue cerrando con un solo `package-reviewer`.
Y `record-review --verdict pass` deja de poder saltar por encima de un finding
bloqueante abierto.

**Dónde vive el defecto hoy**
- `cli_review.py:21-63` — `cmd_record_review`: cero lecturas de `required_reviewers`,
  cero lecturas de `has_open_findings`.
- `feature-state.py:569-587` — el enforcement completo, solo en `start-review-panel`.
- `model.py:819-822` — `package_accept_ready` pide "un review con verdict pass", no
  "el panel requerido".
- `transitions.py:102-107` — la deuda, escrita, con la frase que la justifica.
- `tests/test_harness.py:9024-9039` — el test que documenta la puerta y hoy pasa.
- `Global/_canonical/agents/orchestrator.md:103-108` — **la doctrina que respalda el
  defecto** (F-035-001): `record-review` como verbo del ciclo normal, panel "when
  multiple specialist reviewers are useful". Es superficie de PKG-A, no contexto.

**Criterios**
- **AC-A.1** Un paquete cuyo panel resuelto es `FULL_REVIEW_PANEL` (`model.py:96`) no
  puede quedar registrado con un `record-review` como su único review. El verbo se
  rechaza con `REVIEW_PANEL_REQUIRED`, nombrando los roles faltantes y el verbo correcto
  (`start-review-panel`). El HOW (si el chequeo vive en `cmd_record_review`, en un
  predicado compartido con `package_accept_ready`, o en los dos) es **UNVERIFIED** para
  architecture; el observable no.
- **AC-A.2** `small`+`low` no cambia: `record-review` sigue siendo la puerta válida y
  barata de un paquete de un solo reviewer (`SINGLE_REVIEW_PANEL`, `model.py:95`). Un
  criterio que rompa este caso rompió el harness, no lo arregló.
- **AC-A.3** (corregido por **F-035-005**) `required_reviewers` se re-deriva de
  `complexity` + riesgo resuelto (`resolve_package_risk`, `model.py:555-562`) en **tres**
  formas de ausencia, que son tres fixtures distintos y no un solo caso:
  (i) **clave ausente** — la forma real de **71 de 76** paquetes medidos;
  (ii) **`null` explícito** — **0** paquetes hoy, pero la forma que un editor a mano
  produce, así que el predicado la cubre igual;
  (iii) **`complexity` ausente/`None`** — **4** paquetes medidos, fail-safe a panel FULL
  (`model.py:571` ya lo hace) que **se conserva**.
  Un paquete legacy `medium`/`high` en cualquiera de las tres formas recibe el mismo
  rechazo que uno recién creado. **Fixtures que engañarían al criterio, nombrados:**
  (a) un test que solo use `create-package --complexity medium`, que **sí** persiste el
  campo (`cli_lifecycle.py:334`), y nunca un state file crudo; (b) un test que escriba
  `required_reviewers: null` y nada más — pasaría en verde y no tocaría **ni un** paquete
  real, porque la forma real es la clave **ausente**. El criterio no está satisfecho hasta
  que existan los tres casos.
- **AC-A.4** (corregido por **F-035-002** y **F-035-004**) `record-review` se rechaza con
  `BLOCKING_FINDING_OPEN` cuando el verdict es `pass` y hay un finding
  `critical`/`high`/`medium` abierto, con el mismo predicado (`has_open_findings`) y el
  mismo conjunto de severidades que `finalize-review-panel` ya usa
  (`cli_review.py:159-160`). Dos límites explícitos:
  1. **`repair_required` y `blocked` no cambian de comportamiento SOLO cuando el panel
     resuelto es `SINGLE_REVIEW_PANEL`.** Si el panel es FULL, AC-A.1 rechaza el **verbo
     completo** por membresía (DEC-DOOR) y ningún verdict pasa — decir "los otros dos
     verdicts no cambian" a secas sería falso, y hay 3 sitios medidos del golden suite que
     lo prueban (`tests/test_harness.py:12399`, `:12451`, `:13006`: paquete `medium`,
     verdict `repair_required`).
  2. **El alcance es el verbo `record-review`, no "toda puerta hacia `PACKAGE_TESTING`".**
     `record-repair --skip-delta` (`cli_repair.py:274-282`) queda fuera por
     DEC-SKIP-DELTA-OUT. Este AC no promete que `PACKAGE_TESTING` con finding abierto se
     vuelva inalcanzable; promete que **`record-review pass` deja de ser una de sus
     puertas**.
- **AC-A.5** (corregido por **F-035-003**) El comentario-deuda de `transitions.py:102-107`
  deja de describir una puerta que ya no existe, **sin** afirmar que la rama quedó
  inalcanzable. Concreto y grepeable: la frase "record-review is outside this package's
  criteria and every package in flight uses it" no sobrevive tal cual. La rama del advisor
  (`transitions.py:96-109`) **no se borra** y **no se declara inalcanzable**: está medido
  que sigue siendo alcanzable por `record-repair --skip-delta`
  (`cli_repair.py:274-282`, guarda de `:246-253` que solo mira los findings **reparados**),
  puerta que este slice deja explícitamente afuera. El comentario nuevo nombra esa puerta
  y cita la decisión que la difiere. Un comentario que nombra una puerta cerrada es peor
  que ninguno; uno que declara inalcanzable un estado alcanzable es peor todavía.
- **AC-A.6** Ningún registro histórico se invalida. Las 27 features en `DONE` y todo
  paquete `accepted`/`superseded` siguen validando igual. El rechazo vive en el verbo
  que muta. **Sin verificar:** si algún gate de repo re-valida los 31 archivos de
  `ai/state/features/` en lote (`check-feature-state.py` no lo hace — mide commits de
  delivery contra state files, `verify.sh:65`); architecture lo confirma antes de elegir
  dónde vive el chequeo.
- **AC-A.7** El cambio existe en las dos copias del CLI. El golden suite corre
  `PROYECTO/ai/scripts/feature-state.py` (`tests/test_harness.py:32`), y
  `build.sh --check` compara `ai/scripts` contra `PROYECTO/ai/scripts`
  (`build.sh:69-79`) y regenera `Global/*/hooks/feature_state_lib`
  (`generate.py:667`). Un cambio en una sola copia es un paquete rojo, no un paquete
  incompleto.
- **AC-A.8** El panel FULL que ahora es obligatorio se paga con despachos del techo que
  ya existe: `MODE_BUDGETS` no se toca (`model.py:123-128`). Si un paquete choca
  `max_spawns_per_package` por tener que instanciar `security-auditor`, eso es
  `HUMAN_DECISION_REQUIRED`.
- **AC-A.9** (nuevo, cierra **F-035-001**) **La doctrina y el contrato se mueven con el
  código, en el mismo paquete.** El rechazo nuevo es contrato público, no un detalle de
  implementación, y hoy la doctrina dice lo contrario:
  `Global/_canonical/agents/orchestrator.md:103` lista `record-review` entre los verbos
  del ciclo normal y `:105-108` presenta el panel como lo que se usa "when multiple
  specialist reviewers are useful". Entonces PKG-A entrega tres cosas juntas:
  1. Un **ADR `Accepted`** que enmienda el contrato de `record-review`: la **firma no
     cambia** (mismo comando, mismos tres verdicts) y lo que se agrega son dos rechazos
     nombrados, `REVIEW_PANEL_REQUIRED` y `BLOCKING_FINDING_OPEN`; `small`+`low` sigue
     siendo la puerta legítima. Lo **redacta `architect`**, no producto: acá se declara
     que el ADR entra en alcance y qué tiene que decidir, no su texto.
  2. `Global/_canonical/agents/orchestrator.md` actualizado, de modo que la doctrina deje
     de recomendar el camino que el CLI ahora rechaza: el panel es **obligatorio** cuando
     el panel resuelto es FULL, y `record-review` queda descrito como la puerta de
     `small`+`low`.
  3. La propagación a los árboles la hace `generate.py` (`copytree`, `generate.py:667`) —
     **no** se editan las copias a mano y `generate.py` **no** se modifica (no-goal).
  El observable: `rg` sobre los árboles generados no encuentra la recomendación vieja, y
  el ADR existe con estado `Accepted`. **Sin verificar:** el número de ADR que le toca y
  si `architect` concluye que hace falta uno o dos (contrato + doctrina) — es su decisión.

### PKG-B — La consola partida (refactor comportamiento-preservante)

**Objetivo.** Cerrar la segunda pasada de extracción de `set_agents_app.py` con
caracterización **previa**, sin que el CLI público de `set-agents` cambie su superficie ni
su comportamiento observable —`stdout`, `stderr` y código de salida idénticos sobre un set
representativo de combinaciones (AC-B.2)— y con el residuo enumerado en una matriz con
experimento propio, no arrastrado (AC-B.6).

**Dónde está el trabajo hoy**
- `ai/scripts/set_agents_app.py` — 4399 líneas, 20 secciones marcadas con banners
  (`# ---`), incluyendo `vault` (`:2839`), `vault doctor` (`:3146`), `mcp` (`:2275`),
  `providers` (`:2590`), `tools discovery` (`:1574`), `menu` (`:3479`).
- Ya extraído: `routing_cli.py` (277 líneas), `vault_ops.py` (455 líneas).
- Residuo de routing, enumerable hoy: `cmd_route_explain` (`:550`),
  `cmd_routing_report` (`:575`), `cmd_route_doctor` (`:586`), `cmd_route_decide`
  (`:671`), `cmd_route_dispatched` (`:794`), `cmd_route_quota_exhausted` (`:800`),
  `cmd_route_terminal` (`:833`), `cmd_routing_open_runs` (`:866`),
  `cmd_routing_recent_writers` (`:874`), `cmd_routing_decisions` (`:882`),
  `cmd_routing_migrate` (`:3619`).
- Residuo de vault, enumerable hoy: `cmd_vault_init` (`:2869`), `find_vault` (`:2900`),
  `vault_link_private` (`:2989`), `cmd_vault_doctor` (`:3146` en adelante),
  `vault_menu`.
- El bloqueo, ya escrito: `routing_cli.py:1-31` y `vault_ops.py:1-23`.

**Criterios**
- **AC-B.1** La caracterización se registra **antes** de mover una línea, como evidencia
  del paquete: para cada combinación del set representativo de AC-B.2, el comando corrido
  y sus **tres** canales capturados (`stdout`, `stderr`, código de salida). Una
  caracterización escrita después del movimiento no es caracterización: es una foto del
  resultado.
- **AC-B.2** (corregido por **F-035-007**) El CLI público no cambia, y "no cambia" es
  **medible en tres canales**, no "los mismos flags y tokens":
  1. **Superficie.** Toda flag hoy declarada en el `argparse` de
     `set_agents_app.py:4008-4154` sigue existiendo con el mismo nombre y la misma
     aridad/`metavar`. Lista medida en "Contratos públicos" abajo.
  2. **Comportamiento.** Para un **set representativo de combinaciones** —cada grupo de
     la tabla de "Contratos públicos" con al menos: una invocación válida, una con
     argumento faltante, una con valor inválido, más `--help` y la invocación sin
     argumentos— el `stdout` **completo**, el `stderr` **completo** y el **código de
     salida** son idénticos antes y después. No "el token de la primera línea": la salida
     entera. Los tokens medidos (`APP_STATUS`, `VAULT_INIT_OK`/`VAULT_INIT_SKIP`,
     `VAULT_LINK_SKIP`, `VAULT_LINK_CONFLICT`, `TOOL`, `MCP`) son un subconjunto de lo
     comparado, no el criterio.
  3. **Normalización, cerrada y declarada de antemano.** Solo se normalizan valores que
     varían entre dos corridas del **mismo** binario: timestamps, rutas absolutas de
     `tmp`/`$HOME`, duraciones/latencias en ms, PIDs, versiones y orden no determinístico
     donde el comando no lo garantiza. La lista de normalizadores se escribe **antes** de
     comparar; un normalizador agregado **después** de ver un diff es el diff
     escondiéndose, y eso es un finding, no un ajuste.
  4. **Los mutantes se caracterizan aislados.** Las flags que escriben (`--vault-init`,
     `--vault-link`, `--scaffold`, `--update`, `--tools-install`, `--mcp-add`/`--mcp-remove`,
     `--provider-add`/`--provider-remove`, `--plugin-on`/`--plugin-off`,
     `--model-pin-set`/`--model-pin-clear`, `--routing-migrate`, `--prune-dead`) y las que
     tocan credenciales o red (`--provider-verify`, `--check-update`, `--quota-failover-e2e`,
     `--fresh-probes`) se caracterizan en un `HOME`/proyecto temporal desechable, con
     `--dry-run` donde exista. **Nunca** contra el árbol real ni contra credenciales
     vivas, y **nunca** se registra el valor de un secreto — solo su presencia/ausencia.
     Una flag que no se pueda caracterizar sin efecto lateral se declara así en la
     evidencia; declararla es el criterio, correrla a ciegas no.
- **AC-B.3** Comportamiento preservado, no "mejorado". Nada de renombrar salidas,
  reordenar campos, arreglar un bug de paso ni cambiar un default. Si aparece un bug
  real durante el movimiento, se registra como finding y se repara aparte — no viaja de
  polizón en el diff del refactor.
- **AC-B.4** El residuo queda **enumerado**, no arrastrado: cada comando de routing/vault
  que se quede en `set_agents_app.py` lleva una razón de una línea que nombra el global
  mutable o el mecanismo concreto que lo ancla (`PROJECT_KEY`, `PROJECT_ROOT`/`ROOT`,
  `ROUTING_WARNINGS`, `app_config`/`write_app_config`, o el `_import()` de
  `tests/test_harness.py:663-684`). Residuo sin razón = paquete rojo.
- **AC-B.5** La duplicación no crece. Las duplicaciones existentes son el techo, no una
  licencia: `atomic_write`/`_BACKED_UP` en `vault_ops.py` y
  `_MAX_FEATURE_BYTES`/`_MAX_FEATURE_FILES` en `routing_cli.py`, ambas con su razón ya
  escrita en el docstring. Una duplicación nueva necesita la misma clase de razón
  medida.
- **AC-B.6** (corregido por **F-035-006**) Dos cierres legales
  (DEC-EXTRACT-TWO-OUTCOMES): el residuo se movió, o se probó anclado y se enumeró. El
  cierre (b) **no se satisface reformateando docstrings que ya existen**. Exige una
  **matriz nueva**, una fila por comando residual, con cuatro columnas:
  `comando` → `dependencia concreta que lo ancla` (nombre del global mutable, del helper o
  del mecanismo) → `experimento o lectura hecha` (el intento de mover y qué falló, o el
  `rg`/lectura que prueba el acoplamiento, con `file:line`) → `resultado`. Sin la tercera
  columna no hay cierre: "está anclado porque el docstring de `routing_cli.py:1-31` ya lo
  dice" es documentación preexistente, no evidencia producida por este paquete. La
  documentación que ya está en el árbol es el **formato** de la matriz, no su contenido.
  El conteo de `wc -l` de `set_agents_app.py` se **reporta** como evidencia; no es una meta
  que se pueda cumplir borrando comentarios o código muerto disfrazado de extracción.
- **AC-B.7** `routing_core/` (`__init__`, `catalog`, `domain`, `gates`, `inference`,
  `service`, `store`, `usage`) y la semántica de vault de ADR-0012/ADR-0056 no se
  rediseñan. Se mueven llamadores, no contratos.
- **AC-B.8** La mordida de PKG-B es asimétrica y hay que decirlo: **ningún test
  existente debe cambiar de color**. Un test que se pone rojo es el defecto, no la
  señal de éxito. La red es la caracterización de AC-B.1 más `tests/test_routing.py`,
  `tests/test_harness.py` y `./build.sh --check`.

### PKG-C — `TIPS-USO.md` al día (y el puntero que evita la contradicción)

**Objetivo.** `TIPS-USO.md` describe los cinco árboles que el repo genera y deja de
afirmar un control plane único; `docs/COMO-FUNCIONA.md` deja de decir que TIPS está
atrasado.

**Criterios**
- **AC-C.1** `TIPS-USO.md:5-14` deja de afirmar "OpenCode is the orchestration control
  plane" y "the other two harnesses are single-task lanes, not orchestrators". Lo que
  queda dicho es lo medido: Claude Code, Cursor y OpenCode pueden orquestar (roster
  completo instalado); lo que **no** cambia por runtime es la lane y la ceremonia — sin
  `init` con señal de riesgo no hay panel (ADR-0064, invariante 2). La advertencia
  concreta sobre Codex (`:12-14`: `spawn_agent` hereda el modelo de sesión y puede
  forkear el transcript) **se conserva**: es una medición, no doctrina vieja.
- **AC-C.2** Los inventarios de TIPS dejan de omitir árboles que el repo genera. Medido
  hoy: `:3` (tres targets vs cinco directorios en `Global/`), `:45`
  (`Global/{opencode,claude-code,codex}` sin `cursor` ni `pi`), `:127-129` ("Native
  agents", sin Cursor ni `pi`).
- **AC-C.3** `:133-134` deja de decir "the three harnesses' own session stores". Medido:
  `ai/scripts/cost-report.py:20-23` y `:836-843` cubren Cursor explícitamente ("every
  runtime including Cursor"; vacío en la lane de routing porque los subagentes nativos
  de Cursor no pasan por los CLIs). La redacción nueva no promete más cobertura de la
  medida.
- **AC-C.4** `docs/COMO-FUNCIONA.md:227-230` deja de afirmar que TIPS está atrasado, y
  `:439-448` (§11, la lista de las tres piezas diferidas) deja de presentarlas como
  pendientes sin más: apunta a este spec. Mismo paquete que AC-C.1 — si se mueve una
  sola superficie, el repo se contradice al revés.
- **AC-C.5** No se reescribe TIPS de punta a punta. Fuera de este paquete: la sección
  "Required lifecycle" (`:117-121`), la política de MCP (`:150-156`) y el bloque de
  bootstrap/instalación (`:25-32`). Este paquete corrige afirmaciones **medidamente
  falsas**, no gustos de redacción.
- **AC-C.6** `README.md:305` describe TIPS como "control plane, lanes, drift". Si la
  corrección de AC-C.1 deja esa línea falsa, se ajusta; si sigue siendo cierta como
  índice, se deja. Lo que no se acepta es no haberla mirado.

---

## Fuera de alcance (no-goals, uno por uno)

1. **Partir `tests/test_harness.py`.** Es el contrato golden (~15 025 líneas). Partirlo
   sin ACs propios pierde mordidas — el mismo argumento que
   `docs/COMO-FUNCIONA.md:426` ya deja escrito. No es objetivo de esta feature.
2. **Desinstalar / scaffold de menú** en la consola. Ya diferido en 034-consola; sigue
   diferido.
3. **Inflar `MODE_BUDGETS`** (`model.py:123-128`). El panel FULL obligatorio se paga con
   el techo que existe.
4. **`--route-decide` en Cursor.** Prohibido en el anfitrión; PKG-B mueve los comandos
   de routing sin habilitarlos acá.
5. **Engram.** No entra. La memoria es el vault (ADR-0012/ADR-0056), y la mención de
   Engram en `TIPS-USO.md:150-156` queda fuera de PKG-C (AC-C.5) — no se convierte esto
   en un debate de memoria.
6. **Reabrir 032 / 033 / 034 como producto.** Pines Cursor, menú freeze, lanes, techo
   frontier y escritor barato quedan como están.
7. **Rediseñar `routing_core/` o la semántica del vault.** PKG-B mueve llamadores.
8. **Cambiar `NON_ACCEPTING_ACTORS` / `REFUTING_ACTORS` / `RISK_SIGNAL_REQUIRED`.**
   PKG-A agrega membresía obligatoria; no reabre quién acepta, quién refuta ni cómo se
   elige el modo.
9. **ADRs de store / API Gateway / deploy.** Esos ejes siguen siendo **n/a**: es CLI de
   estado, movimiento de módulo y documentación. **Corregido por F-035-001:** el ADR de
   **enmienda del contrato público de `record-review`** ya **no** es no-goal — es AC-A.9,
   en alcance, redactado por `architect`. Lo que queda fuera es que **producto** escriba
   ADRs, y ADRs de ejes que este pedido no toca.
10. **Aflojar, saltear o borrar un test de regresión** para que PKG-A cierre. Los siete
    sitios afectados se reescriben con su razón nueva. En particular: **nunca** se baja el
    `--complexity` de un fixture de `medium` a `small` para esquivar el guarda de AC-A.1.
    Eso convierte un test que cubría el camino FULL en uno que cubre el camino SINGLE — es
    pérdida de cobertura disfrazada de reparación (F-035-004).
11. **Un tercer camino de review** (nuevo verbo, nueva fase, nuevo panel). PKG-A cierra
    una puerta; no abre otra.
12. **`record-repair --skip-delta`** (F-035-002, `cli_repair.py:274-282`). Es la otra
    puerta viva hacia `PACKAGE_TESTING` con un finding abierto y está medida, pero cerrarla
    es un slice propio: decisión registrada en
    `docs/notas/decisiones/2026-08-20 035-skip-delta-fuera-del-slice.md`. AC-A.4 y AC-A.5
    se limitan al verbo `record-review`. La rama advisora de `transitions.py:96-109`
    **se conserva** justamente porque esta puerta la mantiene alcanzable.
13. **Modificar `ai/scripts/generate.py`.** La propagación de `orchestrator.md` a los
    cuatro árboles la hace el `copytree` que ya existe (`generate.py:667`); PKG-A cambia el
    canónico y regenera, no el generador.

---

## Primer corte entregable

**PKG-A.** Es el único de los tres que cambia lo que el harness *permite*; B y C
cambian cómo se lee el árbol. Si solo entrara uno, entra A.

---

## Contratos públicos

**CLI de estado (`feature-state.py`).**
- Sigue siendo el único escritor de `ai/state/features/*.json`.
- `record-review` conserva su **firma** y sus tres verdicts (`pass`, `repair_required`,
  `blocked`). **Pero el rechazo nuevo SÍ es cambio de contrato** (F-035-001): con panel
  resuelto FULL el verbo entero se rechaza (cualquier verdict), y con panel SINGLE se
  rechaza `pass` si hay un finding bloqueante abierto. Eso cambia qué invocaciones que hoy
  funcionan dejan de funcionar, y por eso viaja con ADR + doctrina en el mismo paquete
  (AC-A.9). Decir "solo cambia cuándo acepta `pass`" era subdeclararlo.
- `start-review-panel`, `record-subreview`, `finalize-review-panel`,
  `extend-review-panel`, `record-late-review` no cambian de firma.
- `record-repair --skip-delta` **no cambia** en nada (no-goal 12).
- El envelope de error sigue siendo `{"ok": false, "error": ...}` con exit 2 — la forma
  que todo test parsea (razón escrita en `cli_review.py:66-74`).

**Doctrina (`Global/_canonical/agents/orchestrator.md`).** `:103-108` es superficie de
contrato, no prosa: es lo que un orquestador lee para elegir el verbo. Se enmienda en el
mismo paquete (AC-A.9) y se propaga con `generate.py:667` sin editar copias a mano.

**CLI de `set-agents` — flags que deben seguir existiendo** (medidas en el `argparse`,
`set_agents_app.py:4008-4154`):

| grupo | flags |
|---|---|
| estado / observabilidad | `--status`, `--json`, `--context`, `--graph`, `--feature-id`, `--out`, `--limit`, `--project`, `--doctor`, `--doctor-all`, `--harness` |
| routing | `--route-explain`, `--routing-report`, `--route-doctor`, `--route-decide`, `--route-dispatched`, `--route-terminal`, `--route-quota-exhausted`, `--routing-open-runs`, `--routing-recent-writers`, `--routing-decisions`, `--routing-migrate`, `--quota-failover-e2e`, `--quota-error`, `--latency-ms`, `--usage`, `--fresh-probes` |
| vault | `--vault-init`, `--vault-link`, `--vault`, `--vault-doctor`, `--repair`, `--include-notes`, `--private`, `--company` |
| instalación / update | `--check-update`, `--update`, `--yes`, `--no-install`, `--auto-update`, `--scaffold` |
| herramientas / MCP / plugins | `--tools`, `--tools-install`, `--dry-run`, `--mcp`, `--mcp-add`, `--mcp-remove`, `--mcp-on`, `--mcp-off`, `--plugins`, `--plugin-on`, `--plugin-off` |
| proveedores | `--provider-list`, `--provider-add`, `--provider-remove`, `--provider-verify`, `--include-legacy`, `--prune-dead`, `--base-url`, `--npm`, `--label`, `--model` |
| posturas / metodología / modelos | `--posturas`, `--postura`, `--metodologias`, `--metodologia`, `--model-preference-set`, `--provider`, `--model-preference-role-override`, `--model-preference-show`, `--model-pin-set`, `--model-pin-clear` |

**Documentación.** `TIPS-USO.md` y `docs/COMO-FUNCIONA.md` son documentos humanos, no
bloques `notas:auto`. Nada de lo que PKG-C escribe entra a un bloque regenerado por
`feature-state.py`.

---

## Dinero, identidad, auditoría, concurrencia

- **Dinero.** El único costo nuevo es de cuota: un panel FULL obligatorio instancia
  `security-auditor` donde antes no lo hacía. Se paga con `MODE_BUDGETS` sin cambios
  (invariante 1). No hay techo en USD (sigue el no-goal de ADR-0035).
- **Identidad.** No se tocan credenciales, `.env`, ni probes. PKG-B mueve código que
  lee configuración; no cambia qué lee ni la redacta distinto.
- **Auditoría.** Este spec es, en su núcleo, una mejora de auditoría: hoy un paquete
  `medium`/`high` puede mostrar "review pass" sin decir quién revisó. El registro nuevo
  tiene que dejar leer *qué panel se exigía* y *quién lo cumplió*, sobre paquetes donde el
  campo **no está** — `required_reviewers` ausente en **71 de 76** paquetes medidos,
  poblado en 5, `null` explícito en 0 (F-035-005).
- **Concurrencia.** El registro por evento no cambia: `record-subreview` sigue siendo
  idempotente por rol (`cli_review.py:105-106`) y `replayed()` sigue cubriendo los
  reintentos. PKG-A no agrega estado concurrente nuevo.

---

## Riesgos

| riesgo | mitigación |
|---|---|
| PKG-A rompe los tres paquetes vivos (032 `C1`, 011 `P1`, 002 `P1`) | DEC-LEGACY: la negativa dispara en el verbo, y esos tres están en `PACKAGE_GATES`/`BLOCKED` — todavía no llegaron a review. El camino correcto es `start-review-panel`, que ya existe |
| El chequeo pasa en fixture y falla en producción | AC-A.3 corregido (F-035-005): exige **tres** fixtures — clave ausente (la forma de 71/76 paquetes), `null` explícito (0 hoy, pero lo produce un editor a mano) y `complexity` ausente (4 medidos). Un test escrito solo contra `null` pasaría en verde sin tocar un paquete real |
| El código cierra la puerta y la doctrina sigue recomendándola | AC-A.9 (F-035-001): ADR + `Global/_canonical/agents/orchestrator.md` en el **mismo** paquete, propagados por `generate.py:667`. Un CLI que rechaza lo que su doctrina aconseja es peor que el gap original |
| Un fixture baja su `complexity` a `small` para pasar el guarda | No-goal 10 (F-035-004): eso convierte un test del camino FULL en uno del camino SINGLE. Es pérdida de cobertura, y los 5 sitios `medium` están enumerados uno por uno |
| El cambio vive en una sola copia del CLI y ningún test lo ve | AC-A.7: el golden suite corre `PROYECTO/ai/scripts/feature-state.py` (`tests/test_harness.py:32`); `build.sh --check` es la mordida |
| Reescribir `tests/test_harness.py:9024-9039` pierde el invariante, o lo reescribe de forma incoherente (usando `record-late-review` mientras sigue afirmando "ninguna late review ocurrió") | AC-A.5 corregido (F-035-003): se parte en **dos** tests coherentes — el rechazo por `record-review pass` y el advisor después de una puerta que de verdad quede. La rama no se declara inalcanzable porque `record-repair --skip-delta` la mantiene alcanzable |
| PKG-B se vuelve un refactor sin techo | DEC-EXTRACT-TWO-OUTCOMES + AC-B.4/AC-B.6: residuo enumerado con razón, o movido. Dos cierres legales |
| PKG-B arregla un bug "de paso" y contamina el diff | AC-B.3: el bug se registra como finding y se repara aparte |
| PKG-B agrega un tercer docstring de deviation sin bajar líneas | AC-B.6: eso explícitamente no es un cierre legal |
| PKG-C corrige TIPS y deja `COMO-FUNCIONA` contradiciéndolo | DEC-TIPS-POINTER + AC-C.4: mismo paquete, las dos superficies |
| PKG-C se vuelve una reescritura de gusto | AC-C.5: lista cerrada de secciones fuera de alcance |
| El panel FULL obligatorio choca `max_spawns_per_package` | AC-A.8: `HUMAN_DECISION_REQUIRED`, no un techo más grande |

---

## Assumptions (HOW — UNVERIFIED, para architecture)

1. **Dónde vive el chequeo de membresía.** Candidatos: dentro de `cmd_record_review`
   (`cli_review.py:21-63`), en un predicado compartido con `package_accept_ready`
   (`model.py:800-827`), o en los dos (el patrón "un invariante se enforcea en *cada*
   transición del registro" ya está escrito en el docstring de `require_verified`,
   `cli_review.py:278-284`). Producto exige el observable, no el sitio.
2. **Nombres y forma exactos de los errores.** `REVIEW_PANEL_REQUIRED` y
   `BLOCKING_FINDING_OPEN` son los tokens que producto pide; el wording final y si
   viajan como prefijo o como campo del envelope es de architecture.
3. **Firma del predicado de re-derivación** para `required_reviewers` ausente. Producto
   fija la semántica (fail-safe a FULL); architecture decide si es una función nueva o
   `required_reviewers_for` llamado en sitio.
4. **Si algún gate de repo re-valida los 31 state files en lote.** Medido que
   `check-feature-state.py` no lo hace (`verify.sh:65`); el resto **sin verificar**.
5. **Puertas restantes hacia `PACKAGE_TESTING` con findings abiertos.** Medido:
   `finalize-review-panel` chequea (`cli_review.py:159-160`); `record-delta-review`
   chequea (lo afirma el propio comentario de `transitions.py:103`); `record-review` no
   chequea (el defecto de AC-A.4); **`record-repair --skip-delta` no chequea los findings
   que no reparó** (`cli_repair.py:246-253` mira solo los `--finding-id` de la llamada, y
   `:280-282` pone `PACKAGE_TESTING`) — puerta **real y fuera de alcance** (no-goal 12).
   **Sin verificar:** si existe una `transition` directa que llegue ahí. `architect` audita
   todas las puertas en T-001 y **reporta**; con este slice **solo cierra `record-review`**.
6. **Nombres de módulo y firmas de PKG-B** (`routing_lifecycle.py`?
   `vault_doctor.py`? otro): **UNVERIFIED**. Producto exige CLI intacto, caracterización
   previa y residuo enumerado; no nombra archivos.
7. **Si el `_import()` de `tests/test_harness.py:663-684` puede arreglarse
   estructuralmente** para desbloquear más extracción, o si tocarlo es un cambio al
   contrato golden que necesita ACs propios. Esto decide cuál de los dos cierres de
   DEC-EXTRACT-TWO-OUTCOMES aplica. **UNVERIFIED**, y es la pregunta más cara de PKG-B.
8. **Resuelto, ya no es assumption (F-035-001).** El rechazo nuevo **es** cambio de
   contrato público y el ADR entra en alcance (AC-A.9). Lo que queda **UNVERIFIED** es de
   `architect`: el número del ADR, si alcanza uno (contrato + doctrina en un documento) o
   hacen falta dos, y la redacción exacta de la enmienda de
   `Global/_canonical/agents/orchestrator.md:103-108`.
9. **La forma de la comparación de AC-B.2** (F-035-007): si los tres canales se comparan
   con un script de caracterización propio del paquete, con `tests/test_routing.py`
   extendido, o a mano contra archivos capturados. Producto fija **qué** se compara
   (`stdout`+`stderr`+exit, set representativo, normalizadores declarados de antemano) y
   qué se aísla (mutantes y credenciales); el mecanismo es de architecture. **UNVERIFIED.**

---

## Spec audit

> **Segunda pasada (2026-08-20), post `spec-challenger` `revision_required`.** Los siete
> hallazgos F-035-001..007 están aplicados y cada AC corregido cita el suyo. Lo que **no**
> se relitigó: DEC-DOOR y el recorte de `skip-delta` (decisión del orquestador).

### Detección / ausencia — universo nombrado

| requisito | universo | ausencia | ¿la fuente carga la señal? |
|---|---|---|---|
| AC-A.1 panel FULL exigido | todo paquete cuyo panel resuelto es `FULL_REVIEW_PANEL` — derivado de `complexity`+riesgo, **no** de los que tienen el campo poblado | tres formas distintas, no una: clave **ausente** (71/76), `null` explícito (0/76), `complexity` ausente (4/76) → se re-deriva, fail-safe FULL (AC-A.3); ninguna es "sin requisito" | Sí, pero **no** donde uno esperaría, y la medición vieja lo decía mal (F-035-005): `required_reviewers` se persiste en `create-package` (`cli_lifecycle.py:334`), al cambiar `complexity` (`:377`) y en `start-review-panel` (`feature-state.py:569`). Re-medido 2026-08-20 sobre 76 paquetes: **ausente 71 / poblado 5 / `null` 0**. La forma real es la clave **ausente**, así que un predicado que pregunte `is None` no toca ni un paquete real |
| AC-A.9 doctrina | los cuatro árboles que `generate.py:667` genera desde `Global/_canonical/agents/orchestrator.md` | una copia sin regenerar sigue recomendando el camino rechazado; el observable es `rg` sobre los árboles, no sobre el canónico | Sí: `:103-108` es texto grepeable y `build.sh --check` ya verifica la regeneración |
| AC-A.1 "corrió `security-auditor`" | subreviews del panel del paquete | panel inexistente → no hay evidencia → rechazo. Ausencia **es** la señal, no un caso benigno | `review_panels[].subreviews[].role` existe (`cli_review.py:110-116`); `reviews[]` de `record-review` **no** carga el rol del panel, solo `actor` (`:44`) |
| AC-A.4 finding bloqueante abierto | findings del paquete en `critical`/`high`/`medium` no cerrados/refutados, **en el verbo `record-review`** | sin findings → `pass` legítimo, no un rechazo. Y la ausencia de este guarda en **otras** puertas no es un hueco tapado a medias: `record-repair --skip-delta` queda declarado fuera (no-goal 12), no olvidado | Sí: `has_open_findings` ya existe y `finalize-review-panel` lo usa (`cli_review.py:159`) |
| AC-B.2 comportamiento del CLI | el set representativo de combinaciones por grupo (válida / argumento faltante / valor inválido / `--help` / sin argumentos) | una diferencia en `stderr` o en el exit code con `stdout` idéntico **es** una regresión; medir solo el token de primera línea la deja pasar (F-035-007) | Sí, con una condición: los normalizadores se declaran **antes** de comparar. Uno agregado después de ver un diff es el diff escondiéndose |
| AC-A.6 registros históricos | 31 archivos en `ai/state/features/`; 27 features `DONE` | ninguno se re-juzga; la negativa vive en el verbo que muta | `status`/`final_state` existen y se leen; el lote **no** se re-valida por `check-feature-state.py` (`verify.sh:65`) |
| AC-B.2 flags del CLI | las flags declaradas en `set_agents_app.py:4008-4154` | una flag que desaparece es defecto, no simplificación | Sí: el `argparse` es la fuente y es enumerable con `rg` |
| AC-B.4 / AC-B.6 residuo | comandos routing/vault que sigan en `set_agents_app.py` | residuo **sin razón** es el defecto; residuo con razón **producida por este paquete** es un cierre legal. Residuo justificado citando documentación preexistente **no** cierra (F-035-006) | Los docstrings de `routing_cli.py:1-31` y `vault_ops.py:1-23` son el **formato**, no la evidencia. La señal que la matriz tiene que cargar es la columna "experimento o lectura hecha" con `file:line`, que hoy **no existe** en el árbol |
| AC-C.2/C.3 inventarios de TIPS | árboles que `Global/` genera y runtimes que `cost-report.py` cubre | un runtime omitido es el defecto; TIPS no tiene que listar runtimes que el repo no genera | Sí: `ls Global/` (cinco) y `cost-report.py:20-23`, `:836-843` |

### Parejas que disparan sobre la misma entidad

| par | conflicto | precedencia |
|---|---|---|
| AC-A.1 (FULL exige panel) vs AC-A.2 (`small+low` cierra con uno) | los dos deciden si `record-review` es válido | disjuntos por construcción: `required_reviewers_for` (`model.py:565-575`) devuelve exactamente uno de los dos conjuntos |
| AC-A.1 vs `feature-state.py:584-587` (rechaza panel inflado en `small+low`) | ambos gobiernan membresía | complementarios: hoy solo existe el rechazo del panel grande; A.1 agrega el del review chico. Ninguno se relaja |
| AC-A.1 vs `extend-review-panel` (`feature-state.py:624-679`) | un panel puede crecer después de abierto | `extend` sigue siendo el camino de sumar un rol mid-panel; A.1 no lo toca ni lo vuelve obligatorio |
| **AC-A.1 (rechaza el verbo en FULL) vs AC-A.4 (rechaza `pass` con finding abierto)** | los dos rechazan `record-review`, y el enunciado viejo de A.4 decía "`repair_required`/`blocked` no cambian" sin condición — falso cuando el panel es FULL (F-035-004) | **precedencia explícita: A.1 primero.** Con panel FULL cae el verbo entero, cualquier verdict. A.4 solo gobierna el caso panel SINGLE, donde `repair_required`/`blocked` sí siguen intactos. Los 3 sitios `medium` + `repair_required` (`:12399`, `:12451`, `:13006`) son la prueba de que la precedencia hacía falta escribirla |
| AC-A.4 (rechaza `pass` con finding abierto) vs `record-review repair_required` en panel SINGLE | las dos salidas conviven con findings abiertos | `repair_required`/`blocked` no cambian: son las salidas correctas. Solo `pass` se cierra |
| AC-A.4 vs `transitions.py:96-109` (el advisor ya aconseja `PACKAGE_REPAIR`) | uno aconseja, el otro rechaza | el rechazo gana **en su verbo** y el consejo queda vivo (AC-A.5) porque `record-repair --skip-delta` sigue alcanzando ese estado. Un advisor que aconseja bien no sustituye un guarda, y un guarda parcial no autoriza a borrar el advisor |
| AC-A.5 (retirar el comentario-deuda) vs invariante 6 (no aflojar tests) | reescribir el test podría leerse como aflojarlo, y una reescritura ingenua se vuelve **incoherente**: usar `record-late-review` para alcanzar el estado y seguir afirmando que ninguna late review ocurrió (F-035-003) | dos tests coherentes en vez de uno contradictorio (AC-A.5 / T-005). El comentario cita este spec, patrón 034 AC-B.2 |
| AC-A.5 (el advisor se conserva) vs no-goal 12 (`skip-delta` afuera) | conservar una rama cuya única puerta está fuera de alcance parece deuda arrastrada | es lo contrario: la rama es alcanzable **hoy** por `skip-delta` (`cli_repair.py:246-253`, `:280-282`), así que conservarla es exactitud y borrarla sería el defecto. El comentario nombra la puerta y la decisión que la difiere |
| AC-A.9 (doctrina enmendada) vs no-goal 13 (`generate.py` no se toca) | cambiar cuatro árboles sin tocar el generador | se edita **solo** el canónico y se corre la regeneración que ya existe (`copytree`, `generate.py:667`); `build.sh --check` es la mordida |
| AC-A.9 (ADR en alcance) vs no-goal 9 (producto no redacta ADRs) | parece contradicción | no lo es: producto **declara** que el ADR entra y qué tiene que decidir; `architect` lo **redacta**. La frontera es quién escribe, no si existe |
| AC-A.3 (fail-safe FULL) vs AC-A.6 (no invalidar histórico) | un paquete legacy `high` con el campo ausente podría quedar trabado, y los **4** paquetes sin `complexity` caerían al fail-safe FULL | DEC-LEGACY: `accepted`/`superseded`/`DONE` quedan fuera, y los 4 sin `complexity` están todos ahí (medido). Los tres paquetes vivos medidos todavía no entraron a review |
| AC-A.8 (techo intacto) vs AC-A.1 (panel obligatorio) | más roles obligatorios, mismo techo de despachos | gana el techo → `HUMAN_DECISION_REQUIRED`. No se sube `MODE_BUDGETS` |
| AC-A.7 (dos copias) vs PKG-B (mueve `set_agents_app.py`, que **no** está en `PROYECTO/`) | dos reglas de paridad distintas | son universos distintos: `feature_state_lib`/`feature-state.py` se espejan; `set_agents_app.py` vive solo en `ai/scripts`. Confirmado con `ls`/`rg` de `PROYECTO/ai/scripts` |
| AC-B.3 (nada de mejoras) vs AC-B.8 (ningún test cambia de color) | un bug real descubierto al mover | el bug se registra como finding y se repara aparte; el diff del refactor queda limpio |
| AC-B.6 (`wc -l` como evidencia) vs AC-B.3 (preservar comportamiento) | bajar líneas tienta a borrar | el conteo se **reporta**, no es meta; borrar comentarios o código muerto no cuenta como extracción |
| AC-B.2 (comparar los tres canales) vs AC-B.2.4 (mutantes aislados) | las flags que escriben no se pueden comparar dos veces sin ensuciar el árbol | precedencia: el aislamiento gana. `HOME`/proyecto temporal + `--dry-run` donde exista; una flag que no se pueda caracterizar sin efecto lateral se **declara** en la evidencia en vez de correrse a ciegas |
| AC-C.1 (TIPS deja de decir "control plane único") vs `COMO-FUNCIONA:227-230` (dice que TIPS lo dice) | corregir uno vuelve falso al otro | DEC-TIPS-POINTER/AC-C.4: mismo paquete, las dos superficies |
| AC-C.1 vs `COMO-FUNCIONA:221` ("control plane histórico en `TIPS-USO.md`") | la tabla remite a una afirmación que va a cambiar | AC-C.4: se revisa la celda junto con `:227-230` |
| AC-C.1 (los tres orquestan) vs invariante 2 (ADR-0064 / `RISK_SIGNAL_REQUIRED`) | "podés orquestar desde cualquiera" podría leerse como "hay panel en cualquiera" | AC-C.1 lo dice explícito: lo que no cambia por runtime es la lane. Sin señal no hay panel |
| AC-C.5 (no tocar MCP en TIPS) vs no-goal 5 (Engram) | TIPS menciona Engram | se deja como está: corregir TIPS no es la ocasión de relitigar memoria |
| AC-C.6 (`README:305`) vs AC-C.5 (alcance cerrado) | ampliar a README parece scope creep | una línea de índice, y solo si la corrección la vuelve falsa. Mirarla es obligatorio; cambiarla, condicional |
| PKG-A vs PKG-B | los dos tocan `ai/scripts/` | rutas disjuntas: A en `feature_state_lib/`+`feature-state.py` (y su espejo `PROYECTO/`), B en `set_agents_app.py`+módulos nuevos. El planner lo fija con `owned_paths` |

### HOW marcado UNVERIFIED

Los nueve ítems de Assumptions (el 8 viejo quedó resuelto por F-035-001 y se reemplazó por
la pregunta que sí queda abierta: cuántos ADRs y con qué número). Ninguna sección vacía:
una lista vacía acá habría significado que no miré.

### Mordida del golden suite — enumerada, no estimada (F-035-004)

La cuenta vieja ("25 sitios de `record-review`") mezclaba invocaciones del CLI con strings
de `history`/`event` en fixtures. Re-medido el 2026-08-20:

- `rg -c 'record-review' tests/test_harness.py` → **31** apariciones del string.
- `rg -n '"record-review"' tests/test_harness.py` → **25** apariciones como argumento
  citado, de las cuales **5** son entradas de `history`/`event` en fixtures armados a mano
  (`:9514`, `:9530`, `:9636`, `:12234`, `:12739`) y no invocan nada.
- **Invocaciones reales del CLI: 20.** Clasificadas una por una (complejidad del paquete
  desde el `--complexity` de su `create-package` o del helper que lo crea):

| # | `file:line` | test | complejidad | verdict | ¿cae? |
|---|---|---|---|---|---|
| 1 | `:8580` | `test_done_ready_reaches_done_after_a_real_block_and_reopen_cycle` | `medium` (`:8568`) | `pass` | **sí — AC-A.1** |
| 2 | `:10170` | `test_non_runtime_package_accepts_without_runtime_qa` | `medium` (`:10160`) | `pass` | **sí — AC-A.1** |
| 3 | `:12399` | `test_record_repair_commit_fail_open_when_git_cannot_answer` | `medium` (`:12385`) | `repair_required` | **sí — AC-A.1** (el verbo, no el verdict) |
| 4 | `:12451` | `test_record_repair_commit_accepted_when_git_verifies_it` | `medium` (`:12437`) | `repair_required` | **sí — AC-A.1** |
| 5 | `:13006` | `test_record_repair_commit_fail_open_in_real_shallow_clone` | `medium` (`:12992`) | `repair_required` | **sí — AC-A.1** |
| 6 | `:9032` | `test_next_does_not_blame_a_late_review_that_never_happened` | `small` (helper `:440`) | `pass` + finding `high` inline | **sí — AC-A.4** |
| 7 | `:11048` | `test_accept_package_rejects_open_findings_and_bad_actors` | `small` (helper `:440`) | `pass` + finding `high` inline | **sí — AC-A.4** |
| 8–20 | `:457`, `:9281`, `:9802`, `:9836`, `:9865`, `:9903`, `:9949`, `:10012`, `:10037`, `:10124`, `:10147`, `:12704`, `:13634` | varios | `small` (`create_ready_package` `:440`, `_notes_project` `:3798`) | 12 × `repair_required`, 1 × `pass` sin findings (`:13634`) | **no** |

**Mordida conocida: 7 sitios de 20.** 13 quedan intactos. Esto ya no es "una cuenta que el
implementer confirma": está contada. Lo que **sí** queda por confirmar es si la suite
completa descubre un sitio que esta clasificación estática no vio (un fixture que muta
`complexity` después de crear el paquete, por ejemplo) — eso es T-006, y por eso T-006
sigue existiendo aunque acotado.

### Qué no pude verificar

- Si algún gate de repo re-valida en lote los 31 archivos de `ai/state/features/`
  (medido solo que `check-feature-state.py` no lo hace).
- Si existe una `transition` directa que alcance `PACKAGE_TESTING` con findings
  bloqueantes abiertos. Medí las cuatro puertas por verbo: `finalize-review-panel` chequea,
  `record-delta-review` chequea, `record-review` no (se cierra acá),
  `record-repair --skip-delta` no (queda fuera, no-goal 12).
- Si el `_import()` de `tests/test_harness.py:663-684` puede arreglarse sin ACs propios
  contra el contrato golden.
- Si la suite completa descubre un octavo sitio afectado (ver la tabla de arriba: la
  clasificación es estática).
- El número que le toca al ADR de AC-A.9, y si `architect` decide uno o dos documentos.
- El slug/id concreto que `security-auditor` resuelve en Cursor (no hace falta para
  este contrato).
