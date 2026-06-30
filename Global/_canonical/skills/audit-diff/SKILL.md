---
name: audit-diff
description: Read-only diff audit against spec/tasks/acceptance — scope control, test integrity, edge cases, actionable findings with a strict schema. Load after implementation, before declaring a task done.
license: MIT
compatibility: opencode
metadata:
  enabled_for: orchestrator, auditor, security-auditor, db-auditor, performance-auditor
---

# Audit Diff

## When to use
After implementation and verify, before a task is marked complete.

## Inputs
`git diff`, active spec/task/acceptance, verification output, project rules (AGENTS.md).

## Outputs
`AUDIT_PASS: no concrete findings against the provided scope.` or a findings list.

## Procedure
1. Read the task and acceptance criteria FIRST.
2. Inspect the diff in context, not files in isolation.
3. Scope control: no opportunistic refactors, no unrelated churn.
4. Test integrity: tests prove the behavior and were not weakened/skipped.
5. Failure paths and edge cases covered.
6. Produce ONLY actionable findings.

## Finding schema
```
- id: AUD-001
  severity: blocker|major|minor
  file: path/to/file.ext:line
  evidence: exact code/behavior
  impact: why it matters
  minimal_fix: smallest safe change
  verification: command/test/check that proves the fix
```

## Rule
Never patch code here. Never approve on the implementer's word. Vague comments are not findings.
