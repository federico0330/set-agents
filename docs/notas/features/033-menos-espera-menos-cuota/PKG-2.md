# 033-menos-espera-menos-cuota · PKG-2

<!-- notas:auto -->
## Motivo

- objetivo: El menu Modelos no congela: probe asincronico, cache con TTL y degradacion con nombre
- ruteo: cursor-host native subagent; no route-decide → implementer (inherit)
- complejidad: high
- riesgo: medium
- paths: `ai/scripts/setup_models.py`, `ai/scripts/models_config.py`

## Tareas

- [x] primer render antes de 300 ms con lo que ya esta en disco (completed) · unittest tests.test_models_wizard_first_paint, unittest tests.test_models_wizard_ui.test_first_paint_does_not_call_detect_subscriptions
- [x] probe y catalogo de modelos fuera del camino critico, con with_progress (completed) · unittest tests.test_models_wizard_ui.test_refresh_key_probes_via_with_progress_and_redraws, unittest tests.test_harness.TuiTests.test_with_progress_without_a_tty_writes_not_one_byte_to_stdout
- [x] cache en disco con TTL y antiguedad visible, mas tecla de refresco (completed) · unittest tests.test_probe_subscriptions.test_wizard_cache_ttl_starts_at_10_and_60_minutes, unittest tests.test_models_wizard_ui.test_refresh_is_appended_indexes_0_4_stay_pinned
- [x] reemplazar el except Exception mudo de setup_models.py:356-359 por degradacion nombrada (completed) · unittest tests.test_models_wizard_ui.test_refresh_degrades_named_when_probe_raises_and_stays_usable, BUILD_CHECK_PASS

## Hallazgos

- F-PKG2-01 [high] closed — correctness
- F-PKG2-02 [medium] closed — correctness

## Recorrido

- review: repair_required (2 hallazgos)
- verificación: 0 refutados, 2 sostenidos
- repair: F-PKG2-01, F-PKG2-02 → 5 archivos
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `check-owned-paths`: pass
- gate `build-check`: pass
- gate `verify`: pass
- gate `git-diff-check`: pass
- gate `risk-classification`: pass

## Spawns

- SPAWN-001 implementer · modelo cursor/inherit
- SPAWN-002 gate-runner · modelo cursor/inherit
- SPAWN-003 package-reviewer · modelo cursor/inherit
- SPAWN-004 security-auditor · modelo cursor/inherit
- SPAWN-005 finding-verifier · modelo cursor/inherit
- SPAWN-006 repair-agent · modelo cursor/inherit
- SPAWN-007 delta-reviewer · modelo cursor/inherit

context pack: `docs/specs/033-menos-espera-menos-cuota/context/PKG-2.md`

↩ [[features/033-menos-espera-menos-cuota|033-menos-espera-menos-cuota]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
