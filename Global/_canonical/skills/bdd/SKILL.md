---
name: bdd
description: Behavior-Driven Development — the behavioral validation layer between SDD and package implementation. Turn business rules into Given-When-Then scenarios in acceptance.md and verify packages/integration against observable behavior.
license: MIT
compatibility: opencode
metadata:
  enabled_for: product-analyst, test-writer, orchestrator, runtime-verifier, package-reviewer
---

# Behavior-Driven Development (BDD)

## When to use
After SDD has fixed the WHAT (spec + rules + contracts), before package planning/implementation. BDD validates
observable behavior and bridges product intent to technical verification.

## Flow
1. For each business rule in `spec.md`, write one or more scenarios in `acceptance.md` as Given / When / Then.
2. Describe what the user/actor observes, not internal calls or fields.
3. Cover happy path and important business failures: conflict, expiry, empty, unauthorized, limits.
4. Hand scenarios to `package-planner` and `package-reviewer`; after behavior converges, `test-writer` derives
   end-stage regression tests and `runtime-verifier` confirms running behavior when applicable.

## Layering
- **SDD** = intent: rules, contracts, invariants, security constraints, architecture.
- **BDD** = observable whole-system behavior in business language.
- **Regression tests** = proof of accepted behavior after package review/delta review.

## Human connection point
Before implementation, walk the user through scenarios, actor -> action -> observable outcome, and invite changes.
Implementation starts only after the scenarios and spec are aligned and approved.

## Verification
Every scenario must map to at least one package review check and, after convergence, at least one regression or
runtime verification path. Unverified behavior is a gap, not a pass.

## Output
`acceptance.md` with Given-When-Then scenarios ready for package planning, package review, regression tests, and
runtime verification.
