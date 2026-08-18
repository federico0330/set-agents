---
name: sdd
description: Spec-Driven Development — turn intent into spec, plan, tasks, and acceptance criteria before package planning and code.
license: MIT
compatibility: opencode
metadata:
  enabled_for: orchestrator, product-analyst, architect, spec-challenger, package-planner
---

# Spec-Driven Development (SDD)

## When to use
Before implementing any non-trivial change. SDD fixes the WHAT, BDD validates observable behavior, then approved
work is decomposed into packages for implementation, gates, independent review, repair, and integration.

## Flow
1. `spec.md` — problem, users, business rules, invariants, in-scope, explicit non-goals.
2. `plan.md` — sequence, dependencies, risks, decision points.
3. `tasks.md` — work items linked to acceptance criteria, package candidates, validations, and risk checkpoints.
4. `acceptance.md` — Given/When/Then criteria with expected result/status.
5. `design.md` + ADR when architecture/data/security/money decisions exist.
6. `spec-challenger` reviews before USER_APPROVAL.
7. `package-planner` decomposes only after approval.

## Rules
- Every requirement is observable and testable.
- Make money, identity, audit, authorization, concurrency, and public contracts explicit.
- Mark assumptions as unverified until architecture/data review confirms them.
- The approved spec is the contract; package review fails implementation that drifts from it.
