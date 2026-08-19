# 033-pkg6-dos-despachos-extra-autorizados

<!-- notas:auto -->
- fecha: 2026-08-19 · actor: orchestrator
- alcance: [[features/033-menos-espera-menos-cuota|033-menos-espera-menos-cuota]] · [[features/033-menos-espera-menos-cuota/PKG-6|PKG-6]]

## Contexto

Federico autorizo dos despachos extra para cerrar PKG-6 (repair + delta). El techo scoped en codigo (MODE_BUDGETS) no se toca. record-spawn del noveno pondria la feature en BLOCKED y reopen resetearia el contador y la fase a PACKAGE_PLANNING, rompiendo el ciclo.

## Decisión

Se despacha repair-agent y despues delta-reviewer sin record-spawn. La excepcion queda en este log, no en model.py. El contador del paquete sigue en 8/8.

## Consecuencias

Section 2 no vera estos dos roles. El techo scoped en codigo sigue en 8. PKG-6 puede cerrar.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
