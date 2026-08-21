# Techo JSON vuelve a 8 al cerrar PKG-A

<!-- notas:auto -->
- fecha: 2026-08-20 · actor: orchestrator
- alcance: [[features/035-panel-honesto-consola-y-tips|035-panel-honesto-consola-y-tips]] · [[features/035-panel-honesto-consola-y-tips/PKG-A|PKG-A]]

## Contexto

federico autorizo data.budgets.max_spawns_per_package 8->10 solo para repair-agent y delta-reviewer de PKG-A. MODE_BUDGETS.scoped sigue 8. PKG-A accepted 10/10. PKG-B y PKG-C no heredan el extra.

## Decisión

Revertir data.budgets.max_spawns_per_package 10->8 en el JSON de la feature, constante MODE_BUDGETS intacta. Autorizacion era solo el cierre de A.

## Consecuencias

PKG-B y PKG-C arrancan 0/8. Chocar el techo otra vez es HUMAN_DECISION_REQUIRED, no otro bump.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
