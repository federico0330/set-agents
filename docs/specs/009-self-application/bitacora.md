# Bitácora — 009-self-application

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-17T23:09:09+00:00

[2026-07-28T16:26:03+00:00] spec-challenger · started
Cliente: Antes de tocar nada, mando a un revisor independiente a buscarle agujeros al contrato de la feature 009. Es el único de los contratos que nunca pasó por esa instancia, y justo es el contrato que dice que el arnés no se aplica sus propias reglas. Ya le encontré yo un error de diagnóstico sin buscarlo, así que hay motivo para mirar el resto.
Ingeniería: Contract 1.0.0 (hash 70954fe7…) went from init straight to PACKAGE_PLANNING with no SPEC_CHALLENGE recorded; spec.md:3 says 'Not yet challenged'. Spawning a read-only spec-challenger on a different model than the writer (clean-context independence, ADR-0011). It is fed the AC-02 false-premise finding and the AC-03 dangling-path measurement as known input so its budget goes to what I did not see. … _(truncado al render)_

[2026-07-28T16:42:00+00:00] spec-challenger · done
Cliente: El revisor independiente encontró once problemas en el contrato, cinco de ellos serios, y verifiqué a mano los tres que cambian decisiones. El mejor es una ironía: la feature que existe para que no se pueda entregar sin dejar registro, había sido abierta ella misma declarando una aprobación que nunca ocurrió. Vos decidiste sumar dos criterios nuevos al contrato y ahora lo corrijo antes de escribi… _(truncado al render)_
Ingeniería: spec-challenger returned revision_required with 11 findings (F-01..F-11, 5 blockers). Independently verified before acceptance: F-03 (fnmatch('knowledge/security.md','knowledge') is False, so P1's declared ownership pattern matches nothing inside the directory), F-02 (docs/specs/003-trusted-routing-pi-runtime/design.md:455 exists and P3 does not own it), F-07 (005-portable-harness holds only P1 i… _(truncado al render)_

[2026-07-28T16:56:51+00:00] P1-knowledge-home · package-reviewer · started
Cliente: Mando el primero de dos revisores independientes a auditar el paquete entero. No escribió nada de esto y corre en otro modelo, así que lo mira sin los sesgos del que lo hizo.
Ingeniería: Panel RP-01, member 1 of 2, dispatched concurrently per the 006-P1 rule. Sonnet 5 against an Opus 5 writer: clean context is the primary independence guarantee (ADR-0011). Read-only, never patches.

[2026-07-28T16:56:52+00:00] P1-knowledge-home · architect · started
Cliente: El segundo revisor mira otra cosa: no si está bien hecho, sino si estaba bien pensado. Si el domicilio nuevo es el correcto y si el guard nuevo va a envejecer bien o va a molestar hasta que alguien lo apague.
Ingeniería: Panel RP-01, member 2 of 2, same batch. Distinct lens from the package-reviewer: design durability of the two-tier home, the waiver mechanism's failure mode, and the blast radius of a prose ratchet over every canonical prompt.

[2026-07-28T17:10:08+00:00] P1-knowledge-home · finding-verifier · started
Cliente: Antes de arreglar nada, mando un tercer revisor a tratar de tumbar los ocho hallazgos. Su trabajo no es confirmarlos: es demostrar que están mal. Lo que sobreviva a eso es lo que arreglo.
Ingeniería: Third distinct model in the chain (Fable 5) after an Opus 5 writer and two Sonnet 5 reviewers, so the refutation is independent of both the author and the finding authors. ADR-0009 requires a verified_verdict before record-repair will accept a critical/high/medium finding.

[2026-07-28T17:27:10+00:00] P1-knowledge-home · delta-reviewer · started
Cliente: Ultimo control: un revisor mira solamente lo que cambie al reparar, no el paquete entero. Es la pasada que verifica que arreglar no haya roto otra cosa.
Ingeniería: Delta review of repair batch 1 closing F-02, F-03, F-04. Sonnet 5, clean context, read-only. Scope is the delta: ai/scripts/check-canonical-paths.py (new), verify.sh, save_memory.py, tests/test_harness.py.

[2026-07-28T17:38:31+00:00] P1-knowledge-home · orchestrator · done
Cliente: El arnes ya tiene la memoria que les daba a todos sus proyectos y a si mismo no. Diez de sus propios prompts mandaban a leer una carpeta que no existia, y como la orden decia leela si existe, no fallaba nunca: simplemente no pasaba nada. Ahora existe, y ademas hay un control que rompe la verificacion si cualquier instruccion futura vuelve a apuntar a un lugar inexistente. Ese mismo control ya enc… _(truncado al render)_
Ingeniería: P1-knowledge-home accepted. The cross-project tier moved from the root knowledge/ to docs/ai/knowledge/_global/ with its single consumer repointed, and the harness gained the project tier it never had, seeded verbatim from the PROYECTO template. The AC-03 guard shipped as ai/scripts/check-canonical-paths.py, proven failing with count=27 before the fix and CANONICAL_PATHS_OK after, and it repaired… _(truncado al render)_

[2026-07-28T18:06:50+00:00] P2-state-machine-required · started
Cliente: Arranco el segundo paquete de la 009. El arnes exige que toda feature quede registrada en su maquina de estados y no lo controla en ningun lado: la feature 006 se entrego entera - codigo, revisiones, 12 commits, 209 tests verdes - y no figura en el registro, ni va a figurar nunca. Este paquete hace que eso sea un error visible y no un silencio, y de paso cierra el agujero del otro lado: hoy el ar… _(truncado al render)_
Ingeniería: P2-state-machine-required, AC-05/AC-06/AC-07/AC-13. Tres decisiones cerradas con el usuario: el gate vive solo en verify.sh (lo unico que corre el CI en Linux y macOS; .git/hooks no se versiona, asi que un pre-commit es invisible al CI y a un clon nuevo), la senal de entrega son los commits que nombran feature+paquete (medido: 006 no dejo evidence/, ni context/, ni bitacora.md, asi que un gate de… _(truncado al render)_

[2026-07-28T19:08:40+00:00] P2-state-machine-required · package-reviewer · started
Cliente: Mando el primero de dos revisores independientes a auditar el paquete entero. No escribio nada de esto y corre en otro modelo, asi que lo mira sin los sesgos del que lo hizo.
Ingeniería: Panel RP-01, miembro 1 de 2, despachado concurrentemente por la regla de 006-P1. Sonnet 5 contra un escritor Opus 5: contexto limpio como garantia primaria de independencia (ADR-0011). Read-only, nunca parchea.

[2026-07-28T19:08:40+00:00] P2-state-machine-required · architect · started
Cliente: El segundo revisor mira otra cosa: no si esta bien hecho, sino si estaba bien pensado. Si usar los mensajes de commit como senal de entrega es una base solida o algo que se va a romper el dia que alguien escriba un commit distinto.
Ingeniería: Panel RP-01, miembro 2 de 2, mismo lote. Lente distinta a la del package-reviewer: durabilidad de la senal de historia, el costo de volver --approved-by requerido en un CLI que ya documentan tres runtimes, y el radio de un gate nuevo en verify.sh que corre para todos.

[2026-07-28T19:09:40+00:00] P2-state-machine-required · started
Cliente: Los dos revisores estan trabajando en paralelo sobre el paquete terminado. El primero audita si esta bien hecho; el segundo, si estaba bien pensado - sobre todo si apoyarse en los mensajes de commit como senal de entrega es una base solida o algo que se rompe el dia que alguien escriba un commit distinto.
Ingeniería: Panel RP-01 despachado concurrentemente, ambos Sonnet 5 con contexto limpio contra un escritor Opus 5. Independencia degradada respecto de ADR-0011: cross-provider no disponible, se preserva contexto limpio y modelo distinto. Seis gates verdes antes de abrir el panel: 216 tests OK sin skips, VERIFY_PASS, FEATURE_STATE_OK, CANONICAL_PATHS_OK, SELF_SCAFFOLD_SYNC_OK files=2, OWNERSHIP_PASS sobre 29 … _(truncado al render)_

[2026-07-28T19:18:12+00:00] P2-state-machine-required · architect · done
Cliente: Volvio el revisor de diseno: pide reparacion por una sola cosa, y es buena. El gate nuevo reconoce una entrega por como esta escrito el mensaje del commit, y esa convencion no esta escrita en ninguna parte: se aprende mirando el historial. El dia que alguien commitee distinto, el gate se queda callado y la entrega pasa igual, pero ahora con la tranquilidad falsa de que hay un control.
Ingeniería: Panel RP-01 miembro 2, veredicto repair_required, 5 hallazgos, 1 high. F-02 verificado por mi antes de aceptarlo: los tres greps de convencion de commits sobre Global/_canonical, PROYECTO/prompt.md y docs/ devuelven vacio, y ningun prompt canonico menciona 'git commit'. Los otros cuatro son observaciones: acoplamiento del test de portabilidad al historial real, --approved-by como texto libre sin … _(truncado al render)_

[2026-07-28T19:19:40+00:00] P2-state-machine-required · finding-verifier · started
Cliente: Antes de arreglar nada, mando un tercer revisor a tratar de tumbar los nueve hallazgos. Su trabajo no es confirmarlos: es demostrar que estan mal. Lo que sobreviva a eso es lo que arreglo.
Ingeniería: Tercer modelo distinto de la cadena (Fable 5) despues de un escritor Opus 5 y dos revisores Sonnet 5, asi que la refutacion es independiente del autor y de los autores de los hallazgos. ADR-0009 exige verified_verdict antes de que record-repair acepte un hallazgo critical/high/medium.

[2026-07-28T21:12:11+00:00] P2-state-machine-required · delta-reviewer · started
Cliente: Ultimo control: un revisor mira solamente lo que cambie al reparar, no el paquete entero. Es la pasada que verifica que arreglar no haya roto otra cosa.
Ingeniería: Delta review del lote de reparacion 1, cierra F-01, F-02, F-03 y F-08. Sonnet 5, contexto limpio, read-only. Alcance: ai/scripts/check-feature-state.py, Global/_canonical/commands/feature-batch.md y sus generados, tests/test_harness.py.

[2026-07-28T21:19:37+00:00] P2-state-machine-required · done
Cliente: 009-P2 entregado y aceptado. Entregar una feature por fuera del registro del arnes ahora rompe la verificacion en vez de pasar en silencio, y abrir el expediente de una feature exige el hash real del documento que se aprobo, no una palabra cualquiera. La revision encontro cuatro problemas reales y los cuatro estan arreglados; cinco mas cayeron al probarse que no eran ciertos.
Ingeniería: PACKAGE_ACCEPTED. 4 spawns de 12, 1 ciclo de review de 2, 1 lote de reparacion, 1 tanda de verificacion sobre 9 hallazgos: 4 sostenidos y reparados (F-01 case-sensitivity, F-02 convencion sin declarar, F-03 falso positivo en clon shallow, F-08 token de paquete sin anclar), 5 refutados con artefacto. 217 tests OK sin skips (base 214). Gates: verify, self-scaffold-sync, whitespace, ownership, featu… _(truncado al render)_

[2026-07-28T21:53:52+00:00] P3-panel-integrity · started
Cliente: Arrancamos el ultimo paquete de la feature 009. El arnes se revisa a si mismo con un panel de revisores, y ese panel tiene tres agujeros que aparecieron usandolo de verdad, no leyendolo: se puede abrir un panel sin decir quien revisa (y el desajuste recien se descubre despues de haber pagado el revisor), corregirlo devuelve 'listo' sin corregir nada, y un revisor independiente que llega tarde no … _(truncado al render)_
Ingeniería: Paquete P3-panel-integrity, AC-08/09/10/11. Nueve excepciones de ownership registradas antes de tocar nada (cinco prompts canonicos, los tres arboles regenerados de Global/ y PROYECTO/prompt.md). La exploracion encontro algo que el contrato no sabia: un reintento de start-review-panel con el mismo --event-id y sin --panel-id mintea RP-02 en vez de colisionar, quema el segundo y ultimo ciclo de re… _(truncado al render)_

[2026-07-28T22:12:24+00:00] P3-panel-integrity · package-reviewer · started
Cliente: Le pedimos a un revisor independiente, con otro modelo y sin ver como se escribio el codigo, que trate de romper lo que acabamos de construir. Es la regla de la casa: quien implementa nunca aprueba su propio trabajo.
Ingeniería: Panel RP-01, miembro 1 de 2, declarado en la llamada de apertura con --role (que ahora es obligatorio, gracias a este mismo paquete). Sonnet 5, contexto limpio, read-only. Foco: el cortocircuito de replay por event-id, los rechazos de record-late-review, la clave nueva late_reviews contra nueve archivos de estado que la preceden, y si los 16 tests fallan de verdad sobre el arbol previo.

[2026-07-28T22:12:24+00:00] P3-panel-integrity · architect · started
Cliente: El segundo revisor mira otra cosa: no si el codigo anda, sino si el conjunto tiene sentido y si lo que los manuales prometen es lo que el sistema hace.
Ingeniería: Panel RP-01, miembro 2 de 2, concurrente con el package-reviewer. Sonnet 5, contexto limpio, read-only. Es el mismo rol cuyos cinco hallazgos, en 007-P0, no tuvieron canal -- que es la razon por la que existe AC-10.

[2026-07-28T22:36:31+00:00] P3-panel-integrity · finding-verifier · started
Cliente: Antes de arreglar nada, un tercer revisor con la consigna invertida: su trabajo es matar cada hallazgo, no confirmarlo. Lo que sobrevive a eso es lo que se repara. Sirve para no gastar cambios de codigo en problemas que no existen.
Ingeniería: Fable 5, cuarto modelo distinto de la cadena tras un escritor en Opus 5 y dos revisores en Sonnet 5. Read-only. Los cuatro hallazgos en un solo lote. Ojo con F-01 y F-02: el patron raiz preexiste en record_event y en record-subreview, asi que la pregunta real no es si el defecto existe sino si este paquete lo empeoro o solo lo heredo.

[2026-07-28T22:51:48+00:00] P3-panel-integrity · delta-reviewer · started
Cliente: Ultimo control: un revisor nuevo mira solo lo que se cambio para arreglar los tres problemas, no el paquete entero. Confirma que se arreglaron de verdad y que el arreglo no rompio otra cosa.
Ingeniería: Sonnet 5, contexto limpio, read-only, alcance limitado a los cuatro archivos del lote. Foco: si replayed() unifico bien las dos definiciones que antes podian discrepar, si blacklistear source_role rompe algun ingreso legitimo, y si los cuatro tests de reparacion fallan de verdad sobre el arbol previo a la reparacion.

[2026-07-28T23:21:56+00:00] P3-panel-integrity · done
Cliente: Cerrado. Ahora no se puede abrir una revision sin decir quien revisa, intentar corregirla a medias falla en vez de mentir que funciono, se puede sumar un especialista a mitad de camino dejando escrito por que, y un revisor que llega tarde tiene por fin donde entregar lo que encontro -- con la aceptacion del paquete negandose mientras eso siga abierto. La revision encontro cinco problemas y tres e… _(truncado al render)_
Ingeniería: P3 aceptado. 238 tests (base 217, +21), ninguno skipeado, VERIFY_PASS, SELF_SCAFFOLD_SYNC_OK files=2, OWNERSHIP_PASS sobre 130 archivos. Cinco hallazgos: cuatro sostenidos y reparados, uno refutado con evidencia. Un solo ciclo de review profundo con panel de dos miembros concurrentes, dos lotes de reparacion, dos delta reviews. Cadena de cuatro modelos: escritor Opus 5, dos revisores Sonnet 5, re… _(truncado al render)_

[2026-07-29T16:55:25+00:00] P3-panel-integrity · integrator · started
Cliente: Antes de cerrar del todo esta parte del arnes (la que hace que el sistema se aplique sus propias reglas), un integrador revisa que los tres paquetes entregados funcionen juntos y no dejen nada suelto.
Ingeniería: Integracion de 009-self-application: verify.sh y build.sh --check ya corrieron en verde (284 tests, SELF_SCAFFOLD_SYNC_OK) a nivel orquestador; el integrador confirma que P1+P2+P3 juntos siguen satisfaciendo el contrato 1.1.0 (13 ACs) y consolida evidencia en docs/specs/009-self-application/evidence/.
