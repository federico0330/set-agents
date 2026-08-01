# 010-spawn-provenance · P1-spawn-provenance

<!-- notas:auto -->
## Motivo

- objetivo: Mintear spawn_id determinístico en record-spawn, nodo spawn (sin edges) en el grafo de 006, y el fix de done_ready() sobre blockers resueltos
- complejidad: small
- paths: `ai/scripts/feature-state.py`, `PROYECTO/ai/scripts/feature-state.py`, `tests/test_harness.py`, `docs/adr/0014-spawn-provenance-node.md`, `docs/adr/README.md`, `docs/specs/010-spawn-provenance/evidence/**`, `docs/specs/010-spawn-provenance/context/**`, `ai/state/features/010-spawn-provenance.json`, `ai/state/STATUS.md`, `ai/state/narrative-log.jsonl`, `ai/state/decisions-log.jsonl`, `docs/notas/**`

## Tareas

- [x] T-01-spawn-id-mint-and-replay-guard (completed) · unittest: test_record_spawn_mints_sequential_spawn_ids_from_the_counter, test_record_spawn_on_a_package_with_a_precedent_counter_but_no_spawns_list_continues_the_counter, test_record_spawn_replay_guard_is_first_and_produces_exactly_one_entry, test_record_spawn_rejects_duplicate_spawn_id_against_a_desynced_counter (red->green)
- [x] T-02-spawns-list-schema-and-setdefault (completed) · compact_package()['spawns']==[]; covered by same T-01 tests + PROYECTO/ai byte-identical
- [x] T-03-graph-spawn-node-type-and-label (completed) · unittest: test_graph_spawn_node_type_renders_label_and_no_edges, test_graph_spawn_node_absent_when_package_has_no_spawns_key (red->green); full graph suite (-k graph) green, 27 tests
- [x] T-04-rename-repoint-legacy-spawn-test (completed) · renamed test_graph_never_emits_spawn_nodes_and_survives_legacy_fixtures_without_commit -> test_graph_omits_spawn_nodes_for_a_package_lacking_spawns_list_and_survives_legacy_fixtures_without_commit, comment repointed to AC-02's surviving invariant; unittest green
- [x] T-05-done-ready-blockers-fix (completed) · unittest: test_done_ready_reaches_done_after_a_real_block_and_reopen_cycle (real CLI), test_done_ready_still_blocks_when_any_blocker_lacks_resolved_at_fixture, test_done_ready_passes_when_every_blocker_has_resolved_at_fixture (red->green)
- [x] T-06-adr-0014-and-index-supersession-note (completed) · docs/adr/0014-spawn-provenance-node.md created; docs/adr/0013 status line annotated; docs/adr/README.md rows updated; unittest: test_every_adr_on_disk_has_a_row_in_the_index, test_the_adr_index_never_lists_a_file_that_is_not_there green
- [x] T-07-regression-coverage-ac05 (completed) · unittest discover: 467 tests OK; ./ai/scripts/verify.sh -> VERIFY_PASS; ./build.sh --check -> SELF_SCAFFOLD_SYNC_OK files=2; git diff --check clean; check-owned-paths.py flags exactly docs/adr/0013-execution-graph-view.md as read_only_violations (expected, see evidence)

## Hallazgos

- P1-REV-001 [medium] closed — Replay guard order is not proved at exhausted spawn budget

## Recorrido

- review: repair_required (1 hallazgos)
- verificación: 0 refutados, 1 sostenidos
- repair: P1-REV-001 → 1 archivos
- delta review: pass
- testing: pass
- runtime QA: pass (waived)
- gate `unittest-discover`: pass
- gate `verify.sh`: pass
- gate `build-check`: pass
- gate `diff-check`: pass

↩ [[features/010-spawn-provenance|010-spawn-provenance]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
