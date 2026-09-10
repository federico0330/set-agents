# 049-identidad-honesta-modelos · PKG-C2

<!-- notas:auto -->
## Motivo

- objetivo: Rehacer consola cache-first y convergencia en candidato Git aislado
- ruteo: Replacement explicitly chosen by user after unrecoverable dirty-worktree candidate identity; isolated Git reconstructio… → frontend-engineer (inherit)
- complejidad: medium
- riesgo: medium
- riesgo: TTY first-paint, exclusive local apply and isolated candidate identity must remain honest and recoverable.
- paths: `ai/scripts/setup_models.py`, `ai/scripts/onboarding.py`, `tests/test_console_model_state_049.py`, `tests/test_model_apply_049.py`, `tests/test_models_wizard_ui.py`, `tests/test_menu_ui.py`
- depende de: PKG-A, PKG-B

## Tareas

- [x] cache-first-home (completed) · Isolated candidate focal suite 55/55; cache-only Estado behavior preserved
- [x] explicit-refresh-and-child-errors (completed) · Isolated candidate focal suite 55/55; explicit refresh and truthful child status
- [x] model-state-wizard (completed) · Isolated candidate focal suite 55/55; four-source evidence model panel
- [x] serialized-apply-readback (completed) · Isolated candidate focal suite 55/55; lock/apply/readback behavior
- [x] router-restore-plugin-regressions (completed) · Isolated candidate focal suite 55/55; navigation/default/plugin regressions
- [x] isolated-candidate-rebuild (completed) · FOUNDATION_REF 168cd65996f5e5e96c5c1f8131b1090a92879ef5; C2_REF 5ab059e2dd863384178205a57324ec6fe7b47074; seven-path delta; no Global

## Hallazgos

- PKG-C2-F01 [high] closed — integration
- PKG-C2-F02 [high] closed — integration
- PKG-C2-F03 [high] closed — correctness
- PKG-C2-F04 [high] closed — data-integrity
- PKG-C2-F05 [high] closed — data-integrity
- PKG-C2-F06 [high] closed — correctness
- PKG-C2-F07 [high] closed — correctness
- PKG-C2-F08 [high] closed — correctness
- PKG-C2-F09 [medium] closed — resilience
- PKG-C2-F10 [medium] closed — correctness
- PKG-C2-F11 [medium] closed — resilience
- PKG-C2-F12 [medium] closed — testing
- PKG-C2-SEC-001 [high] closed — security
- PKG-C2-SEC-002 [high] closed — data-integrity
- PKG-C2-SEC-003 [high] closed — data-integrity
- PKG-C2-SEC-004 [medium] closed — security
- PKG-C2-SEC-005 [medium] closed — resilience
- C2-UX-F01 [high] closed — ux
- C2-UX-F02 [high] closed — ux
- C2-UX-F03 [high] closed — ux
- C2-UX-F04 [medium] closed — ux
- C2-UX-F05 [medium] closed — ux-security
- C2-UX-F06 [medium] closed — ux
- PKG-C2-DELTA-F01 [high] closed — security
- PKG-C2-DELTA-F02 [medium] closed — correctness
- PKG-C2-DELTA-F03 [medium] closed — correctness
- PKG-C2-DELTA-F04 [medium] closed — correctness
- PKG-C2-DELTA-F05 [high] closed — security

## Recorrido

