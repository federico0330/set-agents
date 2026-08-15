# Buenos días — digest del proyecto

<!-- notas:auto -->
_Ventana: desde `2026-08-14T09:56:16` · generado 2026-08-15T12:56:16+00:00_

## Necesita tu decisión

- **002-adaptive-pi-orchestration** — HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhausted 12 spawns plus 2 deep-review cycles. Requires redesign of trusted catalog/observations and crash-safe telemetry before further implementation. (hace 21 días)
- **011-quota-failover** — HUMAN_DECISION_REQUIRED: AC-06 exige una suscripción Anthropic controlada y genuinamente agotada junto a un proveedor alterno usable; la precondición no está verificada en esta sesión. El runner fail-closed fue verificado y no ejecutó Pi ni mutó DB sin ella. (hace 15 días)
- **024-listo-para-terceros** — HUMAN_DECISION_REQUIRED: los cuatro paquetes estan aceptados con review independiente, pero la feature NO se cierra. generate.py:475 shippea el codename de un cliente real (replenishment-v2 / RPL-P0A) al orchestrator.md que se instala en la maquina de cada tercero, y el repo es PUBLICO (gh repo view -> visibility PUBLIC). Verificado por el orquestador: esta en Global/opencode/agents/orchestrator.md, en el ~/.config/opencode instalado, y en 8 archivos del repo, mas specs, dos ADRs y ~50 fixtures. Estaba registrado como deuda en 016 cuando el repo era privado; paso a publico alrededor del 2026-08-07 y eso lo convierte de deuda en exposicion viva. Una feature llamada 'listo para terceros' no puede cerrarse con un codename de cliente llegando a cada tercero. Decision del humano entre: sanear solo el arbol actual y aceptar el historial publico; reescribir historia con filter-repo y forzar push; o volver el repo privado mientras decide. Ninguna la toma el harness porque es informacion de un tercero y la remediacion completa es irreversible. Nota completa en docs/notas/decisiones/2026-08-14 HUMAN-DECISION-codename-de-cliente-real-en-repo-publico.md (hace 1 días)

## Qué quedó listo

