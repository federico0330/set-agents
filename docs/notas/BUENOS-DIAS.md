# Buenos días — digest del proyecto

<!-- notas:auto -->
_Ventana: desde `2026-08-17T11:27:12` · generado 2026-08-18T14:27:12+00:00_

## Necesita tu decisión

- **002-adaptive-pi-orchestration** — HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhausted 12 spawns plus 2 deep-review cycles. Requires redesign of trusted catalog/observations and crash-safe telemetry before further implementation. (hace 24 días)
- **011-quota-failover** — HUMAN_DECISION_REQUIRED: AC-06 exige una suscripción Anthropic controlada y genuinamente agotada junto a un proveedor alterno usable; la precondición no está verificada en esta sesión. El runner fail-closed fue verificado y no ejecutó Pi ni mutó DB sin ella. (hace 18 días)

## Qué quedó listo

- **032-cursor-como-runtime · orchestrator** — Aviso honesto: esta tanda la escribi y la probe yo mismo, sin un revisor independiente, porque la sesion tiene la delegacion desactivada. Los tests estan y pasan, pero la revision cruzada que el harness normalmente exige quedo pendiente.
  - aprendimos: La prohibicion de delegar no bloquea el trabajo, bloquea la aceptacion: se puede entregar codigo probado y dejar el sello pendiente sin mentir en el estado.
  - conviene ahora: Cuando haya un proveedor con cuota, correr un revisor independiente sobre los dos paquetes y recien ahi aceptarlos.
  - por qué ahora: Registrar la degradacion es la unica forma de que despues no se lea como un paquete aceptado normalmente.
  - alternativa: La alternativa era aceptarlos igual apoyandose en que los tests pasan, o revisarlos yo mismo con contexto limpio; las dos convierten la separacion de deberes en un tramite.
- **032-cursor-como-runtime · C1 · orchestrator** — Cursor ya puede correr el harness: quedan instalados los 28 roles y las 42 habilidades, y cada proyecto recibe las reglas y los comandos. Ningun rol elige modelo por su cuenta: usan el que vos elijas en Cursor, justamente para que no vuelva a pasar lo de las cuotas.
  - aprendimos: Cursor tambien lee subagentes desde los directorios de Claude Code, pero su frontmatter propio no coincide con el de ese runtime, asi que el atajo de reusar la instalacion existente habria mentido sobre lo que el agente puede hacer.
  - conviene ahora: Revision independiente de los dos paquetes, y hooks de evento de Cursor como trabajo siguiente.
  - por qué ahora: Federico agoto las cuotas de opencode, codex y claude; Cursor es el unico runtime pago disponible y era el unico que el harness no sabia configurar.

## Qué se está haciendo

- **032-cursor-como-runtime** — fase `PACKAGE_IMPLEMENTATION`

## Qué falta

- **002-adaptive-pi-orchestration** 5 hallazgos abiertos
- **011-quota-failover** 5 tareas pendientes en P1-quota-failover
- **032-cursor-como-runtime** → sigue la implementación local del paquete
- **032-cursor-como-runtime** 1 tarea pendientes en C2

## Qué cambió en el software

- **consola** — Los spawners de codex/opencode/claude ahora materializan el bloque de vault con degradacion honesta y sink protegido para fallas transitorias. (025-consola-minima-y-flexible/D5-vault-en-todo-spawn)
- **estado** — dos nuevos verbos: cmd_reopen extendido con --from-done (DONE→PACKAGE_PLANNING), cmd_amend_package (agrega tasks a paquetes no-accepted); amend-package y reopen-from-done en MUTATING_COMMANDS (031-registro-correctivo/P1-verbos-correctivos)
- **estado** — dos nuevos verbos: cmd_reopen extendido con --from-done, cmd_amend_package nuevo; MUTATING_COMMANDS actualizado (031-registro-correctivo/P1-verbos-correctivos)
- **narracion-notas** — guarda de punteros insensible a caja (lower_ident); densidad real excluye muletillas; --result started con validación de flags requeridos (028-narracion-que-ensena/N1-campos-que-obligan)
- **narracion-notas** — guarda de punteros insensible a caja (lower_ident); densidad real excluye muletillas; --result started con validación (028-narracion-que-ensena/N1-campos-que-obligan)
- **narracion-notas** — AC-18: orchestrator.md documenta cuándo correr digest; test actualizado para verificar contenido no nombre (028-narracion-que-ensena/N2-doctrina-que-explica)
- **narracion-notas** — límite de render elevado a 400; campos learned/next/why/alternative visibles en bitácora y digest (028-narracion-que-ensena/N3b-los-campos-donde-se-leen)
- **estado** — ai/scripts/check-feature-state.py: nuevo script que genera el grafo de ejecución de features y paquetes (006-execution-graph/P3-graph-view)
- **estado** — spawn provenance node en el grafo de estado: cada spawn queda trazable al paquete que lo originó, con su decision_id de routing (010-spawn-provenance/P1-spawn-provenance)

## Decisiones nuevas

