# 033-menos-espera-menos-cuota · PKG-1

<!-- notas:auto -->
## Motivo

- objetivo: Una sola dimension opencode: colapsar go-zen/zen/openai-only en un solo valor por area
- ruteo: cursor-host native subagent; no route-decide → implementer (inherit)
- complejidad: high
- riesgo: high
- paths: `models.toml`, `ai/scripts/models_config.py`, `ai/scripts/setup_models.py`, `ai/scripts/generate.py`, `build.sh`, `active-profile`

## Tareas

- [x] models.toml: 38 mapas de tres lanes pasan a string, conservando el valor go-zen (completed) · test_opencode_cells_reject_a_restored_lane_map, conservation list in PKG-1-implementer.md
- [x] models_config: sacar LANES, active_profile y auto_profile; adaptar resolve_role y load_role_tiers (completed) · test_manual_lane_scripts_and_profile_axis_are_gone, test_generate_rejects_the_dead_profile_flag
- [x] setup_models y build.sh: sacar el eje lane de la UI y del flag --profile (completed) · test_campo_is_exactly_the_four_axes, BUILD_CHECK_PASS
- [x] AC-1.6: prueba de que un proveedor agotado falla ruidoso o rutea a otro, nunca en silencio (completed) · test_ac16_exhausted_provider_fails_loudly_naming_provider_and_action, bite RED ModelsError not raised; GREEN after cp
- [x] reescribir los 7 archivos de test que fijan las tres lanes conservando su invariante (completed) · unittest probe/wizard/decide/spawn 76 OK, test_auto_profile.py deleted with invariant note in evidence and commit body if present

## Recorrido

- review: pass (0 hallazgos)
- testing: pass
- runtime QA: pass
- gate `check-owned-paths`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass
- gate `risk-classification`: pass
- gate `verify`: pass

## Spawns

- SPAWN-001 implementer · modelo cursor/inherit
- SPAWN-002 package-reviewer · modelo cursor/inherit
- SPAWN-003 security-auditor · modelo cursor/inherit

context pack: `docs/specs/033-menos-espera-menos-cuota/context/PKG-1.md`

↩ [[features/033-menos-espera-menos-cuota|033-menos-espera-menos-cuota]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
