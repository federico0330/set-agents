---
name: repair-loop
description: Turn concrete audit findings into minimal fixes, re-verify, and re-audit — without expanding scope or weakening tests. Load when an audit produced actionable findings.
license: MIT
compatibility: opencode
metadata:
  enabled_for: orchestrator, implementer, debugger, auditor
---

# Repair Loop

## When to use
After an audit produced concrete findings (blocker/major/minor).

## Inputs
Findings file/output, active task/spec, current diff.

## Outputs
Minimal repair diff · full verification result · re-audit result.

## Procedure
1. Parse findings; reject vague ones (send back for evidence).
2. Sort blocker → major → minor.
3. For each finding, make ONLY the minimal fix. Do not batch unrelated repairs.
4. Run the finding-specific verification, then full `ai/scripts/verify.sh`.
5. Re-run the SAME auditor (read-only, fresh context) to confirm closure.
6. Stop after `MAX_ITER` or if the same finding/state repeats → `HUMAN_DECISION_REQUIRED`.

## Rules
- Never modify acceptance criteria or weaken tests to close a finding.
- The implementer cannot mark a finding resolved without a re-audit.
- A finding that reappears twice is a stop condition, not a third attempt.
