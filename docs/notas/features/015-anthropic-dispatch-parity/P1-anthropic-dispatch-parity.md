# 015-anthropic-dispatch-parity · P1-anthropic-dispatch-parity

<!-- notas:auto -->
## Motivo

- objetivo: Redirect routed decisions resolving to provider anthropic onto a real Claude-Code CLI subprocess spawn (CLI-level read-only/bounded-write tool ceiling, mandatory --setting-sources user containment), close the review-independence gap for the 12-day two-provider window without relaxing ADR-0011 D4, update the shared orchestrator doctrine across harnesses, fix two static-config model collisions, and record the design in a new ADR.
- ruteo: High complexity: auth/authz-adjacent review-independence fix, untrusted-code-execution containment (headless CLI spawn … → implementer (frontier)
- complejidad: high
- riesgo: SEC: headless Claude-Code spawn without --setting-sources user + cwd containment reopens R2-03/R3-01's tool-ceiling byp…
- riesgo: SEC: Bash must be categorically absent from every AC-02 argv, both role classes; no parameter may widen it (SEC-A02 pre…
- riesgo: AUTHZ regression: AC-04 must not weaken ADR-0011 D4 -- day-13 fixture (only anthropic authenticated) must still hard-ha…
- riesgo: ADR-number race: 0017/0018 are soft-claimed by 013/014 but not materialized on disk -- re-verify docs/adr/ listing live…
- riesgo: Doctrine test regression: test_orchestrator_doctrine_branches_on_route_decide_reason_taxonomy must iterate every genera…
- riesgo: Scope creep: AC-06's models.toml edit must touch ONLY the two named cells -- any other [areas.*]/[roles.*] value change…
- paths: `ai/scripts/routing_core/service.py`, `ai/scripts/claude_code_spawn.py`, `Global/_canonical/agents/orchestrator.md`, `Global/opencode/agents/orchestrator.md`, `Global/claude-code/agents/orchestrator.md`, `Global/codex/agents/orchestrator.toml`, `models.toml`, `docs/adr/0019-anthropic-dispatch-parity.md`, `tests/test_routing.py`, `tests/test_harness.py`

## Tareas

- [x] AC-01: provider-aware effective-runtime redirect in RoutingService.route()'s exclusion loop (service.py, 8 sites) + hermetic 4-shape proof against live-machine-shaped inventory (completed) · python3 -m unittest tests.test_routing -v -k test_ac01 => OK (5 tests: new-pairs unrelated + 4 AC-01 shapes a/b/c/d, all green). service.py: 8/8 facts.selected_runtime-keyed sites (137,144,145,195,200,201,206,208) addressed -- 137/145/195/200/201/206/208 now key on the per-route effective runtime via new _effective_runtime()/identity[1]/fallback[1]; 144 (PI_SIMULATION_ONLY guard) intentionally left reading facts.selected_runtime, counted+commented. :128 conflict check untouched. py_compile clean.
- [x] AC-02: new SEPARATE Claude-Code-lane CLI subprocess spawn module (stdin delivery, CLI tool-ceiling by role class, mandatory --setting-sources user + cwd boundary + no --add-dir, writer/review lifecycle split, no double-decision) + subprocess-mocked spawn tests + argv-ceiling tests (completed) · New module ai/scripts/claude_code_spawn.py (never calls set_agents_spawn.route_and_spawn, structural precedent only). 27 new tests in tests.test_routing.ClaudeCodeSpawnTests, all green: argv-ceiling both role classes, forbidden-flag fail-closed guard, stdin delivery (never positional), cwd containment, success/model_mismatch/failure classification (incl. R2-08 overload/empty-modelUsage shape), dispatch_writer lifecycle (dispatched->spawn->terminal, never --route-decide, exception-safe close), dispatch_review (zero routing-store bookkeeping, diff payload reaches stdin). Full suite: python3 -m unittest discover -s tests -v => 521 tests, OK, 0 failures, 0 skips (baseline 494 + 27 new). ./ai/scripts/verify.sh => VERIFY_PASS.
- [x] AC-03: rewrite canonical orchestrator doctrine (same-lane/cross-lane-redirect/true-off-lane), regenerate via ./build.sh into every generated harness copy, update test_harness.py generically (not hardcoded to 3 files) (completed) · Global/_canonical/agents/orchestrator.md:160-247 rewritten: step 2 now branches same-lane/cross-lane-redirect/true-off-lane on data.runtime, runtime-agnostic (never hardcodes opencode as host harness); step 3's hard-denial letter 'c' preserved unchanged so ADR-0011 D4's citation of 'step 3c' stays accurate. ./build.sh regenerated all 3 currently-generated copies (opencode/claude-code/codex .toml) clean, CHECK_PASS. test_harness.py::test_orchestrator_doctrine_branches_on_route_decide_reason_taxonomy rewritten to discover every Global/*/agents/orchestrator.* copy generically (excluding _canonical), asserting >=3 found and the new doctrine text. python3 -m unittest tests.test_harness -k test_orchestrator_doctrine_branches -v => OK.
- [x] AC-04: add doctrine branch for verified-review shape spawning via AC-02; end-to-end pipeline test + D4-preservation test on non-vacuous day-13 fixture + diff-payload-reaches-reviewer assertion (completed) · Doctrine step 3b (new): verified review shape spawns via the same-lane/cross-lane rule, never BASE by default; benign REVIEW_IDENTITY_UNVERIFIED kept as 3b's second sub-case. tests/test_routing.py: test_ac04b_day13_fixture_writer_redirects_but_reviewer_still_hard_halts (non-vacuous day-13 fixture, writer genuinely redirects, reviewer still REVIEWER_INDEPENDENCE_UNAVAILABLE) and test_ac04a_verified_review_shape_dispatches_via_ac02_cross_lane_with_diff_payload_reaching_stdin (real diff text asserted present in stdin payload, not just dispatch mechanics). python3 -m unittest tests.test_routing -k test_ac04 -v => OK (2 tests).
- [x] AC-05: confirm/name residual benign/unverified review path exposure; regression test for unchanged benign path (balanced-tier .claude residual withdrawn by AC-06(b)) (completed) · Verified against real spec text: AC-05 requires only a confirming regression test, no new production code. tests/test_routing.py::test_ac05_benign_unverified_review_path_unchanged_and_claude_axis_residual_withdrawn: benign path unchanged, and [areas.audit]/[areas.judge].claude == 'fable', not in {haiku,sonnet,opus}. python3 -m unittest tests.test_routing -k test_ac05 -v => OK.
- [x] AC-06: models.toml values-only collision fixes (go-zen a; [areas.audit/judge].claude opus->fable b) + generic (non-hardcoded) collision-detection regression tests (completed) · models.toml:93,99 claude opus->fable. models.toml:96 areas.audit.opencode.go-zen -> openai/gpt-5.5; areas.judge.opencode.go-zen deliberately untouched (out of approved 2-cell scope), residual logged (log-decision slug areas-judge-go-zen-colisiona-residuo-fuera-de-alcance) and recorded in ADR-0019 D8. Updated pre-existing test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart literal expectation to match the approved value change. New generic tests test_ac06a_audit_go_zen_lane_value_no_longer_collides_with_any_implement_tier_ladder and test_ac06b_claude_axis_audit_judge_collide_with_nothing_generically. python3 -m unittest tests.test_routing -k test_ac06 tests.test_harness -k test_repo_go_zen -v => OK.
- [x] AC-07: zero-catalog-diff restated as a regression test (build_snapshot already admits claude-code/anthropic identities, catalog.py untouched) (completed) · Confirmed accurate: catalog.py has zero diff (git status shows none). New test test_ac07_build_snapshot_already_admits_claude_code_anthropic_identities_zero_catalog_diff proves build_snapshot already allows the claude-code/anthropic identity for all 3 anthropic routes across all 3 runtimes, and _PAIR_COMMANDS carries exactly the 3 pre-existing anthropic pairs. python3 -m unittest tests.test_routing -k test_ac07 -v => OK.
- [x] AC-08: new docs/adr/0019-anthropic-dispatch-parity.md recording items (a)-(e) + docs/adr/README.md row (completed) · Re-verified live before writing: ls docs/adr/ lists through 0016 only, 013/014 still have no packages materializing 0017/0018 -- 0019 confirmed free. Wrote docs/adr/0019-anthropic-dispatch-parity.md (D1-D9 + Scale/Data/Security + Consecuencias) covering items (a)-(e), citing both pre-existing decisions-log 'record dont fix' notes verbatim-sourced, the new AC-06(a) judge/go-zen residual, and all 6 SEC-001..SEC-006 checkpoint findings by their inline comment markers. Added docs/adr/README.md index row.

## Hallazgos

- SEC-P1-001 [critical] closed — Doctrina permite incrustar el diff sin revisar directamente en el texto de instrucción, evadiendo el wrapper de nonce q…
- SEC-P1-002 [critical] closed — El mecanismo que la doctrina manda invocar no tiene punto de entrada CLI ni entrada en la lista blanca de permisos del …
- SEC-P1-003 [medium] closed — El log de auditoría de SEC-002 nunca llega a ningún destino durable: no hay manejador de logging configurado
- F-01 [high] closed — model_mismatch usa la tabla de alias del lane pi (PI_MODEL_MAP) para validar spawns de Claude Code; opus resuelve disti…
- F-02 [medium] closed — El propio contrato (AC-06(i) vs Non-goals) es internamente inconsistente sobre el alcance del test de colisión; se reso…
- F-03 [medium] closed — El redirect de AC-01 puede disparar en un caso no especificado para el lane pi (par genuinamente ausente), y el spawner…
- F-04 [medium] closed — La rama same-lane de AC-03 tiene condición runtime-agnostic pero acción todavía shaped para OpenCode; falla en vivo cua…
- F-05 [low] closed — El gate de ownership falla por razones no relacionadas (diff_ref desactualizado), sin señal real
- F-06 [low] closed — El test de AC-04(a) no verifica que el archivo de doctrina generado realmente seleccione la rama cross-lane
- F-07 [low] closed — El checkpoint temprano de seguridad no quedó registrado en el historial formal del paquete
- DR-01 [high] closed — SEC-P1-002 quedó a medias: la entrada en coord_policy.SAFE_ARGV solo se propaga al lane de Claude Code, pero la rama cr…
- DR-02 [medium] closed — --routing-test-root quedó en la lista blanca de coord_policy y accesible por el CLI real; permite que el binding de aud…
- DR-03 [low] closed — El archivo JSONL de auditoría se abre con open() plano (modo de proceso, típicamente 0644) en vez de 0600 como el resto…
- DR-04 [low] closed — --task - junto con --supplementary - produce una revisión vacía y sin protección de nonce, sin que nada lo reporte
- DR-05 [low] closed — Los tests del CLI nuevo no interceptan stdout, contaminando la salida real de la suite (higiene, sin impacto de correct…

## Recorrido

- review: repair_required (10 hallazgos)
- verificación: 0 refutados, 10 sostenidos
- verificación: 0 refutados, 5 sostenidos
- repair: SEC-P1-001, SEC-P1-002, SEC-P1-003, F-01, F-02, F-03, F-04, F-05, F-06, F-07 → 13 archivos
- repair: DR-01, DR-02, DR-03, DR-04, DR-05 → 10 archivos
- delta review: repair_required
- delta review: pass
- testing: pass
- testing: pass
- runtime QA: fail
- runtime QA: pass

context pack: `docs/specs/015-anthropic-dispatch-parity/context/P1-anthropic-dispatch-parity.md`

↩ [[features/015-anthropic-dispatch-parity|015-anthropic-dispatch-parity]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
