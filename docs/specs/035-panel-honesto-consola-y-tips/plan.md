# 035 — Plan

> Secuencia, dependencias, riesgos y qué obliga a parar y preguntar. Mediciones del
> 2026-08-20; donde no medí, digo **sin verificar**.
>
> **Revisión post-challenge (2026-08-20).** Incorpora `F-035-001..007`. DEC-DOOR y el
> recorte de `record-repair --skip-delta` no se relitigan.

---

## Secuencia

| # | paquete candidato | por qué en este orden |
|---|---|---|
| 1 | **PKG-A** — panel honesto (CLI de estado) | Es el único de los tres que cambia lo que el harness **permite**. Los otros dos cambian cómo se lee el árbol. Si solo entrara uno, entra A. |
| 2 | **PKG-B** — extraer routing/vault de la consola | El más caro y el más incierto (el techo real lo decide T-102). Va después de A para que un `HUMAN_DECISION_REQUIRED` acá no bloquee el valor de A. |
| 3 | **PKG-C** — TIPS + puntero desde COMO-FUNCIONA | Barato, sin código, sin dependencia. Puede ir en paralelo con B; se pone último solo porque nada depende de él. |

PKG-A no depende de B ni de C. B y C son independientes entre sí y de A — las
`owned_paths` son disjuntas (tabla en `tasks.md`). El planner puede paralelizar B y C si
el techo de despachos lo permite: `MODE_BUDGETS.scoped.max_spawns_per_package == 8`
(`ai/scripts/feature_state_lib/model.py:125`) y **no se sube**.

---

## Dependencias

**Internas**
- T-001 (auditar las puertas hacia `PACKAGE_TESTING`) antes de T-003/T-004, y **su
  entregable es la tabla, no el cierre de todas las puertas**. Instalar el guarda solo en
  la puerta que motivó el AC es el defecto que el docstring de `require_verified`
  (`ai/scripts/feature_state_lib/cli_review.py:278-284`) ya documenta; la mitigación en este
  slice es que el comentario de `transitions.py` diga la verdad sobre cuáles quedan
  abiertas, no cerrarlas todas fuera de alcance.
- T-002 (predicado tolerante a la ausencia) antes de T-003. Sin eso, el guarda pasa en
  fixture y falla contra los datos reales. **Medición corregida (F-035-005):** de **76
  paquetes** en 31 archivos de `ai/state/features/`, `required_reviewers` está **ausente en
  71**, poblado en 5 y en `null` explícito en **0**; `complexity` falta en 4. La forma real
  es la **clave ausente**, no `null` — un predicado escrito contra `is None` no toca ni un
  paquete real.
- **T-010 (ADR + doctrina) dentro de PKG-A, antes de T-008** (F-035-001). El rechazo nuevo
  es contrato público y hoy `Global/_canonical/agents/orchestrator.md:103-108` recomienda
  la puerta que el CLI va a rechazar. T-008 es el que regenera los árboles donde vive la
  copia, así que el orden importa.
- T-101 (caracterización de los **tres** canales) es un **gate duro** de PKG-B: bloquea
  T-103. Incluye la lista de normalizadores, escrita antes de la primera comparación.
- T-102 (techo real de la extracción) decide cuál de los dos cierres legales aplica
  (DEC-EXTRACT-TWO-OUTCOMES).
- T-201 y T-203 van en el **mismo** paquete. Corregir `TIPS-USO.md` sin tocar
  `docs/COMO-FUNCIONA.md:227-230` produce la contradicción inversa.

**Externas / de infraestructura**
- **Paridad de copias.** El golden suite corre el CLI **del template**:
  `FEATURE_STATE = ROOT / "PROYECTO/ai/scripts/feature-state.py"`
  (`tests/test_harness.py:32`). `build.sh:69-79` gatea `ai/scripts` ↔
  `PROYECTO/ai/scripts` (`SELF_SCAFFOLD_DRIFT`) y `ai/scripts/generate.py:667` regenera
  `Global/*/hooks/feature_state_lib` por `copytree` en cuatro árboles (`claude-code`,
  `codex`, `cursor`, `opencode`). Un cambio de PKG-A en una sola copia es invisible para
  los tests.
- **`set_agents_app.py` no vive en `PROYECTO/`** (verificado con `rg`), así que PKG-B no
  tiene obligación de espejo. Son dos universos de paridad distintos y conviene no
  confundirlos.
- **Cursor como anfitrión.** Sin `--route-decide`, sin lanes de routing, sin Engram. La
  independencia writer/reviewer se sostiene con pines de familia distinta (034/ADR-0063)
  o se registra como degradación ruidosa en la evidencia del review.

---

## Presupuestos y ceremonia

