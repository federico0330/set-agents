# ADR-0065 — Enmienda del contrato público de `record-review`: membresía del panel y finding bloqueante

- Estado: **Accepted** (2026-08-20). Feature `035-panel-honesto-consola-y-tips`, PKG-A.
  Aprobado con el Feature Contract (hash
  `296e051fccfd0cea2f222cc7061987f6b66507d9ed2b10539d7e58ea3169331c`), AC-A.9.
- **Enmienda de contrato público, no bugfix.** La firma de `record-review` no cambia
  (mismo comando, mismos tres verdicts `pass|repair_required|blocked`), pero invocaciones
  que hoy funcionan dejan de funcionar. Por eso viaja con la doctrina en el mismo paquete.
- No enmienda ni supersede ningún ADR previo. `MODE_BUDGETS` (ADR-0061),
  `RISK_SIGNAL_REQUIRED` (ADR-0064), `NON_ACCEPTING_ACTORS`/`REFUTING_ACTORS` y ADR-0023
  quedan intactos.
- **Ejes store / API Gateway / deploy: n/a.** Ya declarado y registrado como `n/a` en el
  `axes_log` de la feature (`spec.md:13-15`). Esto es una enmienda del contrato de un CLI
  de estado local: no introduce persistencia nueva, ni superficie de red, ni cambio de
  despliegue. No se redacta ADR de esos ejes ni se difiere ninguno con umbral: no existen
  en esta feature.

## Contexto

`start-review-panel` **enforcea** la membresía obligatoria del panel: resuelve
`required_reviewers` (`feature-state.py:569`, vía `persist_review_requirements`,
`model.py:578-583`), rechaza escritores (`:570-575`), rechaza un panel al que le falta un
rol requerido (`:576-583`) y rechaza un panel **inflado** cuando el requerido es uno solo
(`:584-587`).

`cmd_record_review` (`cli_review.py:21-63`) no consulta nada de eso. Acepta un `pass` de
un único actor y pone la feature en `PACKAGE_TESTING` (`:54-56`). Tampoco consulta
`has_open_findings`, a diferencia de `finalize-review-panel` (`cli_review.py:158-160`) y de
`record-delta-review` (`cli_repair.py:335-336`). Resultado observable: un paquete
`medium`/`high` llega a `DONE` con `security-auditor` nunca instanciado, y un `pass` salta
por encima de un finding `high` abierto.

La asimetría es exacta y es lo que vuelve esto un defecto de contrato y no una preferencia:
**hoy el CLI rechaza un panel inflado para `small`+`low` y acepta un review encogido para
`medium`/`high`.**

Y la doctrina respalda el defecto (F-035-001). `Global/_canonical/agents/orchestrator.md:103`
lista `record-review` entre los verbos del ciclo normal, y `:105-108` presenta el panel como
lo que se usa "when multiple specialist reviewers **are useful**" — opcional, a criterio del
orquestador. Cerrar el verbo sin enmendar esa frase deja al harness rechazando lo que su
propia doctrina recomienda, que es peor que el gap original.

El universo real está medido (F-035-005, `spec.md:153`): sobre **76 paquetes** en 31
archivos de `ai/state/features/`, `required_reviewers` está **ausente en 71**, poblado en 5,
`null` explícito en **0**; `complexity` ausente en 4.

## Decisión

1. **La firma no cambia. Se agregan dos rechazos nombrados.** `record-review` conserva su
   nombre, sus argumentos y sus tres verdicts. Lo que cambia es **cuándo acepta**, y eso es
   contrato: se declara como tal, no como detalle de implementación.

2. **`REVIEW_PANEL_REQUIRED` — membresía, alcanza a los tres verdicts (DEC-DOOR).** Cuando
   el panel resuelto del paquete es `FULL_REVIEW_PANEL` (`model.py:96`), `record-review` se
   **rechaza entero**: `pass`, `repair_required` y `blocked` por igual. No se endurece el
   verbo para que "cubra" el panel con varias llamadas, porque cada llamada gasta un
   `attempts.deep_review_cycles` (`cli_review.py:46`) contra un techo de 2
   (`model.py:123-127`): dos roles en dos llamadas gastarían el presupuesto entero de review
   de un paquete. El camino correcto ya existe y el mensaje lo nombra
   (`start-review-panel` → `record-subreview` × rol → `finalize-review-panel`).

3. **`BLOCKING_FINDING_OPEN` — solo `pass`, mismo predicado y mismas severidades.** Con
   panel resuelto `SINGLE_REVIEW_PANEL`, un `record-review --verdict pass` se rechaza si
   `has_open_findings(package, {"critical", "high", "medium"})` — literalmente el mismo
   predicado y el mismo conjunto que `finalize-review-panel` usa en `cli_review.py:159-160`.
   No se inventa un predicado nuevo ni un conjunto de severidades nuevo. El conjunto de
   findings evaluado incluye los que llegan por `--finding` en **esa misma llamada**: los dos
   sitios medidos del golden suite (`tests/test_harness.py:9032`, `:11048`) son exactamente
   `record-review pass --finding <high>`, y un chequeo que corriera antes del merge no los
   vería.

