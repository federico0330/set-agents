---
name: regression-tests
description: End-stage regression tests written after package review/delta review converges, as proof of accepted behavior. Tests are never the approval gate and must assert real expected values.
license: MIT
compatibility: opencode
metadata:
  enabled_for: test-writer
---

# Regression Tests

## When to use
After package behavior has converged through independent review, or after final integration has converged.
Never write tests to replace spec review, and never weaken tests to pass.

## Why tests are not approval
A passing test can still encode the wrong expectation. The approval gate is independent review against the
approved spec/package contract. Regression tests lock in accepted behavior for the future.

## Procedure
1. Read accepted package summary, BDD acceptance criteria, and implementation.
2. For each criterion, write a test asserting the observable expected behavior from the spec.
3. Cover important failure/edge paths.
4. Run the relevant suite. If a test fails, report it as a real signal; do not loosen assertions.

## Rules
- Assert behavior and contracts, not internals.
- Keep tests deterministic.
- For concurrency, actually race operations and assert exactly one wins.
- Never skip, `only`, delete, or weaken assertions.

## Output
Passing regression tests traced to acceptance criteria and package ids.
