# 004-adaptive-dispatch · P3-pi-lane

<!-- notas:auto -->
## Motivo

- objetivo: Pi as fourth executable runtime: true cross-provider per-spawn model selection via pi --model CLI subprocess, consuming --route-decide; managed pinned install + doctor; probe pairs + PI_SIMULATION_ONLY flip
- ruteo: New runtime axis (4th executable runtime, live model selection); in-session Claude implementer, independent gates+panel… → implementer (claude-in-session)
- complejidad: high
- paths: `docs/adr/0007-pi-lane.md`, `ai/scripts/set_agents_spawn.py`, `ai/scripts/routing_core/catalog.py`, `ai/scripts/routing_core/service.py`, `ai/scripts/models_config.py`, `models.toml`, `ai/scripts/generate.py`, `ai/scripts/install.py`, `ai/scripts/set_agents_app.py`, `tests/test_routing.py`, `tests/test_harness.py`, `docs/architecture/overview.md`, `docs/specs/004-adaptive-dispatch/context/P3-pi-lane.md`, `docs/specs/004-adaptive-dispatch/evidence/P3-*`

## Tareas

- [x] T-301 (completed) · ADR-0007 written (CLI-subprocess vs SDK w/ live proof, guards-as-flags, model-id map, flip conditions); managed pinned pi install (PI_PINNED_VERSION/pi_pinned_argv) + --doctor --harness pi (version+auth key-set+list-models, no token dump)
- [x] T-302 (completed) · minimal pi target: validate_pi_target in generate.py; no generated pi tree; spawner passes canonical role prompt via --append-system-prompt; fresh-context/no-delegation/depth-0
- [x] T-303 (completed) · set_agents_spawn.py CLI-subprocess spawner: spawn/route_and_spawn/doctor; JSON stream parse agent_start->agent_settled; decided-model verification via message.model; crash(exit!=0/missing settled)=>failure; P1 lifecycle integration. Live: openai-codex full success
- [x] T-304 (completed) · guards as flags + per-guard tests: --no-session fresh ctx, --no-extensions depth-0 (live: zero delegation tool at widest tier), read-only allowlist until green (live: read-only child could not write when asked)
- [x] T-305 (completed) · (pi,openai-codex)+(pi,anthropic) pairs + _parse_pi_models + pi_auth_provider_keys (positives-only); PI_MODEL_MAP (openai-codex identity; anthropic opus->claude-opus-4-8/sonnet->claude-sonnet-5/haiku->claude-haiku-4-5); PI_SIMULATION_ONLY flip service.py:132 gated on doctor; overview.md updated. Live-QA fixed real -- separator bug

## Hallazgos

- PKG-N01 [low] closed — integration
- PKG-N02 [low] closed — scalability
- PKG-N03 [low] accepted — correctness
- PKG-N04 [low] accepted — correctness
- SEC-A01 [high] closed — security
- SEC-A02 [medium] closed — security
- SEC-A04 [low] closed — security
- SEC-A05 [low] closed — security

## Recorrido

- review: repair_required (8 hallazgos)
- repair: SEC-A01, SEC-A02, SEC-A04, SEC-A05, PKG-N01, PKG-N02 → 6 archivos
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `p3-package-gates`: pass
- gate `r1-post-repair-verification`: pass

context pack: `docs/specs/004-adaptive-dispatch/context/P3-pi-lane.md`

↩ [[features/004-adaptive-dispatch|004-adaptive-dispatch]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
