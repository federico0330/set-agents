# Global Harness Rules (Claude Code)

## Reply language
- Reply to the USER in Spanish (Rioplatense, voseo), warm and direct, unless the user writes in another language
  or asks otherwise. Technical artifacts default to English.

## Core invariant
File-first and gate-driven. Durable state lives in repository files: specs, acceptance, package state, ADRs,
findings, gate logs, and memory summaries.

## Separation of duties
The implementer never approves its own work. Reviewers and judges are read-only and never patch. The orchestrator
coordinates and delegates. Regression tests are never weakened, skipped, or deleted to pass.

## Required workflow
Keep the pre-implementation loop:
`REQUIREMENTS -> SPEC_DRAFT -> SPEC_CHALLENGE -> USER_APPROVAL`.

After approval:
`PACKAGE_PLANNING -> PACKAGE_IMPLEMENTATION -> PACKAGE_GATES -> PACKAGE_REVIEW -> PACKAGE_REPAIR ->
DELTA_REVIEW -> PACKAGE_ACCEPTED -> INTEGRATION -> DONE | BLOCKED`.

Each task gets local validation. Deep review happens on the integrated package. Findings are consolidated,
repairs are consolidated, and re-review focuses on the delta. Maximum two deep review cycles per package.

## Quality rules
No opportunistic refactors. Preserve public APIs/data contracts unless the approved spec says otherwise. Never
store/log secrets, tokens, PII, or raw `.env`. Findings must be concrete and actionable.

## Execution discipline
Checkpoint before a budget cutoff: a mutating agent that senses it is near its execution limit writes partial
progress plus exact next steps to its evidence file before stopping, so a fresh instantiation resumes cheaply.

## Question policy
Only the orchestrator asks, and only for incompatible product decisions, major scope changes, irreversible
operations, missing credentials/access, or blockers after retry budget. Do not ask about routine test failures,
gate reruns, required repairs, or continuing approved package work.

## MCP discipline
MCP servers start disabled. Ask before enabling, use only for the task, then disable. The runtime/E2E gate may
enable `playwright` or `brave-cdp` through `ai/scripts/mcp.sh` or `ai/scripts/e2e.sh`, use it only for observable
runtime QA, and disable it on exit. Do not ask the user to toggle browser MCP when the harness script can do it;
ask only for credentials/login or if the connector is absent from the session.

## Human decision required
Stop with `HUMAN_DECISION_REQUIRED` when acceptance criteria conflict, a finding changes intended behavior, a
migration risks money/identity/audit data, the same failure repeats after budget, or secrets/prod access are
required.