- review: repair_required (23 hallazgos)
- verificación: 0 refutados, 23 sostenidos
- verificación: 0 refutados, 4 sostenidos
- verificación: 0 refutados, 1 sostenidos
- repair: PKG-C2-F01, PKG-C2-F02, PKG-C2-F03, PKG-C2-F04, PKG-C2-F05, PKG-C2-F06, PKG-C2-F07, PKG-C2-F08, PKG-C2-F09, PKG-C2-F10, PKG-C2-F11, PKG-C2-F12, PKG-C2-SEC-001, PKG-C2-SEC-002, PKG-C2-SEC-003, PKG-C2-SEC-004, PKG-C2-SEC-005, C2-UX-F01, C2-UX-F02, C2-UX-F03, C2-UX-F04, C2-UX-F05, C2-UX-F06 → 4 archivos
- repair: PKG-C2-DELTA-F01, PKG-C2-DELTA-F02, PKG-C2-DELTA-F03, PKG-C2-DELTA-F04 → 4 archivos
- repair: PKG-C2-DELTA-F05 → 2 archivos
- delta review: repair_required
- delta review: repair_required
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `focused-tests`: pass
- gate `py-compile`: pass
- gate `diff-check`: pass
- gate `candidate-no-global`: pass
- gate `root-candidate-cmp`: pass
- gate `owned-paths`: pass
- gate `risk-classification`: pass
- gate `repair-ceiling`: pass

## Spawns

- SPAWN-001 package-planner · modelo anthropic/sonnet · effort medium · route dec1_518e93642f0b61c150e5c265bcc26b7c
- SPAWN-002 frontend-engineer · modelo static/static-base · effort high · route dec1_28a1ef8a5dcdd30b03167c36bb1592c1
- SPAWN-003 frontend-engineer · modelo static/static-base · effort high · route dec1_0be7338e9d580b06bedc9e87473be649
- SPAWN-004 frontend-engineer · modelo static/static-base · effort high · route dec1_f9900fd85fedb35e027f8c6703c352e8
- SPAWN-005 gate-runner · modelo anthropic/sonnet · effort medium · route dec1_02c3b1b151980d5c2bc96571074cba6c
- SPAWN-006 gate-runner · modelo anthropic/sonnet · effort medium · route dec1_72171b75d6868a71630de5bdb46b693a
- SPAWN-007 gate-runner · modelo anthropic/sonnet · effort medium · route dec1_57df7520c29de855d0251550393d368f
- SPAWN-008 package-planner · modelo anthropic/sonnet · effort medium · route dec1_8bda95d826330bcea795f2694a58f135
- SPAWN-009 package-reviewer · modelo anthropic/opus · effort medium · route dec1_131cbdd48e192d074e65c91d3702b202
- SPAWN-010 security-auditor · modelo anthropic/opus · effort medium · route dec1_03354e2cc54a22eef477fdf5ef2fa252
- SPAWN-011 ux-ui-designer · modelo anthropic/sonnet · effort medium · route dec1_7a746bc8ce2814d9d77c96f9d448b70e
- SPAWN-012 package-planner · modelo anthropic/haiku · effort medium · route dec1_d54f1092238efc1c7a90371d34c16d28
- SPAWN-013 finding-verifier · modelo anthropic/opus · effort medium · route dec1_7375c32735338a519566e9129a4ef868
- SPAWN-014 package-planner · modelo anthropic/haiku · effort medium · route dec1_6426c035251b7d04ade820e0e946840b
- SPAWN-015 finding-verifier · modelo anthropic/opus · effort medium · route dec1_7375c32735338a519566e9129a4ef868
- SPAWN-016 repair-agent · modelo static/static-base · effort high · route dec1_d6bd0a9ca2e154d675b4b5253d598f53
- SPAWN-017 package-planner · modelo anthropic/haiku · effort medium · route dec1_ebef5f60044a2736e7da811236991ad0
- SPAWN-018 repair-agent · effort high
- SPAWN-019 delta-reviewer · effort high
- SPAWN-020 finding-verifier · effort high
- SPAWN-021 repair-agent · effort high
- SPAWN-022 delta-reviewer · effort high
- SPAWN-023 finding-verifier · effort high
- SPAWN-024 repair-agent · effort high
- SPAWN-025 delta-reviewer · effort high
- SPAWN-026 runtime-verifier · effort medium

context pack: `docs/specs/049-identidad-honesta-modelos/context/PKG-C2.md`

↩ [[features/049-identidad-honesta-modelos|049-identidad-honesta-modelos]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
