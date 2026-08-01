# P2-discovered-inventory se separa de 008 y pasa a ser la feature 012, mismo patrón que 010/006

<!-- notas:auto -->
- fecha: 2026-07-30 · actor: orchestrator
- alcance: [[features/008-dynamic-selection|008-dynamic-selection]]

## Contexto

acceptance_criteria de 008 en ai/state/features/008-dynamic-selection.json solo tiene AC-01..AC-10 (las de P1-uninterrupted-delegation, ya accepted). cmd_init es el unico escritor de acceptance_criteria; sumar AC-11..AC-22 (el contrato de P2 ya verificado en 3 rondas de spec-challenger, veredicto ready_for_user_approval) exige init --force, que reconstruye el archivo de estado desde base_state y destruiria el historial real de P1 (spawns, panel de revision, aceptacion) -- no solo historia de planning descartable como en re-inits anteriores (008-P1 original, 009-P1, 007-P0). Es el mismo bloqueo arquitectonico G-01 que forzo a que 006-P3.1 se separara en la feature 010 esta misma sesion.

## Decisión

Mismo patron que 010: P2-discovered-inventory se escribe como una feature nueva y separada, 012-discovered-inventory, con su propio spec.md, sus propios AC-01..AC-12 (renumerados desde AC-11..AC-22), init propio y ciclo de paquete propio. docs/specs/008-dynamic-selection/spec.md revierte su seccion P2 al parrafo original sin ACs mas un puntero a 012, preservando el estado real de 008 (P1 accepted, P1b deferred, P3 scoped) sin afirmar contrato tracked que el archivo de estado de 008 no tiene. La correccion inline de P1b (F-16, citas store.py/service.py) y la nota de costo/context sondeable pero fuera de alcance (F-18) se preservan en 008/spec.md -- son del mismo tipo que las correcciones AC-05/AC-10 que 008 ya documenta como 'recorded inline, not in a separate log', no requieren re-init.

## Consecuencias

012-discovered-inventory se inicializa con hash propio sobre su spec.md nuevo. 008 sigue en PACKAGE_ACCEPTED con 1/1 paquete, sin tocar su approved_spec.hash mas alla de las correcciones inline ya precedentes. El campo subscription/metered que P3 de 008 necesita leer ahora vive en 012's AC-XX, no en 008-P2 -- se actualiza la referencia cruzada en la seccion P3 de 008/spec.md.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
