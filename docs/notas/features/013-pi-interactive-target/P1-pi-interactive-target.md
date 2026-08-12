# 013-pi-interactive-target · P1-pi-interactive-target

<!-- notas:auto -->
## Motivo

- objetivo: Fourth generated harness target for pi interactive (agents/skills/prompts/doctrine) plus install/verify/build wiring, collision guard, E2E load check, dispatch-lane closure, and ADR-0007 amendment + ADR-0017 skeleton
- ruteo: Architecture-critical fourth harness target, new HOME write surface, fail-closed security guard, cross-package ownershi… → implementer (None)
- complejidad: high
- riesgo: New HOME write target outside the three previously-audited harness roots (AC-08)
- riesgo: Fail-closed collision guard is the only protection against clobbering third-party content in ~/.pi/agent/agents/ (AC-09)
- riesgo: AC-12 requires an ownership exception on a file this package does not own by default
- riesgo: Every generate.py/orchestrator.md line citation in the approved spec is stale post-004/015
- paths: `ai/scripts/generate.py`, `ai/scripts/install.py`, `ai/scripts/verify.sh`, `build.sh`, `Global/pi/**`, `Global/_shared/AGENTS.pi.md`, `docs/adr/0017-pi-interactive-target.md`, `docs/adr/0007-pi-lane.md`, `docs/adr/README.md`, `tests/test_harness.py`, `ai/state/decisions-log.jsonl`

## Tareas

- [x] Agents converter + role file (AC-02/03/04) (completed) · python3 -m unittest tests.test_harness.HarnessTests.test_pi_agents_generated_with_required_frontmatter_fields tests.test_harness.HarnessTests.test_pi_validate_fails_closed_on_hand_edited_agent_file tests.test_harness.HarnessTests.test_pi_target_validate_requires_canonical_prompt_per_role -v -> OK (3 tests)
- [x] Doctrine file Global/_shared/AGENTS.pi.md (AC-07) (completed) · python3 -m unittest tests.test_harness.HarnessTests.test_pi_doctrine_file_has_twelve_sections_and_orchestrator_operating_content -v -> OK
- [x] Skills + prompts converters (AC-05/06) (completed) · python3 -m unittest tests.test_harness.HarnessTests.test_pi_skills_copy_byte_identical_to_canonical tests.test_harness.HarnessTests.test_pi_prompts_strip_agent_field_and_inject_subagent_instruction -v -> OK
- [x] Install target + collision guard (AC-08/09) (completed) · python3 -m unittest tests.test_harness.HarnessTests.test_pi_install_target_and_managed_write_set_is_bounded tests.test_harness.HarnessTests.test_pi_install_collision_guard_fails_closed_in_preview_and_write_mode -v -> OK; scratch install.py --preview against scratch $HOME confirmed AC-08/AC-09 manually
- [x] Freshness/build wiring (AC-11) (completed) · ./build.sh --check -> SELF_SCAFFOLD_SYNC_OK files=2; ./build.sh --diff clean 4th pi diff after ./build.sh regenerated tracked Global/pi; verify.sh freshness loop extended with diff -ruN Global/pi
- [x] End-to-end pi --verbose load check (AC-13) (completed) · SET_AGENTS_PI_E2E=1 python3 -m unittest tests.test_harness.HarnessTests.test_pi_verbose_startup_actually_loads_the_generated_tree_e2e -v -> OK, real pi 0.83.0 verified live against scratch HOME: [Context]/~/.pi/agent/AGENTS.md, [Skills]/user/*, [Prompts]/user/* all present, no [Agents] section (correct, pi core has none). Default (no env var) -> skipped, not silently passed. BLOCKED-by-environment: pi-subagents extension not installed in this sandbox (no ~/.pi/agent/npm/node_modules), so the subagent({action:list})/subagents-doctor half of AC-13 (proving Global/pi/agents/** discoverability) could not be exercised live here -- recorded as a known gap for a future environment with pi-subagents active, not faked.
- [x] Dispatch-lane closure + ADR-0017 skeleton + ADR-0007 amendment (AC-12/14) (completed) · python3 -m unittest tests.test_harness.HarnessTests.test_dispatch_lane_argv_closes_skills_and_prompt_templates tests.test_harness.HarnessTests.test_adr_0017_and_0007_amendment_and_superseding_decision_recorded -v -> OK; feature-state.py log-decision recorded ac09-ac10-pi-minimal-target-superseded-by-013

## Hallazgos

- SEC-01 [high] closed
- SEC-02 [low] refuted · refutado por finding-verifier: El scope agents/-only es exactamente lo que el contrato aprobado manda: AC-09 razona que skills/ y prompts/ estaban vac… [docs/specs/013-pi-interactive-target/spec.md:696-706 vs ai/scripts/install.py:2…]
- RF-01 [medium] closed
- RF-02 [medium] closed
- RF-03 [low] closed
- RF-04 [low] closed
- RF-05 [low] closed

## Recorrido

- review: repair_required (7 hallazgos)
- verificación: 1 refutados, 6 sostenidos
- repair: SEC-01, RF-01, RF-02, RF-03, RF-04, RF-05 → 5 archivos
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `unittest-full`: pass
- gate `verify-sh`: pass
- gate `build-check-diff`: pass
- gate `install-collision-guard`: pass
- gate `pi-e2e`: pass

context pack: `docs/specs/013-pi-interactive-target/context/P1-pi-interactive-target.md`

↩ [[features/013-pi-interactive-target|013-pi-interactive-target]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
