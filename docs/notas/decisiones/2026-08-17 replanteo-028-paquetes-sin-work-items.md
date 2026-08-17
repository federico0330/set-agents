# Los tres paquetes de 028 se replantean porque fueron creados sin work items

<!-- notas:auto -->
- fecha: 2026-08-17 · actor: orchestrator
- alcance: [[features/028-narracion-que-ensena|028-narracion-que-ensena]]

## Contexto

Los tres paquetes de 028 (N1, N2, N3b) figuraban 'planned' con cero tasks. model.package_review_ready exige tasks_complete (ai/scripts/feature_state_lib/model.py:481-482: bool(tasks) AND todas completed) e integrated, asi que el motor niega la transicion a PACKAGE_REVIEW con 'package must be integrated locally'. create-package no-opea sobre un package_id existente (cli_lifecycle.py:307-308) y update-package no tiene --task, asi que no hay forma de agregarles work items. record-late-review tampoco aplica: exige un panel cerrado previo.

## Decisión

Se retiran los tres registros malformados con supersede-package, declarando en --reason el motivo REAL (creados sin work items, no una enmienda de alcance) y se recrean con los mismos acceptance criteria, sus work items reales y el diff_ref con SHA. No se edita el JSON a mano ni se declara una enmienda de alcance que no ocurrio.

## Consecuencias

Las notas de 028 van a mostrar tres paquetes superseded ademas de los tres vivos. A cambio el registro dice la verdad: que trabajo se hizo, quien lo reviso y con que evidencia. Queda expuesta una carencia del harness: un paquete creado malformado no tiene verbo de correccion que no sea retirarlo.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
