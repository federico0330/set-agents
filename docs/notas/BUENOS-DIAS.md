# Buenos días — digest del proyecto

<!-- notas:auto -->
_Ventana: desde `2026-08-18T15:30:21` · generado 2026-08-19T18:30:21+00:00_

## Necesita tu decisión

- **002-adaptive-pi-orchestration** — HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhausted 12 spawns plus 2 deep-review cycles. Requires redesign of trusted catalog/observations and crash-safe telemetry before further implementation. (hace 26 días)
- **011-quota-failover** — HUMAN_DECISION_REQUIRED: AC-06 exige una suscripción Anthropic controlada y genuinamente agotada junto a un proveedor alterno usable; la precondición no está verificada en esta sesión. El runner fail-closed fue verificado y no ejecutó Pi ni mutó DB sin ella. (hace 20 días)

## Qué quedó listo

- **033-menos-espera-menos-cuota · PKG-5 · orchestrator** — El segundo paquete quedo aceptado: los veinte minutos de chequeo ahora muestran progreso, la falla apenas ocurre, y un resumen con los tests mas lentos. Un primer intento se cayo porque el reporter no encontraba los tests; se arreglo y se clavo con una prueba.
  - aprendimos: Invocar un script deja el path de import en la carpeta del archivo; cambiar el directorio de trabajo no lo arregla. Un probe dentro del mismo proceso no ve ese crash porque tests ya era importable.
  - conviene ahora: Implementar el paquete del menu Modelos para que pinte en menos de 300 ms con lo que ya esta en disco, y los datos vivos lleguen despues.
  - por qué ahora: Sin eso, abrir Modelos sigue congelando unos dieciseis segundos, que es lo que mas se siente al usarlo.
- **033-menos-espera-menos-cuota · PKG-2 · finding-verifier** — El menu Modelos todavia no trae solo los datos vivos: hay que corregir dos fallas concretas antes de darlo por bueno.
  - aprendimos: Una tecla de forzar refresco no sustituye el refresco in-place que pide el contrato del primer frame.
  - conviene ahora: Un solo repair-agent cierra los dos hallazgos, con tests de mordida, y no toca el primer frame.
  - por qué ahora: Sin el vivo automatico el operador ve pins viejos hasta que descubre una tecla; reparar ahora gasta el unico ciclo de review que queda.
- **033-menos-espera-menos-cuota · PKG-2 · orchestrator** — El menu Modelos ya pinta al toque y despues trae solo los datos vivos, sin etiquetar como fallido lo que todavia no se midio. Lo damos por cerrado.
  - aprendimos: El vivo automatico tiene que ir despues del primer frame, no escondido atras de una tecla de forzar.
  - conviene ahora: Sigue el picker agrupado por proveedor, sin parpadeo, testeable sin terminal real.
  - por qué ahora: El menu ya no congela; lo que mas se siente ahora es elegir entre una lista plana de 125 ids.
- **033-menos-espera-menos-cuota · PKG-3 · orchestrator** — Elegir un modelo ahora es una lista agrupada, con lo actual marcado y sin que parpadee la pantalla. Lo damos por cerrado.
  - aprendimos: Leer el valor actual no puede pasar por un parser que hace setdefault: eso escribe tablas vacias.
  - conviene ahora: Sigue colapsar las tres lanes de OpenCode a un solo modelo por area.
  - por qué ahora: La consola ya pinta rapido y se puede elegir; lo que queda es el eje lane, de alto riesgo.
- **033-menos-espera-menos-cuota · PKG-1 · orchestrator** — OpenCode queda en un solo modelo por area, el que ya usabas. Si un proveedor se agota, el error nombra al proveedor y te dice que reasignes. Lo damos por cerrado.
  - aprendimos: Sacar auto_profile no es un agujero si el agotamiento falla con nombre; el swap silencioso de lane era el defecto.
  - conviene ahora: Ultimo paquete: que las cuotas alcancen, con context pack y aviso al 80 por ciento de spawns.
  - por qué ahora: Las lanes ya no existen; lo que queda es no gastar despachos de mas.
- **033-menos-espera-menos-cuota · PKG-6 · implementer** — El harness ya no arranca un paquete a ciegas: hace falta el resumen, los gates baratos no llaman a un modelo, y el reporte de costos dejo de medir cero.
  - aprendimos: When the lib changes, the generated copies have to travel in the same package or a clean checkout lies about sync.
  - conviene ahora: Freeze the candidate and run the package gates, using the local runner for the cheap commands.
  - por qué ahora: Without freeze the risk classifier has no candidate, and without gates the review would bless an unproven tree.
- **033-menos-espera-menos-cuota · PKG-6 · package-reviewer** — El ahorro de cuota todavia no cierra: el aviso del 80% se apaga cuando hay varios paquetes, y un panel chico puede abrir con el revisor equivocado.
  - aprendimos: Status was summing every package against the per-package ceiling, so the 80% warning only worked on a one-package fixture.
  - conviene ahora: Verify the three findings, then repair what survives. One spawn slot remains.
  - por qué ahora: A false finding would spend the last spawn on a useless patch and leave the real repair unreachable.
