# 011-quota-failover · P1-quota-failover

<!-- notas:auto -->
## Motivo

- objetivo: Atomically classify the exact settled Anthropic/Pi quota exhaustion, preserve its failed dispatch and authorize at most one stored-fallback linked replacement while globally excluding the exhausted provider until next UTC day.
- ruteo: atomic routing lifecycle and accounting require high-capability implementation → implementer (hosted coding model)
- complejidad: high
- riesgo: SQLite migration/schema integrity
- riesgo: transaction concurrency/idempotency
- riesgo: accounting integrity
- riesgo: reviewer independence
- riesgo: external-E2E precondition
- paths: `ai/scripts/routing_core/store.py`, `ai/scripts/routing_core/service.py`, `ai/scripts/routing_core/domain.py`, `ai/scripts/set_agents_spawn.py`, `ai/scripts/set_agents_app.py`, `tests/test_routing.py`, `tests/test_harness.py`, `docs/specs/011-quota-failover/evidence/`

## Tareas

- [x] additive schema/migration and invariants (completed) · tests/test_routing.py
- [x] narrow classifier + Pi terminal plumbing (completed) · tests/test_routing.py
- [x] BEGIN IMMEDIATE close/exhaust/authorize idempotent transition + selection exclusion (completed) · tests/test_routing.py
- [x] deterministic routing/migration/concurrency tests (completed) · tests/test_routing.py
- [x] credential-gated real exhausted-provider E2E runner/evidence (completed) · tests/test_routing.py

## Recorrido

- review: pass (0 hallazgos)
- testing: pass
- runtime QA: pass
- gate `verify.sh`: pass
- gate `build-check`: pass

context pack: `docs/specs/011-quota-failover/context/P1-quota-failover.md`

↩ [[features/011-quota-failover|011-quota-failover]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
