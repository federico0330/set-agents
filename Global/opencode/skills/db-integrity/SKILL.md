---
name: db-integrity
description: Data integrity checklist — atomic transactions, working optimistic concurrency, validate-before-mutate, auditing failed attempts, money types, safe migrations. Load when touching schema, money, transactions, concurrency, or audit trails.
license: MIT
compatibility: opencode
metadata:
  enabled_for: db-auditor, architect, implementer, debugger
---

# DB Integrity

## When to use
Any change touching schema, migrations, money, multi-step writes, optimistic concurrency, duplicate
detection, reconciliation, or audit trails.

## Inputs
`git diff`, the data model / entities, repository & transaction code, migrations, active acceptance criteria.

## Outputs
`DB_PASS` or findings (`id, severity, file:line, evidence, impact, minimal_fix, verification`).

## Checklist (each item = a concrete check)
1. **Atomicity** — Writes that must succeed together run in ONE transaction. Reject multiple independent
   `SaveChanges`/commits that can leave a half-done state if the process dies mid-way.
   - Good: `BeginTransaction → mutate seat + reservation + auditlog → Commit` (rollback on catch).
2. **Concurrency actually fires** — The version token is incremented in the SAME write. Prefer a single
   atomic conditional UPDATE: `WHERE Id=@id AND Version=@read` then check rows-affected; 0 ⇒ conflict.
   Reject `Version++` placed after `SaveChanges` (dead code — the conflict never triggers).
3. **Validate before mutating** — exists (404), not already done (409), not expired (409) BEFORE money moves.
4. **Audit the failed attempt** — every attempt (success AND failure) is recorded; the failure record uses
   its OWN unit of work / `SaveChanges`, NOT the rolled-back transaction (else it silently disappears).
5. **Money** — integer minor units or exact decimal; never binary floating point.
6. **Migrations** — reversible, no silent data loss/reinterpretation; constraints/indexes for tenancy,
   FKs, statuses, duplicate uniqueness; duplicates proposed for human review, never auto-merged.

## Verification ideas
After a concurrency test: exactly one writer wins (one 409), and `SELECT * FROM AuditLog` shows ALL attempts,
losers included. Kill the process between steps in a test/staging harness → no half-committed state remains.
