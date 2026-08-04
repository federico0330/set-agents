# Buenos días — digest del proyecto

<!-- notas:auto -->
_Ventana: desde `2026-08-01` · generado 2026-08-04T18:23:43+00:00_

## Qué quedó listo

- **006-execution-graph · P3-graph-view · integrator** — El integrador confirmo que la vista de grafo funciona y encaja con todo lo entregado: las diez condiciones acordadas se cumplen y no aparecio ningun problema nuevo. La ficha de esta pieza queda cerrada tal como se acordo: completa, sin marcarla con un sello final que prometeria mas de lo que se ras…
- **008-dynamic-selection · P1-uninterrupted-delegation · integrator** — El integrador reviso la pieza que evita pausas innecesarias al delegar trabajo: las diez condiciones acordadas estan cumplidas y conviven bien con lo entregado despues. Solo falta la corrida final de pruebas globales antes del sello de terminado.
- **008-dynamic-selection · orchestrator** — La seleccion dinamica de modelos quedo oficialmente terminada: todas las pruebas del proyecto pasaron y la pieza convive bien con el resto. La parte que depende de medir cuotas reales queda en pausa hasta que eso sea posible.
- **010-spawn-provenance · P1-spawn-provenance · integrator** — El integrador confirmo que el registro de procedencia de cada delegacion funciona y quedo bien conectado: las cinco condiciones acordadas se cumplen y los pendientes del traspaso anterior ya estaban ejecutados. Igual que con la vista de grafo, esta ficha queda cerrada sin sello final, tal como se d…
- **012-discovered-inventory · P1-discovered-inventory · integrator** — El integrador confirmo que el inventario de modelos descubiertos quedo bien integrado: los 16 hallazgos de revision estan cerrados y verificados, y las compuertas de seguridad siguen cerradas como se acordo (se puede sondear, no rutear).
- **013-pi-interactive-target · package-planner** — El planificador termino: todo el objetivo interactivo de Pi cabe en un solo paquete de trabajo con siete tareas, e identifico que varias referencias del contrato quedaron desactualizadas por trabajo posterior (solo numeros de linea, no el contenido).
- **013-pi-interactive-target · P1-pi-interactive-target · implementer** — El implementador termino las siete tareas: el agente Pi ya tiene su propio juego de agentes, habilidades e instrucciones instalable, con guardia contra pisar archivos ajenos, prueba real de arranque (verificada en vivo contra pi 0.83.0) y la documentacion de arquitectura al dia. Solo una mitad de l…
- **013-pi-interactive-target · P1-pi-interactive-target · orchestrator** — El paquete de Pi quedo aceptado: implementado, revisado por dos revisores, reparado, re-revisado y probado de punta a punta. Falta solo la integracion final.
- **013-pi-interactive-target · P1-pi-interactive-target · integrator** — El integrador confirmo que el destino Pi encaja con todo el sistema: los otros tres destinos quedaron intactos byte a byte, la doctrina de seguridad esta pareja en los cuatro runtimes y la documentacion de arquitectura es coherente.
- **016-audit-debt-repayment · integrator** — El integrador confirmo que las dos piezas de la feature de deuda conviven sin acoplarse y que el contrato quedo cubierto por completo: de las seis deudas originales, tres quedan saldadas y tres siguen diferidas por decision explicita.
- **sin-feature · implementer** — El arreglo chico quedo aplicado y revisado por un segundo agente: la limpieza del registro de entrada a reparacion ahora funciona aunque la transicion manual no nombre el paquete.

## Qué se está haciendo

- **006-execution-graph** — fase `PACKAGE_ACCEPTED`
- **010-spawn-provenance** — fase `PACKAGE_ACCEPTED`

## Qué falta

- **006-execution-graph** → `INTEGRATION` — all packages accepted
- **010-spawn-provenance** → `INTEGRATION` — all packages accepted

## Decisiones nuevas