- **033-menos-espera-menos-cuota · PKG-6 · finding-verifier** — Los tres problemas que encontro la revision siguen en pie. No queda margen de despachos para arreglarlos sin pasarse del tope de este modo de trabajo.
  - aprendimos: A duplicate follow-up spawn plus a separate local-gate-runner consumed the slack that repair-plus-delta needed.
  - conviene ahora: Human decides: two extra spawns to finish PKG-6, or stop the package here.
  - por qué ahora: The ninth spawn would freeze the feature. Skipping the second look after a high finding is not allowed.
  - alternativa: Seguir con dos despachos extra (repair y la segunda mirada) sin tocar el tope del modo en el codigo, o dejar PKG-6 abierto.
- **033-menos-espera-menos-cuota · PKG-6 · orchestrator** — El ultimo paquete cerro: el harness avisa el presupuesto a tiempo, no deja un panel chico con el revisor equivocado, y el reporte de costos deja de contar dos veces lo mismo.
  - aprendimos: A test that used the small+low missing-role hole as setup broke verify until it was restaged on a high panel, eating the last 5 lines of the repair ceiling.
  - conviene ahora: Integration: module-impact or waiver on all six packages, remedir the 2026-08-18 baseline, AC-4.5 CI SHAs if push is authorized.
  - por qué ahora: Without the before/after comparison the feature has not proved it saved wait or quota.
- **033-menos-espera-menos-cuota · PKG-6 · integrator** — Los seis paquetes cerraron. El menu deja de congelar, el gate bajo de veinte minutos a trece, y el reporte de costos deja de medir cero. Falta subir a GitHub para probar Windows/macOS en la misma corrida.
  - aprendimos: Section 1 token totals did not drop on this window; the Cursor-host saving is invisible there. Section 2 going from 0 to 144 is the harness registry closing the omission.
  - conviene ahora: Push main when you want AC-4.5; three green jobs in one GitHub run. Then DONE/judge.
  - por qué ahora: Without a push there is no SHA triple for Windows/macOS/linux in the same cycle, which is the last acceptance leftover from PKG-4.
- **034-cuota-organica-y-writer-barato · orchestrator** — Aprobaste el contrato: el escritor arranca barato, un arreglo caro si falla, y un cambio chico no abre el proceso grande. El contexto sigue en Obsidian, no en Engram.
  - aprendimos: Engram no entra cuando el vault Obsidian ya es mandatory; el challenge bloqueo por HOW (grano de promotion, writer_tier=fast, pin repair pesado), no por recorte.
  - conviene ahora: package-planner crea PKG-A..D con context packs; luego implementer PKG-A.
  - por qué ahora: Sin plan de paquetes no hay implementacion legal; el context pack es obligatorio al entrar implementacion.
  - alternativa: none
- **034-cuota-organica-y-writer-barato · PKG-A · orchestrator** — El cambio chico ya no puede colarse a la ceremonia completa: si alguien arranca un trabajo mediano o grande sin decir por que es riesgoso, el sistema lo corta. Los chequeos automaticos de este lote dieron verde.
  - aprendimos: The ownership gate does not know which files this package created versus which were already dirty, so generated vault notes and a previous feature leftover must be waived by directory rather than by widening product ownership.
  - conviene ahora: An independent reviewer who did not write the change checks the six acceptance criteria, then we skip app runtime checks because this package has no user interface.
  - por qué ahora: Gates exist to prove the bite before a reviewer spends a spawn. They passed, so the remaining cost is independence, not more local compile.
  - alternativa: none
- **034-cuota-organica-y-writer-barato · PKG-A · orchestrator** — El primer lote ya esta cerrado: un arreglo chico no puede colarse a la ceremonia grande sin decir el riesgo. Alguien que no escribio el cambio lo reviso y dio el visto bueno.
  - aprendimos: The CLI mode flag default staying scoped is what makes a naked init fail closed; the operational default for a tiny change is simply not calling init.
  - conviene ahora: Implement the cheap writer default, rewrite the fast-suffix test without deleting it, and persist a single salvage plus the consecutive-failure promotion counter.
  - por qué ahora: Without the cheap default the rest of the quota work has nothing to count as first-attempt green.
  - alternativa: none
- **034-cuota-organica-y-writer-barato · PKG-B · orchestrator** — El escritor barato y el salvamento unico ya pasaron los chequeos automaticos: el modelo por defecto es gratis, y si falla solo hay un intento caro.
  - aprendimos: A package gate against the last commit still sees files the previous accepted package dirtied, so those paths need a pinpoint waiver rather than a wider product ownership.
  - conviene ahora: Two independent reviewers look at quota routing and at whether salvage can be abused, then we skip app runtime checks.
  - por qué ahora: Quota defaults and a salvage override change who spends money; that is why the security pass sits with the package review instead of waiting for a later audit.
  - alternativa: none
- **034-cuota-organica-y-writer-barato · PKG-B · orchestrator** — El escritor barato ya esta en default y el salvamento unico funciona. Si el barato falla dos paquetes seguidos, el proximo sube un escalon. Eso ya esta cerrado.
  - aprendimos: A named-gate PASS is not package close. The consecutive-miss counter is a package grain; resetting it per event hid promotion.
  - conviene ahora: Implement the frontier cap of four per package and sixteen per feature, plus the cost-report percent that must not count salvage-green as first attempt.
  - por qué ahora: Without a cap distinct from spawn count, salvage and judges still burn quota inside the same budget as cheap writers.
  - alternativa: none
