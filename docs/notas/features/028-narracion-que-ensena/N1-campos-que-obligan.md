# 028-narracion-que-ensena · N1-campos-que-obligan

<!-- notas:auto -->
## Motivo

- objetivo: Agregar campos y guardas de narración exigible en log-narrative
- paths: `ai/scripts/narration_lint.py`, `ai/scripts/feature-state.py`, `ai/scripts/feature_state_lib/cli_reporting.py`, `tests/test_narracion_contrato.py`

## Tareas

- [x] wire-guard-cli (completed) · focal tests green
- [x] cover-attack-corpus (completed) · focal tests green

## Hallazgos

- N1-F01 [high] closed — correctness
- N1-F02 [high] closed — process
- N1-F03 [medium] closed — missing

## Recorrido

- review: repair_required (3 hallazgos)
- verificación: 0 refutados, 3 sostenidos
- repair: N1-F01, N1-F02, N1-F03 → 1 archivos
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `verify`: pass

## Spawns

- SPAWN-001 package-reviewer · modelo anthropic/sonnet

↩ [[features/028-narracion-que-ensena|028-narracion-que-ensena]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
