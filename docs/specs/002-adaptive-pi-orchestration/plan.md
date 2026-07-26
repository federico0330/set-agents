# Implementation plan

1. Establish the approved contract, BDD scenarios, ADR, baseline evidence, and challenge corrections.
2. Implement schema-2 configuration, deterministic routing contracts/policies, privacy-safe telemetry, native gates,
   and CLI explanation/reporting.
3. Implement Pi generation and managed lifecycle with pinned dependency metadata, child isolation, and hard-denies.
4. Integrate parity/golden/security/migration/simulation tests and update user/operator documentation.
5. Run package gates, independent reviews, consolidated repair/delta review, end-stage regressions, integration
   verification, and final judge.

## Package candidates

- `P1-routing-core`: configuration schema, catalog, router, flow policy, telemetry, CLI, and native gates.
- `P2-pi-runtime`: Pi generation, dependency lock, lifecycle, doctor, child runner, and permission guards.
- `P3-integration-docs`: four-runtime parity, rollout/upstream documentation, benchmark harness, and global evidence.

## Decision points

- Exact audited Pi package versions and integrity values come from authoritative package metadata.
- Live OAuth smoke and real IEY benchmark execution require locally available authenticated providers/projects;
  deterministic simulations remain the CI acceptance floor.
- Pi stays opt-in until the stated operational sample is complete.
