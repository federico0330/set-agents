# 012-discovered-inventory · P1-discovered-inventory

<!-- notas:auto -->
## Motivo

- objetivo: Reemplazar el catálogo de proveedores escrito a mano por un inventario sondeado del entorno real (OpenCode Zen/Go + los dos existentes), con captura fail-closed, mapa credencial/CLI-id separado, campo curado subscription/metered, y family normalizada entre providers para ids compartidos.
- complejidad: medium
- paths: `ai/scripts/routing_core/catalog.py`, `ai/catalogs/models.toml`, `ai/scripts/models_config.py`, `docs/adr/0016-discovered-inventory.md`, `docs/adr/README.md`, `docs/specs/012-discovered-inventory/**`, `ai/state/features/012-discovered-inventory.json`, `ai/state/STATUS.md`, `ai/state/decisions-log.jsonl`, `ai/state/narrative-log.jsonl`, `docs/notas/**`

## Tareas

- [x] Extender _OPENCODE_PROVIDER_KEYS y agregar el mapa provider->id-CLI (AC-02/AC-03) (completed) · unittest tests.test_routing.RoutingTests.test_ac01_new_pairs_are_registered_in_the_closed_pair_table_only, unittest tests.test_routing.RoutingTests.test_ac02_ac03_credential_and_cli_id_maps_are_independently_addressable
- [x] Mover el allowlist de [catalog] a los 3 sitios de lockstep + agregar ROUTING_PROVIDERS (AC-04/AC-05) (completed) · unittest tests.test_routing.RoutingTests.test_ac04_allowlist_ceiling_moved_in_lockstep_across_the_three_sites, unittest tests.test_routing.RoutingTests.test_ac05_new_providers_are_probeable_not_routable_today, models_config.load_config round-trip check (opencode_zen/opencode_go emit)
- [x] Regla de colisión de family entre providers para ids compartidos (AC-07) (completed) · unittest tests.test_routing.RoutingTests.test_ac07_family_collision_rule_is_pure_and_wired_into_build_snapshot
- [x] Mapa curado subscription/metered a nivel de provider (AC-08) (completed) · unittest tests.test_routing.RoutingTests.test_ac08_subscription_metered_map_is_provider_keyed_not_a_row_field
- [x] Property test de route_id estable con fixture sintético (AC-09) (completed) · unittest tests.test_routing.RoutingTests.test_ac09_route_id_identity_is_provider_agnostic_for_a_synthetic_discovered_row
- [x] Tests deterministas AC-01..AC-10 (exit codes, cache, gates fail-closed) (completed) · unittest tests.test_routing.RoutingTests.test_ac10_probe_fails_closed_on_nonzero_exit_for_the_new_pairs, python3 -m unittest discover -s tests (482 tests, OK)
- [x] P2 local live-parity gate credential-gated (AC-10 verificación) (completed) · unittest tests.test_routing.RoutingTests.test_ac10_p2_local_live_parity_gate (ran LIVE, credentials present, ok)
- [x] docs/adr/0016-discovered-inventory.md + fila en README (completed) · docs/adr/0016-discovered-inventory.md created; docs/adr/README.md row added; 0016 confirmed next free number

## Hallazgos

- F-01 [high] closed — testing
- F-02 [high] closed — testing
- F-03 [medium] closed — testing
- F-04 [medium] closed — integration
- F-05 [medium] closed — correctness
- F-06 [medium] closed — scalability
- F-07 [medium] closed — integration
- F-08 [low] closed — integration
- F-09 [low] closed — integration
- F-10 [low] closed — testing
- F-11 [low] closed — testing
- F-12 [low] closed — correctness
- F-13 [low] closed — integration
- SEC-001 [critical] closed — 
- SEC-002 [medium] closed — security
- N-02 [low] closed — documentation

## Recorrido

- review: repair_required (14 hallazgos)
- verificación: 0 refutados, 14 sostenidos
- verificación: 0 refutados, 2 sostenidos
- repair: SEC-001, F-01, F-02, F-03, F-04, F-05, F-06, F-07, F-08, F-09, F-11, F-12, F-13 → 7 archivos
- repair: SEC-002, F-10, N-02 → 3 archivos
- delta review: repair_required
- delta review: pass
- testing: pass
- runtime QA: pass (waived)
- gate `verify.sh`: pass
- gate `unittest-suite`: pass
- gate `ownership-check`: pass
- gate `git-diff-check`: pass

context pack: `docs/specs/012-discovered-inventory/spec.md`

↩ [[features/012-discovered-inventory|012-discovered-inventory]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
