# Repair ceiling: freeze 0 lines no congela techo 0

<!-- notas:auto -->
- fecha: 2026-08-20 · actor: orchestrator
- alcance: [[features/035-panel-honesto-consola-y-tips|035-panel-honesto-consola-y-tips]] · [[features/035-panel-honesto-consola-y-tips/PKG-A|PKG-A]]

## Contexto

candidate_identity.changed_lines era 0 porque freeze fue HEAD vs HEAD (trabajo uncommitted). record-repair hubiera congelado budget_lines=0 y check-repair-ceiling vs working tree fallaria el diff entero de PKG-A (476 lineas owned).

## Decisión

Se quito changed_lines del freeze (arboles intactos). ADR-0023 additive-only: sin ceiling, check-repair-ceiling es PASS. Cap efectivo de complexity high sigue 200. Repair medido por evidencia: ~28 lineas de tests + condicion has_open_findings.

## Consecuencias

check-repair-ceiling sin ceiling. MODE_BUDGETS intacto.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