4. **Precedencia escrita: membresía primero.** Con panel FULL cae el verbo entero
   (decisión 2) y nunca se llega a evaluar findings. Decir "`repair_required` y `blocked` no
   cambian" a secas sería falso: solo es cierto en panel SINGLE. Tres sitios del golden
   suite lo prueban (`tests/test_harness.py:12399`, `:12451`, `:13006`: paquete `medium`,
   verdict `repair_required`).

5. **`small`+`low` no cambia.** `record-review` sigue siendo la puerta legítima y barata del
   paquete de un solo reviewer (`SINGLE_REVIEW_PANEL`, `model.py:95`). Un criterio que rompa
   este caso rompió el harness en vez de arreglarlo.

6. **Rechazar no cobra un ciclo.** Los dos rechazos son `raise StateError`, **nunca**
   `block_with_reason`. Consecuencia mecánica, no promesa: `mutate` (`feature-state.py:156-179`)
   solo escribe cuando el `updater` retorna truthy y no levanta; una excepción descarta la
   mutación entera, incluido el `attempts["deep_review_cycles"] += 1` de `cli_review.py:46`.
   `block_with_reason`, en cambio, **retorna** y persiste un `BLOCKED`: usar un rechazo de
   membresía por esa vía convertiría un verbo equivocado en una feature bloqueada. Por eso el
   guarda de membresía se instala **antes** del chequeo de presupuesto de `:31-34`.

7. **Ausencia no significa "sin requisito" (DEC-ABSENCE).** El panel se **resuelve**, no se
   lee. `required_reviewers` ausente (71/76), `null` explícito (0/76 hoy, pero es lo que
   produce un editor a mano) o presente-pero-inservible se re-derivan de `complexity` +
   riesgo resuelto (`resolve_package_risk`, `model.py:548-562` → `required_reviewers_for`,
   `model.py:565-575`). El fail-safe de `complexity` ausente/`None` a `medium` — o sea, a
   panel FULL — **se conserva** (`model.py:571`), y tiene 4 clientes medidos, no cero.

8. **El rechazo vive en el verbo que muta, y en ningún otro lado (DEC-LEGACY).** No se
   agrega el chequeo a `package_accept_ready` (`model.py:800-827`) ni a ningún camino de
   validación de lectura. Un paquete `accepted`/`superseded` y una feature `DONE` no se
   re-juzgan: las 27 features en `DONE` siguen validando igual. El invariante se sostiene
   igual hacia adelante porque `reviews[]` tiene exactamente dos escritores
   (`cli_review.py:45` y `:147`) y ambos quedan conscientes de la membresía.

9. **La doctrina se mueve con el código, en el mismo paquete.**
   `Global/_canonical/agents/orchestrator.md:102-108` deja de presentar `record-review` como
   el verbo default del ciclo y el panel como opcional. El panel pasa a ser **obligatorio**
   cuando el panel resuelto es FULL, y `record-review` queda descrito como la puerta de
   `small`+`low`. La propagación a los cinco árboles generados la hace el `generate.py` que
   ya existe; `generate.py` **no** se modifica (no-goal 13) y las copias **no** se editan a
   mano.

10. **Este slice cierra `record-review` y nada más.** La auditoría de puertas
    (`docs/specs/035-panel-honesto-consola-y-tips/evidence/PKG-A-doors.md`) enumera seis
    puertas reales hacia `PACKAGE_TESTING`. `record-repair --skip-delta`
    (`cli_repair.py:246-253`, `:280-282`) queda **fuera por decisión registrada**
    (`docs/notas/decisiones/2026-08-20 035-skip-delta-fuera-del-slice.md`). Por lo tanto
    `PACKAGE_TESTING` con un finding bloqueante abierto **sigue siendo alcanzable**, la rama
    advisora de `transitions.py:96-109` se conserva, y su comentario nombra esa puerta. Este
    ADR no promete lo contrario.

## Opciones rechazadas

- **Endurecer `record-review` para que acepte un panel multi-rol** (varias llamadas, una por
  rol). Gasta el presupuesto de deep review completo (decisión 2) y duplica, peor, el
  mecanismo que `review_panels[]` ya implementa con idempotencia por rol
  (`cli_review.py:105-106`). Sería el tercer camino de review que el spec declara no-goal 11.
