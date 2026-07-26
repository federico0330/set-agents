# Work items

## P1 — Routing core

- P1-T1: implement schema-1 migration and schema-2 runtime/orchestrator/routing configuration.
- P1-T2: implement `TaskEnvelope`, eligibility filters, tiering, route ranking, independent-review policy, and
  single-fallback behavior.
- P1-T3: implement proportional flow plans, checkpoint policy, and allowlisted `harness_gate`.
- P1-T4: implement privacy-safe route/spawn telemetry and aggregated reports.
- P1-T5: expose route explanation and routing report CLI commands with focused tests.

## P2 — Pi runtime

- P2-T1: select and integrity-lock exact Pi runtime dependencies.
- P2-T2: generate Pi role artifacts from canonical sources and validate semantic parity.
- P2-T3: add managed Pi install/update/drift/status/rollback behavior.
- P2-T4: implement fresh-context child launch contracts with minimum tools and no delegation.
- P2-T5: implement Pi hard-denies, protected-path checks, and redaction.
- P2-T6: expose Pi doctor checks without credential access or disclosure.

## P3 — Integration and rollout

- P3-T1: add catalog, outage, fallback, partial-write, risk, and low-risk flow integration fixtures.
- P3-T2: add disposable benchmark commands and privacy-safe evidence format.
- P3-T3: document Pi opt-in, rollback, upstream doctrine, deliberate deviations, and disabled bridge.
- P3-T4: repair the baseline bootstrap test so it reflects observed installed/missing tools.
- P3-T5: run global reproducibility, lifecycle, policy, regression, and shell gates.
