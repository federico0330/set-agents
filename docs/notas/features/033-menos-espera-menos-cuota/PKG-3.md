# 033-menos-espera-menos-cuota · PKG-3

<!-- notas:auto -->
## Motivo

- objetivo: Elegir modelo sin scrollear: agrupado por proveedor, contador, valor actual marcado, sin parpadeo
- ruteo: cursor-host native subagent; no route-decide → implementer (inherit)
- complejidad: high
- riesgo: medium
- paths: `ai/scripts/tui.py`, `ai/scripts/setup_models.py`

## Tareas

- [x] secciones por proveedor no seleccionables en el picker (completed) · unittest tests.test_harness.TuiTests.test_reduce_skips_section_headers_on_up_down_and_never_selects_them, unittest tests.test_models_wizard_ui.test_choose_groups_by_provider_and_maps_selected_index_to_the_model_id
- [x] contador de posicion, indicadores de scroll y marca del valor actual (completed) · unittest tests.test_harness.TuiTests.test_render_shows_position_counter_and_match_count_when_filtering, unittest tests.test_harness.TuiTests.test_render_shows_scroll_arrows_when_content_is_outside_the_viewport, unittest tests.test_harness.TuiTests.test_render_marks_current_value_and_run_picker_starts_the_cursor_on_it
- [x] anotaciones atenuadas (free, quien lo usa) y busqueda al tipear (completed) · unittest tests.test_harness.TuiTests.test_render_dims_free_and_used_by_suffixes, unittest tests.test_harness.TuiTests.test_reduce_a_letter_in_navigate_enters_search_without_slash
- [x] sacar el borrado de pantalla completo de tui.py:818 y probarlo a nivel bytes (completed) · unittest tests.test_harness.TuiTests.test_render_redraw_does_not_emit_full_screen_wipe_2j, BUILD_CHECK_PASS

## Hallazgos

- PKG3-F01 [medium] closed — correctness
- PKG3-F02 [medium] closed — data-integrity

## Recorrido

- review: repair_required (2 hallazgos)
- verificación: 0 refutados, 2 sostenidos
- repair: PKG3-F01, PKG3-F02 → 3 archivos
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `check-owned-paths`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass
- gate `risk-classification`: pass
- gate `verify`: pass
- gate `repair-ceiling`: pass

## Spawns

- SPAWN-001 implementer · modelo cursor/inherit
- SPAWN-002 package-reviewer · modelo cursor/inherit
- SPAWN-003 security-auditor · modelo cursor/inherit
- SPAWN-004 finding-verifier · modelo cursor/inherit
- SPAWN-005 repair-agent · modelo cursor/inherit
- SPAWN-006 delta-reviewer · modelo cursor/inherit

context pack: `docs/specs/033-menos-espera-menos-cuota/context/PKG-3.md`

↩ [[features/033-menos-espera-menos-cuota|033-menos-espera-menos-cuota]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
