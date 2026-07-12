---
name: feature-contract
description: Produce or evaluate an approved Feature Contract: concise spec, non-goals, acceptance criteria, assumptions, risks, and version/hash before package planning.
license: MIT
compatibility: opencode
metadata:
  enabled_for: product-analyst, architect, spec-challenger, package-planner, orchestrator
---

# Feature Contract

## When to use
Drafting or checking the spec before implementation.

## Required contents
- Problem, users, scope, non-goals.
- Observable behavior and acceptance criteria.
- BDD scenarios in Given-When-Then form.
- Domain invariants and public contracts.
- Risks, assumptions, and explicit decisions.
- Approval marker with version/hash.

## Rules
- Do not leave product decisions implicit.
- Acceptance criteria must be testable and traceable to packages later.
- After approval, do not change criteria without a new human decision.
