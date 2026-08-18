# Bitácora — 027-controles-que-miran

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-18T15:34:35+00:00

[2026-08-14T16:35:05+00:00] P1-alcance-y-aislamiento · repair-agent · started · modelo openai/gpt-5.6-terra · effort medium
Cliente: Corregir el último detalle de aislamiento para que una prueba no altere el estado de otra.
Ingeniería: PACKAGE_REPAIR de 027/P1. Finding P1-F01 medium ya verificado: _import confunde ausencia con sys.modules[name]=None. El repair-agent sólo toca tests/test_harness.py y evidencia; luego habrá delta-review independiente.

[2026-08-14T16:36:04+00:00] P2-nada-escribe-afuera · package-planner · started · modelo openai/gpt-5.6-terra · effort high
Cliente: Dejar definido cómo se comprueba cada control pendiente antes de activarlo.
Ingeniería: PACKAGE_PLANNING complementario: P2/P3 no tenían context pack y P4 acaba de materializarse tras AC-08/09. El planner delimita archivos, pruebas rojo/verde, riesgos y gates sin tocar código ni estado.

[2026-08-14T16:41:38+00:00] P1-alcance-y-aislamiento · gate-runner · started · modelo openai/gpt-5.6-luna · effort low
Cliente: Confirmar por separado que el último arreglo no afectó ninguna prueba.
Ingeniería: PACKAGE_GATES posterior a reparación de P1-F01. Repetir test dirigido y los módulos tests.test_harness/tests.test_routing con heartbeat, más git diff --check; el reparador no puede aprobar su propio cambio.

[2026-08-14T16:41:38+00:00] P1-alcance-y-aislamiento · repair-agent · done
Cliente: La reparación comprobó que las pruebas preservan incluso el estado especial de un módulo bloqueado.
Ingeniería: Repair-agent retornó: P1-F01 quedó cubierto con centinela y caso None, mordida rojo/verde y diff check. Los módulos aislados fueron lanzados pero el entorno del agente los cortó a 30s; se delega gate runner independiente antes del delta.

[2026-08-14T16:42:24+00:00] P2-nada-escribe-afuera · package-planner · done
Cliente: Los controles pendientes ya tienen una forma concreta de comprobarse antes de aplicarlos.
Ingeniería: Planner retornó tres context packs: P2 guarda de escritura por destino; P3 gate pi previo al subproceso y códigos de modelo; P4 match de directorios y casos borde. P2/P3 se enlazan al estado; P4 se materializa al volver a PACKAGE_PLANNING después de P1.

[2026-08-14T16:49:12+00:00] P1-alcance-y-aislamiento · delta-reviewer · started · modelo openai/gpt-5.6-sol · effort high
Cliente: Una segunda mirada independiente confirma que el detalle corregido quedó realmente cubierto.
Ingeniería: DELTA_REVIEW de P1-F01. Repair gpt-5.6-terra; reviewer delta debe ser contexto limpio/modelo distinto. Examina sólo sentinel/None, mordida y evidencia; registra sin verificar los módulos completos interrumpidos, sin suplantarlos por pase.

[2026-08-14T16:49:12+00:00] P1-alcance-y-aislamiento · gate-runner · done
Cliente: La comprobación puntual pasó; los chequeos largos no llegaron a completar por una interrupción del entorno.
Ingeniería: Gate runner: test dirigido P1-F01 y git diff --check PASS. tests.test_harness y tests.test_routing interrumpidos por heartbeat con exit 130, sin traceback ni conteo; quedan SIN VERIFICAR y no se registran como PASS.

[2026-08-14T16:52:44+00:00] P1-alcance-y-aislamiento · delta-reviewer · done
Cliente: La segunda revisión confirmó que el arreglo conserva todos los estados posibles sin afectar el resto.
Ingeniería: Delta-reviewer gpt-5.6-sol PASS: P1-F01 cerrado, cero findings nuevos, no requiere full review. Test dirigido y mutación en memoria verdes/rojos correctos; módulos completos post-repair quedan sin verificar por interrupción exit 130, sin evidencia de falla.

