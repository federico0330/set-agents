# 025-consola-minima-y-flexible · D4-harness-por-CLI

<!-- notas:auto -->
## Motivo

- objetivo: Instalar y desinstalar el harness por CLI, sin tocar los otros
- complejidad: medium
- paths: `ai/scripts/install.py`, `install.sh`, `ai/scripts/set_agents_app.py`, `tests`, `docs/adr`
- depende de: D3-posturas-de-autonomia

## Tareas

- [x] Instalar solo en un CLI y dejar los otros virgenes (AC-09) (completed) · D4-gates-runtime-qa.md escenario A pass en hogar temporal.
- [x] Desinstalar de uno sin tocar los otros (AC-10) (completed) · D4-gates-runtime-qa.md escenario B pass sin tocar otros carriles.
- [x] Usar un CLI virgen por esta vez, sin desinstalar (AC-11) (completed) · D4-gates-runtime-qa.md escenario C pass sin uninstall.

## Hallazgos

- D4-F01 [high] closed — correctness
- D4-DR02 [low] closed — documentation

## Recorrido

- review: repair_required (1 hallazgos)
- review: pass (0 hallazgos)
- review tardía (delta-reviewer): 0 hallazgos
- verificación: 0 refutados, 1 sostenidos
- verificación: 0 refutados, 1 sostenidos
- repair: D4-F01 → 6 archivos
- repair: D4-F01, D4-DR02 → 4 archivos
- delta review: repair_required
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `d4-install-isolation`: pass
- gate `d4-uninstall-isolation`: pass
- gate `d4-virgin-lane`: pass

## Spawns

- SPAWN-001 gate-runner · modelo openai-codex/gpt-5.6-luna · effort low · route MODEL_STATIC_FALLBACK
- SPAWN-002 gate-runner · modelo openai-codex/gpt-5.6-terra · effort medium · route MODEL_STATIC_FALLBACK
- SPAWN-003 package-reviewer · modelo openai-codex/gpt-5.6-sol · effort xhigh · route MODEL_STATIC_FALLBACK
- SPAWN-004 package-reviewer · modelo openai-codex/gpt-5.6-terra · effort high · route MODEL_STATIC_FALLBACK
- SPAWN-005 finding-verifier · modelo openai-codex/gpt-5.6-sol · effort xhigh · route MODEL_STATIC_FALLBACK
- SPAWN-006 repair-agent · modelo openai-codex/gpt-5.6-terra · effort medium · route MODEL_STATIC_FALLBACK
- SPAWN-007 delta-reviewer · modelo openai-codex/gpt-5.6-sol · effort xhigh · route MODEL_STATIC_FALLBACK
- SPAWN-008 repair-agent · modelo openai-codex/gpt-5.6-terra · effort medium · route MODEL_STATIC_FALLBACK

context pack: `docs/specs/025-consola-minima-y-flexible/context/D4-harness-por-CLI.md`

↩ [[features/025-consola-minima-y-flexible|025-consola-minima-y-flexible]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
