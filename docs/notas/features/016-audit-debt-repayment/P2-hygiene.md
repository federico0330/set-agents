# 016-audit-debt-repayment · P2-hygiene

<!-- notas:auto -->
## Motivo

- objetivo: Strip client-specific absolute paths/module names from package-gate-runner.md template + add non-blocking reason_code for _effective_runtime redirect
- ruteo: Disjoint low-risk hygiene, additive-only observability, no public contract break → implementer (None)
- complejidad: medium
- riesgo: reason_code mistaken for a real exclusion code: mitigated by AC-09/AC-10 identical success/runtime
- riesgo: template cleanup breaks next consumer: mitigated by AC-08 YAML validity requirement
- paths: `Global/_canonical/opencode-agents/package-gate-runner.md`, `ai/scripts/routing_core/service.py`, `tests/test_routing.py`

## Tareas

- [x] Case-insensitive cleanup of package-gate-runner.md keeping YAML/permission structure valid (completed) · grep -inE case-insensitive universe clean; frontmatter structural check: 15 permission top-level keys intact in order, default-deny '*' preserved on read/external_directory/bash, Ownership exception approved by orchestrator: updated tests/test_harness.py::test_rpl_p0a_package_gate_runner_is_opencode_only_and_strictly_scoped (only that function) to assert genericized placeholders + added negative case-insensitive literal check + 15-permission-key structural check. python3 -m unittest discover -s tests -> 573 tests OK skipped=3. ./ai/scripts/verify.sh -> VERIFY_PASS. ./build.sh --check -> CHECK_PASS + SELF_SCAFFOLD_SYNC_OK files=2. AC-08 grep clean.
- [x] Additive non-blocking reason_code in RouteDecision.reasons on _effective_runtime redirect, success/runtime/identity unchanged (completed) · python3 -m unittest tests.test_routing -v -k test_ac01 -> 6/6 OK; full tests.test_routing -> 204 tests OK (1 skipped, pre-existing)
- [x] New tests in test_routing.py: redirect observability + shapes c/e no-new-code for distinct reasons (completed) · New test test_ac10_shape_b_redirect_observability_... (before/after) + shape (b)/AC-04a existing redirect assertions updated additively + shape (c)/(e) assert absence of RUNTIME_REDIRECTED for their distinct reasons; full tests.test_routing 204 OK

## Hallazgos

- P2F-01 [high] closed — 
- P2F-02 [low] closed — 

## Recorrido

- review: repair_required (2 hallazgos)
- verificación: 0 refutados, 2 sostenidos
- repair: P2F-01, P2F-02 → 2 archivos
- delta review: pass
- testing: pass
- runtime QA: pass (waived)
- runtime QA: pass
- gate `p2-unittest-routing`: pass
- gate `p2-full-suite`: pass
- gate `p2-verify-build`: pass

context pack: `docs/specs/016-audit-debt-repayment/context/P2.md`

↩ [[features/016-audit-debt-repayment|016-audit-debt-repayment]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
