---
name: safe-refactor
description: Behavior-preserving refactoring only — establish a green baseline (add characterization tests if coverage is thin), apply one small transformation at a time, run tests after each step, and revert immediately on any behavior change. Load when restructuring code without changing what it does.
license: MIT
compatibility: opencode
metadata:
  enabled_for: refactor-specialist, implementer, auditor
---

# Safe Refactor

## When to use
Improving structure, names, or design of working code while keeping observable behavior identical. Use when the goal is readability or maintainability, not new behavior.

## Cycle / Checklist
1. **Green baseline** — run the tests; they must pass before you start.
2. **Cover the seam** — if coverage around the target is thin, add characterization tests that pin current behavior first.
3. **One transformation** — apply a single small move: extract, rename, inline, or move.
4. **Re-run tests** — after each step the suite must stay green.
5. **Commit the step** — keep refactor commits separate from any behavior change.
6. **Repeat** — small step, test, commit, until the structure is right.

## Rules
- Behavior-preserving only: inputs and outputs, including edge cases, stay identical.
- One transformation per step; never batch extract + rename + move into one untested jump.
- Tests run after every step; if any test changes behavior, revert that step.
- Never weaken or delete a test to make a refactor pass.
- Keep refactor and behavior change in separate commits/PRs.
- **Escalate** — if refactoring surfaces a real bug, stop, report it, and let it be fixed as its own change; do not silently "fix" it mid-refactor.

## Verification ideas
- Full suite green before and after every step.
- Diff review: does any branch, condition, or boundary value change? If yes, it is not a pure refactor.
- Characterization tests still pass unchanged — proof behavior is preserved.