- `MODE_BUDGETS` intacto (`model.py:123-128`). PKG-A **agrega demanda** al techo: un
  paquete `medium`/`high` que antes cerraba con un `record-review` ahora instancia
  `package-reviewer` **y** `security-auditor`. Ese costo se paga con los 8 despachos que
  ya hay; chocar el techo es `HUMAN_DECISION_REQUIRED`, no un techo más grande.
- Ironía útil y deliberada: **esta misma feature** es el primer cliente de PKG-A. Sus
  propios paquetes van a necesitar el panel completo salvo que el planner los declare
  `small`+`low` con honestidad.
- `max_deep_review_cycles = 2` sigue siendo el techo de review. Es justamente la razón
  por la que `record-review` se **rechaza** en vez de endurecerse (DEC-DOOR): cada
  llamada incrementa `attempts.deep_review_cycles` (`cli_review.py:46`), y cubrir dos
  roles con dos llamadas gastaría el presupuesto entero en un solo panel.

---

## Riesgos, en orden de probabilidad

| # | riesgo | señal temprana | mitigación |
|---|---|---|---|
| 1 | **El barrido del golden suite es más grande de lo enumerado.** Bajó de riesgo con F-035-004: las invocaciones reales del CLI son **20** (no 25 — 5 de las citadas son entradas de `history`/`event`), y están clasificadas una por una: **7 caen** (5 por membresía en paquetes `medium`, 2 por finding abierto), 13 no | la primera corrida completa de la suite después de T-003/T-004 | La enumeración está en `acceptance.md`; T-006 pasó de "descubrir" a **confirmar**. Lo que puede escapar es un fixture que mute `complexity` con `update-package` después de crear el paquete — la clasificación es estática. Checkpoint intacto: si el total se vuelve un paquete propio, **para y lo dice** |
| 2 | **Hay una puerta hacia `PACKAGE_TESTING` no prevista** (una `transition` directa) | T-001 | T-001 es la primera tarea y tiene checkpoint de parada. Ya está medido que las puertas por verbo son cuatro: `finalize-review-panel` chequea, `record-delta-review` chequea, `record-review` no (se cierra), `record-repair --skip-delta` no (**fuera de alcance**, no-goal 12). Un guarda parcial es peor que ninguno **cuando se presenta como completo**; acá el parcial se declara parcial en el comentario de `transitions.py` (AC-A.5) |
| 3 | **El guarda pasa en fixture y falla en producción** por leer `required_reviewers` a secas | un test que solo usa `create-package --complexity medium`, **o** un test que solo cubre `null` | AC-A.3 corregido (F-035-005) nombra los **dos** fixtures que engañan y exige **tres** casos: clave ausente (71/76), `null` explícito (0/76 pero lo produce una edición a mano) y `complexity` ausente (4/76, fail-safe FULL) |
| 3b | **El código cierra la puerta y la doctrina sigue recomendándola** | `rg` sobre `Global/*/agents/orchestrator.md` después de T-003 | T-010 / AC-A.9 (F-035-001): ADR `Accepted` + canónico enmendado + regeneración, en el mismo paquete. `generate.py` no se toca |
| 3c | **El comentario de `transitions.py` queda peor que antes**: declara inalcanzable un estado que `record-repair --skip-delta` sigue alcanzando, o la reescritura del test se vuelve incoherente (usa una late review y a la vez afirma que ninguna ocurrió) | T-001 / T-007: el comentario nuevo no cita un `file:line` real, o el test reescrito menciona late review en el escenario del rechazo | AC-A.5 corregido (**F-035-002**, **F-035-003**): la rama se conserva y su comentario nombra `skip-delta` (`cli_repair.py:246-253`, `:280-282`) citando la decisión que lo difiere; el test se parte en **dos** escenarios coherentes |
| 4 | **PKG-B se vuelve un refactor sin techo** — el escenario clásico y el que ya se difirió una vez | un tercer docstring de "documented deviation" apareciendo sin que baje el conteo | DEC-EXTRACT-TWO-OUTCOMES: dos cierres legales, uno de ellos es "probado anclado y enumerado". T-102 decide temprano cuál aplica |
| 4b | **PKG-B cierra por el camino (b) reciclando docstrings que ya existen** | una "matriz" cuya justificación son citas de `routing_cli.py:1-31` y `vault_ops.py:1-23` | AC-B.6 corregido (F-035-006): la matriz exige la columna **experimento o lectura hecha** con `file:line` propio. La documentación preexistente es el formato, no la evidencia |
| 5 | **PKG-B arregla un bug de paso** y contamina un diff que debía ser comportamiento-preservante | un test que cambia de color | AC-B.3 + AC-B.8: un test rojo en PKG-B **es el defecto**, no la señal de éxito |
| 5b | **PKG-B cambia `stderr` o el exit code sin que nadie lo note**, porque se comparó solo el token de primera línea | ninguna — es exactamente el riesgo de una caracterización que mira poco | AC-B.2 corregido (F-035-007): se comparan `stdout`+`stderr`+**exit** sobre un set representativo (válida / argumento faltante / valor inválido / `--help` / sin args), normalizando solo lo declarado de antemano. El camino de error es donde un refactor de módulos rompe cosas |
| 6 | **PKG-C corrige TIPS y deja `COMO-FUNCIONA` mintiendo al revés** | el diff toca una sola de las dos superficies | DEC-TIPS-POINTER + AC-C.4: mismo paquete |
| 7 | **PKG-A traba los tres paquetes vivos** — 032 `C1` (`medium`, 0 reviews), 011 `P1-quota-failover` (`high`, 0 reviews), 002 `P1-routing-core` (`high`, `repair_required`) | los tres están en `PACKAGE_GATES`/`BLOCKED` | DEC-LEGACY: ninguno entró a review todavía; su camino correcto es `start-review-panel`, que ya existe. Ninguno se "migra" a mano en el JSON |
| 8 | **Un gate de repo re-valida los 31 state files (76 paquetes) en lote** y las 27 features `DONE` se ponen rojas | `verify.sh` después de T-003 | AC-A.6 + T-009. Medido que `check-feature-state.py` no lo hace (`verify.sh:65`); el resto **sin verificar** y architecture lo confirma antes de elegir dónde vive el chequeo. Los **4** paquetes sin `complexity` (que caerían al fail-safe FULL) están todos en features `accepted`/`DONE` — DEC-LEGACY los cubre |
| 9 | **El cambio vive en una sola copia del CLI** y ningún test lo ve | `./build.sh --check` | AC-A.7 / T-008. Es la trampa más silenciosa de este repo |