[2026-08-14T16:52:57+00:00] P1-alcance-y-aislamiento · test-writer · started · modelo openai/gpt-5.6-terra · effort medium
Cliente: Comprobar una vez más que las tres defensas de P1 siguen activas.
Ingeniería: PACKAGE_TESTING requerido tras DELTA_REVIEW. El test-writer no cambia producción: valida cobertura existente de untracked, aislamiento y sys.modules None; no debilita ni borra tests.

[2026-08-14T16:55:08+00:00] P1-alcance-y-aislamiento · test-writer · done
Cliente: Las defensas de P1 siguen activas y comprobadas sin tocar el código.
Ingeniería: Test-writer PASS: AC-01 untracked, AC-02/03 aislamientos en subproceso y P1-F01 de tres estados; tests dirigidos y git diff --check verdes. Módulos completos siguen sin verificar por alcance y por la interrupción previa.

[2026-08-14T16:55:19+00:00] P1-alcance-y-aislamiento · runtime-verifier · started · modelo openai/gpt-5.6-terra · effort medium
Cliente: Verificar en uso real que el control detecta lo que debe y no castiga lo permitido.
Ingeniería: PACKAGE_RUNTIME_QA requerido por runtime_surface=true. Runtime-verifier debe probar el CLI en repo temporal: untracked fuera→OWNERSHIP_FAIL, untracked dentro→OWNERSHIP_PASS, y no habilitar MCP/browser.

[2026-08-14T16:58:50+00:00] P1-alcance-y-aislamiento · runtime-verifier · done
Cliente: El control se probó en uso real: bloquea lo ajeno y permite lo correspondiente.
Ingeniería: Runtime verifier PASS en repo temporal: untracked fuera→OWNERSHIP_FAIL rc=2, dentro→OWNERSHIP_PASS rc=0; fixture eliminado, sin MCP/browser ni estado real.

[2026-08-14T17:00:53+00:00] P1-alcance-y-aislamiento · orchestrator · done
Cliente: P1 queda cerrado: el control ahora detecta archivos nuevos y las pruebas no dependen del orden en que se cargan.
Ingeniería: P1 fue aceptado tras reparación, gates, delta review, regresión y QA de CLI; las corridas largas posteriores interrumpidas permanecen explícitamente sin verificar en la evidencia.

[2026-08-14T17:01:37+00:00] P2-nada-escribe-afuera · implementer · started · modelo openai-codex/gpt-5.6-terra · effort medium
Cliente: Voy a blindar las pruebas para que si alguna intenta tocar tu home o la configuración de los asistentes, falle antes de escribir nada; las pruebas que trabajan en su carpeta temporal siguen funcionando.
Ingeniería: P2 implementa AC-04/05 en el punto de entrada de tests, conserva el aislamiento de P1 y deja evidencia reproducible para gates y revisión.

[2026-08-14T17:14:07+00:00] P2-nada-escribe-afuera · gate-runner · started · modelo openai-codex/gpt-5.6-luna · effort low
Cliente: Ahora verifico la barrera con una mirada separada: confirmamos que no deje escapar escrituras y que las pruebas sigan funcionando.
Ingeniería: P2 entra en PACKAGE_GATES; runner independiente ejecuta pruebas focalizadas y gates, registrando interrupciones como tales.

[2026-08-14T17:14:07+00:00] P2-nada-escribe-afuera · implementer · done
Cliente: La protección ya está puesta: los intentos de tocar tu configuración real fallan y las pruebas temporales siguen permitidas. Falta validar el paquete completo.
Ingeniería: Implementación parcial de P2 entregó guardia en tests y regresiones focalizadas verdes; tests.test_routing completo quedó SIN VERIFICAR por interrupción, sin fallos atribuidos.

[2026-08-14T17:18:23+00:00] P2-nada-escribe-afuera · local-gate-runner · started · modelo openai-codex/gpt-5.6-luna · effort low
Cliente: Repito las pruebas largas de forma controlada para obtener un resultado final verificable; no voy a cambiar el código por un corte de la herramienta.
Ingeniería: Reintento de verificación independiente: persistir y capturar exit code/markers, sin reparar código.