- **034-cuota-organica-y-writer-barato · PKG-C · orchestrator** — El cupo de modelos pesados ya se puede ver y se puede chocar: el quinto de un lote para, y un salvamento verde no cuenta como acierto a la primera.
  - aprendimos: Frontier used is a counter beside spawn count, not inside attempts, so reopen can reset it without touching spawn budget.
  - conviene ahora: Independent review plus a security pass on whether the cap can be bypassed by omitting flags.
  - por qué ahora: A cap that does not fire is quota theatre; a cap that can be skipped by leaving --model empty is the remaining abuse path.
  - alternativa: none
- **034-cuota-organica-y-writer-barato · PKG-C · orchestrator** — El cupo de modelos pesados ya corta de verdad: el quinto de un lote para, y un comando chico ya no disfraza un modelo caro. El reporte muestra que porcentaje del barato cierra a la primera.
  - aprendimos: A caller-controlled --command list is not a role. The 033 P001 exemption is the local-gate-runner role, not the allowlist riding on a heavy spawn.
  - conviene ahora: Emit Cursor frontmatter model per role: cheap writers, distinct-family judges, rewrite the inherit-everywhere test instead of deleting it.
  - por qué ahora: Without Cursor pins the cheap default only exists on OpenCode; this host would keep spending whatever the user picked for every role.
  - alternativa: none
- **034-cuota-organica-y-writer-barato · PKG-D · orchestrator** — En Cursor cada rol ya declara su modelo: quien escribe codigo usa el barato, quien juzga usa otra familia.
  - aprendimos: Cursor cheap is not the OpenCode zen free id; it is a measured Cursor slug in a new models.toml dimension, while RUNTIMES stays without cursor.
  - conviene ahora: Independent review of pins and a security pass on whether inherit-universal or a heavy repair-agent pin can sneak back.
  - por qué ahora: A pin that silently becomes inherit everywhere would spend the session model on every role again, which is the quota leak this package exists to stop.
  - alternativa: none
- **034-cuota-organica-y-writer-barato · PKG-D · orchestrator** — En Cursor cada rol ya declara su modelo: el que escribe codigo usa uno barato, el que juzga usa otra familia, y si el juez deja el modelo en blanco el sistema lo corta. Los cuatro lotes de este trabajo estan cerrados.
  - aprendimos: Cursor inherit is an alias of the parent, so treating the slug as its own family made a reviewer look independent while sharing the writer.
  - conviene ahora: Integrate the four accepted packages: run the global verify, write the integration evidence, then the independent judge. Memory stays in the Obsidian vault, not Engram.
  - por qué ahora: Without a global verify the four packages can be locally green and still fail together. The judge cannot run until that evidence exists.
- **034-cuota-organica-y-writer-barato · PKG-D · orchestrator** — Engram no hace falta: el contexto ya vive en tu vault de Obsidian. El trabajo de cuota y escritor barato cerro: un arreglo chico no abre ceremonia, el que escribe codigo arranca barato, hay un techo de modelos pesados, y en Cursor cada rol declara su modelo.
  - aprendimos: Treating Cursor inherit as its own family made reviewers look independent while they shared the parent model. The vault already covers what Engram would copy.
  - conviene ahora: Nothing left in this pipeline. Commit or release only if you ask for it.
  - por qué ahora: The judge and the global suite already passed, so the remaining work is a human cut, not another agent.

## Qué se está haciendo

- **032-cursor-como-runtime** — fase `PACKAGE_GATES`
- **033-menos-espera-menos-cuota** — fase `INTEGRATION`

## Qué falta

- **002-adaptive-pi-orchestration** 5 hallazgos abiertos
- **011-quota-failover** 5 tareas pendientes en P1-quota-failover
- **032-cursor-como-runtime** → el paquete está listo para la revisión profunda
- **033-menos-espera-menos-cuota** → faltan correr los gates globales finales

## Qué cambió en el software

