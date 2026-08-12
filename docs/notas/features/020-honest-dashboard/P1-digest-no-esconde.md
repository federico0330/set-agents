# 020-honest-dashboard · P1-digest-no-esconde

<!-- notas:auto -->
## Motivo

- objetivo: Que el digest, el hub de notas y --status no escondan lo que necesita una decision humana, con un unico predicado compartido
- complejidad: medium
- paths: `ai/scripts/feature_state_lib/cli_reporting.py`, `ai/scripts/feature_state_lib/render_notes.py`, `ai/scripts/feature-state.py`, `tests/test_harness.py`, `docs/adr/0040-honest-dashboard.md`

## Tareas

- [x] Predicado compartido de feature viva + constante de umbral, consumido por los tres artefactos (AC-02) (completed) · model.py: feature_is_live, open_blocker, days_since, blocked_days, stale_days, feature_is_stale, STALE_THRESHOLD_DAYS; consumido por cmd_digest, _hub_body y cmd_status
- [x] Seccion Necesita tu decision en el digest, dias desde el ultimo blocker sin resolver (AC-01) (completed) · BUENOS-DIAS.md:6-9 verificado en vivo por el orquestador: nombra 002 (hace 18 dias) y 011 (hace 12 dias)
- [x] Marca de estancada para las vivas no bloqueadas, bloqueadas exentas (AC-03) (completed) · tope de dos menciones por feature bloqueada, verificado en el digest regenerado
- [x] blocked_days y stale_days en cmd_status desde el mismo predicado (AC-04) (completed) · cmd_status sobre 002 y 011 devuelve blocked_days 18 y 12, coherente con el digest
- [x] _hub_body deja de saltear las terminales en Que falta (AC-12) (completed) · 00 - Proyecto.md:26-27 verificado por el orquestador: 002 aparece con su bloqueo y sus 5 hallazgos abiertos
- [x] Tests que fallan en rojo contra el codigo de hoy (AC-05, AC-12) + ADR-0040 (completed) · tests/test_digest.py HonestPredicateTests + test_honest_predicate.py (21 unitarios) + 2 en test_harness.py; ADR-0040 indexado. Suite 917 -> 943

## Hallazgos

- F-01 [high] closed — 
- F-02 [medium] closed — 
- F-03 [medium] closed — 

## Recorrido

- review: repair_required (3 hallazgos)
- verificación: 0 refutados, 3 sostenidos
- repair: F-01 → 3 archivos
- repair: F-02 → 3 archivos
- repair: F-03 → 3 archivos
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `verify`: pass
- gate `build-check`: pass
- gate `diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo openai-codex/gpt-5.6-sol · effort medium · route run1_b346026cee37a6594969231ab20357de
- SPAWN-002 package-reviewer · modelo anthropic/sonnet · effort medium · route dec1_7bf90eba2bb44e6ba1be83a1ebd7bc92

context pack: `docs/specs/020-honest-dashboard/context/P1-digest-no-esconde.md`

↩ [[features/020-honest-dashboard|020-honest-dashboard]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
