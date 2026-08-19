# PKG-B waiver del skill de triage que ya cambio el lote anterior

<!-- notas:auto -->
- fecha: 2026-08-19 · actor: orchestrator
- alcance: [[features/034-cuota-organica-y-writer-barato|034-cuota-organica-y-writer-barato]] · [[features/034-cuota-organica-y-writer-barato/PKG-B|PKG-B]]

## Contexto

check-owned-paths vs HEAD sigue viendo el skill de triage sucio porque el lote A lo cambio y no hay commit. PKG-B no lo edito.

## Decisión

Exception puntual de Global/_canonical/skills/request-triage/SKILL.md como suciedad preexistente del lote A, no como ownership de B.

## Consecuencias

P001 se reintenta. El skill sigue siendo de A.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
