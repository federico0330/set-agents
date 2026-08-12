# 019-harness-evolution · P1-provider-auto-adoption

<!-- notas:auto -->
## Motivo

- objetivo: Auto-adopcion de providers autenticados y verificables del runtime opencode: discovered_providers='auto', fuente unica provider->prefijo CLI, guardas de inferencia (cap balanced, reviewer stem fail-closed, flag is_inferred en el sort key), parse de auth corregido y probe-cache con key versionada (ADR-0034)
- complejidad: high
- riesgo: suite-contrato test_routing.py pinea defaults y frases; copilot autenticado sin modelos listables debe fallar cerrado
- paths: `ai/scripts/routing_core/catalog.py`, `ai/scripts/routing_core/service.py`, `ai/scripts/routing_core/inference.py`, `ai/scripts/models_config.py`, `ai/scripts/opencode_spawn.py`, `docs/adr/0034-auto-adopted-providers.md`, `tests/test_discovered_routes.py`, `tests/test_probe_subscriptions.py`

## Tareas

- [x] Medicion viva ya hecha: ver spec 'Medicion en vivo' (M-1..M-4); copilot fail-closed (completed) · implementer P1: ADR-0034 + codigo + tests; verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, 815 tests OK, ownership PASS
- [x] models_config: discovered_providers='auto' + default + emit round-trip + DISCOVERABLE_PROVIDERS lockstep (completed) · implementer P1: ADR-0034 + codigo + tests; verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, 815 tests OK, ownership PASS
- [x] service.build_effective_snapshot: derivar providers del inventario probeado interseccion _PAIR_COMMANDS (completed) · implementer P1: ADR-0034 + codigo + tests; verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, 815 tests OK, ownership PASS
- [x] Fuente unica provider->prefijo CLI compartida catalogo/spawners; PROVIDER_UNSUPPORTED solo para lo desconocido (completed) · implementer P1: ADR-0034 + codigo + tests; verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, 815 tests OK, ownership PASS
- [x] Guardas: inference cap balanced (fuera _FRONTIER_HINTS), reviewer stem fail-closed REVIEW_IDENTITY_UNRESOLVED_INFERRED, is_inferred en sort key (completed) · implementer P1: ADR-0034 + codigo + tests; verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, 815 tests OK, ownership PASS
- [x] Parse auth: filas circulo-vacio no autenticadas; nunca heuristica espacio->guion (completed) · implementer P1: ADR-0034 + codigo + tests; verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, 815 tests OK, ownership PASS
- [x] Probe-cache: auth fresca por composicion, cache solo de listados, key con mtime del binario + schema version, re-rank tras reprobe fallido (completed) · implementer P1: ADR-0034 + codigo + tests; verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, 815 tests OK, ownership PASS
- [x] Pins/preferencias validan contra snapshot efectivo vivo (completed) · implementer P1: ADR-0034 + codigo + tests; verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, 815 tests OK, ownership PASS
- [x] ADR-0034 + indice + reescritura test-por-test de los contratos afectados (completed) · implementer P1: ADR-0034 + codigo + tests; verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, 815 tests OK, ownership PASS

## Hallazgos

- F-01 [medium] closed — testing
- F-02 [medium] closed — integration
- F-03 [low] closed — testing
- F-04 [low] closed — resilience
- F-05 [low] closed — readability
- F-06 [low] closed — integration
- D-01 [low] closed — testing

## Recorrido

- review: repair_required (6 hallazgos)
- verificación: 0 refutados, 2 sostenidos
- repair: F-01, F-03, F-04, F-05 → 4 archivos
- repair: D-01 → 2 archivos
- repair: F-02 → 2 archivos
- delta review: repair_required
- delta review: pass
- testing: pass
- testing: pass
- runtime QA: pass
- runtime QA: pass
- gate `ownership-check`: pass
- gate `build-check`: pass
- gate `unit-suite`: pass

## Spawns

- SPAWN-001 implementer · modelo openai-codex/gpt-5.6-terra · effort high · route run1_0cfd681259db860bf92c208e31194547

context pack: `docs/specs/019-harness-evolution/context/P1-provider-auto-adoption.md`

↩ [[features/019-harness-evolution|019-harness-evolution]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