[2026-08-14T17:18:23+00:00] P2-nada-escribe-afuera · gate-runner · done
Cliente: Las pruebas focalizadas y el build pasaron; las corridas largas se cortaron sin resultado final, por eso todavía no cierro este control.
Ingeniería: Gate independiente: AC-04/05 parciales; cuatro comandos quedaron SIN VERIFICAR por interrupción del canal, sin fallo de producto reproducible.

[2026-08-14T17:19:07+00:00] P2-nada-escribe-afuera · local-gate-runner · blocked
Cliente: El reintento local no pudo correr las pruebas necesarias por una regla de su herramienta; no cambió nada ni se tomó como resultado del paquete.
Ingeniería: P001 del rol local-gate-runner sólo permitió py_compile; no es un fallo reproducible de P2. Se reencamina a gate-runner de alcance completo.

[2026-08-14T17:19:08+00:00] P2-nada-escribe-afuera · gate-runner · started · modelo openai-codex/gpt-5.6-terra · effort medium
Cliente: Reencamino la verificación a un runner que sí puede ejecutar las pruebas completas, sin tocar el código.
Ingeniería: El intento local fue bloqueado por P001 de rol; se solicita runner de gates completo con sesión persistente y evidencia de códigos finales.

[2026-08-14T17:46:37+00:00] P2-nada-escribe-afuera · orchestrator · blocked
Cliente: P2 queda pausado de forma segura: la protección focalizada funciona, pero la prueba completa no alcanzó a terminar y no voy a darla por buena sin su resultado final.
Ingeniería: Tras dos reintentos de gate y una sesión persistente, tests.test_harness siguió progresando pero produjo un E y no devolvió traceback/resumen antes de agotar el presupuesto; proceso de test interrumpido con exit 130. Estado BLOCKED/HUMAN_DECISION_REQUIRED con evidencia P2-gates-retry.md.

[2026-08-14T17:55:57+00:00] P2-nada-escribe-afuera · orchestrator · started
Cliente: Con tu autorización, reabro P2 para darle a la suite el tiempo que necesita y obtener un resultado completo, sin cambiar nada del producto.
Ingeniería: Autorización humana registrada; se repite sólo tests.test_harness en sesión persistente con log duradero antes de continuar los gates.

[2026-08-14T18:10:30+00:00] P2-nada-escribe-afuera · repair-agent · started · modelo openai-codex/gpt-5.6-terra · effort medium
Cliente: La prueba que simulaba un archivo global alterado se moverá por completo a un sandbox; la protección se mantiene estricta.
Ingeniería: Root cause confirmado por unittest: test_build_check_detects_global_drift_and_names_the_file muta Global/opencode/AGENTS.md bajo ROOT. Reparación debe reproducir el drift en una copia temporal, sin whitelist en la guardia.

[2026-08-14T18:15:19+00:00] P2-nada-escribe-afuera · repair-agent · done
Cliente: La prueba de drift ahora hace su simulación en una copia temporal y ya no toca archivos reales; la protección se mantiene estricta.
Ingeniería: Reparación mínima: test_build_check_detects_global_drift_and_names_the_file clona el checkout en TemporaryDirectory y ejecuta build.sh allí; sin cambios a guardia ni build.sh.

[2026-08-14T18:15:30+00:00] P2-nada-escribe-afuera · gate-runner · started · modelo openai-codex/gpt-5.6-luna · effort low
Cliente: Comprobamos por separado que la corrección no toca tu repo real y que el test conserva su detección de cambios indebidos.
Ingeniería: Gate post-repair de P2 ejecuta test reparado, regresiones AC-04/05 y chequeos rápidos; se reserva la última instancia para revisión independiente.

