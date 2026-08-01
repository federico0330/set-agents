# El registro de la 007 se reconcilia con acta antes de abrir P1

<!-- notas:auto -->
- fecha: 2026-07-29 · actor: orchestrator
- alcance: [[features/007-quota-visibility|007-quota-visibility]] · [[features/007-quota-visibility/P1-schema-normalize|P1-schema-normalize]]

## Contexto

Medido hoy sobre ai/state/features/007-quota-visibility.json en revision 29: (1) P0-role-affinity quedo en status repair_required con 6 hallazgos abiertos y un panel cerrado, sobre codigo que ya fue revertido en el arbol -- git status sobre ai/catalogs/routes.v1.toml y tests/test_routing.py esta limpio y el catalogo tiene las 6 filas de la linea base, no las 12 que P0 produjo; done_ready:481-496 exige que TODO paquete este accepted, asi que P0 bloquea DONE para siempre. (2) El blocker de P0 tiene resolved_at, resolved_by user y resolved_reason, pero sigue en el array, y done_ready:490-491 chequea la verdad de la lista y no si algun blocker sigue abierto: la 007 es la primera feature viva que pisa el defecto registrado en una-feature-bloqueada-y-reabierta-no-puede-llegar-nunca-a-done. (3) El hash del spec derivo: el estado afirma bb15ad8ada1be91159ea0c53889967c099fe5cf7cd9cfb07ef0b66d4291f0ce5 y el disco tiene 4b4ec109dff77ae15e4cd08fda8506735356b746edb8f0a65b26f20e89263d03, o sea el registro afirma la aprobacion de bytes que ya no existen -- una de las cuatro derivas que cuatro-archivos-de-estado-afirman-un-spec-que-ya-no-existe registro como deuda. (4) P1-schema-normalize declara owned_paths incompletos: le faltan el archivo de estado, STATUS.md, los dos .jsonl, docs/notas y docs/specs de la propia feature.

## Decisión

Re-init con acta, decidido con el usuario, mismo procedimiento que 008-P1 y 009-P1. El JSON integro se volco a docs/specs/007-quota-visibility/evidence/state-before-reinit.json antes de tocar nada: 30 entradas de historia, 4 paquetes, 22 AC. Se enmienda spec.md retirando la seccion P0 y sus AC-20/21/22 con un puntero -- su alcance ya fue reasignado a la feature 008 por la decision p0-role-affinity-reverted -- y NO se edita el contrato de la 008, que es de otra feature con paquetes abiertos. Se re-inicializa con AC-01..AC-19 y se recrean los tres paquetes con owned_paths correctos. La alternativa, parchar, no existe: cmd_update_package es una lista blanca que no puede cambiar status, owned_paths, tasks ni acceptance_criteria, y no hay estado deferred ni superseded -- el defecto ya registrado en estado-no-sabe-amendar-un-contrato-revisado.

## Consecuencias

Se descartan 30 entradas de historia. Nada de sustancia se pierde: el panel de P0 y sus 6 hallazgos son sobre codigo que ya no existe en el arbol, y los cinco hallazgos del architect que nunca entraron al registro del paquete ya viven en p0-architect-findings-outside-package-record. La 007 vuelve a poder llegar a DONE. El re-init esquiva el bug de done_ready para esta feature; NO lo arregla -- sigue siendo una linea (filtrar por blockers sin resolved_at, como ya hace summarize_feature) y sigue siendo deuda para cualquier otra feature que se bloquee y se reabra. Y queda dicho que esta es la tercera vez que un paquete nace teniendo que re-inicializar la feature entera para poder trabajar: 008, 009 y ahora 007.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
