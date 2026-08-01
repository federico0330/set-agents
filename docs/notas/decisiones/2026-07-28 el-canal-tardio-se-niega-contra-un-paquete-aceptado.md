# Un hallazgo que llega despues de aceptado el paquete se rechaza en vez de registrarse

<!-- notas:auto -->
- fecha: 2026-07-28 · actor: orchestrator
- alcance: [[features/009-self-application|009-self-application]] · [[features/009-self-application/P3-panel-integrity|P3-panel-integrity]]

## Contexto

AC-10 crea record-late-review para que una revision independiente que vuelve despues de cerrado el panel aterrice en el registro del paquete. Queda un caso que el comando no puede servir: el paquete ya aceptado. package_accept_ready ya corrio, LEGAL_TRANSITIONS['PACKAGE_ACCEPTED'] no tiene arista a PACKAGE_REPAIR y cmd_reopen solo aplica desde BLOCKED, asi que un hallazgo registrado ahi no lo lee nadie nunca mas.

## Decisión

Se rechaza con un error que nombra el hecho de que no hay vuelta. Decidido con el usuario. La alternativa -- aceptarlo y sacar el paquete de accepted -- es redisenar el ciclo de review, que el spec excluye explicitamente, y toca presupuesto de review, integracion e integrated. Registrarlo sin consecuencia produciria un paquete que muestra un hallazgo bloqueante abierto y estado accepted al mismo tiempo, que es mentira peor que el rechazo.

## Consecuencias

La refutacion adversarial de F-04 mostro que el mensaje no es un callejon sin salida como se temia: block es un verbo real y done_ready se niega a llegar a DONE mientras haya blockers, o sea el hallazgo frena la feature hasta que un humano autorice el reopen, que es la escalacion HUMAN_DECISION_REQUIRED que la doctrina prescribe. Lo que falta es contabilidad: por ese camino el hallazgo no recibe severidad, verificacion ni reparacion. Cerrarlo de verdad requiere una arista de reapertura de paquete, que es otro paquete.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