- **La revision correctiva de D5 no puede aterrizar en el registro del paquete** — La delta review se ejecuta igual con un delta-reviewer independiente sobre el diff real 8091b0b..1014b02 acotado a los cuatro spawners, y su resultado se persiste como archivo de evidencia mas esta decision, NO como delta_review del paquete. No se falsea el registro del paquete ni se edita el JSON a mano para simular un camino que la maquina de estados no tiene.
- **Los tres paquetes de 028 se replantean porque fueron creados sin work items** — Se retiran los tres registros malformados con supersede-package, declarando en --reason el motivo REAL (creados sin work items, no una enmienda de alcance) y se recrean con los mismos acceptance criteria, sus work items reales y el diff_ref con SHA. No se edita el JSON a mano ni se declara una enmienda de alcance que no ocurrio.
- **Correccion: los paquetes de 028 tampoco se pueden replantear -- el motor no tiene salida** — No se fuerza. 028 queda en PACKAGE_GATES con su gate verde registrado; la revision independiente y las cinco reparaciones viven en docs/specs/028-narracion-que-ensena/evidence/N-package-review.md y en el codigo con sus mordidas probadas. Se registra blocker HUMAN_DECISION_REQUIRED.
- **tests/test_narracion_digest.py nunca se creó** — Registrar como deuda. Diferencia es sólo el nombre del archivo; el comportamiento está cubierto. No bloquea el cierre.
- **AC-16 AGENTS.codex.md: confirmación de deriva no registrada** — Fue deriva, no decisión. Registrar como deuda. El revisor verificó el origen pero no hay registro formal de la confirmación previa al unify.
- **D5-DR03: asimetría de cobertura anti-cacheo de fallos transitorios** — No es defecto vivo. Registrado como deuda. No bloquea el cierre.
- **Windows nativo es objetivo de bootstrap, no de runtime** — No se construye soporte nativo de Windows. README.md:107 ya declara el camino de Windows como install.ps1 -> WSL administrado, o sea que el harness corre sobre Linux aunque la maquina sea Windows, y verify-linux es el gate que lo cubre. Los tests que necesitan la toolchain POSIX saltan con la razon nombrada (tests/__init__.py, require_posix_toolchain), que es el mecanismo que el repo ya usaba en tests/test_provider_registry.py:463. Se corrige ADR-0041, cuyo punto 4 certificaba que 'la suite pasa en Windows'.
- **El espejo PROYECTO/ queda fijado entero, no por lista de nombres** — La paridad se afirma sobre el conjunto completo de archivos que existen en los dos arboles, con verify.sh como unica excepcion declarada y justificada (el del harness gatea este repo, el del template sniffea el stack de un proyecto generico: responden preguntas distintas). Las dos derivas se sincronizaron.
- **El locale de la maquina no decide como se escriben los artefactos del harness** — encoding='utf-8' explicito en toda lectura y escritura de texto de ai/scripts (barrido completo, 15 archivos), el temporal parcial se borra en el fallo, y el fallo de render_status se rutea a _log_render_failure como ya hacian render_notes y render_modules en vez de desaparecer. Un test AST fija la propiedad sobre todo ai/scripts.
- **Los dos hallazgos abiertos dentro de features cerradas ya estaban reparados** — Los dos estan reparados en el codigo. P1F-01 ('el pop de repair_entry anidado bajo if args.package_id'): ai/scripts/feature_state_lib/cli_lifecycle.py:277-285 resuelve por package_by_id con fallback a current_package_id y nombra el hallazgo en el comentario; el test que el suggested_fix pedia existe, tests/test_harness.py:8650 test_cmd_transition_pops_stale_repair_entry_without_package_id. F-04 ('CHECK_PASS y SELF_SCAFFOLD_SYNC_OK no comparan contra el estado real de Global/'): build.sh:117-127 ahora corre diff -ruN de los cuatro arboles contra una generacion fresca y emite GLOBAL_TREE_SYNC_OK o falla, que es la implementacion del punto 1 de ADR-0041. Ademas SELF_SCAFFOLD_SYNC_OK paso de dos archivos nombrados a mano a los 23 del espejo completo.
- **El orquestador de OpenCode sale de opencode-go y vuelve a la lane openai-codex** — models.toml [areas.coord].opencode go-zen pasa de 'opencode-go/grok-4.5' a 'openai/gpt-5.5'. openai/gpt-5.5 ya esta curado en [catalog].opencode_zen y usado por [areas.audit] y [areas.judge], y no colisiona con ningun [roles.<rol>.tiers.*] (todos luna/sol/terra). Las lanes zen y openai-only quedan como estaban.
- **Cursor entra como runtime anfitrion, nunca como lane de ruteo** — Los 28 roles se emiten con 'model: inherit' y validate_cursor_target (ai/scripts/generate.py) mata el build si alguno pinea un id concreto. Cursor no entra en models_config.RUNTIMES ni en routing_core.domain.SELECTED_RUNTIMES: no es lane de despacho.
- **En Cursor no se instalan hooks de evento en esta version** — El target cursor se instala sin hooks.json. La superficie que gobierna en Cursor es su propio modelo de permisos, y eso se dice explicitamente en README, INSTALACION y en la doctrina que el propio agente lee (Global/_shared/AGENTS.cursor.md).
- **Por que el harness agota cuotas: convierte un prompt humano en N prompts de proveedor** — La conclusion medida es que el harness no gasta de mas por prompt: gasta porque multiplica prompts. Cada spawn que el orquestador despacha por CLI es, para el proveedor, un prompt nuevo iniciado por el usuario, no una tool call autonoma adentro de una sesion. 246 despachos contra un tope de 300 mensuales explica exactamente 'dos prompts mios = un mes de cuota'. En opencode-go el mecanismo es otro pero el efecto es igual: tope diario, y el coordinador solo ya lo agotaba.

## Quick-fixes

- P1F-01 cerrado: fix validado — cmd_transition ya tiene try/except alrededor del pop de repair_entry, cubriendo el caso sin --package-id via fallback a current_package_id. Test test_cmd_transition_pop… (done)
- F-04 (020-honest-dashboard/P2-anclas-verificables) cerrado: verify.sh ahora pasa --profile go-zen a ./build.sh --output al comparar contra Global/. En CI, auto_profile() devolvía openai-only (PROVIDE… (done)
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