- **generacion-arboles** — Tres lanes OpenCode (go-zen/zen/openai-only) colapsaron a un string. active_profile, auto_profile, --profile y active-profile desaparecieron. Si el proveedor esta exhausto, falla en voz alta en vez d… (033-menos-espera-menos-cuota/PKG-1)
- **generacion-arboles** — El wizard de modelos pinta el primer frame desde disco antes de probear suscripciones. El probe vivo corre despues, o con la tecla Refrescar. (033-menos-espera-menos-cuota/PKG-2)
- **consola** — El picker agrupa por proveedor, muestra n de total, marca el actual con un punto, y wipea con ESC H J en vez de 2J. ENTER en un header no selecciona. (033-menos-espera-menos-cuota/PKG-3)
- **estado** — PACKAGE_IMPLEMENTATION exige context pack. gate-runner all-P001 se rechaza a favor de local-gate-runner. El panel sale de complexity/risk. Status avisa al 80% del techo DEL PAQUETE actual. (033-menos-espera-menos-cuota/PKG-6)
- **narracion-notas** — STATUS.md y las notas muestran spawns usados/techo del paquete corriente y WARN 80% antes del tope duro. (033-menos-espera-menos-cuota/PKG-6)
- **estado** — init scoped y feature exigen un token de riesgo nombrado antes de escribir state; sin token el comando muere y no deja JSON. (034-cuota-organica-y-writer-barato/PKG-A)
- **generacion-arboles** — La doctrina canónica (triage y orquestador) unifica el default 1-3 con el error nombrado del CLI; los espejos de cada runtime se regeneran desde canónico. (034-cuota-organica-y-writer-barato/PKG-A)
- **routing** — El default de los escritores code-rw es el modelo gratis del catalogo que cumple tools; hay un solo salvage pesado por paquete y el contador de misses baratos es por paquete cerrado, no por gate suel… (034-cuota-organica-y-writer-barato/PKG-B)
- **estado** — record-spawn --salvage exige --model no vacio; record-gate ya no resetea el consecutivo en un PASS parcial; el reset ocurre al pasar de gates a review si el paquete cerro green-on-first. (034-cuota-organica-y-writer-barato/PKG-B)
- **estado** — Hay un cupo de modelos pesados (4 por paquete, 16 por feature) distinto del tope de despachos. Un comando P001 no disfraza un rol pesado. reopen puede resetear solo ese contador. (034-cuota-organica-y-writer-barato/PKG-C)
- **narracion-notas** — STATUS muestra frontier_used/cap. cost-report seccion 2 muestra percent green-on-first-attempt derivado; salvage-verde no es first-attempt; no se suma con seccion 1. (034-cuota-organica-y-writer-barato/PKG-C)
- **generacion-arboles** — generate.py emite model: por rol en Cursor; inherit en un reviewer (review-ro + audit/judge) muere en load_roles y validate_cursor_target. El escritor y repair-agent quedan en composer-2.5; los juece… (034-cuota-organica-y-writer-barato/PKG-D)
- **generacion-arboles** — El orquestador canónico documenta un solo salvage por paquete: si el escritor code-rw barato deja el gate rojo, repair-agent corre una vez más con override de invocación; el pin de repair-agent sigue… (034-cuota-organica-y-writer-barato/PKG-B)

## Decisiones nuevas

- **Orden de paquetes: CI y gate primero, consola despues, lane y cuota al final** — Implementar un paquete por vez hasta accepted, en este orden: PKG-4, PKG-5, PKG-2, PKG-3, PKG-1, PKG-6. No abrir el siguiente con el anterior a medias.
- **Independencia de review en Cursor: mismo modelo, contexto limpio, degradacion registrada** — Delegar solo con subagentes nativos de Cursor (implementer, package-reviewer, finding-verifier, etc.). Registrar la degradacion same-model/clean-context en record-subreview --evidence y finalize-review-panel --evidence de cada paquete. Nunca --route-decide ni dispatch.
- **PKG-4 se commitea antes del freeze porque el candidato exige refs ya en git** — Un commit con el diff de PKG-4 mas los context packs y notas de 033, despues freeze-candidate --baseline HEAD^ --candidate-ref HEAD. No es un commit oportunista: es el invariante del freeze.
- **El presenter del gate vive en un modulo Python testeable, no en el shell** — El implementer escribe ai/scripts/verify_reporter.py y tests/test_verify_reporter.py. Esas dos rutas se registran como excepciones de owned_paths (update-package no expone --owned-path). verify.sh solo invoca el reporter. AC-5.6 no se implementa en este paquete salvo prueba de aislamiento.
- **Digest no ensucia el diff de un paquete con bitacoras ajenas** — Revertir esas bitacoras a HEAD. Registrar excepciones docs/notas y docs/specs/033-menos-espera-menos-cuota, igual que en PKG-4. El fallo de producto es otro: ImportError tests al invocar verify_reporter.py como script.
- **El vivo llega solo despues del primer frame; el test de labels se aisla** — Si el cache falta o vencio, el segundo ciclo del menu mide vivo con with_progress y vuelve a pintar. La tecla Refrescar sigue forzando. Primer frame sigue sin probe. El test de labels mockea detect_subscriptions. None de primer frame no se etiqueta como probe fallido; despues del vivo se llena live_discovered.
- **033-pkg6-techo-scoped-deja-repair-fuera** — No se despacha repair-agent. No se llama record-spawn contra el techo. El paquete queda en PACKAGE_REPAIR con findings upheld y verification grabada, a la espera de decision humana: dos despachos extra para cerrar el ciclo, o parar.
- **033-pkg6-dos-despachos-extra-autorizados** — Se despacha repair-agent y despues delta-reviewer sin record-spawn. La excepcion queda en este log, no en model.py. El contador del paquete sigue en 8/8.
- **033-push-main-para-ac-4-5** — Push de main a origin (no force). La corrida que dispare ese push es la de AC-4.5. No se commitean notas ni bitacoras ajenas en este paso.
- **034 slice: cuota + ruteo orgánico; Engram no entra** — En alcance: (1) escritor barato + un salvage caro + techo frontier + % green-on-first-attempt; (2) ruteo orgánico real: quick-fix 1-3 archivos como default operativo, no solo doctrina ADR-0020; (3) Cursor pinnea modelo por rol, enmendar 032 AC-06. Fuera: 16 runtimes, RDD nativo, installer Go, bench Gentle, perfiles OpenCode Tab, Engram. Engram no se implementa: el vault Obsidian (ADR-0012) ya es la memoria durable y Federico lo usa como contexto.
- **Engram no-goal: el vault Obsidian ya es el contexto** — Engram queda fuera de 034. El contexto durable es docs/notas/ (vault) mas feature-state.py. No hay paquete Engram ni MCP enable de engram para este slice.
- **Excepciones de ownership PKG-A: docs vivos, spec 034 y suciedad 033** — Waivers de directorio: docs/notas/, docs/modules/, docs/specs/, docs/adr/, docs/architecture/. Se suman a los mirrors Global/*/PROYECTO y tests vecinos ya aprobados. No ensancha owned_paths de producto.
- **Excepciones de ownership PKG-B: lifecycle, espejos y docs vivos** — Waivers: cli_lifecycle.py, Global/*/, PROYECTO feature_state_lib/, docs/{notas,modules,specs,adr,architecture}/, tests vecinos de init. No se ensancha owned_paths de producto.
- **PKG-B waiver del skill de triage que ya cambio el lote anterior** — Exception puntual de Global/_canonical/skills/request-triage/SKILL.md como suciedad preexistente del lote A, no como ownership de B.
- **Excepciones PKG-C: suciedad de A/B, espejos y docs** — Waivers de directorio para Global, PROYECTO, docs, y archivos puntuales de A/B. owned_paths de C no se ensancha.
- **Excepciones PKG-D: arboles emitidos y suciedad A/B/C** — Waivers de Global/, PROYECTO/, docs/, tests/fixtures/models.toml y scripts de estado de A/B/C. owned_paths de D no se ensancha.
- **No spawn test-writer: cada AC ya tiene mordida** — Skip test-writer. A-D already landed bite tests in test_harness (organic init, cheap writer, frontier cap, mixed inherit). No test-gap finding exists to close. Remaining spawns: integrator (global verify + evidence), adversarial-judge, memory-scribe (local vault only, Engram is no-goal).
- **memory-scribe al cierre sin gastar el techo 12** — Mint gate-runner y adversarial-judge con record-spawn (11 y 12). memory-scribe corre al cierre SIN record-spawn, misma forma que 033-pkg6-dos-despachos-extra-autorizados. El techo en codigo no se toca. La excepcion queda en este log.
<!-- /notas:auto -->