[2026-08-14T18:18:32+00:00] P2-nada-escribe-afuera · gate-runner · done
Cliente: La corrección quedó comprobada: la simulación se hace en una copia temporal, las protecciones siguen funcionando y el build está correcto.
Ingeniería: Gate post-repair 4/4 PASS: fixture drift, regresiones AC-04/05, git diff --check y build.sh --check. Permanece la suite extensa autorizada en sesión persistente.

[2026-08-14T18:30:12+00:00] P2-nada-escribe-afuera · package-reviewer · started · modelo openai-codex/gpt-5.6-sol · effort xhigh
Cliente: Las protecciones y pruebas completas ya pasaron; una revisión independiente verifica que no haya atajos ni efectos colaterales.
Ingeniería: Última instancia de P2: package-review read-only contra AC-04/05, diff integrado, reparación de fixture y evidencia de gates.

[2026-08-14T18:49:28+00:00] P2-nada-escribe-afuera · orchestrator · started
Cliente: El verificador encontró pruebas que dependían de datos reales de tu máquina; las hago autónomas en su sandbox sin tocar ni leer tus credenciales.
Ingeniería: verify.sh: 1125 tests, 3 routing fails + 1 provider-registry error por PROVIDER_UNAUTHENTICATED/estado CLI bajo HOME aislado. Seguimiento de repair-agent existente sin gastar nuevo spawn: fixtures deben declarar proveedor/estado temporal.

[2026-08-14T20:42:03+00:00] P2-nada-escribe-afuera · package-reviewer · done
Cliente: La revisión detectó tres caminos por los que una prueba podría salirse de su espacio temporal; los cerramos antes de aceptar el paquete.
Ingeniería: Review independiente repair_required: P2-F01 descendientes sin frontera, P2-F02 symlink-padre, P2-F03 estado global al cambiar HOME. Reparación consolidada requerida.

[2026-08-14T21:37:59+00:00] P2-nada-escribe-afuera · repair-agent · started
Cliente: La revisión endurecida encontró tres compatibilidades de pruebas, no una escritura real fuera del área aislada: el entorno temporal debe quedar disponible para comandos legítimos y los procesos abortados deben conservar su código esperado.
Ingeniería: Reutilizo la reparación ya asignada —sin ampliar presupuesto— para ajustar el sandbox de procesos, mantener /tmp privado escribible y preservar señales de hijos. Este diagnóstico queda asentado antes del cambio.

[2026-08-14T21:42:10+00:00] P2-nada-escribe-afuera · gate-runner · started
Cliente: Los cambios ya están en el árbol; falta una comprobación independiente de los casos concretos antes de gastar otra corrida larga.
Ingeniería: Reutilizo el ejecutor de gates para correr los cinco focales desde una sesión limpia y registrar el resultado. No modifica código ni estado.

[2026-08-14T21:47:53+00:00] P2-nada-escribe-afuera · gate-runner · started
Cliente: La prueba combinada no falló: quedó colgada antes de informar resultado, así que no la tomo como válida ni como aprobada.
Ingeniería: Aíslo el caso huésped con límite y registro propio; así distingo un problema de la frontera anidada de una interacción entre focales. El chequeo de formato sigue en verde.

[2026-08-14T22:03:04+00:00] P2-nada-escribe-afuera · gate-runner · started
Cliente: La corrección de la frontera anidada está aplicada. El resultado del focal no quedó capturado de forma confiable, así que no lo doy por aprobado.
Ingeniería: Corro el gate portátil desde un ejecutor limpio con salida persistente; si pasa, recién entonces inicio la suite completa.

[2026-08-14T22:10:25+00:00] P2-nada-escribe-afuera · gate-runner · done
Cliente: El caso portátil ahora pasó en una copia temporal, sin tocar tu instalación ni configuración: 1 prueba, 132 segundos, OK.
Ingeniería: La frontera heredada funciona. El gate completo autorizado bajo el sandbox endurecido es el que decide si P2 pasa a revisión delta.

