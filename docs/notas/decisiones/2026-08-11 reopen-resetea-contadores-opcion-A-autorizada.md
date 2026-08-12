# Federico autorizo la opcion A: reopen resetea el contador cuyo agotamiento produjo el blocker

<!-- notas:auto -->
- fecha: 2026-08-11 · actor: orchestrator
- alcance: [[features/019-harness-evolution|019-harness-evolution]] · [[features/019-harness-evolution/P5-tools-discovery|P5-tools-discovery]]

## Contexto

Blocker registrado en el slug reopen-no-resetea-el-contador-de-verificacion: P5 quedo estructuralmente inaceptable con el trabajo hecho, porque reopen limpia el blocker pero deja attempts['verifications'] armado y require_verified guarda las dos puertas de salida de un finding medium. Se plantearon tres opciones; Federico eligio A (arreglar el harness) sobre B (reset a mano registrado como bypass) y C (supersede-package).

## Decisión

Se arregla el harness. Criterio de diseno fijado por el orquestador: el reset es DIRIGIDO, no general -- reopen resetea unicamente el contador cuyo agotamiento produjo el blocker que esta resolviendo, nunca todos los budgets, porque un reopen que limpia spawns, gate_failures, deep_review_cycles y repair_batches de una convierte el mecanismo de recuperacion en una via para saltear todas las protecciones de runaway a la vez. Y la asociacion blocker->contador se persiste ESTRUCTURADA en el blocker (block_with_reason recibe la clave del contador), no se infiere con un match sobre el texto de la razon: inferir politica de una cadena en prosa es el mismo error de forma que la nota SEC-001 de coord_policy documenta como caro. El orquestador NO escribe el arreglo: es el mismo actor que agoto el presupuesto, asi que lo delega a un agente mutador fresco.

## Consecuencias

Toca ai/scripts/feature_state_lib/{cli_lifecycle,cli_review,cli_repair}.py y feature-state.py, con copias byte-identicas en los 4 arboles de Global/ y en PROYECTO/ que exigen ./build.sh. Es el modulo estado, ownership de P3 (aceptado): excepcion de ownership autorizada por Federico al elegir A. Lleva ADR-0039 porque extiende el contrato de reopen, y test de regresion del ciclo completo agotar->bloquear->reabrir->verificar.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
