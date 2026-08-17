# 025-consola-minima-y-flexible · D2-trabajo-visible

<!-- notas:auto -->
## Motivo

- objetivo: Que se vea que el harness esta trabajando, sin romper pipes ni CI
- complejidad: small
- paths: `ai/scripts/tui.py`, `ai/scripts/set_agents_app.py`, `tests`
- depende de: D1-superficie-humana

## Tareas

- [x] Spinner o progreso para todo lo que tarde mas de 300 ms (AC-04) (completed) · D2-gates-runtime-qa.md: TTY, NO_COLOR y línea final; 67 TuiTests pass.
- [x] Degradacion sin TTY, con NO_COLOR y en pipes; nunca unico indicador de estado (AC-05) (completed) · D2-gates-runtime-qa.md: streams separados, stdout JSON puro y fallback estático pass.

## Hallazgos

- D2-F01 [high] closed — correctness
- D2-F02 [medium] closed — correctness
- D2-DR01 [high] closed — correctness
- D2-DR02 [low] closed — testing

## Recorrido

- review: repair_required (2 hallazgos)
- verificación: 0 refutados, 2 sostenidos
- verificación: 0 refutados, 2 sostenidos
- repair: D2-F01, D2-F02 → 4 archivos
- repair: D2-F01, D2-DR01, D2-DR02 → 5 archivos
- delta review: repair_required
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `d2-tui-tests`: pass
- gate `d2-menu-ui`: pass
- gate `d2-route-doctor`: pass

## Spawns

- SPAWN-001 gate-runner · modelo openai-codex/gpt-5.6-luna · effort low · route MODEL_STATIC_FALLBACK
- SPAWN-002 package-reviewer · modelo openai-codex/gpt-5.6-sol · effort xhigh · route MODEL_STATIC_FALLBACK
- SPAWN-003 finding-verifier · modelo openai-codex/gpt-5.6-sol · effort xhigh · route MODEL_STATIC_FALLBACK
- SPAWN-004 repair-agent · modelo openai-codex/gpt-5.6-terra · effort medium · route MODEL_STATIC_FALLBACK
- SPAWN-005 delta-reviewer · modelo openai-codex/gpt-5.6-sol · effort xhigh · route MODEL_STATIC_FALLBACK
- SPAWN-006 finding-verifier · modelo openai-codex/gpt-5.6-sol · effort xhigh · route MODEL_STATIC_FALLBACK
- SPAWN-007 repair-agent · modelo openai-codex/gpt-5.6-terra · effort medium · route MODEL_STATIC_FALLBACK
- SPAWN-008 delta-reviewer · modelo openai-codex/gpt-5.6-sol · effort xhigh · route MODEL_STATIC_FALLBACK

↩ [[features/025-consola-minima-y-flexible|025-consola-minima-y-flexible]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