[2026-08-14T22:10:30+00:00] P2-nada-escribe-afuera · gate-runner · started
Cliente: Se inicia la validación completa bajo el aislamiento ya comprobado.
Ingeniería: Gate determinista completo: unittest, build/check, verificación y chequeo de diff; no se aprobará P2 sin resultados completos.

[2026-08-14T23:05:09+00:00] P2-nada-escribe-afuera · gate-runner · blocked
Cliente: El gate no falló, pero tampoco terminó: quedó detenido después de una prueba de instalación y se cortó de manera controlada a los 36 minutos. No lo tomo como validación.
Ingeniería: Es un bloqueo reproducible del runner endurecido, no un problema de producto. Vuelvo a la reparación para localizar el primer descendiente que queda esperando y evitar que la frontera cambie su semántica.

[2026-08-14T23:14:40+00:00] P2-nada-escribe-afuera · repair-agent · done
Cliente: La causa era una simulación incompleta: faltaba el stub de pnpm, y el instalador intentaba calentar Pi por red. Ya quedó simulado; el focal termina en 2,6 segundos.
Ingeniería: Es una corrección de fixture, no de la barrera. Se relanza el gate completo con todos los stubs necesarios; si cierra, pasa a revisión delta.

[2026-08-14T23:46:51+00:00] P2-nada-escribe-afuera · gate-runner · done
Cliente: La validación completa pasó: 1130 pruebas y todos los controles globales en verde.
Ingeniería: verify.sh confirmó la frontera endurecida y el diff limpio; el paquete pasa a revisión delta focalizada.

[2026-08-15T03:34:41+00:00] P3-gates-que-preguntan-antes · implementer · started · modelo anthropic/claude-sonnet-5 · effort medium
Cliente: Que el harness deje de esperar un minuto por una credencial que ya sabe invalida, y que un aviso informativo deje de frenar una delegacion valida.
Ingeniería: Implementer concurrente. AC-06 mueve el gate de pi antes del _run_cached preservando el parse fail-closed; AC-07 extiende el filtro de marcadores informativos de _decide_status.

[2026-08-15T03:34:41+00:00] P3-gates-que-preguntan-antes · package-reviewer · started · modelo anthropic/claude-opus-5 · effort high
Cliente: Una segunda mirada, sin haber escrito el codigo, intenta romper lo que se hizo antes de darlo por bueno.
Ingeniería: Independencia degradada segun ADR-0011: mismo proveedor, modelo distinto, contexto limpio. Declarado en la evidencia del review.

[2026-08-15T03:34:42+00:00] P3-gates-que-preguntan-antes · repair-agent · started · modelo anthropic/claude-sonnet-5 · effort medium
Cliente: Arreglar de una sola vez todo lo que la revision encontro, sin abrir frentes nuevos.
Ingeniería: Pase consolidado sobre P3-F01 a P3-F05. F06 y F07 quedan fuera de alcance y se registran como decision.

[2026-08-15T03:37:54+00:00] P4-owned-paths-matchea-directorios · implementer · started · modelo anthropic/claude-sonnet-5 · effort medium
Cliente: Que cuando un paquete declare una carpeta, el control entienda que eso incluye lo que hay adentro.
Ingeniería: Implementer concurrente. matches() suma una regla de descendencia junto al fnmatch existente, en las dos copias del script.

[2026-08-15T03:37:54+00:00] P4-owned-paths-matchea-directorios · package-reviewer · started · modelo anthropic/claude-opus-5 · effort high
Cliente: Una segunda mirada intenta romper el arreglo del control de alcance antes de darlo por bueno.
Ingeniería: Independencia degradada ADR-0011: mismo proveedor, modelo distinto, contexto limpio. El reviewer corrio mutantes y un barrido de las 27 features reales.

[2026-08-15T03:37:54+00:00] P4-owned-paths-matchea-directorios · repair-agent · started · modelo anthropic/claude-sonnet-5 · effort medium
Cliente: Arreglar de una vez lo que la revision encontro, incluido un agujero que el propio arreglo habia abierto.
Ingeniería: Pase consolidado P4-F01 a F04 y F06. F05 y F07 los resuelve el orquestador.
