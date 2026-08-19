# 034-cuota-organica-y-writer-barato · PKG-B

<!-- notas:auto -->
## Motivo

- objetivo: Escritor barato/free que cumple tools; un salvage pesado por paquete; test -fast reescrito no borrado
- ruteo: cursor-host native subagent; no --route-decide (032); inherit → implementer (inherit)
- complejidad: high
- riesgo: high
- paths: `models.toml`, `ai/scripts/feature-state.py`, `ai/scripts/feature_state_lib/model.py`, `ai/scripts/feature_state_lib/cli_repair.py`, `Global/_canonical/agents/orchestrator.md`, `tests/test_harness.py`
- depende de: PKG-A

## Tareas

- [x] T-B01 (completed) · V-B01 inventory + pin opencode/deepseek-v4-flash-free + test_new_feature_does_not_dispatch_implementer_at_fast
- [x] T-B02 (completed) · hot-path rewrite + cp RED/GREEN bite + unittest test_repo_go_zen_routes_hot_path
- [x] T-B03 (completed) · rg -- -fast tests/ remaining hits are not implementer/product-analyst BASE; independence asserts kept
- [x] T-B04 (completed) · record-spawn --salvage + SALVAGE_ALREADY_USED + repair-agent pin cheap
- [x] T-B05 (completed) · cheap-red+salvage-red consecutive=1; second salvage rejected; next_rung base never fast

## Hallazgos

- F-B01 [high] closed — correctness
- F-B02 [medium] closed — correctness

## Recorrido

- review: repair_required (2 hallazgos)
- verificación: 0 refutados, 2 sostenidos
- repair: F-B01, F-B02 → 5 archivos
- delta review: pass
- testing: pass
- runtime QA: pass (waived)
- gate `P001`: pass
- gate `focused-tests`: pass
- gate `build-check`: pass

context pack: `docs/specs/034-cuota-organica-y-writer-barato/context/PKG-B.md`

↩ [[features/034-cuota-organica-y-writer-barato|034-cuota-organica-y-writer-barato]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
