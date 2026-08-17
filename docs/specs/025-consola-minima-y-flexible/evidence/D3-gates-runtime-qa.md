# D3 gates / runtime QA

Read-only verification of integrated artifact `bec3dcfb2cdd06b98fb4ab82d6490a3858f0a5a9` (Feature 025 D3), run 2026-08-17. No source, configuration, state, or commit changes were made.

## Artifact and focused symbols

`git rev-parse bec3dcf` → `bec3dcfb2cdd06b98fb4ab82d6490a3858f0a5a9` (exit 0). `git show --stat bec3dcf` identifies the D3 artifact in `ai/scripts/set_agents_app.py`, `Global/_canonical/agents/orchestrator.md`, `docs/adr/0054-posturas-de-autonomia.md`, and `tests/test_harness.py`.

The integrated tree contains `POSTURAS`, `postura_actual`, `set_postura`, `postura_gate`, `METODOLOGIAS`, `metodologia_preferida`, `set_metodologia`, `--posturas`, and `--metodologias`; the doctrine contains `Postura de autonomía (ADR-0054)` and `Metodología preferida (ADR-0054)`. Exit 0 for the symbol scan.

## Gates

| Gate | Command | Exit | Result |
|---|---|---:|---|
| Focused D3 tests | `python3 -m unittest tests.test_harness.HarnessTests.test_postura_persiste_al_reiniciar_el_proceso tests.test_harness.HarnessTests.test_las_tres_posturas_dan_tres_resultados_distintos_para_el_mismo_escenario tests.test_harness.HarnessTests.test_el_canal_de_postura_llega_a_donde_el_agente_lo_lee tests.test_harness.HarnessTests.test_posturas_screen_muestra_la_explicacion_en_pantalla tests.test_harness.HarnessTests.test_postura_desconocida_no_se_acepta tests.test_harness.HarnessTests.test_metodologia_persiste_y_muestra_explicacion_en_pantalla tests.test_harness.HarnessTests.test_rdd_se_reconcilia_con_strict_tdd_no_lo_duplica tests.test_harness.HarnessTests.test_app_config_writers_postura_y_metodologia_no_se_pisan` | 0 | PASS — 8 tests, all `OK`. |
| Isolated CLI runtime | `d3=$(mktemp -d /tmp/d3-runtime.XXXXXX); SET_AGENTS_STATE="$d3" python3 ai/scripts/set_agents_app.py --posturas; SET_AGENTS_STATE="$d3" python3 ai/scripts/set_agents_app.py --postura consultiva; SET_AGENTS_STATE="$d3" python3 ai/scripts/set_agents_app.py --posturas; SET_AGENTS_STATE="$d3" python3 ai/scripts/set_agents_app.py --metodologia rdd; SET_AGENTS_STATE="$d3" python3 ai/scripts/set_agents_app.py --metodologias; sed "$d3/config.toml"; rm -rf "$d3"` | 0 | PASS — default is `autonoma`; a fresh process reports persisted `consultiva`; `rdd` persists and is explained. |

## Observable results

- `--posturas` renders all three explanations and the runtime channel; absent config defaults to `autonoma`, preserving existing behavior.
- After `--postura consultiva`, a new process renders `actual: consultiva`; config contains `postura = "consultiva"`.
- `postura_gate` focused test asserts three distinct outcomes for one scenario: `actua`, `propone_y_espera`, and `pregunta_antes_delegar`.
- `--metodologia rdd` followed by `--metodologias` renders `preferencia actual: rdd`, the TDD-strict/RDD explanation, and SDD explanation; config contains `metodologia_preferida = "rdd"`.
- Focused reconciliation test confirms RDD names ADR-0022/`strict-tdd` and does not introduce a second strict-TDD toggle.

## Summary JSON

```json
{"artifact":"bec3dcfb2cdd06b98fb4ab82d6490a3858f0a5a9","focused_tests":{"exit":0,"passed":8},"runtime_cli":{"exit":0,"default":"autonoma","persisted_postura":"consultiva","persisted_metodologia":"rdd"},"status":"PASS"}
```
