# P1F-01 aceptado como deuda low: el pop de repair_entry depende del --package-id opcional

<!-- notas:auto -->
- fecha: 2026-08-02 · actor: orchestrator
- alcance: [[features/016-audit-debt-repayment|016-audit-debt-repayment]] · [[features/016-audit-debt-repayment/P1-harness-debt|P1-harness-debt]]

## Contexto

RP-P1-01 (pass) encontro que el pop de repair_entry en cmd_transition:2027 esta bajo if args.package_id, y --package-id es opcional en transition. Un transition PACKAGE_REPAIR sin package-id saltea el pop; con refute-all previo + late finding, un repair_entry rancio auto-escapa donde la inferencia vieja respondia False. La convencion del arnes siempre pasa --package-id en transiciones de fase de paquete, y el danio es saltear una pasada de repair vacia.

## Decisión

Se acepta como deuda registrada (no bloquea la aceptacion del paquete, verdict pass del panel). Fix exacto anotado: hoist del pop resolviendo via package_by_id con fallback a current_package_id, en try/except StateError, + variante del test omitiendo --package-id. Candidata a quick-fix en la proxima pasada.

## Consecuencias

Mientras tanto, toda transicion manual a PACKAGE_REPAIR debe llevar --package-id (ya es la convencion). El test existente cubre el caso con package-id.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