## Notas propias (contenido manual previo, preservado)

# Buenos días, Fede

Escrito la noche del 2026-07-27. Todo lo de abajo está commiteado, con gate verde y pusheado a `origin/main`.
**Enmienda 2026-07-29 (feature 007-P3):** la sección 3 y la fila 4 de la cola de trabajo (sección 5) se
corrigieron ese día — esas dos partes específicas no estaban commiteadas al momento de la corrección.

---

## 1. Qué quedó listo

**Feature 006 `execution-graph`, paquetes P1 y P2, entregados y auditados.**

Ocho commits nuevos, de `90e9948` a `02ed998`. La suite pasó de **181 a 209 tests**, cero salteados, ninguna
regresión debilitada. `VERIFY_PASS`, `CHECK_PASS`, `GLOBAL_PORTABILITY_OK`, `SELF_SCAFFOLD_SYNC_OK`,
`INSTALL_PASS`, `DRIFT_OK`. La instalación global está sincronizada.

### P1 — `false-edges` (`90e9948`)

Prosa canónica, cero código. Quedó escrito en el orquestador que el panel de review sale **concurrente en un
solo batch**, que consolidar/aplanar/deduplicar **no lleva agente** (es `feature-state.py`), y la regla
general: abanicá cuando ninguna salida alimenta a otra entrada — **esto compra latencia, NO cuota**.

Un ítem del plan lo maté por medición: "gates concurrentes" ahorraba ~2 segundos porque `unittest` es 208 de
los 220 segundos de `verify.sh`. Arista falsa real, valor cero.

### P2 — `finding-verification` (`1e46ed2` + tres rondas de reparación)

**El hueco que cerró:** un hallazgo de review iba directo a `repair-agent` sin que nadie intentara refutarlo, y
`feature-state.py` no tenía forma de retirar un hallazgo sin parchear código. Un reviewer equivocado te
forzaba un cambio de código y te quemaba uno de los dos ciclos de review.

Ahora hay un rol `finding-verifier` (read-only, tier audit) entre el panel y la reparación, con la consigna
invertida: **matar** cada hallazgo, no confirmarlo. Y el CLI lo hace cumplir, no la prosa:

- solo `finding-verifier` puede refutar, nunca un hallazgo que él mismo levantó, y `--actor` es obligatorio
- `record-repair` se niega a correr sin registro de verificación, y rechaza cualquier hallazgo `medium+` sin veredicto
- refutar exige evidencia con forma real: `file:line`, un comando `$` con su salida, o un `AC-NN`
- `upheld` es terminal para verificación — se acabó preguntar hasta que cambie la respuesta
- verificar **no** consume ciclo de review
- si se refutan todos, el paquete salta directo a testing: te ahorrás la reparación *y* el delta review

