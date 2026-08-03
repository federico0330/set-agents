# Cierre parcial de audit-debt-006-p2: PR-07/08/09 saldadas por 016; PR-06/10/11 siguen diferidas

<!-- notas:auto -->
- fecha: 2026-08-03 · actor: orchestrator
- alcance: [[features/016-audit-debt-repayment|016-audit-debt-repayment]]

## Contexto

La feature 016-audit-debt-repayment llego a DONE con P1-harness-debt y P2-hygiene aceptados. El registro original de deuda es docs/notas/decisiones/2026-07-28 audit-debt-006-p2.md (6 items).

## Decisión

De los 6 hallazgos de audit-debt-006-p2: PR-07 (repair_entry autoritativo, 6 sitios + fallback), PR-08 (extraccion _apply_verification_waiver/_apply_verdicts) y PR-09 (docstring + puntero ADR-0009 D7) quedan CERRADOS por 016. PR-06 (doble contador de budget), PR-10 (forma del suite) y PR-11 (mutate sin compare-and-swap) siguen diferidos sin cambios, por decision del usuario 2026-08-02; PR-11 sigue siendo la unica invariante de atomicidad del arnes y es candidata a paquete propio futuro.

## Consecuencias

Deuda nueva registrada durante 016: P1F-01 (pop de repair_entry en cmd_transition depende de --package-id opcional), low, aceptada con fix exacto anotado, candidata a quick-fix. La limpieza de package-gate-runner.md que figuraba como deuda sin paquete en BUENOS-DIAS queda cerrada por AC-08.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