- **Redirect de _effective_runtime es silencioso, sin reason_code** — No es una vulnerabilidad, pero _effective_runtime (service.py) redirige de un lane a otro sin dejar reason_code ni exclusion. El ADR-0019 (AC-08) debe registrar que el rastro de auditoría debería mos…
- **setting-sources user confía en scope generado desde el propio repo** — --setting-sources user confía en ~/.claude/**, que build.sh --install puebla desde Global/claude-code/** de este mismo repo. Un spawn writer-class (dentro del límite de contención por cwd) puede edit…
- **areas.judge.opencode.go-zen colisiona con la misma escalera implementer, fuera de alcance** — No se toca. El contrato aprobado (Non-goals) restringe AC-06 a exactamente dos celdas nombradas de models.toml ([areas.audit].opencode."go-zen" y [areas.audit]/[areas.judge].claude); [areas.judge].op…
- **areas.judge.opencode.go-zen colisión CERRADA (F-02, amplía AC-06a); nuevo residuo areas.ops** — [areas.judge].opencode."go-zen" pasa de "openai/gpt-5.6-sol" a "openai/gpt-5.5" (mismo valor y mismo patrón que [areas.audit], models.toml:115). El test de AC-06(i) se reescribe genérico como el spec…
- **areas.ops.opencode.go-zen colision CERRADA (F-03); AC-06(a) queda genericamente cerrado, sin residuo** — El usuario aprobo explicitamente cerrar tambien esta tercera celda, mismo patron que audit/judge. [areas.ops].opencode."go-zen" pasa de "openai/gpt-5.6-terra" a "openai/gpt-5.4-mini" (models.toml:141…
- **Pasada de integración 2026-08-02: 008 y 012 a DONE; 006 y 010 quedan PACKAGE_ACCEPTED por diseño** — 008-dynamic-selection y 012-discovered-inventory transicionan INTEGRATION->DONE con gate global registrado. 006-execution-graph NO transiciona: su spec (docs/specs/006-execution-graph/spec.md:198-204…
- **AC-08/AC-14 supersedes ac09-ac10-pi-minimal-target-accepted: pi gains a real install.py target and generated agent tree** — This decision explicitly supersedes ac09-ac10-pi-minimal-target-accepted for the interactive surface: install.py gains a fourth target, pi -> ~/.pi/agent, and generate.py emits a real Global/pi/agent…
- **AC-13: la mitad de discoverability viva del roster queda environment-gated, no BLOCKED de feature** — Se registra el gap como decision persistida en vez de blocker de fase: el test existe, degrada con nombre, y debe correrse en una maquina con pi-subagents instalado antes de considerar AC-13 completa…
- **Los gates de suite completa no se corren en paralelo: build.sh colisiona en staging compartido** — Los gates que invocan build.sh (unittest discover completo, verify.sh) se ejecutan secuencialmente, nunca dos agentes a la vez. Un fallo de gate con build.sh exit 1 + FileNotFoundError en artefactos …
- **P1F-01 aceptado como deuda low: el pop de repair_entry depende del --package-id opcional** — Se acepta como deuda registrada (no bloquea la aceptacion del paquete, verdict pass del panel). Fix exacto anotado: hoist del pop resolviendo via package_by_id con fallback a current_package_id, en t…
- **Cierre parcial de audit-debt-006-p2: PR-07/08/09 saldadas por 016; PR-06/10/11 siguen diferidas** — De los 6 hallazgos de audit-debt-006-p2: PR-07 (repair_entry autoritativo, 6 sitios + fallback), PR-08 (extraccion _apply_verification_waiver/_apply_verdicts) y PR-09 (docstring + puntero ADR-0009 D7…
- **AC-01(i): grunt no puede flippear provider en verified review con catalogo de 2 proveedores** — Se documenta esta limitacion como comportamiento esperado, no como defecto: el test de efecto real de grunt (test_grunt_class_live_effect_against_real_effective_runtime_inventory) prueba supervivenci…

## Quick-fixes

- P1F-01: cmd_transition's repair_entry pop for PACKAGE_REPAIR was nested under 'if args.package_id:'; since --package-id is optional on transition, a manual transition without it skipped the pop and l… (done)
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
