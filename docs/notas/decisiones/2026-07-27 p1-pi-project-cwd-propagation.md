# Pi lifecycle propagates project context by explicit cwd

<!-- notas:auto -->
- fecha: 2026-07-27 · actor: orchestrator
- alcance: [[features/005-portable-harness|005-portable-harness]] · [[features/005-portable-harness/P1-portable-core|P1-portable-core]]

## Contexto

P1-DLT-001 showed SET_AGENTS_PROJECT written by a set_agents_app subprocess cannot affect its set_agents_spawn parent. P1-DLT-002 requires durable guest identity evidence.

## Decisión

Pass one routing_cwd from route_and_spawn into all three lifecycle app-CLI subprocess calls; keep APP_CLI absolute and store location unchanged. Guest proof reads dispatches.project_key from the hermetic SQLite database.

## Consecuencias

Ownership expands only to ai/scripts/set_agents_spawn.py. The prior D5 environment-export mechanism is compatibility-only and no longer relied on for Pi.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
