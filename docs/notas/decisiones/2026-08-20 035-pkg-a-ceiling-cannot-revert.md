# No se puede bajar el JSON a 8: PKG-A ya gasto 10

<!-- notas:auto -->
- fecha: 2026-08-20 · actor: orchestrator
- alcance: [[features/035-panel-honesto-consola-y-tips|035-panel-honesto-consola-y-tips]] · [[features/035-panel-honesto-consola-y-tips/PKG-A|PKG-A]]

## Contexto

fail_if_invalid en model.py:499 rechaza el state file si algun paquete tiene attempts.spawns mayor al techo. PKG-A tiene 10. Bajar a 8 dejo la feature inmutable (update-package y transition fallaron).

## Decisión

Restaurar data.budgets.max_spawns_per_package a 10. MODE_BUDGETS.scoped sigue 8. PKG-B se planifica a 8 despachos por disciplina, no porque el JSON lo corte. Mentir attempts.spawns de A esta prohibido.

## Consecuencias

El JSON no puede volver a 8 hasta que este feature cierre. Chocar 8 en B es decision humana aunque la maquina deje pasar hasta 10.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
