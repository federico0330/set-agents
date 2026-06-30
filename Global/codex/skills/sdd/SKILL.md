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
Before implementing any non-trivial change. SDD controls WHAT to build; TDD controls HOW to prove behavior.

## Flow
1. **spec.md** — problem, users, business rules, invariants, in-scope, explicit non-goals.
2. **plan.md** — sequence, dependencies, risks, decision points.
3. **tasks.md** — ordered small tasks `T-001…`, each linked to acceptance criteria and a review gate.
4. **acceptance.md** — each criterion as a testable Given/When/Then with expected result/status.
5. (when architecture/data/security/money) **design.md + ADR** from the architect before implementation.

## Inputs / Outputs
- In: the idea (optionally a brainstorm note). Out: the four docs under `docs/specs/<id>/`, ready for TDD.

## Rules
- Every requirement is observable and testable; no vague "fast/secure" without a measurable bar.
- Mark the first shippable slice; defer the rest to non-goals.
- Make money/identity/audit/concurrency rules explicit when present.
- The spec is the contract: implementation that drifts from it fails audit.
