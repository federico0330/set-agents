# 006-execution-graph · P3-graph-view

<!-- notas:auto -->
## Motivo

- objetivo: Grafo de ejecución navegable: nodos/aristas derivados en lectura del estado existente, set-agents --graph emite mermaid, sin librerías de terceros
- complejidad: high
- paths: `ai/scripts/check-feature-state.py`, `docs/adr/0013-execution-graph-view.md`, `docs/adr/README.md`

## Tareas

- [x] Modelo de nodo/arista: build_execution_graph() con join estructural (AC-20, AC-26 blockers con las 3 ramas, AC-27 labels) (completed) · python3 -m unittest tests.test_harness.HarnessTests.test_graph_produjo_edges_join_structurally_across_all_three_review_sources tests.test_harness.HarnessTests.test_graph_verification_edges_and_waived_verification_node tests.test_harness.HarnessTests.test_graph_repair_edge_and_commit_chain tests.test_harness.HarnessTests.test_graph_blocker_edges_anchor_to_package_or_feature_in_all_three_cases -v -> OK (4 tests); manual adversarial smoke against the real ai/state/features/*.json (whole-repo scan, 714 lines) confirmed no crash and correct joins
- [x] render_mermaid(): namespace disjunto subgraph/nodo, asserts estructurales, esqueleto vacío (AC-22, AC-23) (completed) · python3 -m unittest tests.test_harness.HarnessTests.test_graph_node_ids_and_labels_follow_ac22_ac27_exactly tests.test_harness.HarnessTests.test_graph_no_state_file_emits_ac23_skeleton_and_exits_zero tests.test_harness.HarnessTests.test_graph_partial_multi_feature_run_never_aborts tests.test_harness.HarnessTests.test_graph_whole_repo_scan_processes_every_state_file_when_no_feature_id_given -v -> OK (4 tests); validate_mermaid_structure adversarially fed 4 broken inputs (bad header, reserved word id, unbalanced subgraph, subgraph/node id collision) and confirmed each is caught
- [x] --commit opcional en record-repair, validación fail-open 7-40 hex (AC-21) (completed) · python3 -m unittest tests.test_harness.HarnessTests.test_record_repair_commit_format_gate_rejects_before_any_git_lookup tests.test_harness.HarnessTests.test_record_repair_commit_fail_open_when_git_cannot_answer tests.test_harness.HarnessTests.test_record_repair_commit_accepted_when_git_verifies_it -v -> OK (3 tests, covers format-reject, fail-open with no .git, real-repo accept + real-repo reject)
- [x] Subcomando graph (--feature-id, --root, --out) en feature-state.py + gemelo PROYECTO/ (AC-22, AC-23) (completed) · python3 ai/scripts/feature-state.py graph --feature-id nonexistent -> AC-23 skeleton exit 0; graph against real ai/state/features/*.json (whole repo, single feature) -> valid mermaid; PROYECTO/ai/scripts/feature-state.py kept byte-identical via cp + cmp; ./build.sh --check -> SELF_SCAFFOLD_SYNC_OK files=2
- [x] Enganche en render_notes(): grafo.md, backlink [[grafo]], guard de nombre reservado (AC-24) (completed) · python3 -m unittest tests.test_harness.HarnessTests.test_render_notes_writes_grafo_md_reusing_graph_construction_with_backlink tests.test_harness.HarnessTests.test_create_package_rejects_literal_grafo_case_sensitive -v -> OK (2 tests); manual sync-notes run confirmed grafo.md content matches graph subcommand output verbatim and feature note carries the [[grafo]] backlink
- [x] set-agents --graph: wrapper subprocess delgado en set_agents_app.py (AC-25) (completed) · python3 -m unittest tests.test_harness.HarnessTests.test_set_agents_graph_wrapper_matches_feature_state_graph_output -v -> OK; manual: set-agents --graph --feature-id nonexistent-xyz reproduces the AC-23 skeleton byte-for-byte
- [x] Reestructurar los 4 grupos de test_feature_state_gate_fails... + test nuevo in-process del guard de shallow-clone (AC-28) (completed) · python3 -m unittest tests.test_harness.HarnessTests.test_feature_state_gate_fails_when_a_delivered_feature_has_no_state_file tests.test_harness.HarnessTests.test_stale_waivers_guard_survives_independent_of_which_feature_is_waived -v -> OK (2 tests); ./ai/scripts/verify.sh -> FEATURE_STATE_OK against the real repo post-retirement
- [x] Tests AC-29: fixtures sintéticos para historia legacy sin --commit, spawns fuera de alcance (completed) · python3 -m unittest tests.test_harness.HarnessTests.test_graph_never_emits_spawn_nodes_and_survives_legacy_fixtures_without_commit -v -> OK; fixtures are synthetic (write_graph_fixture), never the live ai/state/features/*.json of other in-flight features, per AC-29
- [x] ADR-0013 + fila en docs/adr/README.md + log-decision del primer init sin backfill (completed) · docs/adr/0013-execution-graph-view.md created (D1..D4, Rejected: sections, file:line citations verified against the tree); docs/adr/README.md row added; feature-state.py log-decision run for slug p3-graph-view-abre-el-tracking-de-la-feature-006-sin-backfillear-p1-p2, linked to feature-006-delivered-outside-state-machine and AC-07 of 009-self-application

## Hallazgos

- PR-01 [high] closed — El join de actor de reviews[] es por posicion contra history, no estructural: con verdict blocked, cmd_record_review ap…
- PR-02 [medium] closed — 45 de 195 findings reales (23%) sin arista produjo: son exactamente los de delta_reviews[], fuente no incluida en el jo…
- PR-03 [medium] closed — Colision de ids de nodo y subgraph: dos package_id/feature_id que normalizan igual (ej. P1-a b vs P1-a-b) generan el mi…
- PR-04 [low] closed — Escaping con backslash no es el mecanismo de Mermaid (usa entidades); ya visible en el vault real como backslashes lite…
- PR-05 [low] closed — render_notes re-deriva la raiz del grafo por convencion de path (out_dir.parent.parent) en vez de usar el features_dir …
- PR-06 [low] closed — Modo whole-repo sin --feature-id y sin ai/state/features no anuncia nada (flowchart TD vacio, exit 0), indistinguible d…
- PR-07 [low] closed — La rama shallow-clone y la rama git-ausente (OSError) de AC-21 no tienen test, solo la rama no-repo esta cubierta.
- PR-08 [low] closed — build_execution_graph no acepta las formas legacy de packages (dict indexado, id en vez de package_id, camelCase) que _…
- SEC-001 [critical] closed — El escaping de labels Mermaid usa backslash, que Mermaid no implementa (usa entidades #quot; etc) -- un finding id adve…
- SEC-002 [critical] closed — La linea %% no data for {fid} es la unica interpolacion de render_mermaid sin pasar por _mermaid_escape -- un feature_i…
- SEC-003 [medium] closed — El fail-open de --commit (decision de producto ya aceptada) no deja ninguna senal auditable: a diferencia del precedent…
- SEC-004 [medium] closed — Log injection en _log_render_failure: context/exc no pasan por _short() antes de escribirse a ai/state/render-failures.…
- SEC-005 [low] closed — build_execution_graph deriva el path de lectura de features_dir/{fid}.json sin contencion -- un feature_id con path tra…
- D-01 [medium] closed — 6 de 8 grafo.md ya escritos en el vault (002,003,004,007,008,009) son artefactos del escaper vulnerable pre-fix (backsl…
- D-02 [low] closed — SEC-004 agrego render-failures.log* a .gitignore del repo pero no al PROYECTO/.gitignore que bootstrap_project.py distr…
- D-03 [low] closed — La linea de PR-06 (%% no state directory at ...) se appendea DESPUES de que render_mermaid ya valido y retorno -- nada …
- D-04 [low] closed — cmd_graph en modo whole-repo (glob de *.json) no atrapa TypeError de un packages:null/123 o un commit no-string -- trac…
- D-05 [low] closed — El guard de lockstep de PR-01 (len(plain_reviews)==len(review_events)) se aplico al pareo de reviews[] pero no al pareo…

## Recorrido

- review: repair_required (13 hallazgos)
- verificación: 0 refutados, 10 sostenidos
- verificación: 0 refutados, 1 sostenidos
- repair: SEC-001, SEC-002, PR-01, PR-02, PR-03, SEC-003, SEC-004, SEC-005, PR-04, PR-05 → 5 archivos
- repair: PR-06, PR-07, PR-08 → 3 archivos
- repair: D-01, D-02, D-03, D-04, D-05 → 10 archivos
- delta review: repair_required
- delta review: repair_required
- delta review: pass
- testing: pass
- runtime QA: pass (waived)
- gate `verify.sh`: pass
- gate `unittest`: pass
- gate `build.sh--check`: pass
- gate `git-diff--check`: pass

↩ [[features/006-execution-graph|006-execution-graph]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
