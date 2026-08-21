# 035 — Criterios de aceptación (BDD)

> Escenarios en lenguaje de negocio, observables de punta a punta. Cada uno cita
> `file:line` **medido el 2026-08-20** o dice **sin verificar**. El actor es quien
> observa, no la función que corre.
>
> **Revisión post-challenge (2026-08-20).** Los ACs corregidos citan el hallazgo
> `F-035-00N` de `spec-challenger` que cierran. DEC-DOOR y el recorte de
> `record-repair --skip-delta` no se relitigan.

---

## Diagrama de flujo (actor → acción → resultado observable)

```
                        ┌──────────────────────────────────────────┐
                        │  PKG-A · Panel honesto (CLI de estado)   │
                        └──────────────────────────────────────────┘

  orquestador                 CLI de estado                     lo que se observa
  ───────────                 ─────────────                     ─────────────────

  paquete small+low
  record-review pass  ──────▶ panel requerido = 1 rol   ──────▶  ACEPTA
                              (model.py:95)                      → PACKAGE_TESTING
                                                                 (sin cambios · A-2)

  paquete medium/high
  record-review       ──────▶ panel requerido = 2 roles ──────▶  RECHAZA exit 2
  CUALQUIER verdict           (model.py:96)                      REVIEW_PANEL_REQUIRED
  (pass / repair_required                                        "falta security-auditor
   / blocked)                                                     → start-review-panel"
                                                                 (A-1 · precede a A-4)

  paquete legacy              tres formas de ausencia:
  required_reviewers  ──────▶ clave ausente (71/76)     ──────▶  RECHAZA igual
  no usable                   null explícito (0/76)              (A-3)
                              complexity ausente (4/76)
                              → fail-safe FULL
                              (model.py:565-575, :571)

  panel completo:
  start-review-panel  ──────▶ subreview package-reviewer ─────▶  ACEPTA
   + record-subreview ×2      + subreview security-auditor       → PACKAGE_TESTING
   + finalize pass                                               (A-1 camino verde)

  paquete small+low
  record-review pass  ──────▶ has_open_findings         ──────▶  RECHAZA exit 2
  con finding high            (mismo predicado que        BLOCKING_FINDING_OPEN
  abierto                     finalize, cli_review.py:159)       (A-4 · solo panel SINGLE)

  paquete small+low           repair_required / blocked  ─────▶  ACEPTA (sin cambios)
  con finding abierto ──────▶ siguen siendo las salidas          (A-4 límite 1)
                              legítimas

  record-repair       ──────▶ NO se toca en este slice  ──────▶  sigue llegando a
  --skip-delta                (cli_repair.py:274-282)            PACKAGE_TESTING con
                                                                 otro finding abierto
                                                                 → el advisor se conserva
                                                                 (A-5 · no-goal 12)

  orquestador lee     ──────▶ ADR Accepted + doctrina    ─────▶  la doctrina ya no
  la doctrina                 orchestrator.md:103-108            recomienda la puerta
                              (regenerada, generate.py:667)      que el CLI rechaza
                                                                 (A-9)

  paquete accepted /  ──────▶ no se re-juzga            ──────▶  intacto
  feature DONE (×27)                                             (A-6)


                        ┌──────────────────────────────────────────┐
                        │  PKG-B · Consola partida                 │
                        └──────────────────────────────────────────┘

  Federico
  set-agents --status ─────▶ mismo comando, módulo nuevo ─────▶  stdout + stderr + exit
  --vault-doctor             (caracterización previa de           IDÉNTICOS, normalizando
  --route-explain …          los tres canales, AC-B.1)            solo timestamps/rutas/
  + faltante + inválido                                           latencias declarados
  + --help + sin args                                             de antemano
                                                                 (B-1, B-2)

  flags que escriben  ─────▶ HOME/proyecto temporal,     ─────▶  caracterizadas aisladas;
  o tocan credenciales       --dry-run donde exista               ningún secreto queda
                                                                 registrado
                                                                 (B-2 punto 4)

  quien lea el módulo ─────▶ matriz comando → dependencia ────▶  cada residuo con su
                             → experimento/lectura              experimento propio, no
                             → resultado                        un docstring reciclado
                                                                 (B-4, B-6)


                        ┌──────────────────────────────────────────┐
                        │  PKG-C · TIPS al día                     │
                        └──────────────────────────────────────────┘

  Federico lee        ─────▶ TIPS-USO.md                 ─────▶  cinco árboles, tres que
  "cómo se usa esto"         + COMO-FUNCIONA.md                  orquestan, Cursor en
                             (misma entrega)                     cost-report · y COMO-FUNCIONA
                                                                 ya no dice "TIPS atrasado"
                                                                 (C-1..C-4)
```

---

## PKG-A — Panel honesto

### AC-A.1 — Un paquete medium/high no cierra su review con un solo reviewer

