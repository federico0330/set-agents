---
description: Data integrity / DB review of the diff
agent: package-reviewer
---
Read-only data-integrity review of the current diff (or: $ARGUMENTS), focused on the data-integrity
checklist: atomic transactions, working optimistic concurrency, validate-before-mutate, auditing of failed
attempts, money types, and safe migrations. Return findings with `category: data-integrity`, or note no
concrete findings.