El hallazgo refutado **nunca se borra**: queda con su motivo, su evidencia y quién lo mató, renderizado en la
nota del paquete. Eso es el expediente.

---

## 2. Cómo se entregó (esto importa más que el qué)

El paquete pasó por el ciclo completo y **no salió bien a la primera, en ninguna de las tres rondas**:

| etapa | resultado |
|---|---|
| Panel concurrente (`package-reviewer` + `security-auditor`) | `repair_required`, **13 hallazgos** tras deduplicar |
| Pasada de refutación (el nodo aplicado a sí mismo) | **13 de 13 sostenidos**, cero refutaciones — intentó refutar seis en serio y falló por evidencia en todas. Además ruteó un hueco que el panel no vio |
| Delta review #1 | `repair_required`, **2 `high` nuevos** — introducidos por mi propia reparación |
| Delta review #2 | `repair_required`, **2 más** — introducidos por la reparación de la reparación |
| Auditoría final (seguridad + arquitectura, sobre el todo entregado) | `repair_required`, **15 hallazgos** — 11 de arquitectura, 4 de seguridad |

Los tres `high` del panel decían todos lo mismo, y es la lección de la noche: **puse la ceremonia en el prompt
y dejé el CLI blando**. El `implementer` podía refutar un hallazgo `critical` de seguridad contra su propio
diff; mi chequeo de evidencia era truthiness de Python (`true`, `{}` y `"   "` pasaban); y nada obligaba a
verificar antes de reparar, porque `--skip-delta` se chequea adentro de `record-repair` pero mi `--skip-reason`
no guardaba nada.

Y después, reparando eso, metí dos regresiones más: un guardián que se anulaba solo cuando había un
`record-spawn` de por medio (o sea, siempre, porque la doctrina lo obliga), y un presupuesto de verificaciones
más chico que los flujos que los otros presupuestos ya permiten, que terminaba en `BLOCKED` estando dentro de
todo.

Y la auditoría final, que es la que más me enseñó, encontró el error de fondo que las tres rondas no vieron
**porque cada una miró solo su propio diff**:

> **Instalé la invariante en un comando, no en el modelo de hallazgos.**

"Un hallazgo `medium+` no sale del conjunto abierto sin veredicto" lo puse en `record-repair`. Las tres fugas
estaban **afuera** de los dos comandos que endurecí, en las puertas que ningún diff tocaba:

- `record-delta-review --closed-finding` **no tenía ninguna guarda** — ni severidad, ni veredicto, ni
  reparación, ni actor. Era la única de las cuatro rutas de escritura terminal sin control. Un hallazgo
  `critical` de seguridad salía del conjunto abierto sin cambio de código y sin registro, y el paquete se
  aceptaba.
- Un hallazgo re-levantado en el ciclo 2 **heredaba el veredicto del ciclo 1**: una credencial reutilizable
  que autorizaba una reparación con un juicio emitido contra otro diff.
- `--new-finding` con un id existente appendeaba un duplicado, y como todos los lookups son first-match, el
  paquete quedaba **sin salida por CLI**.

Y la de seguridad, peor y de la misma familia: `verified_verdict` y `repair_attempts` —los campos que mis
guardas nuevas **leen**— eran asignables al nacer. Un `upheld` pre-seteado vuelve el hallazgo permanentemente
irrefutable, elegido por quien lo levanta. Un `repair_attempts` negativo hace que `max_repairs_per_finding` no
dispare nunca. Lo cerré por **whitelist**, porque blacklistear una clave por vez es exactamente lo que habían
hecho las tres rondas anteriores.

**Todo eso lo encontraron los revisores, no yo.** Nueve reparados, seis registrados como deuda explícita en
`ai/state/decisions-log.jsonl` (`audit-debt-006-p2`), con el criterio de cada uno.

---

## 3. ¿Está listo para usar pi-agent como querés?

**Sí, sin nada pendiente de tu parte.** El bloqueante que describía esta sección cuando la escribí ya no
existe — corrección registrada el 2026-07-29 (decisión
`buenos-dias-anthropic-surcharge-claim-was-wrong-supersedes-first-pass`, feature 007-P3): ver más abajo qué
decía antes y qué se verificó.

### Lo que sí está

- `pi 0.81.1` instalado, pinneado y verde: `--doctor --harness pi` da `doctor_green: true`, `version_ok: true`,
  con los dos proveedores autenticados (`anthropic` + `openai-codex`).
- El carril Pi es **real**, no simulación (ADR-0007, feature 004 P3 aceptada). Es el único runtime del repo que
  permite cruzar proveedor **en la misma invocación del orquestador** — que es exactamente lo que pedís.
- El reparto que querés ya es el default del catálogo:
  - **orquestar con gpt** → `[orchestrator.pi] model = "gpt-5.6"`
  - **planificar con claude** → los roles de `duty=docs` (`architect`, `package-planner`, `product-analyst`) caen en `[areas.docs] claude = "sonnet"`
  - **implementar con gpt** → `[areas.implement] codex = "gpt-5.6-terra"`