---

## Qué dispara una decisión humana

Se para con `HUMAN_DECISION_REQUIRED` o `BLOCKED`, citando el bloqueo exacto, cuando:

1. **T-001 encuentra que cerrar todas las puertas cambia el comportamiento de un verbo
   que este spec no nombró.** Eso es alcance nuevo, no una consecuencia.
2. **El barrido de T-006 excede lo que cabe en PKG-A** (riesgo 1). El pedido de Federico
   fue "las tres"; convertir A en dos paquetes es una decisión suya, no del implementer.
3. **T-102 concluye que la extracción real exige tocar el `_import()` de
   `tests/test_harness.py:663-684`.** Eso es un cambio al contrato golden y necesita ACs
   propios. Se registra y PKG-B cierra por el camino (b).
4. **Un paquete choca `max_spawns_per_package` por el panel FULL nuevo** (AC-A.8). Nunca
   se sube el techo para desatascar.
5. **Aparece un eje de arquitectura que este spec declaró n/a** (store / API Gateway /
   deploy). No debería: es CLI de estado, movimiento de módulo y documentación. Si
   aparece, es `architect` quien decide el ADR — no se improvisa. **Nota (F-035-001):** el
   ADR de enmienda del contrato de `record-review` **no** dispara pregunta: ya está en
   alcance (AC-A.9 / T-010) y su redacción es de `architect`.
6. **Un test de regresión tendría que aflojarse** para que algo cierre. Los siete sitios
   afectados se reescriben con su razón nueva; cualquier otra cosa para. En particular,
   bajar un `--complexity medium` a `small` **no** es una reescritura y no se autoriza sin
   decisión humana explícita.
7. **T-006 descubre un sitio afectado que no está en los siete enumerados.** No para el
   trabajo, pero se **registra**: significa que la enumeración del contrato estaba
   incompleta y la mordida se recalcula antes de reescribir.

**No** dispara pregunta: un gate rojo de rutina, un rerun, una reparación exigida por el
review, ni seguir con trabajo ya aprobado. El pedido del 2026-08-20 ("Si, hagamos esas
3") es la decisión de alcance y ya está tomada.

---

## Definición de terminado (feature)

1. Los tres paquetes candidatos aceptados, o los que el planner haya agrupado en su
   lugar cubriendo los mismos ACs.
2. Los **siete** sitios de mordida **vistos rojos y después verdes**, con las corridas en
   la evidencia. Un test que nunca se vio rojo no prueba nada.
3. `./build.sh --check` y `ai/scripts/verify.sh` verdes, con paridad de copias **y** los
   cuatro árboles regenerados (incluye `orchestrator.md`).
4. La caracterización de PKG-B fechada **antes** del primer movimiento de código, con los
   tres canales y la lista de normalizadores escrita antes de comparar.
5. La matriz de residuo de PKG-B con su columna de experimento/lectura completa — ninguna
   fila justificada solo con documentación preexistente.
6. `TIPS-USO.md` y `docs/COMO-FUNCIONA.md` sin afirmaciones contradictorias entre sí.
7. `docs/specs/README.md` con la fila de 035 en el estado que corresponda.
8. **Un ADR nuevo, `Accepted`** (F-035-001): la enmienda del contrato público de
   `record-review`, redactada por `architect`. Cualquier ADR **adicional** sigue necesitando
   un eje medido.
