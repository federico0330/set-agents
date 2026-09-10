# PKG-C2 repair ceiling exceeded after unique retry

<!-- notas:auto -->
- fecha: 2026-09-10 · actor: orchestrator
- alcance: [[features/049-identidad-honesta-modelos|049-identidad-honesta-modelos]] · [[features/049-identidad-honesta-modelos/PKG-C2|PKG-C2]]

## Contexto

Unique repair-agent retry produced REPAIRED_C2_REF=726017d7c7297b9d87a75317dbe025db99489296 on NEW_FOUNDATION_REF=3878fb0d. Independent numstat vs foundation = 315 lines. Ceiling froze at budget_lines=100 (medium, original 2703). check-repair-ceiling FAIL; record-gate repair-ceiling fail blocked the feature per ADR-0023.

## Decisión

HUMAN_DECISION_REQUIRED: do not open a second repair cycle silently. Options require explicit user authorization: (a) waive/raise the frozen repair ceiling for this measured 315-line delta and continue delta review; (b) authorize a rescope/respec that shrinks the repair surface; (c) accept BLOCKED and stop 049 C2. No delta review, testing, accept, or PKG-D2 until that decision.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
