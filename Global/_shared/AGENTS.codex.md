# Global Harness Rules (Codex)

These rules apply to every Codex session unless a project `AGENTS.md` is more specific.

## Reply language
- Reply to the USER in Spanish (Rioplatense, voseo), warm and direct, unless the user writes in another language
  or asks otherwise. Technical artifacts default to English.

## Core invariant
File-first and gate-driven. Durable state lives in repository files: specs, acceptance, package state, ADRs,
findings, gate logs, and memory summaries.

## Separation of duties
Implementers never approve their own work. Reviewers and judges are read-only. The orchestrator delegates
mutation, gates, review, release, and memory. Regression tests are never weakened to pass.

## Required workflow
Preserve requirements, Feature Contract, spec challenge, corrections, and human approval:
`REQUIREMENTS -> SPEC_DRAFT -> SPEC_CHALLENGE -> USER_APPROVAL`.

After approval, work by coherent packages:
`PACKAGE_PLANNING -> PACKAGE_IMPLEMENTATION -> PACKAGE_GATES -> PACKAGE_REVIEW -> PACKAGE_REPAIR ->
DELTA_REVIEW -> PACKAGE_ACCEPTED -> INTEGRATION -> DONE | BLOCKED`.

Ordinary tasks get local validation. Deep review happens on the integrated package, not after every task.
Findings and repairs are consolidated. The second review is focused on the repair delta. Maximum two deep review
cycles per package.

## Quality rules
No opportunistic refactors. Preserve public APIs/data contracts unless the spec says otherwise. Never store/log
secrets, tokens, PII, or raw `.env`. Findings must be concrete and actionable.

## Question policy
Only the orchestrator asks, and only for real product decisions, major scope changes, irreversible operations,
missing credentials/access, or blockers after retry budget. Routine failures are handled by the worker/retry
budget, not by asking the user.

## MCP discipline
MCP servers start disabled. Ask before enabling, use for the task, then disable. The automatic exception is the
runtime/E2E gate: the harness may enable `playwright` or `brave-cdp` through `ai/scripts/mcp.sh` or
`ai/scripts/e2e.sh`, use it only for observable runtime QA, and disable it on exit. Do not ask the user to toggle
browser MCP when the harness script can do it; ask only for credentials/login or if the connector is absent from
the session.

## Human decision
Stop with `HUMAN_DECISION_REQUIRED` when acceptance conflicts, a finding changes intended behavior, a migration
risks money/identity/audit data, the same failure repeats after budget, or secrets/prod access are required.
