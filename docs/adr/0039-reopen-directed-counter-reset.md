# ADR-0039 — `reopen` resetea el contador que lo bloqueó, estructurado en el blocker, nunca inferido

- Estado: Accepted (2026-08-11). Feature 019-harness-evolution, defecto del motor de estado encontrado
  dogfooding contra `P5-tools-discovery` — autorizado por Federico como arreglo al harness (opción A),
  registrado en `ai/state/decisions-log.jsonl`, slugs `reopen-no-resetea-el-contador-de-verificacion` y
  `reopen-resetea-contadores-opcion-A-autorizada`. No es un AC de 019: es la herramienta que quedó
  bloqueando el cierre de la feature.

## Contexto

Un paquete puede quedar `BLOCKED` porque agotó uno de los presupuestos anti-runaway que
`ai/scripts/feature_state_lib/model.py` define (`spawns`, `deep_review_cycles`, `gate_failures`,
`verifications`, `verification_waivers`, y el `repair_attempts` por finding que `record-repair` cuenta
aparte). `cmd_reopen` (`cli_lifecycle.py`, antes de este fix en las líneas 415-444) mueve la feature de
vuelta a `PACKAGE_PLANNING` y marca los blockers pendientes como resueltos — pero nunca tocaba
`package["attempts"]` ni el `repair_attempts` de ningún finding. El contador que produjo el bloqueo seguía
exactamente en el valor que lo agotó, así que la siguiente llamada al mismo comando (`record-verification`,
`start-review-panel`, `record-gate`, `record-repair`, según cuál budget se haya agotado) volvía a chocar
con el mismo `>= budget` y a bloquear la feature otra vez, en un ciclo sin salida.

**Reproducido, no teórico.** `P5-tools-discovery` (`ai/state/features/019-harness-evolution.json`) registró
una llamada a `record-verification` por finding en vez de un batch — proceso del orquestador, no un defecto
del paquete — y la séptima llamada agotó `max_verifications_per_package=6`. `_apply_verdicts`
(`ai/scripts/feature-state.py:699`, antes del fix) comprueba `attempts.get("verifications", 0) >= budget` y
bloquea **antes** de registrar el veredicto, así que ese finding (y los que venían atrás en la cola)
nunca quedaron verificados. `cmd_reopen` limpió el blocker y devolvió la feature a `PACKAGE_PLANNING`, pero
`attempts["verifications"]` siguió en 6. `require_verified` (`cli_review.py:277-289`) exige un
`verified_verdict` para cerrar cualquier finding por encima de `low` — y las dos únicas puertas de salida,
`record-repair` (`cli_repair.py:220`) y `record-delta-review --closed-finding` (`cli_repair.py:285`), pasan
por ahí. Resultado: cinco findings reparados en el árbol (`F-07..F-11`), imposibles de registrar como
cerrados, y un paquete que `package_accept_ready` (`model.py:441`) nunca iba a aceptar porque
`has_open_findings(package, {"critical","high","medium"})` seguía viendo esos `medium` abiertos.
`--skip-reason` no era una salida: exige que **todos** los findings abiertos sean `low`.

El docstring del propio budget (`model.py:94-100` según se cita en el decisions-log) ya decía que es "un
backstop contra runaway, NO el control anti-reintentos" — pero sin un camino de recuperación, un backstop
se convierte en un callejón sin salida permanente en cuanto el trabajo real (reparar, verificar) ya está
hecho y solo falta que el estado lo refleje.

## Decisión

### 1. El reset es DIRIGIDO — solo el contador que produjo ESTE blocker, nunca todos

`reopen` resetea **únicamente** el contador cuyo agotamiento generó el blocker que está resolviendo en esa
misma llamada. Nunca un reset general de `package["attempts"]`. Un `reopen` que limpiara `spawns`,
`gate_failures`, `deep_review_cycles` y `repair_batches` de una sola vez convertiría el mecanismo de
recuperación en una vía para saltear TODAS las protecciones de runaway juntas — el paquete que agotó su
presupuesto de spawns por descontrol real (no por un error de proceso como P5) recuperaría también, gratis,
presupuesto de deep-review y de gates que nunca gastó de más. El punto de un budget anti-runaway es que
cueste caro agotarlo; un reset amplio en la única puerta de recuperación existente lo volvería barato.

