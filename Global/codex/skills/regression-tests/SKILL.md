---
name: regression-tests
description: End-stage regression tests — written only AFTER the implement⇄audit loop converges, as proof of an already-correct behavior. Tests are never a guardrail to implement (a green test can pass without returning what the spec expects); the read-only auditor is the guardrail. Assert real expected values, never weaken to pass. Load when locking in the converged behavior before declaring a task done.
license: MIT
compatibility: opencode
metadata:
  enabled_for: test-writer
---

# Regression Tests (tests at the end, not as a guardrail)

## When to use
After the implement⇄audit loop has converged — the read-only auditor returned no findings and the implementation
matches the pre-design. You now lock that behavior in with regression tests, before the change is declared done.
NEVER write tests first to drive or gate implementation, and never in a "red phase".

## Why tests are not the guardrail
A passing test does not prove correctness: it can be green while the code returns something other than what the
spec expects (wrong value, wrong shape, right-by-accident). Driving implementation to "make the test pass" just
couples a weak oracle to the code. So the guardrail is the **read-only auditor comparing the implementation
against the fixed spec / design / BDD acceptance**; tests come afterward to catch *future* regressions of a
behavior that is already correct.

## Procedure
1. Read the acceptance criteria and the converged implementation.
2. For each criterion, write a test that asserts the observable behavior the spec requires — the real expected
   value/status, taken from the spec, not from whatever the code currently returns.
3. Run the suite; it should pass against the already-correct implementation (regression proof, not a red phase).
   If a test fails, that is a genuine signal — investigate the code, do not loosen the assertion.

## Rules
- Assert behavior and contracts, not internals.
- Deterministic: inject time, seed randomness, fake network/IO — no real clock/network in unit tests.
- Cover failure/edge paths the spec cares about (conflict, expiry, empty, unauthorized, limits).
- For concurrency, write a test that actually races two operations and asserts exactly one wins.
- NEVER skip/`only`/delete/weaken assertions to get green. A weakened test is a failed gate.

## Inputs / Outputs
- In: BDD acceptance criteria + the converged implementation (post-AUDIT_PASS). Out: passing regression tests
  that lock in the behavior, each traced to its acceptance criterion.
