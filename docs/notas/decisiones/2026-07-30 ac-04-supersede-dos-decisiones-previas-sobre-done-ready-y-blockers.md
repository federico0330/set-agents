# AC-04 supersede dos decisiones previas sobre done_ready() y blockers

<!-- notas:auto -->
- fecha: 2026-07-30 · actor: orchestrator
- alcance: [[features/010-spawn-provenance|010-spawn-provenance]]

## Contexto

docs/notas/decisiones/2026-07-28 una-feature-bloqueada-y-reabierta-no-puede-llegar-nunca-a-done.md y docs/notas/decisiones/2026-07-29 done-ready-does-not-filter-resolved-blockers.md ya habian nombrado este mismo gap (done_ready() trata cualquier blockers no vacio como descalificante, sin mirar resolved_at) sin repararlo.

## Decisión

AC-04 de 010-spawn-provenance lo repara: done_ready() ahora filtra por 'not b.get("resolved_at")', mismo criterio que summarize_feature() ya usaba. Una feature con todos sus blockers resueltos puede llegar a DONE; con uno sin resolver, sigue sin poder.

## Consecuencias

005-portable-harness es el sujeto real que esto desbloquea (2 blockers, los dos resueltos). La rama 'sigue bloqueando' del fix es alcanzable solo por fixture, no por ningun camino de CLI real hoy (LEGAL_TRANSITIONS[BLOCKED] = set()).
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