### 2. La asociación blocker→contador se persiste ESTRUCTURADA en el blocker, nunca inferida del texto

`block_with_reason` (`cli_lifecycle.py:396`) ahora acepta un parámetro `counter: dict | None` que, cuando
se pasa, se guarda tal cual en el dict del blocker (`blocker["counter"] = counter`). `cmd_reopen` lee esa
clave — nunca hace pattern-matching sobre `reason`. La razón es la misma que la nota SEC-001 de
`ai/scripts/coord_policy.py` (línea ~70) ya documenta como cara: inferir política de una cadena en prosa es
frágil por construcción, y en este código base la mayoría de las razones de bloqueo SON texto libre del
usuario o del caller —`args.evidence or "package testing blocked"`, `args.reason or "delta review blocked"`
— exactamente el tipo de string que un match sobre keywords leería mal o que un actor podría escribir para
disparar (o evitar) un reset con la palabra correcta en el lugar equivocado. Una clave estructurada, escrita
por el mismo código que decidió bloquear, no tiene esa superficie.

Dos formas cerradas para `counter` (ninguna otra se reconoce):

- `{"scope": "attempts", "key": <nombre>}` — para un contador de `package["attempts"][<nombre>]`:
  `spawns`, `deep_review_cycles`, `gate_failures`, `verifications`, `verification_waivers`.
- `{"scope": "finding", "key": "repair_attempts", "finding_id": <id>}` — para el `repair_attempts` por
  finding que `record-repair` incrementa (`cli_repair.py:231`, dentro de `cmd_record_repair`). Este
  contador vive en el finding, no en `package["attempts"]`, así que necesita su propio `finding_id` para
  ubicarse — es la razón por la que hay dos scopes y no uno.

### 3. Mapeo completo — todos los llamadores de `block_with_reason`

| Sitio | Razón | `counter` |
|---|---|---|
| `feature-state.py:396` (`cmd_record_spawn`) | "spawn budget exhausted" | `{"scope":"attempts","key":"spawns"}` |
| `feature-state.py:474` (`cmd_start_review_panel`) | "deep review budget exhausted" | `{"scope":"attempts","key":"deep_review_cycles"}` |
| `cli_review.py:33` (`cmd_record_review`) | "deep review budget exhausted" | `{"scope":"attempts","key":"deep_review_cycles"}` |
| `cli_repair.py:319` (`cmd_record_delta_review`) | "deep review budget exhausted before full re-review" | `{"scope":"attempts","key":"deep_review_cycles"}` |
| `cli_repair.py:49` (`cmd_record_gate`) | "gate failure budget exhausted" | `{"scope":"attempts","key":"gate_failures"}` |
| `feature-state.py:671` (`_apply_verification_waiver`) | "verification waiver budget exhausted for …" | `{"scope":"attempts","key":"verification_waivers"}` |
| `feature-state.py:703` (`_apply_verdicts`) | "verification budget exhausted for …" | `{"scope":"attempts","key":"verifications"}` |
| `cli_repair.py:234` (`cmd_record_repair`) | "repair budget exhausted for `<finding_id>`" | `{"scope":"finding","key":"repair_attempts","finding_id":<id>}` |

