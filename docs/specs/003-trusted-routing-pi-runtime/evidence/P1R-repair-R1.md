# P1R-R1 — consolidated repair evidence

Baseline reviewed: `51b84e3f8782789ac532d0c0e50167cf917a7eda` (never `HEAD`).

| Findings | Root cause repaired | Changed surface | Verification evidence |
|---|---|---|---|
| PKG-001, SEC-001 | A caller-constructible decision crossed the durable authorization boundary. | `domain.py`, `service.py`, `store.py`, `test_routing.py` | One-use opaque permit, CSPRNG `run1_` shape, snapshot identity revalidation, roster-derived writer class, terminal actual identity review test. |
| PKG-003, SEC-002, SEC-003 | Synthetic auth/default inventory and simulation shared mutation composition. | `catalog.py`, `routing.py`, `set_agents_app.py`, tests | Closed pair argv probe table; missing/nonzero/ambiguous probe makes that pair unavailable; simulation owns no store/permit and emits only explanatory decision. |
| PKG-004 | Facts were TTL-reusable and arbitrary-version values could be accepted. | `domain.py`, `service.py`, tests | Internal scope capability, exact `routing-v2` version, 30s freshness, single-scope identity and conservative caller conflict test. |
| PKG-007, SEC-006 | Catalog carried dynamic runtime and used non-contract encoding/partial roster. | `routes.v1.toml`, `domain.py`, `catalog.py`, tests | Exact closed TOML schema, no runtime key, length-prefixed static binding, truncation collision rejection and complete canonical roster coverage. |
| PKG-002, PKG-005, SEC-004, SEC-005 | Path/state checks mutated before validation and adopted unknown SQLite. | `store.py`, tests | Fixed production root, explicit test-only root injection, no-follow `lstat`, private identities/modes, exclusive first init, integrity/meta/table validation before use. |
| PKG-006, SEC-008 | Lifecycle transitions had no complete constrained state/audit unit. | `store.py`, `service.py`, tests | `BEGIN IMMEDIATE` transitions record allowlisted event+rollup atomically; replay/rejection audit uses independent transaction; fallback/partial/terminal state is sticky. |
| PKG-008 | Retention/report used seconds and unindexed approximation. | `store.py`, tests | UTC milliseconds, transactional 90-day/10k deletion, insertion-time rollups, compaction-only counter, access indexes and nearest-rank retained all/per-route percentiles. |
| PKG-009 | Tests asserted implementation shape rather than attack boundary. | `tests/test_routing.py`, `routing_core/gates.py` | Focused suite covers scope/facts, pair isolation, Pi, opaque authorization, fallback closure, terminal writer review, no-state explain and immutable gate argv. |
| PKG-010, SEC-007 | CLI could use raw error text and accept conflicting routing modes. | `routing.py`, `set_agents_app.py`, tests | Schema-2 redacted envelope, stable 0/1/2 routing handling, corrected strict legacy regex and conflict rejection. |

## Commands run

| Command | Exit | Timing |
|---|---:|---:|
| `python3 -m unittest discover -s tests -p 'test_routing.py' -v` | 0 | 20.5s |
| two named `tests.test_harness.HarnessTests` regressions | 0 | 0.48s |
| `python3 ai/scripts/setup_models.py --check` | 0 | <1s |
| required `py_compile` set | 0 | <1s |
| `RoutingTests.test_gate_and_telemetry_negative_cases` | 0 | 0.09s |
| `./ai/scripts/verify.sh` (independent rerun) | 0 | ~47s |
| `git diff --check` | 0 | <1s |

## Residual reasoning

Python's SQLite API opens by verified pathname rather than a retained descriptor. The adapter validates before and after opening and fails closed on detected replacement. A malicious same-UID concurrent path swap remains outside the approved local-state threat model, as ADR-0005 states; no product behavior was invented to claim otherwise. External runtime dispatch remains outside P1R: callers must durably call `mark_dispatched` before external invocation.

## Destilado

El batch reemplaza permisos y hechos falsificables por capacidades internas de un solo uso, cierra el catálogo a datos auditables y vuelve la persistencia conservadora ante corrupción, enlaces y reintentos. La explicación queda sin capacidad de mutar, y los rechazos/transiciones tienen evidencia operativa sin guardar contenido sensible.
