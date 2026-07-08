---
name: sdd
description: Spec-Driven Development — turn intent into spec → plan → tasks → acceptance criteria before code. Load at the start of any non-trivial feature so the WHAT is fixed before the HOW.
license: MIT
compatibility: opencode
metadata:
  enabled_for: orchestrator, product-analyst, architect
---

# Spec-Driven Development (SDD)

## When to use
Before implementing any non-trivial change. The stack is **SDD → BDD → implement⇄audit loop → regression tests**:
SDD fixes the WHAT (intent, rules, contracts), BDD validates the behavior against the business (Given-When-Then),
then the implementation is built and driven to convergence by a read-only auditor (not by tests), and regression
tests are written at the very end as proof of the converged behavior.

## Flow
1. **spec.md** — problem, users, business rules, invariants, in-scope, explicit non-goals.
2. **plan.md** — sequence, dependencies, risks, decision points.
3. **tasks.md** — ordered small tasks `T-001…`, each linked to acceptance criteria and a review gate.
4. **acceptance.md** — each criterion as a testable Given/When/Then with expected result/status. This is the
   BDD behavioral layer (the product↔tech bridge) — apply the `bdd` skill; it feeds the implement⇄audit loop and
   `runtime-verifier`.
5. (when architecture/data/security/money) **design.md + ADR** from the architect before implementation.

## Inputs / Outputs
- In: the idea (optionally a brainstorm note). Out: the four docs under `docs/specs/<id>/`, ready for the
  implement⇄audit loop.

## Rules
- Every requirement is observable and testable; no vague "fast/secure" without a measurable bar.
- Mark the first shippable slice; defer the rest to non-goals.
- Make money/identity/audit/concurrency rules explicit when present.
- The spec is the contract: implementation that drifts from it fails audit.
