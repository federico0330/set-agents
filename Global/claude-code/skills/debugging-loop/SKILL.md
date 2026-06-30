---
name: debugging-loop
description: Root-cause a failing gate (verify/test/build) and apply the smallest fix, with a regression test and hard stops. Load when a deterministic gate fails.
license: MIT
compatibility: opencode
metadata:
  enabled_for: debugger, implementer
---

# Debugging Loop

## When to use
`ai/scripts/verify.sh` fails, a test fails, or a build breaks.

## Inputs
`ai/state/verify.log`, the failing output, the diff, the active task.

## Outputs
Root cause · minimal fix · verification result · regression test (added if missing).

## Procedure
1. Reproduce deterministically. Read the actual failure, not a guess.
2. Form a ROOT-cause hypothesis (not the symptom); confirm before editing.
3. Apply the minimal fix; add a regression test that fails before / passes after if none exists.
4. Re-run the specific check, then full `verify.sh`.
5. Stop conditions → `HUMAN_DECISION_REQUIRED`: same failure repeats twice, ambiguous cause, or the fix
   needs a product decision, migration, or secret/prod access.

## Rule
Fix the cause, not the test. Never adjust expectations to silence a failure.
