---
name: safe-implementation
description: Ship the smallest safe diff that satisfies the task — preserve public APIs and data contracts, resist opportunistic refactors, confirm uncertain or versioned APIs via context7, then run focused tests and verify.sh. Load when implementing or fixing against a defined scope.
license: MIT
compatibility: opencode
metadata:
  enabled_for: implementer, debugger
---

# Safe Implementation

## When to use
Implementing a task, acceptance criterion, or bug fix where scope is defined and regressions are costly. Use whenever you are about to change working code.

## Cycle / Checklist
1. **Scope** — restate exactly what must change; everything else stays untouched.
2. **Locate** — find the minimal set of files and symbols to edit.
3. **Confirm APIs** — for any uncertain, external, or versioned API, load context7 and verify the real signature before calling it.
4. **Edit small** — make the smallest change that satisfies the task; no drive-by cleanups.
5. **Test focused** — run the tests covering the touched code first for a fast signal.
6. **Verify** — run `verify.sh` (or the project's full gate) before declaring done.
7. **Report** — list changed files, verification results, and the next gate.

## Rules
- Smallest safe diff: change only what the task requires.
- No opportunistic refactors, renames, or formatting sweeps mixed into a feature/fix.
- Preserve public APIs, signatures, and data contracts unless the task is explicitly to change them.
- Do not invent API shapes — verify versioned/external calls via context7.
- **Stop conditions**: ambiguous requirement, repeated test failure with no clear cause, or work drifting out of scope — stop and report instead of guessing.

## Inputs / Outputs
- **Inputs**: the task/acceptance criteria, the relevant files, and the verification command.
- **Outputs**: a minimal diff, the list of changed files, focused-test and verify.sh results, and the next gate (review, PR, or follow-up).
