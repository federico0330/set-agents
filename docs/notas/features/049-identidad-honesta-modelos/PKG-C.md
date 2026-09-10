# 049-identidad-honesta-modelos · PKG-C

<!-- notas:auto -->
## Motivo

- objetivo: Consola cache-first y wizard de convergencia por readback
- ruteo: Route decision dec1_874f5386d86738581762fbe607c1dc46 was supplied; its resolved provider/model is not present in readab… → frontend-engineer (inherit)
- complejidad: medium
- riesgo: medium
- riesgo: TTY first-paint and exclusive local apply must remain honest and recoverable.
- paths: `ai/scripts/setup_models.py`, `ai/scripts/onboarding.py`, `tests/test_console_model_state_049.py`, `tests/test_model_apply_049.py`
- depende de: PKG-A, PKG-B

## Tareas

- [x] cache-first-home (completed) · First picker cache-only; explicit refresh; focal first-frame PASS
- [x] explicit-refresh-and-child-errors (completed) · Refresh preserves stale cache; run_tty truthful; focal PASS
- [x] model-state-wizard (completed) · Four sourced evidence facts and temporary /model copy; focal PASS
- [x] serialized-apply-readback (completed) · Exclusive lock, persist/apply/readback and pending state; focal PASS
- [x] router-restore-plugin-regressions (completed) · Disjoint router/restore plus read-only plugin warning; legacy migration suite PASS

## Hallazgos

- PKG-C-F01 [high] closed — data-integrity
- PKG-C-F02 [medium] closed — correctness
- PKG-C-F03 [high] closed — resilience
- PKG-C-F04 [medium] closed — correctness
- PKG-C-F05 [high] closed — correctness
- PKG-C-F06 [high] closed — testing
- PKG-C-F07 [medium] closed — testing
- PKG-C-SEC-001 [medium] closed — security
- PKG-C-SEC-002 [high] closed — security
- PKG-C-SEC-003 [high] closed — data-integrity
- PKG-C-SEC-004 [high] closed — correctness
- PKG-C-SEC-005 [medium] closed — resilience
- PKG-C-UX-F01 [high] closed — correctness
- PKG-C-UX-F02 [high] closed — resilience
- PKG-C-UX-F03 [high] closed — interaction
- PKG-C-UX-F04 [high] closed — correctness
- PKG-C-UX-F05 [medium] closed — security
- PKG-C-UX-F06 [medium] closed — correctness

## Recorrido

- review: repair_required (18 hallazgos)
- verificación: 0 refutados, 18 sostenidos
- repair: PKG-C-F01, PKG-C-F02, PKG-C-F03, PKG-C-F04, PKG-C-F05, PKG-C-F06, PKG-C-F07, PKG-C-SEC-001, PKG-C-SEC-002, PKG-C-SEC-003, PKG-C-SEC-004, PKG-C-SEC-005, PKG-C-UX-F01, PKG-C-UX-F02, PKG-C-UX-F03, PKG-C-UX-F04, PKG-C-UX-F05, PKG-C-UX-F06 → 6 archivos
- gate `full-ui-suite`: pass
- gate `py-compile`: pass
- gate `diff-check`: pass
- gate `owned-paths`: pass
- gate `risk-classification`: pass
- gate `repair-ceiling`: fail

## Spawns

- SPAWN-001 ux-ui-designer · modelo static/static-base · effort medium
- SPAWN-002 frontend-engineer · modelo static/static-base · effort high
- SPAWN-003 frontend-engineer · modelo static/static-base · effort medium
- SPAWN-004 local-gate-runner · modelo local/cheap-local · effort low
- SPAWN-005 gate-runner · modelo anthropic/haiku · effort low
- SPAWN-006 frontend-engineer · modelo static/static-base · effort low
- SPAWN-007 gate-runner · modelo anthropic/haiku · effort low
- SPAWN-008 package-reviewer · modelo anthropic/haiku · effort medium · route dec1_e03bf32129a76eae494addac20ea0d36
- SPAWN-009 security-auditor · modelo anthropic/haiku · effort medium · route dec1_374ad91de455788a7547437f7f2af4f3
- SPAWN-010 ux-ui-designer · modelo static/static-base · effort medium
- SPAWN-011 finding-verifier · modelo anthropic/haiku · effort medium · route dec1_6cdbb926c88ff66e3e8fde12d0d1c6f8
- SPAWN-012 repair-agent · modelo static/static-base · effort high
- SPAWN-013 gate-runner · modelo anthropic/sonnet · effort medium · route dec1_13d86a3d56ed7dd5900675f0518c7d4e
- SPAWN-014 package-planner · modelo anthropic/haiku · effort medium · route dec1_63a4242092cac6309a2a2e4139ce3b87
- SPAWN-015 debugger · modelo static/static-base · effort high · route dec1_945820c9bc97fe702068b7ba59bbf4ae
- SPAWN-016 debugger · modelo static/static-base · effort high · route dec1_b186ef08f46a4f71965517dcd35f7deb

context pack: `docs/specs/049-identidad-honesta-modelos/context/PKG-C.md`

↩ [[features/049-identidad-honesta-modelos|049-identidad-honesta-modelos]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