- **027-controles-que-miran · P1-alcance-y-aislamiento · repair-agent** — La reparación comprobó que las pruebas preservan incluso el estado especial de un módulo bloqueado.
- **027-controles-que-miran · P2-nada-escribe-afuera · package-planner** — Los controles pendientes ya tienen una forma concreta de comprobarse antes de aplicarlos.
- **027-controles-que-miran · P1-alcance-y-aislamiento · gate-runner** — La comprobación puntual pasó; los chequeos largos no llegaron a completar por una interrupción del entorno.
- **027-controles-que-miran · P1-alcance-y-aislamiento · delta-reviewer** — La segunda revisión confirmó que el arreglo conserva todos los estados posibles sin afectar el resto.
- **027-controles-que-miran · P1-alcance-y-aislamiento · test-writer** — Las defensas de P1 siguen activas y comprobadas sin tocar el código.
- **027-controles-que-miran · P1-alcance-y-aislamiento · runtime-verifier** — El control se probó en uso real: bloquea lo ajeno y permite lo correspondiente.
- **027-controles-que-miran · P1-alcance-y-aislamiento · orchestrator** — P1 queda cerrado: el control ahora detecta archivos nuevos y las pruebas no dependen del orden en que se cargan.
- **027-controles-que-miran · P2-nada-escribe-afuera · implementer** — La protección ya está puesta: los intentos de tocar tu configuración real fallan y las pruebas temporales siguen permitidas. Falta validar el paquete completo.
- **027-controles-que-miran · P2-nada-escribe-afuera · gate-runner** — Las pruebas focalizadas y el build pasaron; las corridas largas se cortaron sin resultado final, por eso todavía no cierro este control.
- **027-controles-que-miran · P2-nada-escribe-afuera · local-gate-runner** — El reintento local no pudo correr las pruebas necesarias por una regla de su herramienta; no cambió nada ni se tomó como resultado del paquete.
- **027-controles-que-miran · P2-nada-escribe-afuera · orchestrator** — P2 queda pausado de forma segura: la protección focalizada funciona, pero la prueba completa no alcanzó a terminar y no voy a darla por buena sin su resultado final.
- **027-controles-que-miran · P2-nada-escribe-afuera · repair-agent** — La prueba de drift ahora hace su simulación en una copia temporal y ya no toca archivos reales; la protección se mantiene estricta.
- **027-controles-que-miran · P2-nada-escribe-afuera · gate-runner** — La corrección quedó comprobada: la simulación se hace en una copia temporal, las protecciones siguen funcionando y el build está correcto.
- **027-controles-que-miran · P2-nada-escribe-afuera · package-reviewer** — La revisión detectó tres caminos por los que una prueba podría salirse de su espacio temporal; los cerramos antes de aceptar el paquete.
- **027-controles-que-miran · P2-nada-escribe-afuera · gate-runner** — El caso portátil ahora pasó en una copia temporal, sin tocar tu instalación ni configuración: 1 prueba, 132 segundos, OK.
- **027-controles-que-miran · P2-nada-escribe-afuera · gate-runner** — El gate no falló, pero tampoco terminó: quedó detenido después de una prueba de instalación y se cortó de manera controlada a los 36 minutos. No lo tomo como validación.
- **027-controles-que-miran · P2-nada-escribe-afuera · repair-agent** — La causa era una simulación incompleta: faltaba el stub de pnpm, y el instalador intentaba calentar Pi por red. Ya quedó simulado; el focal termina en 2,6 segundos.
- **027-controles-que-miran · P2-nada-escribe-afuera · gate-runner** — La validación completa pasó: 1130 pruebas y todos los controles globales en verde.

## Qué se está haciendo

- **006-execution-graph** — fase `PACKAGE_ACCEPTED` — ⚠️ estancada hace 12 días
- **010-spawn-provenance** — fase `PACKAGE_ACCEPTED` — ⚠️ estancada hace 12 días
- **025-consola-minima-y-flexible** — fase `PACKAGE_IMPLEMENTATION`

## Qué falta

- **002-adaptive-pi-orchestration** 5 hallazgos abiertos
- **006-execution-graph** → P3-graph-view: falta declarar el impacto de módulo o marcarlo como exento
- **010-spawn-provenance** → P1-spawn-provenance: falta declarar el impacto de módulo o marcarlo como exento
- **011-quota-failover** 5 tareas pendientes en P1-quota-failover
- **025-consola-minima-y-flexible** → sigue la implementación local del paquete
- **025-consola-minima-y-flexible** 3 tareas pendientes en D1-superficie-humana

## Qué cambió en el software

- **narracion-notas** — LICENSE MIT, CONTRIBUTING, CHANGELOG, SECURITY, matriz de soporte medida y upstream re-apuntable (024-listo-para-terceros/C4-higiene-de-repo-publico)
- **routing** — El gate de credenciales de pi pasa a correr ANTES del subproceso pinneado de --list-models, y _decide_status suma MODEL_PINNED y los dos MODEL_REQUEST_ nombrados a su lista de marcadores informativos. (027-controles-que-miran/P3-gates-que-preguntan-antes)
- **routing** — El gate de credenciales de pi pasa a correr ANTES del subproceso pinneado de --list-models, y _decide_status suma MODEL_PINNED y los dos MODEL_REQUEST_ nombrados a su lista de marcadores informativos. (027-controles-que-miran/P3-gates-que-preguntan-antes)

## Decisiones nuevas