- **Fable eliminado.** Era el único lugar donde el arnés todavía lo pinneaba (`[areas.coord]`, y solo para el
  orquestador corriendo dentro de Claude Code). Lo pasé a `sonnet`. El router adaptativo nunca lo elegía —
  fable no existe en `routes.v1.toml`. Verificado: ningún agente compilado lo menciona.

### Lo que decía acá y ya no es cierto (corregido 2026-07-29)

Esta sección afirmaba que el ruteo adaptativo estaba apagado por una base `routing.db` en schema 4
irrecuperable (`routing-db-schema4-unmigratable`), y ofrecía `rm
~/.local/state/set-agentes/routing-v2/routing.db` como remediación de una línea. **La remediación está
retirada, y no por lo que esta sección decía antes.** Verificado hoy contra el disco: `routing.db` **sí
existe**, pero en **schema 6** — la creó la propia verificación en vivo de 007-P2 (un spawn real por el carril
Pi), con un dispatch registrado. `--route-decide` la abre sin problema; no hay nada que borrar ni que migrar
en esta máquina.

Los dos backups schema-4 reales que sí existían (`~/.local/state/set-agentes/routing-v2/backups/routing-v4-*.db`)
siguen intactos y siguen **rechazados a propósito**: no difieren del canónico solo en comentarios (el caso que
007-P1 arregló, AC-03) sino que además les falta el `CHECK` que documenta el bloque `-- N03:` — eso es AC-04/
AC-05, y esa clase de divergencia se sigue rechazando por diseño, con un diagnóstico que nombra qué objeto
diverge. Por decisión del usuario (2026-07-28) esos dos backups se descartan, no se recuperan; 007-P1 es
"future-proofing y diagnóstico honesto", no recuperación de esa base puntual. No hay ningún comando tuyo
pendiente.

### Sobre tu presupuesto y las sesiones largas

Con suscripciones de USD 100 y sesiones de 4-5 horas en 2-3 proyectos simultáneos, el cuello de botella es
cuota, no capacidad. Dos cosas a favor y una advertencia:

- Las reglas de economía de spawns que entraron en P1 están escritas contra este escenario exacto: el panel
  concurrente compra **wall-clock, no cuota** (cada subagente recarga su contexto igual), y el cap blando de
  ~12 spawns por paquete sigue vigente.
- El verificador nuevo es **+1 spawn de tier audit por paquete**, y solo cuando el bundle tiene algo por encima
  de `low`. Si el paquete es todo-`low` se saltea con waiver registrado. Vale la pena medirlo en tu primer
  paquete real antes de dar por buena la relación costo/beneficio.
- **Corregido 2026-07-29 (antes decía que el carril `anthropic` de Pi "cobra por token como extra-usage"; era
  incorrecto, decisión `buenos-dias-anthropic-surcharge-claim-was-wrong-supersedes-first-pass`):** no hay
  sobrecargo por token —
  `~/.pi/agent/auth.json` entra por `anthropic → {"type": "oauth"}`, la misma suscripción y el mismo bucket de
  cuota que el resto. El `"You're out of extra usage"` que viste solo prueba que la cuota incluida se agotó en
  ese momento. Lo asimétrico, medido, es el consumo por unidad de trabajo: el carril Pi es un subprocess CLI
  por spawn (ADR-0007), conversación fría sin caché entre spawns — dos muestras en vivo lo confirman, 3221
  tokens de entrada por 6 de salida (feature 004) y 3321 por 5 (spawn real de verificación de 007-P2). Cuánto
  pesa eso comparado entre `anthropic` y `openai-codex` **no está medido y queda fuera de alcance a
  propósito** (contrato 007, "Alcance explícitamente excluido"): en esta máquina `routes.v1.toml` le da
  prioridad a `openai-codex` sobre `anthropic` en todos los tiers y el catálogo habilita proveedores
  todo-o-nada, así que un `--route-decide` de producción no **selecciona** `anthropic` como carril primario —
  sigue existiendo como `fallback_provider` (así quedó registrado en el único dispatch real que hay), pero eso
  no es una elección comparable a propósito, es un plan B que no se llegó a usar.

---

## 4. Graph engineering: qué de todo eso implementé

Te lo separo en tres, porque el hilo mezclaba cosas ciertas, cosas que ya tenías, y marketing.

### Ya lo tenías, sin llamarlo así (verificado contra el repo, no supuesto)

| Paso del hilo | Dónde ya vivía |
|---|---|
| El modelo clasifica, el código decide | Feature 004: el orquestador clasifica complexity/risk y `routes.v1.toml` (datos, no prosa) elige tier y modelo |
| Contratos tipados en las aristas | Context packs + ACs + `ai/state/features/*.json` — y **mejor que el hilo**, porque están en disco y sobreviven al proceso, no en RAM |
| Nadie corrige su propio examen | Separación de deberes en `CLAUDE.md`, reviewers read-only, `NON_ACCEPTING_ACTORS` |
| Escalonar modelos por nodo | Tiers `fast`/`balanced`/`frontier` |
| La arista es gratis, no pagues un agente para un flatMap | `feature-state.py` consolida en código |
| Un solo escritor por archivo | `owned_paths` por paquete |

### Lo que implementé esta noche

