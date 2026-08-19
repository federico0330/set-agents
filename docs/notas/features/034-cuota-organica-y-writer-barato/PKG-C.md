# 034-cuota-organica-y-writer-barato · PKG-C

<!-- notas:auto -->
## Motivo

- objetivo: Techo frontier 4/16 distinto de max_spawns; percent green-on-first-attempt en cost-report S2
- ruteo: cursor-host native subagent; no --route-decide (032); inherit → implementer (inherit)
- complejidad: medium
- riesgo: high
- paths: `ai/scripts/feature_state_lib/model.py`, `ai/scripts/feature-state.py`, `ai/scripts/feature_state_lib/cli_lifecycle.py`, `ai/scripts/feature_state_lib/render_status.py`, `ai/scripts/cost-report.py`, `tests/test_harness.py`
- depende de: PKG-B

## Tareas

- [x] T-C01 (completed) · unittest cheap spawn no increment; salvage and reviewer yes; P001 no; MODE_BUDGETS scoped=8
- [x] T-C02 (completed) · 5th frontier dies FRONTIER_CAP_EXHAUSTED; max_spawns=8; STATUS frontier 4/4 pkg · 4/16 feat
- [x] T-C03 (completed) · cupo full + salvage/promote HUMAN_DECISION_REQUIRED; reopen resets package frontier_used only
- [x] T-C04 (completed) · cost-report S2 % green-on-first-attempt + frontier; salvage-green bite 1/2 not 2/2; lines 26-30 intact; heartbeat build.sh --check BUILD_CHECK_PASS

## Hallazgos

- SEC-001 [high] closed — security

## Recorrido

- review: repair_required (1 hallazgos)
- verificación: 0 refutados, 1 sostenidos
- repair: SEC-001 → 3 archivos
- delta review: pass
- testing: pass
- runtime QA: pass (waived)
- gate `P001`: pass
- gate `focused-tests`: pass
- gate `build-check`: pass

context pack: `docs/specs/034-cuota-organica-y-writer-barato/context/PKG-C.md`

↩ [[features/034-cuota-organica-y-writer-barato|034-cuota-organica-y-writer-barato]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
