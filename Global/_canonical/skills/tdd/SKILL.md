---
name: tdd
description: Test-Driven Development — red (failing test) → green (minimal code) → refactor. Tests prove behavior and are never weakened to pass. Load when implementing against acceptance criteria.
license: MIT
compatibility: opencode
metadata:
  enabled_for: test-writer, implementer, debugger
---

# Test-Driven Development (TDD)

## When to use
Implementing behavior with acceptance criteria, or hardening untested code before changing it.

## Cycle
1. **Red** — write a test that fails for the right reason (proves it can fail before it passes).
2. **Green** — write the smallest production code that makes it pass.
3. **Refactor** — clean up with the test net green; behavior unchanged.

## Rules
- Assert behavior and contracts, not internals.
- Deterministic: inject time, seed randomness, fake network/IO — no real clock/network in unit tests.
- Cover failure/edge paths the spec cares about (conflict, expiry, empty, unauthorized, limits).
- For concurrency, write a test that actually races two operations and asserts exactly one wins.
- NEVER skip/`only`/delete/weaken assertions to get green. A weakened test is a failed gate.

## Inputs / Outputs
- In: acceptance criteria + design contract. Out: failing tests (red) handed to the implementer, then green.
