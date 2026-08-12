# 021-gates-que-no-mienten-ni-callan · P2-gates-que-no-callan

<!-- notas:auto -->
## Motivo

- objetivo: Que correr los gates no deje al que los corre mudo mas de 60s, y que la doctrina deje de recomendar el patron que lo causa
- complejidad: small
- paths: `ai/scripts/verify.sh`, `Global/_canonical/agents`, `Global/_canonical/skills/spawn-prompt`, `tests/test_harness.py`
- depende de: P1-check-que-verifica

## Tareas

- [x] Modo de gates con latido: ningun intervalo sin emitir supera el umbral (AC-06) (completed) · Verificado por el orquestador: la doctrina esta en Global/_canonical/skills/spawn-prompt/SKILL.md:47-48 y llego a los 4 arboles (2 hits cada uno); heartbeat-run.py streamea linea a linea con latido sintetico; 977 OK / 2 skips, VERIFY_PASS, GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS, DIFFCHECK_CLEAN.
- [x] La doctrina deja de recomendar comando-largo-pipe-tail; frase exacta y testeable (AC-07) (completed) · Verificado por el orquestador: la doctrina esta en Global/_canonical/skills/spawn-prompt/SKILL.md:47-48 y llego a los 4 arboles (2 hits cada uno); heartbeat-run.py streamea linea a linea con latido sintetico; 977 OK / 2 skips, VERIFY_PASS, GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS, DIFFCHECK_CLEAN.
- [x] Dejar escrito que el watchdog es del runtime del agente, no del repo (AC-08) (completed) · Verificado por el orquestador: la doctrina esta en Global/_canonical/skills/spawn-prompt/SKILL.md:47-48 y llego a los 4 arboles (2 hits cada uno); heartbeat-run.py streamea linea a linea con latido sintetico; 977 OK / 2 skips, VERIFY_PASS, GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS, DIFFCHECK_CLEAN.
- [x] Test que prueba que el patron prohibido no aparece en briefs ni plantillas (AC-09) (completed) · Verificado por el orquestador: la doctrina esta en Global/_canonical/skills/spawn-prompt/SKILL.md:47-48 y llego a los 4 arboles (2 hits cada uno); heartbeat-run.py streamea linea a linea con latido sintetico; 977 OK / 2 skips, VERIFY_PASS, GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS, DIFFCHECK_CLEAN.

## Hallazgos

- B-01 [medium] closed
- B-02 [medium] closed
- A-01 [low] closed

## Recorrido

- review: repair_required (2 hallazgos)
- review: repair_required (1 hallazgos)
- verificación: 0 refutados, 3 sostenidos
- repair: B-02 → 3 archivos
- repair: B-01 → 3 archivos
- repair: A-01 → 3 archivos
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `verify`: pass
- gate `build-check`: pass
- gate `diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo openai-codex/gpt-5.6-sol · effort medium · route run1_6bffcca9361c13a28ea235b3412105de
- SPAWN-002 package-reviewer · modelo anthropic/sonnet · effort medium · route dec1_4f989907a100be243087be816b0b85ab
- SPAWN-003 package-reviewer · modelo anthropic/sonnet · effort medium · route dec1_d599d7722c853d56511fd99b31042d0c
- SPAWN-004 package-reviewer · modelo anthropic/sonnet · effort medium · route dec1_d599d7722c853d56511fd99b31042d0c

context pack: `docs/specs/021-gates-que-no-mienten-ni-callan/context/P2-gates-que-no-callan.md`

↩ [[features/021-gates-que-no-mienten-ni-callan|021-gates-que-no-mienten-ni-callan]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
