# Federico autoriza 2 spawns extra en JSON, no MODE_BUDGETS ni CLI reopen

<!-- notas:auto -->
- fecha: 2026-08-20 · actor: orchestrator
- alcance: [[features/035-panel-honesto-consola-y-tips|035-panel-honesto-consola-y-tips]] · [[features/035-panel-honesto-consola-y-tips/PKG-A|PKG-A]]

## Contexto

PKG-A 8/8. Tres medium upheld. CLI reopen (cli_lifecycle.py:610) manda PACKAGE_PLANNING y resetea attempts.spawns a 0, lo que choca SPAWN-001 ya existente (feature-state.py:471-475). MODE_BUDGETS.scoped sigue 8 en model.py:125.

## Decisión

Precedente 003: el harness no tiene verbo de presupuesto. data.budgets.max_spawns_per_package 8->10 autorizado por federico 2026-08-20 para repair-agent y delta-reviewer. Constante MODE_BUDGETS no se toca (AC-A.8).

## Consecuencias

record-spawn 9/10 repair-agent, luego 10/10 delta-reviewer. check-repair-ceiling default vs freeze changed_lines=0 mediria todo el working tree; el gate post-repair usa --changed-lines del delta de repair, cap 200 complexity high.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
