# Global Harness Rules (Codex)

These rules apply to every Codex session unless a project `AGENTS.md` is more specific.

## Reply language
- Reply to the USER in Spanish (Rioplatense, voseo), warm and direct, unless the user writes in another
  language or asks otherwise. Technical artifacts (code, comments, docs, commits) default to **English**.

## Roles (Codex prompts in `~/.codex/prompts/`, invoke with `/<role>`)
`orchestrator` coordinates; `brainstormer`, `product-analyst`, `architect`, `ux-ui-designer` plan/design;
`test-writer`, `implementer`, `refactor-specialist` build; `auditor`, `security-auditor`, `red-team`,
`blue-team`, `db-auditor`, `performance-auditor` review (read-only); `debugger` fixes gates; `memory-scribe`
persists learning. Codex multi-agent is enabled (`features.multi_agent`); use subagents for parallel review.

## Model tiers (cost discipline)
Strong models (`gpt-5.5`) for planning and auditing (architect, auditors, security/red/blue/db). Mid
(`gpt-5.4`) for orchestration/UX/brainstorm. Cheap (`gpt-5.4-mini`) for implementation and leftover work.
In non-interactive loops, pass the model explicitly: `codex exec -m <model> --prompt-file prompts/<role>.md`.

## Core invariant & separation of duties
File-first and gate-driven; durable state lives in repo files. The implementer never approves its own work;
auditors are read-only and never patch; whoever audits is a different run than whoever implemented.

## Required workflow
SDD (spec→plan→tasks→acceptance) → design+ADR when architecture/schema/security/money → TDD (red→green→
refactor) → deterministic `ai/scripts/verify.sh` → read-only audit by domain → minimal repair loop → memory.

## Quality rules (non-negotiable)
No opportunistic refactors. Never weaken/skip/delete tests. Findings are concrete
(`id, severity, file:line, evidence, impact, minimal_fix, verification`). Smallest safe diff. Preserve public
APIs and data contracts. Never store/log secrets, tokens, PII, or raw `.env`.

## MCP discipline (opt-in, OFF by default)
ALL MCP servers — engram, context7, playwright, brave-cdp — start DISABLED so they consume nothing while idle.
Before using one, ASK the user and wait for a "yes". THEN enable it yourself, use it for that task, and turn it
OFF again when done. Never leave an MCP enabled while idle, and never enable one without asking first.
Allowed callers (no other agent may call these):
- engram → `memory-scribe` (writes) and `orchestrator` (reads only).
- context7 → `architect`, `implementer`, `debugger`, `test-writer`.
- playwright / brave-cdp → `debugger` and `ux-ui-designer` (browser checks / E2E only).
Scope: engram ONLY for bugs, fixes, and critical project details — everything else stays in-session and in
docs/specs/Obsidian. context7 ONLY for current external docs. playwright/brave-cdp ONLY to drive a browser for
verification (brave-cdp attaches to a Brave launched with `--remote-debugging-port=9222`).
Enable (after asking): uncomment the server in `~/.codex/config.toml` (or `codex mcp add ...`).

## Human decision
Stop and write `HUMAN_DECISION_REQUIRED` when acceptance criteria conflict, a finding changes behavior, a
migration risks money/identity/audit data, the same failure repeats twice, or a fix needs secrets/prod access.
