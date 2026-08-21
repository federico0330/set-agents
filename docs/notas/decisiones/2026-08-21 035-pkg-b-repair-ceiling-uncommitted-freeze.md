# Sin techo de repair: freeze committed vs HEAD es 0 lineas

<!-- notas:auto -->
- fecha: 2026-08-21 · actor: orchestrator
- alcance: [[features/035-panel-honesto-consola-y-tips|035-panel-honesto-consola-y-tips]] · [[features/035-panel-honesto-consola-y-tips/PKG-B|PKG-B]]

## Contexto

candidate_identity.changed_lines=0 (788eb62 vs HEAD). record-repair con original=0 congela budget_lines=0 (cli_repair.py:217-220) y cualquier repair muere. Precedente PKG-A: pop changed_lines para que ADR-0023 additive-only deje repair_ceiling null.

## Decisión

Pop candidate_identity.changed_lines de PKG-B. El gate post-repair usa --changed-lines del delta reportado, no el working tree entero vs freeze.

## Consecuencias

check-repair-ceiling sin techo pasa. El delta-reviewer re-mide el diff de repair.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