- **HUMAN_DECISION_REQUIRED: un codename de cliente real viaja al orchestrator.md de cada tercero, y el repo es PUBLICO** — NO se toca por iniciativa del harness y 024 NO se cierra como DONE mientras esto siga abierto. La feature se llama 'listo para terceros': cerrarla con un codename de cliente filtrandose a cada tercero seria exactamente el cierre deshonesto que este harness existe para impedir. Los cuatro AC de C4 SI estan satisfechos y el paquete puede aceptarse; lo que queda abierto es la feature.
- **La guarda de escritura de tests degrada en vez de exigir bubblewrap** — Degradacion portable, decidida por Federico el 2026-08-14. El audit hook in-process queda activo siempre y en todo sistema operativo: es la capa que cumple AC-04 y AC-05. La frontera de bubblewrap para procesos hijos se activa solo si shutil.which('bwrap') la encuentra, la copia del repo pasa a ser lazy y solo ocurre cuando esa frontera se monta de verdad, y los tres tests que dependen de la frontera se skipean cuando no esta. Al degradar se emite una linea unica por stderr: una guarda que se apaga en silencio es el defecto que esta feature entera vino a reparar.
- **Defecto latente: matching_modules no entiende la semantica nueva de owned_paths** — No se repara dentro de P4. render_modules.py no esta en los owned_paths del paquete y arreglarlo seria un refactor oportunista, que la doctrina del harness prohibe. Se registra como defecto latente, medido y con su file:line, en la misma familia que F-06, para que lo tome una feature que sea duena de ese archivo.
- **MODEL_PIN_UNAVAILABLE y MODEL_METADATA_INFERRED siguen sin filtrar, y el patron es el defecto** — El comportamiento NO cambia en P3: filtrar MODEL_PIN_UNAVAILABLE excede el AC-07 aprobado (spec.md D-5 nombra solo MODEL_PINNED y MODEL_REQUEST_*) y necesitaria su propio review. Lo que P3 repara es el registro: el comentario de routing_cli.py, el del test y la evidencia pasan a decir la razon verdadera -queda fuera del alcance del AC aprobado, es un hueco conocido y medido- en vez de una afirmacion sobre la semantica del marcador que el codigo fuente desmiente. El hueco queda aca, con su medicion.
- **Defecto latente: cuatro tests leen ai/state/project.json, que esta gitignoreado** — No se repara dentro de 027. tests/test_routing.py es archivo de P3 pero estos cuatro tests no tienen relacion con AC-06 ni AC-07, y arreglarlos seria refactor oportunista. Se registra medido, con su file:line y su mitigacion existente: ai/scripts/seed-state.py reconstruye el estado desde ai/state.seed/.
- **La narracion del orquestador tiene que ensenar, no apuntar a un identificador** — La narracion de cierre de cada agente pasa a ser explicativa por contrato, no descriptiva. Minimo exigible: que se entienda sin abrir la spec ni recordar que significa el identificador; que diga que se aprendio y no solo que se hizo; y que el siguiente paso venga con su porque y, cuando haya mas de un camino razonable, con la alternativa y el criterio para elegir. El identificador puede acompanar, nunca sustituir. Se implementa como feature del repo en la doctrina canonica del orquestador, para que valga en cualquier maquina y no solo en la sesion donde se pidio.
- **Defecto latente: cmd_update ignora install-targets.json y reinstala los cuatro arboles** — No se repara fuera de su paquete. Queda anotado como la primera verificacion que debe hacer el implementer de D4, en un --home temporal: instalar con --harness claude, correr Actualizar, y comprobar si install-targets.json vuelve a los cuatro. Si se confirma, AC-09 NO esta cumplido aunque --target exista, y el paquete cambia de tamano.
- **RDD no es un termino a definir: ya esta en uso instalado, con otro significado** — AC-08 deja de ser 'definir un termino nuevo' y pasa a ser 'reconciliar una sigla ya en uso sin contradecir dos skills instaladas'. Si Federico queria decir otra cosa con RDD, eso es una pregunta para el, no una decision del implementer: se le plantea con las dos acepciones a la vista en vez de elegir una en silencio.
- **Las cinco preguntas del desafio a 028, resueltas con doctrina vigente** — 1) Los cuatro campos que ensenan son obligatorios solo en los HITOS de ADR-0027, no en los spawns intra-fase que orchestrator.md:712 declara 'persisted, not narrated': exigirlos donde nadie los lee fabrica ritual, que es el riesgo opuesto que Federico no nombro pero va a sufrir. 2) --alternative obligatorio solo en blocked de causa tecnica y en PACKAGE_PLANNING, la unica bifurcacion real de la maquina, con --alternative none como valor legal: next_transition RESUELVE la bifurcacion, no la ofrece (transitions.py:66-71). 3) archivo.py:linea permitido en tech porque ADR-0026 lo exige como evidencia, prohibido como contenido unico en learned/next/why. 4) Los paquetes se reordenan a N3a -> N1 -> N2 -> N3b: AC-11..14 no dependen de nada y son lo unico que Federico puede VER en una manana. 5) El digest se regenera en cierre de fase o de turno, no en cada mutacion, porque BUENOS-DIAS.md esta trackeado en git y STATUS.md no (024/C1), y regenerarlo siempre lo mete en el diff de toda feature en vuelo.
- **Defecto: freeze-candidate compara HEAD contra HEAD y el techo de reparacion queda en cero para siempre** — Se restaura repair_ceiling a null para P2, que es lo que el propio ADR-0023 prescribe para un paquete sin medicion valida: 'Si candidate_identity no existe todavia, NO se congela ningun techo -- el mecanismo es aditivo, nunca retroactivo', y check-repair-ceiling.py trata un techo ausente como nada que chequear. No es relajar el control: es devolverle su comportamiento disenado para el caso 'no hay medicion'. El techo no se reconstruye retroactivamente porque no hay dato honesto con que hacerlo: el arbol ya mezcla P2, P3 y P4, y el freeze original nunca midio nada. La reparacion real de P2 midio 493 lineas (436 inserciones, 57 borrados, 3 archivos) para 7 hallazgos verificados, uno de ellos high; queda declarado en la evidencia en vez de simulado en el estado.
- **Defecto: la clave de idempotencia de log-decision no incluye feature_id** — No se monta ningun registro estructurado y repetitivo sobre log-decision hasta que la clave incluya su discriminante. Para la feature 029 se resuelve con un JSONL propio (ai/state/axes-log.jsonl) en vez de tocar log-decision, que ademas evita inflar docs/notas/decisiones/ y la seccion de decisiones del digest. El defecto queda registrado aparte para que lo repare quien sea dueno de cli_reporting.py.
- **P2-F11: run_gate filtra el entorno y el hijo escribe bytecode en el repo real, sin bwrap** — Se acepta P2 con esta limitacion DECLARADA, no reparada. No es reparable dentro del paquete: la guarda de escritura es por interprete y gates.py es codigo de produccion, fuera de los owned_paths de P2. La afirmacion de cierre de AC-04 se corrigio en la evidencia: pasa de 'cero drift, byte-identico' a 'cero drift trackeado y cero drift de Global/, con un residuo medido de bytecode en el camino sin bwrap'. Es hermano de P2-F08.
- **P2-F12 a P2-F15: la guarda cierra los casos nombrados, no las clases** — Se aceptan como deuda declarada y van a una feature de seguimiento, no a un tercer ciclo de reparacion de P2. El paquete ya consumio sus dos ciclos de deep review, ninguno de los cuatro tiene call site vivo, y P2-F14 en particular no es cerrable con addaudithook -mkfifo y mknod no emiten evento en CPython-, o sea es P2-F08 otra vez.
- **Los numeros de ADR de la spec 025 estaban viejos y se corrigieron a favor de los context packs** — Gana la asignacion de los context packs, que es la que refleja el estado real de docs/adr/ y la que ya esta implementada. La linea de la spec se corrigio dejando la correccion visible en el propio documento en vez de reescribirla en silencio, porque una spec aprobada que cambia sin dejar rastro es peor que una spec con un numero viejo. El mapa vigente: 0050 D1, 0053 D2, 0054 D3, 0055 D4, 0056 D5; 0057 para la feature 028 y 0058 para la 029, desempatados aparte el mismo dia.
- **CRITICO: coord_policy.allowed() es un prefix match, y desde el rol read-only se ejecuta codigo arbitrario** — Se abre feature 030 de seguridad y se repara esta noche, con paquete y review independiente. No se parchea agregando -X, --pager y --hostname-bin a FORBIDDEN_OPTIONS: eso seria exactamente la guarda falsa-verde numero doce, porque el defecto no son esos tres flags sino el prefix match. El arreglo es eliminar el '+ r".*"' y hacer que SAFE camine argv completo con modificadores enumerados por comando, que es la disciplina que SAFE_ARGV ya aplica. Un comando cuyo conjunto de flags no se puede enumerar -find, fd, bat, rg, curl- no pertenece a una allowlist de ejecucion silenciosa.
- **CRITICO: los guardas de shell son cuatro copias del mismo invariante, con agujeros distintos cada una** — Los tres guardas de Python deben IMPORTAR coord_policy.FORBIDDEN_SYNTAX en vez de redeclarar su propia copia, y un test parametrico unico tiene que correr el MISMO corpus de metacaracteres contra los cuatro. Entra en la feature 030 junto con SEC-001.
- **El CI lleva doce dias en rojo por tres causas independientes, una por sistema operativo** — Va a la feature 030 como paquete aparte del de seguridad, en este orden: import pwd condicional o restringir el job de Windows al subconjunto que tiene sentido; .resolve() en los tempdirs de los tests de store para macOS; y costura hermetica o skipUnless de credenciales para los tres tests de routing. RoutingStore._check_supported (store.py:376) rechaza explicitamente os.name != posix, asi que correr discover -s tests entero en Windows contradice el propio diseno del store y hay que decidirlo, no parchearlo.
- **Corte de cuota: los cinco agentes concurrentes murieron simultaneamente** — Doctrina de ADR-0011 y CLAUDE.md: una instancia que muere por cuota no fallo en la tarea, no consume presupuesto de reintentos, y se relanza una vez con otro modelo sin preguntar, persistiendo la causa. Se relanza primero el fix de seguridad, que es lo unico critico y lo unico que no dejo nada. Si el limite es de cuenta y no de modelo, el orquestador lo implementa directamente y lo marca explicitamente como NO revisado de forma independiente, pendiente de review cuando vuelva la cuota: dejar un RCE sin parchear en un repo publico es peor que un parche con su limitacion declarada.
- **El RCE de la allowlist quedo cerrado: 24 ataques bloqueados, 25 comandos legitimos intactos** — Cerrado. El prefix match de coord_policy.py:321 se reemplazo por enumeracion de modificadores por comando, siguiendo el patron de _rest_allowed que SAFE_ARGV ya aplicaba. curl valida parseando la URL en vez de con regex, exige una sola URL y prohibe -o, -O, -T, -d, --data*, -K y --config. find y fd salieron de la allowlist por flags no enumerables. sed tambien salio, por decision explicita: su lenguaje ejecuta con e y escribe con w, W, r y R dentro del script, y esa validacion no se sabia defender. FORBIDDEN_SYNTAX quedo centralizado e importado por los dos guardas que antes tenian su propia copia.
- **El fix del RCE deja fuera 'git show HEAD:ruta' y './build.sh --output', medido** — Se integra igual. La alternativa era quedarse con la version anterior, que dejaba pasar el canal de catalogo de MCPs y fallaba un test del repo; esta version pasa los 28. Los dos huecos se declaran en vez de taparse, y son de disponibilidad y no de seguridad: un comando legitimo denegado se nota enseguida, un ataque permitido no.
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