1. **Abanicar lo independiente** (P1) — el panel de review sale concurrente, con la economía escrita al lado:
   compra latencia, no cuota.
2. **Verificación adversarial antes de actuar** (P2) — el paso 09 del hilo, adaptado. El hilo pide *N
   escépticos independientes por hallazgo*; eso multiplica el gasto 3-9× y revienta el cap de spawns. Va **uno
   batcheado**, y la escalada la decide el tier vía `routes.v1.toml`, no un rol nuevo.
3. **Tope con criterio de convergencia** — el dedup corre contra **todo lo visto**, no contra lo que sobrevivió.
   Sin eso los hallazgos refutados reaparecen cada ronda y el bucle no seca nunca.
4. **Regla explícita anti-fontanería** — consolidar no lleva agente.

### Lo que rechacé, y por qué

- **`Workflow` y los workflows dinámicos de Claude Code.** Es exclusivo de un runtime. SET-AGENTES corre sobre
  OpenCode + Claude Code + Codex; atarlo a un vendor contradice la tesis de portabilidad de la 005. El grafo se
  expresa en **datos del arnés**, no en el tooling de nadie.
- **"La coordinación cuesta cero tokens".** Falso a medias, y la mitad falsa es la que te importa: el script no
  paga inferencia, pero cada subagente recarga su contexto. Quedó escrito textual en el orquestador para que no
  se vuelva a deducir mal.
- **"Loop-until-dry".** El cap de 2 ciclos ya converge. Un bucle sin señal dura de convergencia es exactamente
  la forma de quemar cuota.
- **"Decenas o cientos de subagentes".** La concurrencia real la topan los núcleos. Es marketing.

### Lo que queda pendiente del grafo

**006-P3 `graph-view`**, bloqueado por 005-P2 (el vault). La tesis: el grafo de Obsidian y el grafo de ejecución
**son el mismo grafo**. Hoy `docs/notas/` ya renderiza `[[wikilinks]]` hub → feature → paquete → decisión: eso
es estructura. Falta la ejecución — cada spawn como nodo con aristas tipadas (`produjo`, `verificó`, `refutó`,
`reparó`, `bloqueó`), `set-agents --graph` emitiendo el DAG como mermaid, y poder ir de un hallazgo al nodo que
lo produjo, al que lo verificó y al commit que lo reparó, todo con clicks y sin la sesión de chat.

Eso es lo que te da la ventaja de producto que buscabas: `git log docs/notas/` como historial de decisiones
diffeable y offline. Ningún arnés SaaS lo tiene, porque su estado es el transcript.

---

## 5. Cola de trabajo

| # | Qué | Estado |
|---|---|---|
| 1 | ~~**005-P2 `vault-mandatory`**~~ | **entregada** — 005 completa (`DONE` 2026-07-30) |
| 2 | ~~**005-P3 `tui`**~~ | **entregada** — 005 completa |
| 3 | ~~**006-P3 `graph-view`**~~ | **entregada** e integrada (validación 2026-08-02, AC-20..29 pass). 006 queda en `PACKAGE_ACCEPTED` **para siempre** por su propia spec (P1/P2 fueron por waiver); el "próximo paso: INTEGRATION" del tablero es fraseo automático, no trabajo pendiente |
| 4 | ~~Reparación de `migrate_from_v4` en la 005~~ | **entregada** por 007-P1 `schema-normalize` (2026-07-29): `_normalize_ddl()` ignora comentarios y es delimiter-aware en los tres sitios de comparación |
| 5 | ~~Deuda de la auditoría (`audit-debt-006-p2`)~~ | **saldada parcialmente** por la feature 016 (`DONE` 2026-08-02): PR-07 (`repair_entry` autoritativo), PR-08 (extracción waiver/verdicts) y PR-09 (docs) cerradas. Siguen diferidas PR-06, PR-10 y PR-11 — PR-11 (compare-and-swap en `mutate`) sigue candidata a paquete propio. ~~P1F-01~~ **cerrada por quick-fix** (2026-08-02, revisado por segundo agente): el pop de `repair_entry` ya no depende de `--package-id`, con fallback a `current_package_id` y test propio |

**Pasada de integración 2026-08-02:** 008 y 012 transicionadas a `DONE` con gate global verde
(verify.sh 558 tests OK, build check sin drift). 006 y 010 validadas con `pass` pero quedan en
`PACKAGE_ACCEPTED` por diseño registrado (spec 006 §proceso; HANDOFF-PASO9 §5.5) — no son pendientes.
En la misma pasada: **013** (`pi` como cuarto destino generado del arnés), **014** (política de
preferencia de modelos, con efecto real en 6 roles vía el redirect de 015) y **016** (deuda de
auditoría) llegaron a `DONE` con ciclo completo (panel → verificación adversarial → repair → delta →
testing → QA → integración).

~~**Deuda registrada, sin paquete:**~~ **Cerrada por 016 AC-08** (2026-08-02): `package-gate-runner.md`
quedó genericizado con placeholders; un test case-insensitive impide que los literales de cliente vuelvan.

**Límite conocido, documentado en el ADR-0009:** `refuted` es irreversible. `reopen` no toca estados de
hallazgos, así que una refutación equivocada solo se deshace editando el JSON a mano.
