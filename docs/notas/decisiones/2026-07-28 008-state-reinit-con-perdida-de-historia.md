# Re-init forzado del estado de 008, con la historia descartada preservada como evidencia

<!-- notas:auto -->
- fecha: 2026-07-28 · actor: orchestrator
- alcance: [[features/008-dynamic-selection|008-dynamic-selection]]

## Contexto

El contrato de 008 se reescribio despues del SPEC_CHALLENGE: P1 dejo de ser quota-failover (codigo) y paso a ser uninterrupted-delegation (doctrina), y las AC pasaron de 8 a 10. El archivo de estado quedo con el paquete superado P1-quota-failover en status planned y con AC-01..AC-08. feature-state.py no tiene comando para extender acceptance_criteria (cmd_init:1197 es el unico escritor) ni para retirar un paquete (cmd_update_package:1299 es una lista blanca que no incluye owned_paths, tasks ni acceptance_criteria), y done_ready():457 exige que todo paquete este accepted, asi que P1-quota-failover habria bloqueado el cierre de 008 para siempre.

## Decisión

Se corrio init --force. Se descartan tres entradas de historia: el init original, el create-package de P1-quota-failover y el record-spawn del spec-challenger. Antes de borrar, el JSON completo se copio verbatim a docs/specs/008-dynamic-selection/evidence/state-before-reinit.json. No se hand-editeo el archivo de estado: fabricar un registro que parece autoritativo es exactamente la falla que el modelo file-first existe para evitar, y es la misma razon por la que la feature 006 no se backfillea (009-P2 AC-07).

## Consecuencias

La sustancia no se pierde: los 15 hallazgos del spec-challenger viven en el log de enmiendas de docs/specs/008-dynamic-selection/spec.md, y el JSON crudo queda en evidence/. Lo que si se pierde es la marca temporal de esos eventos en la bitacora regenerada. El paquete P1-quota-failover pasa a llamarse P1b en el spec y se recreara cuando 007 libere los archivos que reclama.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