**Dado** un paquete cuyo panel resuelto es `FULL_REVIEW_PANEL`
(`ai/scripts/feature_state_lib/model.py:96` → `["package-reviewer",
"security-auditor"]`, la rama que `required_reviewers_for` toma para cualquier eje
`medium`/`high`, `model.py:565-575`),
**y** que está en `PACKAGE_REVIEW` con sus gates en verde,
**cuando** el orquestador registra `record-review <pkg> <verdict> --actor package-reviewer`
sin panel abierto, **con cualquiera de los tres verdicts** (`pass`, `repair_required`,
`blocked` — DEC-DOOR rechaza el **verbo**, no el verdict),
**entonces** el comando **falla** con exit 2 y el envelope
`{"ok": false, "error": ...}` (la forma que todo caller parsea, razón escrita en
`ai/scripts/feature_state_lib/cli_review.py:66-74`), el error se llama
`REVIEW_PANEL_REQUIRED`, nombra el rol faltante (`security-auditor`) y nombra el verbo
correcto (`start-review-panel`),
**y** la fase **sigue** en `PACKAGE_REVIEW`,
**y** `attempts.deep_review_cycles` **no** se incrementa (hoy sí lo hace en cada
llamada, `cli_review.py:46` — un rechazo no puede cobrar un ciclo).

