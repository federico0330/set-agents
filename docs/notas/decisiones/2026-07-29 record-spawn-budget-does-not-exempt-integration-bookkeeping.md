# record-spawn cuenta la narracion de INTEGRATION contra el presupuesto de implementacion de un paquete ya aceptado

<!-- notas:auto -->
- fecha: 2026-07-29 · actor: orchestrator
- alcance: [[features/003-trusted-routing-pi-runtime|003-trusted-routing-pi-runtime]] · [[features/003-trusted-routing-pi-runtime/P1R-trusted-routing|P1R-trusted-routing]]

## Contexto

Al integrar 003-trusted-routing-pi-runtime hoy, record-spawn P1R-trusted-routing integrator disparo un bloqueo automatico (spawn budget exhausted) porque el paquete ya estaba en 16/16 spawns desde su ciclo de reparacion R1-R3 (2026-07-24/25). cmd_record_spawn (feature-state.py:1531-1541) no distingue una llamada de contabilidad/narracion en fase INTEGRATION (post PACKAGE_ACCEPTED, sin mutacion de codigo) de un spawn real de implementacion o revision -- el mismo contador y el mismo techo aplican a los dos. El bloqueo dejo al paquete en BLOCKED sin ninguna forma limpia de salir: reopen (la unica salida de BLOCKED) manda siempre a PACKAGE_PLANNING, y de ahi la unica salida legal es PACKAGE_IMPLEMENTATION, que ademas pisa el status del paquete ya aceptado con 'package_implementation' -- forzaria un ciclo de reimplementacion/revision fabricado para un paquete que no cambio una linea.

## Decisión

Se corrigio a mano el archivo de estado (ai/state/features/003-trusted-routing-pi-runtime.json), revirtiendo exactamente el evento erroneo: el blocker 'spawn budget exhausted' y el evento de historia 'block' que agrego, devolviendo phase a PACKAGE_ACCEPTED y final_state a null, revision decrementada de 78 a 77. El contador attempts.spawns no se toco porque cmd_record_spawn corta antes de incrementarlo cuando ya esta en el techo -- se mantuvo en 16, su valor real. No se uso reopen porque hubiera fabricado un ciclo de reimplementacion falso en el historial de auditoria de un paquete que genuinamente no requiere ningun cambio. Backup del JSON previo a la correccion en el scratchpad de la sesion.

## Consecuencias

Queda como deuda real para una futura reparacion del harness: (1) cmd_record_spawn deberia exceptuar spawns registrados en fase INTEGRATION (o cualquier fase posterior a PACKAGE_ACCEPTED) del presupuesto de max_spawns_per_package, que existe para acotar el costo de implementar/revisar un paquete, no para acotar cuantos integradores se documentan despues de aceptado; o alternativamente el integrador no deberia llamar record-spawn en absoluto y la narracion de INTEGRATION deberia tener su propio verbo sin presupuesto asociado. (2) reopen() siempre manda a PACKAGE_PLANNING sin importar el motivo del bloqueo -- no hay forma de recuperar un bloqueo administrativo/falso-positivo sobre un paquete ya aceptado sin fabricar un ciclo de reimplementacion o editar el JSON a mano. Los proximos integradores de features ya aceptadas deberian evitar record-spawn si el paquete esta cerca del techo, hasta que se repare esto.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
