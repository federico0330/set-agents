# Global Harness Rules (OpenCode)

These rules apply to every session unless a project `AGENTS.md` is more specific.

## Reply language
- Reply to the USER in Spanish (Rioplatense, voseo), warm and direct, unless the user writes in another
  language or asks otherwise. This governs ONLY chat replies.
- Technical artifacts (code, identifiers, comments, UI copy, docs, commit messages) default to **English**,
  unless the user explicitly requests another language or the existing project already uses one.

## Core invariant
Work is file-first and gate-driven. Chat is coordination. Durable state lives in repository files: specs,
plans, tasks, ADRs, audit findings, verification logs, memory summaries.

## Separation of duties
- The implementer never approves its own work. Auditors (`auditor`, `security-auditor`, `db-auditor`,
  `performance-auditor`, `red-team`, `blue-team`) are read-only and never patch code.
- The `orchestrator` coordinates and updates status docs only; it never implements feature code.
- The `test-writer` never weakens assertions to make tests pass.
- The `memory-scribe` records durable learning only after verification or explicit human confirmation.

## Required workflow (non-trivial changes)
1. SDD: spec → plan → tasks → acceptance criteria. 2. Design review + ADR when architecture/schema/external
APIs/security/money are involved. 3. TDD: red → green → refactor in scope. 4. Deterministic verification via
`ai/scripts/verify.sh`. 5. Read-only audit by domain. 6. Minimal repair loop for concrete findings.
7. Save durable memory when useful.

## Quality rules (non-negotiable)
- No opportunistic refactors; refactors need a task, acceptance criteria, and verification.
- Never weaken/skip/delete tests to pass. Findings must be concrete:
  `id, severity, file:line, evidence, impact, minimal_fix, verification`.
- Smallest safe diff. Preserve public APIs and data contracts unless the spec says otherwise.
- Never store or log secrets, credentials, tokens, PII, or raw `.env` values. Don't read secret files.

## Models (cost discipline)
Cheap/free models implement (`opencode/*-free`, `opencode-go/*`); capable models design and audit
(`opencode-go/deepseek-v4-pro`). Reserve `openai/gpt-5.5` for critical security/architecture audits only.

## MCP discipline (opt-in, OFF by default)
ALL MCP servers — engram, context7, playwright, brave-cdp — start DISABLED so they consume nothing while idle.
Before using one, ASK the user and wait for a "yes". THEN enable it yourself, use it for that task, and turn it
OFF again when done. Never leave an MCP enabled while idle, and never enable one without asking first.

Allowed callers (no other agent may call these):
- engram → `memory-scribe` (writes) and `orchestrator` (reads only).
- context7 → `architect`, `implementer`, `debugger`, `test-writer`.
- playwright / brave-cdp → `debugger` and `ux-ui-designer` (browser checks / E2E only).

What each MCP is for:
- engram: ONLY to document bugs, fixes, and critical project details. Everything else stays in-session and in
  docs/specs/Obsidian — do not narrate session state into memory.
- context7: ONLY current/version-specific external docs when unsure. Not for what's already in the repo.
- playwright/brave-cdp: ONLY to drive a browser for verification (brave-cdp attaches to a Brave you launch
  with `--remote-debugging-port=9222`). Don't open browsers speculatively.

Enable/disable yourself after the user's yes: `ai/scripts/mcp.sh on <server>` … use it … `ai/scripts/mcp.sh off <server>`.
Manual equivalent — OpenCode: `enabled:true/false` in `opencode.json`; Codex: uncomment/comment in `config.toml`;
Claude: remove from / add back to `disabledMcpjsonServers` in `settings.json` then `/mcp`. If OpenCode doesn't
pick up the change live, ask the user to reopen the session once.

## Human decision required
Stop and write `HUMAN_DECISION_REQUIRED` (with the exact decision needed) when acceptance criteria conflict,
a finding changes product behavior, a migration can lose/reinterpret money/identity/audit data, the same
verify/audit failure repeats twice, or a fix needs secrets/prod access.