**Precedencia sobre AC-A.4 (F-035-004).** Este AC se evalúa **primero**. Con panel FULL no
existe un `record-review` legal, así que la excepción de AC-A.4 ("`repair_required` y
`blocked` no cambian") **no** aplica acá. Prueba de que hacía falta escribirlo: tres sitios
del golden suite usan `--complexity medium` con verdict `repair_required`
(`tests/test_harness.py:12399`, `:12451`, `:13006`) y caen por este AC, no por A.4.

### AC-A.2 — Un paquete small+low sigue cerrando con un solo reviewer

**Dado** un paquete `complexity=small` y riesgo resuelto `low`
(`SINGLE_REVIEW_PANEL = ["package-reviewer"]`, `model.py:95`; `DEFAULT_PACKAGE_RISK =
"low"`, `model.py:94`),
**cuando** el orquestador registra `record-review <pkg> pass --actor package-reviewer`,
**entonces** el comando **pasa**, la fase avanza a `PACKAGE_TESTING` y el paquete queda
`testing_required` — exactamente el comportamiento de hoy (`cli_review.py:54-56`).
**Y** el fixture `create_ready_package` (`tests/test_harness.py:431-468`, que crea con
`--complexity small` en `:440`) sigue verde sin tocarlo.

### AC-A.3 — `required_reviewers` sin valor usable no significa "sin requisito"

> Corrige **F-035-005**. La medición anterior ("30 de 31 archivos con `required_reviewers =
> null`") contaba archivos en vez de paquetes y trataba "clave ausente" como si fuera
> "`null` explícito" — dos formas distintas que un predicado distingue.

**Medición re-hecha el 2026-08-20** sobre `ai/state/features/*.json` (31 archivos,
**76 paquetes**), recorriendo los paquetes y clasificando
`"required_reviewers" not in pkg` / `is None` / poblado:

| forma | paquetes |
|---|---|
| `required_reviewers` **ausente** (clave inexistente) | **71** |
| `required_reviewers` **poblado** | **5** |
| `required_reviewers: null` **explícito** | **0** |
| `complexity` **ausente** | **4** (de 76: `high` 25, `medium` 34, `small` 13) |

**Dado** un state file donde el paquete no tiene un panel usable, en cualquiera de sus
**tres** formas —(i) clave `required_reviewers` **ausente**, (ii) `null` explícito,
(iii) `complexity` ausente— y complejidad `medium`/`high` (o ausente),
**cuando** el orquestador intenta `record-review <pkg> <verdict>`,
**entonces** recibe el mismo `REVIEW_PANEL_REQUIRED` que un paquete recién creado, porque
el panel se **re-deriva** de `complexity` + riesgo resuelto (`resolve_package_risk`,
`model.py:555-562`), con **fail-safe a FULL** cuando `complexity` es `None`
(`model.py:571` ya lo hace) — ese fail-safe **se conserva**.

**Los tres fixtures son obligatorios y separados:**
1. state file con la clave `required_reviewers` **ausente** — la forma de 71/76 paquetes.
2. state file con `required_reviewers: null` **explícito** — 0 paquetes hoy, pero es lo que
   produce una edición a mano; el predicado la cubre igual.
3. state file con `complexity` **ausente/`None`** — 4 paquetes medidos; verifica el
   fail-safe FULL, no la derivación normal.

**Dos fixtures que engañarían al criterio, nombrados:**
- (a) un test que solo use `create-package --complexity medium`, que **sí** persiste el
  campo (`ai/scripts/feature_state_lib/cli_lifecycle.py:334`). Pasaría en verde probando
  únicamente el camino que los datos reales no tienen.
- (b) un test que escriba **solo** `required_reviewers: null`. Pasaría en verde y no
  tocaría **ni uno** de los 76 paquetes reales, porque la forma real es la clave
  **ausente**. Este es el fixture que la medición vieja habría autorizado.

El criterio no está satisfecho hasta que existan los tres casos de arriba.

### AC-A.4 — `pass` no salta por encima de un finding bloqueante abierto

> Corrige **F-035-002** (alcance limitado al verbo `record-review`) y **F-035-004**
> (la excepción de `repair_required`/`blocked` vale **solo** con panel SINGLE).

**Dado** un paquete cuyo panel resuelto es `SINGLE_REVIEW_PANEL` (`small`+`low`) — porque si
es FULL manda AC-A.1 y ningún verdict pasa — **y** con un finding `critical`, `high` o
`medium` abierto (ni cerrado ni refutado),
**cuando** el orquestador registra `record-review <pkg> pass`,
**entonces** el comando **falla** con exit 2 y `BLOCKING_FINDING_OPEN`, usando el mismo
predicado y el mismo conjunto de severidades que `finalize-review-panel` ya aplica
(`cli_review.py:158-160`: `has_open_findings(package, {"critical","high","medium"})` →
`StateError("cannot pass review panel with blocking findings open")`),
**y** la fase sigue en `PACKAGE_REVIEW`.

**Y** con panel SINGLE, `record-review <pkg> repair_required` y `record-review <pkg>
blocked` **no** cambian: son las salidas legítimas con findings abiertos
(`cli_review.py:50-58`). Con panel **FULL** esa frase sería falsa — cae el verbo entero por
AC-A.1, y hay tres sitios medidos del golden suite que lo demuestran
(`tests/test_harness.py:12399`, `:12451`, `:13006`: `--complexity medium` +
`repair_required`).

**Y** este AC **no** promete que `PACKAGE_TESTING` con un finding abierto se vuelva
inalcanzable. Promete que **`record-review pass` deja de ser una de sus puertas**.
`record-repair --skip-delta` sigue llegando ahí (`cli_repair.py:280-282`, con la guarda de
`:246-253` que solo mira los findings **reparados**) y queda **fuera de este slice** por
decisión registrada en
`docs/notas/decisiones/2026-08-20 035-skip-delta-fuera-del-slice.md`. Un AC que prometiera
la inalcanzabilidad global sería un AC que no se puede verificar con este diff.

### AC-A.5 — Ningún comentario nombra una puerta que ya se cerró (ni declara inalcanzable lo alcanzable)

> Corrige **F-035-003**. La versión anterior permitía dos salidas incompatibles: alcanzar
> el estado por `record-late-review` **y** conservar la aserción de que ninguna late review
> ocurrió. No se puede tener las dos. La salida correcta es partir el test en dos.

**Dado** que `ai/scripts/feature_state_lib/transitions.py:102-107` hoy documenta la deuda
con la frase *"record-review is outside this package's criteria and every package in flight
uses it"*,
**cuando** AC-A.1 y AC-A.4 cierran esa puerta,
**entonces** esa frase no sobrevive tal cual (grepeable: buscarla no devuelve nada),
**y** la rama del advisor (`transitions.py:96-109`) **no se borra** **y no se declara
inalcanzable**, porque está medido que sigue siendo alcanzable:
`record-repair --skip-delta` pone `data["phase"] = "PACKAGE_TESTING"` directo
(`ai/scripts/feature_state_lib/cli_repair.py:280-282`) y su guarda exige "all **repaired**
findings <= medium" mirando solo los `--finding-id` de esa llamada (`:246-253`), así que un
finding abierto que no se reparó viaja con él,
**y** el comentario nuevo nombra **esa** puerta y cita la decisión que la difiere
(`docs/notas/decisiones/2026-08-20 035-skip-delta-fuera-del-slice.md`).

**El test se parte en dos escenarios coherentes** (reemplaza a
`test_next_does_not_blame_a_late_review_that_never_happened`,
`tests/test_harness.py:9024-9039`):

**(1) El estado ya no se alcanza por `record-review`.**
**Dado** un paquete `small`+`low` en `PACKAGE_REVIEW` con un finding `high`,
**cuando** se corre `record-review PKG-01 pass --finding <high>` (hoy `:9032`),
**entonces** el comando **falla** con exit 2 y `BLOCKING_FINDING_OPEN`, y la fase **sigue**
en `PACKAGE_REVIEW` — la aserción vieja `data["phase"] == "PACKAGE_TESTING"` (`:9036`) se
vuelve imposible y se reemplaza por la del rechazo. Este escenario **no menciona** late
review en ninguna parte, porque no hay ninguna.

**(2) El advisor sigue diciendo la verdad cuando el estado se alcanza de verdad.**
**Dado** un paquete que llegó a `PACKAGE_TESTING` por una puerta que **realmente existe**
—`record-repair --skip-delta` con otro finding abierto (`cli_repair.py:280-282`), o un
`record-late-review` que **sí** se corrió (`ai/scripts/feature-state.py:683-695`)—,
**cuando** el orquestador pide `next`,
**entonces** `advice["next"] == "PACKAGE_REPAIR"` y el `reason` nombra el **finding
bloqueante**, no el mecanismo por el que se llegó: se conservan
`assertIn("blocking finding", ...)` y `assertNotIn("late review", ...)` (`:9038-9039`), que
es exactamente lo que el test protegía. La coherencia está en que ya no se afirma "ninguna
late review ocurrió" mientras se usa una: si el escenario elige la puerta `skip-delta`, no
hay late review y la aserción es literal; si elige `record-late-review`, la aserción sigue
válida porque lo que prohíbe es que el **motivo** culpe al mecanismo, no que el mecanismo
exista. El comentario del test dice cuál de las dos se eligió y por qué.

**Sin verificar:** si existe además una `transition` directa a `PACKAGE_TESTING`. T-001 la
audita y **reporta**; este slice cierra `record-review` y nada más.

### AC-A.6 — El histórico no se re-juzga

**Dado** 27 features en `final_state = DONE` y todo paquete `accepted`/`superseded`
(medido archivo por archivo el 2026-08-20),
**cuando** el cambio de PKG-A está instalado,
**entonces** ninguno de esos archivos empieza a fallar validación, porque la negativa
vive en el verbo que muta y no en la lectura de un registro histórico
(`check-feature-state.py` mide commits de delivery contra state files, no paneles —
`ai/scripts/verify.sh:65`),
**y** los tres paquetes vivos que sí caen bajo la regla nueva son los medidos: 032 `C1`
(`medium`, 0 reviews, feature en `PACKAGE_GATES`), 011 `P1-quota-failover` (`high`, 0
reviews, `BLOCKED`), 002 `P1-routing-core` (`high`, `repair_required`, `BLOCKED`) —
ninguno entró todavía a review, así que su camino correcto es `start-review-panel`, que
ya existe.

### AC-A.7 — El cambio existe en las dos copias del CLI

**Dado** que el golden suite corre el CLI **del template** —
`FEATURE_STATE = ROOT / "PROYECTO/ai/scripts/feature-state.py"`
(`tests/test_harness.py:32`) — y que hay un test que exige que las dos copias existan
(`tests/test_harness.py:8995`),
**cuando** PKG-A modifica `feature_state_lib`/`feature-state.py`,
**entonces** `./build.sh --check` pasa: `SELF_SCAFFOLD_DRIFT` compara `ai/scripts`
contra `PROYECTO/ai/scripts` (`build.sh:69-79`) y `Global/*/hooks/feature_state_lib` se
regenera por `copytree` (`ai/scripts/generate.py:667`, cuatro árboles: `claude-code`,
`codex`, `cursor`, `opencode`).
Un cambio en una sola copia es un paquete **rojo**, no un paquete incompleto.

### AC-A.8 — El panel obligatorio se paga con el techo que existe

**Dado** `MODE_BUDGETS["scoped"]["max_spawns_per_package"] == 8`
(`model.py:125`),
**cuando** un paquete tiene que instanciar `security-auditor` que antes no instanciaba y
con eso choca el techo,
**entonces** `record-spawn` devuelve `BLOCKED` como ya hace hoy y el orquestador
persiste `HUMAN_DECISION_REQUIRED`,
**y** `MODE_BUDGETS` **no** cambia de valor (`model.py:123-128`).

### AC-A.9 — La doctrina no sigue recomendando la puerta que el CLI ahora rechaza

> Cierra **F-035-001**. Este AC es la razón por la que el spec dejó de declarar "cero ADRs
> nuevos": el rechazo nuevo **es** contrato público.

**Dado** que `Global/_canonical/agents/orchestrator.md:103` lista `record-review` entre los
verbos del ciclo normal, y `:105-108` presenta `start-review-panel` / `record-subreview` /
`finalize-review-panel` como lo que se usa *"when multiple specialist reviewers **are
useful**"* — es decir: panel **opcional**, a criterio del orquestador —,
**cuando** PKG-A cierra,
**entonces** se observan tres cosas, **en el mismo paquete**:

1. **Un ADR con estado `Accepted`** que enmienda el contrato público de `record-review`:
   la **firma no cambia** (mismo comando, mismos tres verdicts, mismo envelope de error
   `{"ok": false, ...}` con exit 2), y lo que se agrega son dos rechazos nombrados —
   `REVIEW_PANEL_REQUIRED` (membresía) y `BLOCKING_FINDING_OPEN` (finding abierto) — con
   `small`+`low` conservado como la puerta legítima del verbo. **Lo redacta `architect`**:
   producto declara que entra en alcance y qué tiene que resolver, no su texto.
2. **`Global/_canonical/agents/orchestrator.md` enmendado**, de modo que un orquestador que
   lea la doctrina no elija el camino que el CLI rechaza: el panel queda **obligatorio**
   cuando el panel resuelto es FULL, y `record-review` queda descrito como la puerta de
   `small`+`low`.
3. **Los cuatro árboles regenerados** por el `copytree` que ya existe
   (`ai/scripts/generate.py:667` — `claude-code`, `codex`, `cursor`, `opencode`).
   **`generate.py` no se modifica** y las copias **no** se editan a mano.

**Observable, grepeable:** `rg` sobre `Global/*/agents/orchestrator.md` no encuentra la
recomendación vieja del panel como opcional, el ADR existe con estado `Accepted`, y
`./build.sh --check` pasa (la regeneración es parte de la mordida, igual que en AC-A.7).
**Sin verificar:** el número que le toca al ADR y si `architect` decide uno o dos
documentos (contrato y doctrina pueden ir juntos).

---

### Mordida de PKG-A (tests que hoy PASAN y mañana deben FALLAR)

> Corrige **F-035-004**. La nota vieja decía "25 sitios de `record-review`, cuántos caen es
> una cuenta que el implementer confirma". Estaba mal contado y mal delegado: 25 es el
> número de apariciones **citadas**, de las que 5 son entradas de `history`/`event` en
> fixtures armados a mano. Las invocaciones reales del CLI son **20**, y están clasificadas
> una por una acá abajo.

**Conteo re-medido el 2026-08-20.**
`rg -c 'record-review' tests/test_harness.py` → 31 apariciones del string.
`rg -n '"record-review"' tests/test_harness.py` → 25 como argumento citado.
Menos las 5 de `history`/`event` (`:9514`, `:9530`, `:9636`, `:12234`, `:12739`) →
**20 invocaciones reales del CLI**.

**Mordida conocida: 7 de 20.** Sin estos siete en rojo, PKG-A no se implementó — se
documentó.

| # | sitio | test | por qué cae | reescritura |
|---|---|---|---|---|
| 1 | `:8580` | `test_done_ready_reaches_done_after_a_real_block_and_reopen_cycle` (`:8556-8599`) | `--complexity medium` (`:8568`) → panel FULL; corre `record-review pass` solo y llega a `DONE` (`:8597`). **AC-A.1.** Es el patrón exacto del gap: `security-auditor` nunca corrió y la feature terminó `DONE` | `start-review-panel` + dos `record-subreview` + `finalize-review-panel`. Su invariante vivo —`done_ready()` filtra blockers por `resolved_at`— se conserva intacto |
| 2 | `:10170` | `test_non_runtime_package_accepts_without_runtime_qa` | `--complexity medium` (`:10160`), verdict `pass`. **AC-A.1** | camino del panel; lo que el test protege (un paquete no-runtime acepta sin runtime QA) no se toca |
| 3 | `:12399` | `test_record_repair_commit_fail_open_when_git_cannot_answer` | `--complexity medium` (`:12385`), verdict **`repair_required`**. **AC-A.1 rechaza el verbo, no el verdict** — este sitio es la prueba de que "`repair_required` no cambia" solo vale con panel SINGLE | camino del panel hasta dejar el paquete en `PACKAGE_REPAIR`; la aserción sobre el fail-open de `git` no se toca |
| 4 | `:12451` | `test_record_repair_commit_accepted_when_git_verifies_it` | `--complexity medium` (`:12437`), `repair_required`. **AC-A.1** | ídem |
| 5 | `:13006` | `test_record_repair_commit_fail_open_in_real_shallow_clone` | `--complexity medium` (`:12992`), `repair_required`. **AC-A.1** | ídem |
| 6 | `:9032` | `test_next_does_not_blame_a_late_review_that_never_happened` (`:9024-9039`) | `small`+`low`, `pass` con finding `F-H` `high` inline; afirma `phase == "PACKAGE_TESTING"` (`:9036`). **AC-A.4** | se **parte en dos** escenarios coherentes (AC-A.5): el rechazo, y el advisor sobre una puerta que existe de verdad |
| 7 | `:11048` | `test_accept_package_rejects_open_findings_and_bad_actors` (`:11044-11054`) | `small`+`low`, `pass` con finding `F-001` `high` inline como **setup**. **AC-A.4** hace fallar la preparación, no la aserción | el estado "aceptación con finding `high` abierto" se arma por una vía legal (`repair_required`, o `record-late-review` sobre un paquete ya fuera de review). Las dos aserciones que el test protege —`repair-agent cannot accept packages` y `critical/high findings`— se conservan **las dos** |

**Los 13 sitios que NO caen** (verificado uno por uno): `:457`, `:9281`, `:9802`, `:9836`,
`:9865`, `:9903`, `:9949`, `:10012`, `:10037`, `:10124`, `:10147`, `:12704` — todos
`small`+`low` (helper `create_ready_package`, `--complexity small` en `:440`;
`_notes_project`, `:3798`) con verdict `repair_required` — y `:13634`, `small` con `pass`
sin findings abiertos.

**Regla que no se negocia (no-goal 10):** los que caigan se **reescriben al camino del
panel**, que es lo que la doctrina va a exigir después de AC-A.9 — **nunca** bajando el
`--complexity` del fixture de `medium` a `small` para esquivar el guarda. Eso convierte un
test que cubría el camino FULL en uno que cubre el camino SINGLE: es pérdida de cobertura
disfrazada de reparación.

**Lo que sigue sin verificar:** si la suite completa descubre un octavo sitio que esta
clasificación estática no vio (por ejemplo un fixture que muta `complexity` con
`update-package` después de crear el paquete). Eso es T-006, que por eso sigue existiendo
—acotado a confirmar la enumeración, no a descubrirla.

---

## PKG-B — La consola partida

### AC-B.1 — La caracterización es previa, no una foto del resultado

**Dado** que `ai/scripts/set_agents_app.py` tiene 4399 líneas (`wc -l`, 2026-08-20),
**cuando** el paquete arranca,
**entonces** existe evidencia registrada **antes del primer movimiento de código** con,
para cada combinación del set representativo de AC-B.2, el comando corrido y sus **tres**
canales capturados (`stdout` completo, `stderr` completo, código de salida),
**y** una caracterización fechada después del diff no cuenta.

### AC-B.2 — El CLI público no cambia, y "no cambia" se mide en tres canales

> Corrige **F-035-007**. La versión anterior prometía "misma salida" en la propuesta pero
> solo verificaba flags y el token de primera línea. Con eso, un `stderr` distinto o un
> exit code distinto pasaban en verde. Lo que sigue es la promesa **testable**, y es la que
> la propuesta ejecutiva ahora repite — no "byte a byte mágico".

**Dado** el `argparse` medido en `ai/scripts/set_agents_app.py:4008-4154`,
**cuando** la extracción termina,
**entonces**:

1. **Superficie.** Toda flag sigue existiendo con el mismo nombre y la misma
   aridad/`metavar`. Lista completa por grupos en `spec.md` § Contratos públicos.
2. **Comportamiento observable.** Para un **set representativo de combinaciones** —por cada
   grupo de esa tabla, al menos: una invocación **válida**, una con **argumento faltante**,
   una con **valor inválido**, más `--help` y la invocación **sin argumentos**— el `stdout`
   **completo**, el `stderr` **completo** y el **código de salida** son idénticos a la
   caracterización de AC-B.1. Los tokens medidos —`APP_STATUS` (`:4008`),
   `VAULT_INIT_OK`/`VAULT_INIT_SKIP` (`:2896`), `VAULT_LINK_SKIP` (`:2999`),
   `VAULT_LINK_CONFLICT` (`:3020`), `TOOL` (`:4065`), `MCP` (`:4068`)— quedan **dentro** de
   lo comparado; no son el criterio.
3. **Normalización cerrada y previa.** Se normalizan **solo** valores que cambian entre dos
   corridas del **mismo** binario: timestamps, rutas absolutas de `tmp`/`$HOME`,
   duraciones/latencias en ms, PIDs, versiones, y orden no determinístico donde el comando
   no lo garantiza. La lista se escribe **antes** de la primera comparación. Un normalizador
   agregado **después** de ver un diff es el diff escondiéndose: se registra como finding,
   no como ajuste.
4. **Los mutantes se caracterizan aislados.** Las flags que **escriben** —`--vault-init`,
   `--vault-link`, `--scaffold`, `--update`, `--tools-install`, `--mcp-add`/`--mcp-remove`,
   `--provider-add`/`--provider-remove`, `--plugin-on`/`--plugin-off`,
   `--model-pin-set`/`--model-pin-clear`, `--routing-migrate`, `--prune-dead`— y las que
   tocan **credenciales o red** —`--provider-verify`, `--check-update`,
   `--quota-failover-e2e`, `--fresh-probes`— se corren en un `HOME`/proyecto **temporal
   desechable**, con `--dry-run` donde exista. Nunca contra el árbol real ni contra
   credenciales vivas. **Ningún valor de secreto se registra** en la evidencia: solo su
   presencia o ausencia. Una flag que no se pueda caracterizar sin efecto lateral **se
   declara así** en la evidencia; declararla es cumplir el criterio, correrla a ciegas no.

**Fixture que engañaría al criterio:** comparar solo la primera línea de `stdout` de las
invocaciones felices. Pasaría en verde con un `stderr` nuevo, con un exit code cambiado de
2 a 1, y con cualquier regresión en el camino de error — que es justamente donde un refactor
de módulos rompe cosas.

### AC-B.3 — Comportamiento preservado, no "mejorado"

**Cuando** el implementer encuentra un bug real mientras mueve código,
**entonces** lo registra como finding y se repara **aparte**; no viaja en el diff del
refactor. Nada de renombrar salidas, reordenar campos ni cambiar un default.

### AC-B.4 — El residuo queda enumerado, no arrastrado

**Dado** el residuo enumerable de hoy — routing: `cmd_route_explain` (`:550`),
`cmd_routing_report` (`:575`), `cmd_route_doctor` (`:586`), `cmd_route_decide` (`:671`),
`cmd_route_dispatched` (`:794`), `cmd_route_quota_exhausted` (`:800`),
`cmd_route_terminal` (`:833`), `cmd_routing_open_runs` (`:866`),
`cmd_routing_recent_writers` (`:874`), `cmd_routing_decisions` (`:882`),
`cmd_routing_migrate` (`:3619`); vault: `cmd_vault_init` (`:2869`), `find_vault`
(`:2900`), `vault_link_private` (`:2989`), `cmd_vault_doctor` (`:3146`+), `vault_menu` —
**cuando** el paquete cierra,
**entonces** cada uno de esos comandos **se movió**, o **quedó con una razón de una
línea** que nombra el mecanismo concreto que lo ancla: `PROJECT_KEY`,
`PROJECT_ROOT`/`ROOT`, `ROUTING_WARNINGS`, `app_config`/`write_app_config`, o el helper
`_import()` de `tests/test_harness.py:663-684` (que carga `set_agents_app.py` con
`spec_from_file_location` sin registrarlo en `sys.modules`, de modo que un import
inverso arranca un segundo exec top-level del módulo — la razón ya escrita en
`ai/scripts/routing_cli.py:1-31` y `ai/scripts/vault_ops.py:1-23`).
**Residuo sin razón = paquete rojo.**

### AC-B.5 — La duplicación no crece

**Dado** que las duplicaciones existentes ya tienen su razón escrita
(`atomic_write`/`_BACKED_UP` en `vault_ops.py:1-23`;
`_MAX_FEATURE_BYTES`/`_MAX_FEATURE_FILES` en `routing_cli.py:1-31`),
**cuando** aparece una duplicación nueva,
**entonces** lleva una razón medida de la misma clase, o no entra.

### AC-B.6 — Dos cierres legales, ninguno gratis (y el (b) no es reformatear docstrings)

> Corrige **F-035-006**. Como estaba escrito, el cierre (b) se podía satisfacer copiando lo
> que `routing_cli.py:1-31` y `vault_ops.py:1-23` **ya dicen**. Eso es documentación
> preexistente, no trabajo del paquete.

**Entonces** el paquete pasa si (a) el residuo se movió, o (b) se probó anclado y quedó
enumerado.

**El cierre (b) exige una matriz nueva**, una fila por comando residual, con cuatro
columnas:

| comando | dependencia concreta que lo ancla | experimento o lectura hecha | resultado |
|---|---|---|---|
| p.ej. `cmd_route_decide` (`:671`) | el global mutable que corresponda (`PROJECT_KEY`, `PROJECT_ROOT`/`ROOT`, `ROUTING_WARNINGS`, `app_config`/`write_app_config`) o el `_import()` de `tests/test_harness.py:663-684` | **qué se intentó y qué falló**, o el `rg`/lectura que prueba el acoplamiento, con `file:line` | movido / anclado |

**La tercera columna es la que decide.** "Está anclado porque el docstring de
`routing_cli.py:1-31` ya lo dice" **no** cierra: es cita de documentación que existía antes
del paquete. Lo que cierra es el intento de mover con su falla concreta, o la lectura del
acoplamiento con `file:line` propio. Los docstrings existentes son el **formato** de la
matriz, no su contenido.

**No** pasa una mudanza parcial que agregue un tercer docstring de "documented deviation"
sin bajar líneas ni producir la matriz.
El `wc -l` de `set_agents_app.py` se **reporta** como evidencia (4399 antes, medido
2026-08-20); no es una meta que se pueda cumplir borrando comentarios o código muerto
disfrazado de extracción.

### AC-B.7 — Contratos intactos

`ai/scripts/routing_core/` (`__init__`, `catalog`, `domain`, `gates`, `inference`,
`service`, `store`, `usage`) y la semántica de vault de ADR-0012/ADR-0056 no se
rediseñan. Se mueven llamadores, no contratos.

### AC-B.8 — La mordida de PKG-B es asimétrica (y hay que decirlo)

**Ningún** test existente debe cambiar de color. En un refactor
comportamiento-preservante, un test que se pone rojo es **el defecto**, no la señal de
éxito. La red es: la caracterización de AC-B.1, `tests/test_routing.py`,
`tests/test_harness.py` y `./build.sh --check`. Nombrar acá un test "que debe fallar"
sería nombrar un requisito de romper algo.

---

## PKG-C — TIPS al día

### AC-C.1 — TIPS deja de afirmar un control plane único

**Dado** `TIPS-USO.md:7-14`: "**OpenCode is the orchestration control plane**" … "The
other two harnesses are single-task lanes, not orchestrators",
**cuando** Federico lee TIPS después de esta entrega,
**entonces** lee lo medido: Claude Code, Cursor y OpenCode pueden orquestar (roster
completo instalado; Cursor es anfitrión desde 032; `docs/COMO-FUNCIONA.md:219-230` ya lo
documenta), y lo que **no** cambia por runtime es la ceremonia — sin `init` con señal de
riesgo no hay panel (ADR-0064),
**y** la advertencia concreta sobre Codex (`:12-14`: `spawn_agent` hereda el modelo de
sesión y puede forkear el transcript entero) **sigue estando**: es una medición, no
doctrina vieja.

### AC-C.2 — Los inventarios dejan de omitir árboles que el repo genera

**Dado** `ls Global/` → `claude-code`, `codex`, `cursor`, `opencode`, `pi` (más
`_canonical` y `_shared`),
**cuando** Federico lee `TIPS-USO.md:3` ("versioned source for OpenCode, Claude Code,
and Codex"), `:45` (`Global/{opencode,claude-code,codex}`) y `:127-129` ("Native
agents", tres bullets),
**entonces** ninguna de las tres omite un árbol que el repo genera — Cursor aparece con
su ruta nativa (`~/.cursor/agents/*.md`, 032/ADR-0063) y `pi` deja de ser invisible.

### AC-C.3 — La cobertura de consumo dice lo que mide

**Dado** `TIPS-USO.md:133-134`: "the three harnesses' own session stores … plus a fourth
`pi` lane",
**y** que `ai/scripts/cost-report.py:20-23` y `:836-843` cubren Cursor explícitamente
("this harness's own record of what it dispatched, every runtime including Cursor";
vacío en la lane de routing porque los subagentes nativos de Cursor no pasan por los
CLIs),
**cuando** Federico lee esa sección,
**entonces** la redacción refleja la cobertura medida y no promete más.

### AC-C.4 — El repo no se contradice al revés

**Dado** que `docs/COMO-FUNCIONA.md:227-230` hoy dice "`TIPS-USO.md` todavía dice
'OpenCode es el control plane'" y que `:439-448` (§11) lista las tres piezas como
diferidas,
**cuando** AC-C.1 corrige TIPS **en la misma entrega**,
**entonces** `:227-230` deja de afirmarlo, `:439-448` apunta a este spec en vez de
presentarlas como pendientes sin dueño, y la celda `:221` ("control plane histórico en
`TIPS-USO.md`") se revisa junto con ellas.
Mover una sola superficie deja el repo contradiciéndose en la dirección opuesta.

### AC-C.5 — No es una reescritura de gusto

**Fuera** de este paquete, explícitamente: "Required lifecycle" (`TIPS-USO.md:117-121`),
la política de MCP (`:150-156`, incluida la mención de Engram) y el bloque de
bootstrap/instalación (`:25-32`). Se corrigen afirmaciones **medidamente falsas**, no
preferencias de redacción.

### AC-C.6 — La línea de índice se mira

**Dado** `README.md:305` — "TIPS-USO.md — flujo de trabajo del harness (control plane,
lanes, drift)",
**cuando** AC-C.1 cierra,
**entonces** esa línea se ajustó si quedó falsa, o se dejó porque sigue siendo cierta
como índice. Lo que no se acepta es no haberla mirado.

---

## Trazabilidad

| escenario | hallazgo que cierra | verificación de paquete | regresión / runtime |
|---|---|---|---|
| A-1, A-2 | F-035-004 (precedencia sobre A-4) | review del diff del CLI de estado contra este archivo | tests nuevos + los **7** sitios reescritos de la tabla de mordida |
| A-3 | F-035-005 | review: el predicado maneja las tres formas de ausencia | los **tres** fixtures obligatorios (clave ausente / `null` / `complexity` ausente) |
| A-4 | F-035-002, F-035-004 | review: el alcance es el verbo, y la excepción de verdicts está condicionada al panel SINGLE | tests del rechazo + test de que `repair_required` en `small`+`low` sigue pasando |
| A-5 | F-035-003 | review lee el comentario **y** la reachability por `skip-delta` | grep del texto retirado + los **dos** escenarios coherentes (rechazo / advisor) |
| A-6 | — | review contra los 31 state files / 76 paquetes medidos | suite completa verde sin tocar `ai/state/` |
| A-7 | — | `./build.sh --check` | `tests/test_harness.py:8995` |
| A-8 | — | review: `MODE_BUDGETS` sin diff | test existente de presupuesto de spawns |
| A-9 | F-035-001 | review: ADR `Accepted` + `Global/_canonical/agents/orchestrator.md` en el mismo diff, `generate.py` sin tocar | `rg` sobre los cuatro árboles generados + `./build.sh --check` |
| B-1, B-2 | F-035-007 | review contra la caracterización previa de los tres canales y la lista de normalizadores fechada antes | comparación `stdout`+`stderr`+exit del set representativo; mutantes/credenciales en `HOME` temporal |
| B-3..B-5, B-7, B-8 | — | review del diff | `tests/test_routing.py` + `tests/test_harness.py` + `build.sh --check`, todos **sin** cambiar de color |
| B-6 | F-035-006 | review de la **matriz** comando→dependencia→experimento→resultado; una fila sin tercera columna no cierra | lectura: cero comandos residuales huérfanos |
| C-1..C-6 | — | review de las dos superficies en el mismo diff | sin runtime; la verificación es lectura contra las mediciones citadas |
