---
name: audit-diff
description: Read-only diff audit against spec/package/acceptance — scope control, test integrity, edge cases, and a golden catalog of cheap-but-compounding mistakes. Load for focused audits or package review support.
license: MIT
compatibility: opencode
metadata:
  enabled_for: orchestrator, package-reviewer, security-auditor, adversarial-judge
---

# Audit Diff

## Posture — you supervise a cheaper implementer
You review the work of a faster, cheaper implementer that WILL make the mistakes below. Assume it did. Walk the
whole catalog every time, even when the code compiles and the tests pass — "it runs" is not "it's correct". Your
job is to catch the small, cheap-to-fix failures that quietly become debt and vulnerabilities.

## When to use
After package implementation and gates, before a package is accepted; also for focused checkpoints.

## Inputs
`git diff`, approved spec, package/task scope, acceptance criteria, verification output, project rules.

## Procedure
1. Read the task and acceptance criteria FIRST — you audit the implementation against the spec/design/acceptance,
   NOT against a passing test suite. This is the guardrail: does the code actually return what the spec expects?
2. Inspect the diff in context, not files in isolation.
3. Scope control: no opportunistic refactors, no unrelated churn.
4. Test integrity — local validations are expected during package implementation; end-stage regression tests are
   checked once they exist after package convergence. Judge correctness against the spec/package contract, not a
   green suite alone.
5. Failure paths and edge cases covered.
6. **Walk the golden failure catalog below** — for anything the diff touches.
7. Produce ONLY actionable findings.

## Golden failure catalog (the cheap mistakes a fast implementer makes)
Each is a blocking problem when present, even if the app runs. Load the linked skill for the full checklist.
1. **Pagination in memory / none** — `ToListAsync()` then `Skip/Take` in app code. Fix: `Skip/Take` + `CountAsync`
   in SQL, `AsNoTracking`, return `{data,total,page,pageSize}`. → `performance-scalability`.
2. **Non-atomic multi-write** — several `SaveChanges`/commits for writes that must succeed together. Fix: ONE
   `BeginTransaction/Commit/Rollback`. → `db-integrity`.
3. **Concurrency that never fires** — `Version++` after `SaveChanges` (dead code). Fix: atomic conditional
   `UPDATE ... WHERE Id=@id AND Version=@read`; 0 rows affected ⇒ conflict. → `db-integrity`.
4. **Wrong error status** — conflict returns 500 + stack trace, or every exception collapses to a generic 400/409.
   Fix: typed domain exceptions (Conflict→409, NotFound→404) mapped in ONE global middleware; never leak stack in
   prod. → `error-handling-http`.
5. **Unaudited failed attempt** — the audit `AddAsync` sits inside the rolled-back transaction / has no
   `SaveChanges`, so failures vanish. Fix: record the failed attempt in its OWN unit of work + `SaveChanges`.
   → `db-integrity`.
6. **Data antipatterns** — `DateTime.Now` in business logic (use `UtcNow`); N+1 (use `Include`/projection);
   missing `AsNoTracking` on read-only queries; magic numbers (use named `const`/config). → `performance-scalability`.
7. **Frontend error UX** — native `alert()` instead of the app's toast; no state refresh after a 409 (stale view).
   Fix: app notification + reload the affected state; centralize status→message mapping. → `frontend-error-ux`.
8. **Secrets / repo hygiene** — committed connection strings/secrets; tracked `bin/`, `obj/`, `*.user`,
   `appsettings.Development.json`; dead scaffolding (`Class1.cs`, `WeatherForecast.cs`); commented-out blocks.
   Fix: `.gitignore` + `git rm -r --cached`. → `secrets-hygiene`.
9. **SOLID / clean architecture (cross-cutting)** — god-functions, duplicated logic, presentation mixed with
   data/business logic, dependencies pointing outward, missing an obvious pattern. → `clean-architecture`.

## Anti-deferral rule (the reason things slip through)
A cheap-to-fix structural failure (pagination, `AsNoTracking`, N+1, broken SOLID, missing pattern, non-atomic
transaction, wrong status code, unaudited failure) is a finding to **fix now**, NOT to wave through as
"acceptable for V1" or "not blocking". You may exclude something ONLY if an acceptance criterion explicitly puts
it out of scope — and even then you record it as a finding with that justification, never a silent pass. When in
doubt, it is a finding: it is cheaper to fix now than to let it become a vulnerability.

## Nits vs. findings
Ignore cosmetic nits (formatting, name bikeshedding, subjective style). The catalog items are NOT nits — they are
must-fix. A finding IS a blocking problem (1); no findings = `AUDIT_PASS` (0). Do not grade severity.

## Finding schema
```
- id: AUD-001
  file: path/to/file.ext:line
  evidence: exact code/behavior
  impact: why it blocks (debt/vulnerability it becomes)
  minimal_fix: smallest safe change
  verification: command/test/check that proves the fix
```

## Long-running commands you run yourself
Never pipe a gate/suite you are verifying through a `tail -N` pipe while waiting — silence trips the
runtime's stall watchdog. Run it as `ai/scripts/heartbeat-run.py --interval N -- <command>` (ADR-0041, see
`spawn-prompt/SKILL.md`).

## Rule
Never patch code here. Never approve on the implementer's word. Vague comments are not findings.
