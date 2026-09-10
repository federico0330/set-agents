# 049-identidad-honesta-modelos · PKG-B

<!-- notas:auto -->
## Motivo

- objetivo: ModelState singular y CLI de observación privada
- ruteo: Route decision dec1_874f5386d86738581762fbe607c1dc46 was supplied; its resolved provider/model is not present in readab… → implementer (inherit)
- complejidad: high
- riesgo: high
- riesgo: Public JSON schema and transient OpenCode exports require a fail-closed privacy boundary.
- paths: `ai/scripts/model_state.py`, `ai/scripts/set_agents_app.py`, `tests/test_model_state_049.py`
- depende de: PKG-A

## Tareas

- [x] model-state-schema (completed) · Strict TDD B-1; schema/runtime triangulation; focal PASS
- [x] desired-installed-routing (completed) · Strict TDD B-2; present/absent triangulation; focal PASS
- [x] opencode-observer (completed) · Strict TDD B-3/B-4; mixed sessions, malformed, timeout, cap, no messages; focal PASS
- [x] readonly-cli-argv (completed) · Strict TDD B-5; parser safety net 2/2 and invalid argv rc2
- [x] model-state-regressions (completed) · tests.test_model_state_049 10/10 PASS; py_compile and git diff --check PASS

## Hallazgos

- PKG-B-F01 [high] closed — correctness
- PKG-B-F02 [medium] closed — resilience
- PKG-B-F03 [medium] closed — correctness
- PKG-B-F04 [medium] closed — resilience
- PKG-B-F05 [medium] closed — testing
- PKG-B-SEC-001 [medium] closed — security
- PKG-B-SEC-002 [low] closed — security
- PKG-B-SEC-003 [low] closed — resilience
- PKG-B-DELTA-F01 [medium] closed — resilience
- PKG-B-DELTA-F02 [medium] closed — correctness

## Recorrido

- review: repair_required (8 hallazgos)
- verificación: 0 refutados, 8 sostenidos
- verificación: 0 refutados, 4 sostenidos
- repair: PKG-B-F01, PKG-B-F02, PKG-B-F03, PKG-B-F04, PKG-B-F05, PKG-B-SEC-001, PKG-B-SEC-002, PKG-B-SEC-003 → 2 archivos
- repair: PKG-B-F03, PKG-B-SEC-002, PKG-B-DELTA-F01, PKG-B-DELTA-F02 → 2 archivos
- delta review: repair_required
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `diff-check`: pass
- gate `py-compile`: pass
- gate `focused-tests`: pass
- gate `help-parser-regression`: pass
- gate `owned-paths`: pass
- gate `assertion-quality`: pass
- gate `risk-classification`: pass

## Spawns

- SPAWN-001 implementer · modelo static/static-base · effort high · route dec1_5fbf223d9c07885c41d961d5c51a1403
- SPAWN-002 gate-runner · modelo anthropic/haiku · effort medium · route dec1_b5f483f0c6fda0b0399b823dc13f033b
- SPAWN-003 package-reviewer · modelo anthropic/haiku · effort medium · route dec1_4fb9ab6a45377be7307fbbddb4b922e9
- SPAWN-004 security-auditor · modelo anthropic/haiku · effort medium · route dec1_e045cce042586fb7d193b502c2a5dfe9
- SPAWN-005 finding-verifier · modelo anthropic/haiku · effort medium · route dec1_2859a749338ecfe6401cc6e0ec938179
- SPAWN-006 repair-agent · modelo static/static-base · effort high · route dec1_b6d60ff6a1ead70d9cff48e6cd157241
- SPAWN-007 delta-reviewer · modelo anthropic/haiku · effort medium · route dec1_a7f93ca61e119bc0aec14bd14b176de0
- SPAWN-008 finding-verifier · modelo anthropic/haiku · effort medium · route dec1_713d9b21393dbc0b655ca55bab6a7379
- SPAWN-009 repair-agent · modelo static/static-base · effort medium
- SPAWN-010 delta-reviewer · modelo anthropic/haiku · effort medium · route dec1_c441b0e4ad38c959ceb2c3e29ad28e46

context pack: `docs/specs/049-identidad-honesta-modelos/context/PKG-B.md`

↩ [[features/049-identidad-honesta-modelos|049-identidad-honesta-modelos]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