El resto de los llamadores **no** son agotamientos de contador — son verdictos/decisiones que un humano o
un rol expresó en texto libre (`cmd_block` del usuario, "package review blocked", "review panel blocked",
"repair exceeded its frozen line ceiling", "delta review blocked", "package testing blocked", "runtime QA
blocked") — y pasan `counter=None` (el default): `reopen` no resetea nada para ellos, porque no hay ningún
contador cuyo agotamiento haya producido ese blocker.

### 4. Blockers viejos sin la clave: tolerados, fail-closed

Todo blocker persistido antes de este fix (y cualquiera de los "no es un budget" de arriba) no tiene
`counter`. `_reset_blocker_counter` (`cli_lifecycle.py`) trata eso — y cualquier forma malformada
(`scope` fuera de `{"attempts","finding"}`, `key` ausente, `package_id` ausente, el paquete ya no existe,
la clave no está en `attempts`/el finding) — como no-op silencioso: `reopen` sigue resolviendo el blocker y
moviendo la fase exactamente como antes de este fix, solo que no resetea ningún contador. Fail-closed: el
comportamiento por defecto ante una clave ausente o inesperada es "no resetear nada", nunca "resetear todo
por las dudas".

### 5. Solo se resetea el contador de blockers que ESTA llamada resuelve

`cmd_reopen` itera `data["blockers"]` con el mismo `setdefault` de siempre (`resolved_at`,
`resolved_reason`, `resolved_by`) — pero ahora, antes de escribir, comprueba si el blocker YA tenía
`resolved_at` (es decir, si esta llamada es la que realmente lo resuelve, no una repetición sobre un
blocker ya cerrado en una `reopen` anterior). Solo para los blockers recién resueltos en esta llamada se
invoca `_reset_blocker_counter`. Esto evita que una segunda `reopen` (con nuevos blockers desde entonces)
vuelva a poner a cero un contador que ya fue reseteado y gastado de nuevo desde la última vez.

## Alternativas rechazadas

- **(Opción B del decisions-log) Editar `attempts["verifications"]` a mano en el JSON de estado y
  registrar el bypass.** Rechazada por Federico: resuelve el síntoma en P5 pero deja el defecto del harness
  intacto para el próximo paquete con muchos findings, y cada vez requiere edición manual fuera de banda
  registrada como excepción.
- **(Opción C) `supersede-package` de P5 para presupuesto fresco.** Rechazada: pierde el hilo
  review/repair ya hecho (los 15 findings, las verificaciones, los 5 repairs en el árbol) a cambio de
  presupuesto nuevo — desperdicia trabajo real para rodear un defecto del motor, no lo arregla.
- **Reset general de `package["attempts"]` en cada `reopen`.** Rechazada — ver §1: convierte la única
  puerta de recuperación en una forma de saltear todos los budgets a la vez, sin importar cuál se agotó.
- **Inferir el contador con un regex/keyword-match sobre `reason`.** Rechazada — ver §2: mismo error de
  forma que SEC-001 ya documenta como caro en `coord_policy.py`, y varias razones de bloqueo son texto
  libre que un match ingenuo leería mal.

## Consecuencias

- `block_with_reason` gana un parámetro opcional (`counter`), aditivo — cualquier llamador que no lo pase
  (o cualquier código externo que la invoque) sigue produciendo exactamente el mismo blocker de antes, sin
  la clave `counter`.
- Los blockers ganan una clave opcional `counter` — ningún lector existente de `data["blockers"]`
  (`graph.py`, `render_status.py`, `render_notes.py`, `model.done_ready`) itera un conjunto cerrado de
  claves, así que la adición es segura.
- Un paquete que agota `max_verifications_per_package` (o cualquier otro budget con contador) y se reabre
  con `reopen --reason ... --authorized-by ...` puede volver a llamar al comando que lo agotó sin chocar
  de nuevo contra el mismo blocker — mientras los DEMÁS contadores del mismo paquete quedan exactamente
  donde estaban, verificable con el test de regresión (`tests/test_harness.py`,
  `test_reopen_resets_only_the_counter_that_produced_the_blocker`).
- `ai/scripts/feature_state_lib/` tiene copias byte-idénticas en los árboles de `Global/opencode`,
  `Global/claude-code`, `Global/codex` (vía `hooks/feature_state_lib`, generado por `./build.sh` desde
  `ai/scripts/generate.py`) y en `PROYECTO/ai/scripts/feature_state_lib/` (copiado a mano, sin generador
  propio) — todas requieren el mismo cambio para que `./build.sh` seguido de `./build.sh --check` no
  reporte drift.
