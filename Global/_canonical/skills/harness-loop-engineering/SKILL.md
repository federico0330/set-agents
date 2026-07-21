---
name: harness-loop-engineering
description: Package-based harness workflow: approved spec, coherent packages, local validations, deterministic gates, independent package review, consolidated repair, delta review, and hard stops.
license: MIT
compatibility: opencode
metadata:
  enabled_for: orchestrator, architect, debugger, package-planner, integrator
---

# Harness & Loop Engineering

## Idea
Harness engineering designs the verifiable scaffolding around the model: roles, prompts, permissions, skills,
commands, deterministic scripts, audits, gates, and state. Loop engineering defines controlled cycles with hard
stop conditions.

## Canonical package workflow
```
REQUIREMENTS -> SPEC_DRAFT -> SPEC_CHALLENGE -> USER_APPROVAL -> PACKAGE_PLANNING
-> PACKAGE_IMPLEMENTATION -> PACKAGE_GATES -> PACKAGE_REVIEW -> PACKAGE_REPAIR
-> DELTA_REVIEW -> PACKAGE_TESTING -> PACKAGE_RUNTIME_QA -> PACKAGE_ACCEPTED
-> INTEGRATION -> DONE | BLOCKED
```

`PACKAGE_TESTING` (end-stage regression tests) and `PACKAGE_RUNTIME_QA` (observable runtime proof, skipped
only for a package with no runtime surface) are enforced by both the orchestrator and `feature-state.py`. The
CLI is the source of truth for the exact legal transitions.

The independent package review against the approved spec/package contract is the primary review gate. Local tests
keep workers from accumulating broken code; they do not approve the package. Regression tests are written after
package behavior converges and must never be weakened.

## Rules
- Each ordinary task gets local validation.
- Independent packages (dependencies satisfied, disjoint owned paths) advance in parallel — each carries its
  own phase (state schema v2), so one can be in review while another implements. `ready-packages` returns the
  set safe to run at once.
- Deep review happens on the integrated package, not after every task.
- Deep review cycles are bounded by a mode-scaled budget (`MODE_BUDGETS` in `feature-state.py`: 2 for
  feature/scoped, 1 for quick-fix/incident). When the budget is spent, diagnose once and mark `BLOCKED`.
- Findings are consolidated; repairs are consolidated; re-review is delta-focused.
- Reviewers are read-only and independent from implementers.
- Stop when retry budget is consumed, the same state repeats, or a real human decision is required.
- Durable state lives in `ai/state/features/<feature_id>.json`, not in chat.

## Roles vs pieces
- **Agent/subagent**: role with prompt, permissions, model.
- **Skill**: reusable procedure loaded on demand.
- **Command**: invocable prompt such as `/feature-batch`.
- **Gate**: objective pass/fail condition.
- **State**: compact JSON/YAML evidence, not a transcript.

## Golden rule
Whoever implements does not approve. Efficient models may implement bounded package work; capable independent
models challenge specs, review packages, and judge final evidence.