- **Poner el chequeo también en `package_accept_ready`** ("un invariante se enforcea en cada
  transición", el patrón del docstring de `require_verified`, `cli_review.py:278-284`). Es el
  patrón correcto para findings, y el equivocado acá: `package_accept_ready` corre sobre
  registros ya escritos, así que instalarlo ahí **re-juzga** paquetes cuyo review se registró
  legalmente antes de este cambio, que es exactamente lo que DEC-LEGACY prohíbe (AC-A.6).
  Los findings no tienen ese problema porque un finding abierto es un hecho presente; una
  membresía de panel es un hecho histórico.
- **Endurecer `check_transition` para `PACKAGE_TESTING`** (`transitions.py:33-38`) con
  membresía. No hace falta y sería un segundo guarda sobre el mismo agujero: esa puerta ya
  exige `reviews[]` con verdict `pass`/`repair_required` (`:35-36`), y `reviews[]` solo lo
  escriben los dos verbos que este ADR deja conscientes de la membresía. Duplicar el chequeo
  ahí lo pondría, además, en un camino que sí se recorre sobre estado viejo.
- **Un token único (`REVIEW_REJECTED`) con subcausas en el texto.** Dos causas con dos
  remedios distintos (abrir un panel vs. reparar/refutar un finding) merecen dos tokens
  grepeables; es la misma razón por la que ADR-0064 separó `RISK_SIGNAL_REQUIRED` de
  `RISK_SIGNAL_INVALID`.
- **Tratar `required_reviewers is None` como el caso de ausencia.** Medido: no toca **ni un**
  paquete real (0 de 76). La forma real es la clave **ausente**.
- **Bajar el `--complexity` de los fixtures de `medium` a `small`** para que el golden suite
  pase. Convierte un test del camino FULL en uno del camino SINGLE: pérdida de cobertura
  disfrazada de reparación (no-goal 10, F-035-004).
- **Cerrar `record-repair --skip-delta` de paso.** Es la otra puerta viva y está medida, pero
  cerrarla es un slice propio con su propia mordida en el golden suite.
- **Subir `MODE_BUDGETS.scoped.max_spawns_per_package`** para pagar el `security-auditor` que
  ahora es obligatorio. El panel FULL se paga con el techo que existe; chocarlo es
  `HUMAN_DECISION_REQUIRED` (AC-A.8), no un presupuesto más grande.

## Consecuencias

- **Invocaciones que hoy funcionan dejan de funcionar.** Un `record-review` sobre un paquete
  `medium`/`high` falla con exit 2 y `{"ok": false, "error": "REVIEW_PANEL_REQUIRED: ..."}`.
  Es el punto del ADR, y es la razón de que exista en vez de ser una nota de implementación.
- **Costo de cuota real.** Un panel FULL obligatorio instancia `security-auditor` donde antes
  no lo hacía, dentro del mismo techo de despachos.
- **Auditoría:** el registro pasa a dejar leer *qué panel se exigía* y *quién lo cumplió*,
  sobre paquetes donde el campo no está.
- **Tres paquetes vivos caen bajo la regla nueva** y ninguno se rompe: 032 `C1`
  (`medium`, 0 reviews, feature en `PACKAGE_GATES`), 011 `P1-quota-failover` (`high`, 0
  reviews, `BLOCKED`), 002 `P1-routing-core` (`high`, `repair_required`, `BLOCKED`). Los tres
  todavía no entraron a review; el camino correcto (`start-review-panel`) ya existe.
- **Siete sitios del golden suite se reescriben** (5 de membresía, 2 de finding abierto),
  ninguno se afloja, saltea ni borra.
- **La deuda hermana queda parcialmente abierta y dicha:** ver decisión 10.

## Evidencia

- `ai/scripts/feature_state_lib/cli_review.py:21-63` (el defecto), `:45`, `:46`, `:54-56`,
  `:136-138`, `:147`, `:158-161`, `:278-284`.
- `ai/scripts/feature_state_lib/cli_repair.py:246-253`, `:280-282`, `:335-338`.
- `ai/scripts/feature_state_lib/model.py:90`, `:95-96`, `:123-127`, `:548-562`, `:565-575`,
  `:578-583`, `:751-757`, `:800-827`.
- `ai/scripts/feature_state_lib/transitions.py:33-38`, `:96-109`.
- `ai/scripts/feature_state_lib/cli_lifecycle.py:272-273`, `:334`, `:375-377`.
- `ai/scripts/feature-state.py:156-179` (`mutate` descarta al levantar), `:569-587`,
  `:862-868`, `:1349-1353` (el envelope `{"ok": false, "error": ...}` + exit 2).
- `Global/_canonical/agents/orchestrator.md:102-108`.
- `tests/test_harness.py:32` (el suite corre el binario de `PROYECTO/`), `:8580`, `:9024-9039`,
  `:10170`, `:11044-11054`, `:12399`, `:12451`, `:13006`.
- `docs/specs/035-panel-honesto-consola-y-tips/spec.md` (DEC-DOOR `:152`, DEC-ABSENCE `:153`,
  DEC-LEGACY `:154`, DEC-SIBLING-IN `:155`, DEC-SKIP-DELTA-OUT `:156`, DEC-TOKENS `:157`),
  `acceptance.md` § PKG-A, `design.md`.
- `docs/specs/035-panel-honesto-consola-y-tips/evidence/PKG-A-doors.md` (auditoría T-001).
- `docs/notas/decisiones/2026-08-20 035-skip-delta-fuera-del-slice.md`.
