# Global Harness Rules (Codex)

These rules apply to every Codex session unless a project `AGENTS.md` is more specific.

## Reply language
- Reply to the USER in Spanish (Rioplatense, voseo), warm and direct, unless the user writes in another
  language or asks otherwise. Technical artifacts (code, comments, docs, commits) default to **English**.

## Roles (native agents in `~/.codex/agents/*.toml`)
`orchestrator` only inspects and delegates. Planning includes `product-analyst`, `project-bootstrapper`,
`architect`, and `agent-factory`; mutation uses `test-writer`, `implementer`, `debugger`, and
`refactor-specialist`; deterministic commands use `gate-runner`; audits are read-only; every change ends at
`adversarial-judge`; `github-release-manager` and `memory-scribe` handle gated release and durable learning.

## Model tiers (cost discipline)
Strong models (`gpt-5.5`) for planning and auditing (architect, auditors, security/red/blue/db). Mid
(`gpt-5.4`) for orchestration/UX/brainstorm. Cheap (`gpt-5.4-mini`) for implementation and leftover work.
Codex loads each role's model, reasoning effort, and sandbox from its native agent TOML. Reasoning effort is
tuned by activity: **xhigh** for auditors and the judge (best of the best), **high** for coordination/root-cause
and the frontend aesthetic gate, **medium** for implementation (audited afterward), **low** for mechanical/
script-gated roles.

## Core invariant & separation of duties
File-first and gate-driven; durable state lives in repo files. The implementer never approves its own work;
auditors are read-only and never patch; whoever audits is a different run than whoever implemented.

## Required workflow
The stack is SDD → BDD → implement⇄audit loop → regression tests, in that order (condense or skip only for a scoped-feature, quick-fix, or incident — see `request-triage`):
SDD (spec→plan→tasks + design+ADR, with `system-design-decisions`, when architecture/schema/security/money) →
BDD (acceptance criteria as Given-When-Then behavioral scenarios — the product↔tech bridge) →
**implement⇄audit loop**: implement → read-only audit against the spec/design/acceptance → repair the concrete
findings → audit → … until the auditor returns no findings (implementation matches the pre-design) →
**regression tests** written now (`test-writer`) as proof of the converged behavior → deterministic `gate-runner`
→ read-only audits → `adversarial-judge` → gated GitHub release → memory. Tests are NOT a guardrail for
implementation — a green test can pass without returning what the spec expects; the guardrail is the auditor
against spec/design/acceptance. Tests come at the end, never weakened.

## Quality rules (non-negotiable)
No opportunistic refactors. Never weaken/skip/delete the end-stage regression tests. Findings are binary and concrete
(`id, file:line, evidence, impact, minimal_fix, verification`): a finding IS a blocking problem (1), no findings
= PASS (0), do not grade severity. Smallest safe diff. Preserve public APIs and data contracts. Never store/log
secrets, tokens, PII, or raw `.env`.

## Execution discipline (every agent)
You are ONE role, ONE step in a loop — do only your task. Read only what the task names (spec/task/diff/audit
findings/AGENTS.md); do NOT sweep the repo or model the whole codebase; missing input → ask or return, don't hunt.
No exploratory sandboxes, no re-running past the declared gate, no planning beyond this step. Return fast:
produce the bounded output and STOP. Anti-loop stop clause: finish in one focused pass; if you cannot converge
(missing info, same failure twice, or many more steps needed) STOP and return `HUMAN_DECISION_REQUIRED` with the
exact blocker — never retry the same approach in a loop.

## MCP discipline (opt-in, OFF by default)
ALL MCP servers — engram, context7, playwright, brave-cdp — start DISABLED so they consume nothing while idle.
Before using one, ASK the user and wait for a "yes". THEN enable it yourself, use it for that task, and turn it
OFF again when done. Never leave an MCP enabled while idle, and never enable one without asking first.
**E2E exception:** the `ai/scripts/e2e.sh` wrapper may enable `playwright` automatically for the duration of a
`runtime-verifier` gate and disables it on exit (trap). That is the ONLY automatic MCP enablement.
Allowed callers (no other agent may call these):
- engram → `memory-scribe` (writes) and `orchestrator` (reads only).
- context7 → `architect`, `implementer`, `frontend-engineer`, `debugger`, `test-writer`.
- playwright / brave-cdp → `debugger`, `ux-ui-designer`, and `runtime-verifier` (browser checks / E2E only).
Scope: engram ONLY for bugs, fixes, and critical project details — everything else stays in-session and in
docs/specs/Obsidian. context7 ONLY for current external docs. playwright/brave-cdp ONLY to drive a browser for
verification (brave-cdp attaches to a Brave launched with `--remote-debugging-port=9222`).
Enable (after asking): uncomment the server in `~/.codex/config.toml` (or `codex mcp add ...`).

## Human decision
Stop and write `HUMAN_DECISION_REQUIRED` when acceptance criteria conflict, a finding changes behavior, a
migration risks money/identity/audit data, the same failure repeats twice, or a fix needs secrets/prod access.
