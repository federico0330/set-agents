# 033-menos-espera-menos-cuota · PKG-6

<!-- notas:auto -->
## Motivo

- objetivo: Cuotas que alcanzan: context pack obligatorio, gates sin modelo, panel por riesgo y presupuesto visible
- ruteo: cursor-host native subagent; no route-decide → implementer (inherit)
- complejidad: high
- riesgo: high
- paths: `ai/scripts/feature_state_lib`, `ai/scripts/cost-report.py`

## Tareas

- [x] context pack obligatorio para entrar en PACKAGE_IMPLEMENTATION (completed) · unittest test_package_implementation_requires_a_context_pack_file RED-then-GREEN bite
- [x] gate-runner rechazado cuando todos los comandos son P001: va local-gate-runner (completed) · unittest test_record_spawn_rejects_p001_gate_runner_naming_local_gate_runner, unittest test_p001_allowlist_matches_the_local_gate_guard
- [x] tamano del panel de revision derivado de complexity y risk (completed) · unittest test_start_review_panel_size_follows_complexity_and_risk, unittest test_shrinking_the_panel_cannot_let_implementer_self_approve_or_patch
- [x] spawns usados sobre techo del modo, visibles en status y narracion, aviso al 80% (completed) · unittest test_record_spawn_warns_at_eighty_percent_of_the_mode_ceiling
- [x] cerrar la brecha del registro propio: la seccion 2 de cost-report mide cero (completed) · unittest test_cost_report_section_two_ingests_feature_state_spawns, cost-report.py --since 2026-08-10 Section 2 TOTAL 137

## Hallazgos

- PKG6-F01 [high] closed — correctness
- PKG6-F02 [medium] closed — correctness
- PKG6-F03 [medium] closed — data-integrity

## Recorrido

- review: repair_required (3 hallazgos)
- verificación: 0 refutados, 3 sostenidos
- repair: PKG6-F01, PKG6-F02, PKG6-F03 → 6 archivos
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `check-owned-paths`: pass
- gate `git-diff-check`: pass
- gate `build-check`: pass
- gate `verify`: pass
- gate `risk-classification`: pass
- gate `repair-ceiling`: pass

## Spawns

- SPAWN-001 implementer · modelo cursor/inherit
- SPAWN-002 implementer · modelo cursor/inherit
- SPAWN-003 implementer · modelo cursor/inherit
- SPAWN-004 local-gate-runner · modelo cursor/inherit
- SPAWN-005 gate-runner · modelo cursor/inherit
- SPAWN-006 package-reviewer · modelo cursor/inherit
- SPAWN-007 security-auditor · modelo cursor/inherit
- SPAWN-008 finding-verifier · modelo cursor/inherit

context pack: `docs/specs/033-menos-espera-menos-cuota/context/PKG-6.md`

↩ [[features/033-menos-espera-menos-cuota|033-menos-espera-menos-cuota]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
