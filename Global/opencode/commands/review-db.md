---
description: Data integrity / DB review of the diff
agent: db-auditor
---
Read-only DB review of the current diff (or: $ARGUMENTS).
Check atomic transactions, working optimistic concurrency, validate-before-mutate, auditing of failed
attempts, money types, and safe migrations. Return DB_PASS or findings (DB- schema).
