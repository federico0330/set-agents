---
name: blue-team-hardening
description: Convert red-team and security findings into layered defenses — server-side authz, atomic conditional writes, least privilege, deny-by-default, detection/logging, and response controls — each with a test that proves the attack is blocked. Load when turning confirmed findings into durable mitigations.
license: MIT
compatibility: opencode
metadata:
  enabled_for: blue-team, security-auditor, implementer
---

# Blue Team Hardening

## When to use
After RED-/SEC- findings exist, to design and implement defenses that provably close them at the right layer.

## Inputs
- Confirmed RED-/SEC- findings, the affected code, the auth/data model, logging/alerting infrastructure.

## Outputs
- One hardening entry per finding on the schema below, plus the test that proves the mitigation.

## Layers
- **Prevention (right layer)**: enforce authz server-side, not in the client. Replace check-then-write with atomic conditional writes (`UPDATE ... WHERE status='held'`) to kill races. Apply least privilege and deny-by-default — allowlist, never blocklist.
- **Detection/logging**: log every sensitive attempt, success AND failure, with actor, timestamp, resource, and outcome. Persist the FAILED attempt in its OWN unit of work (separate transaction) so it survives the rollback of the rejected operation.
- **Response**: rate-limit/lockout on repeated failures, alerting on anomaly thresholds, degraded/safe mode under attack.
- **Proof**: write a test that reproduces the red-team scenario and asserts it is now blocked.

## Finding schema
- `id`: BLUE-001
- `addresses`: RED-001 | SEC-003 (the finding id it closes)
- `layer`: prevention | detection | response
- `mitigation`: the concrete defensive change
- `detection`: what is logged/alerted and where
- `test_to_prove`: the test that replays the attack and asserts it fails
- `residual_risk`: what remains unmitigated and why it is acceptable

## Rules
- Fix at the deepest correct layer — prefer DB/atomic and server-side controls over UI guards.
- Every mitigation ships with `test_to_prove`; an untested mitigation is not done.
- Log failures durably in their own transaction — a rolled-back attempt must still leave an audit trail.
- Name residual risk honestly; do not claim a finding is fully eliminated when it is only reduced.
