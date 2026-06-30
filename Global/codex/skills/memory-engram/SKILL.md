---
name: memory-engram
description: Durable high-signal cross-session memory via Engram — save the why behind decisions, verified fixes with root cause, failed approaches, domain invariants, and key commands using stable topic keys to upsert. Load when persisting or recalling project continuity that should outlive the session.
license: MIT
compatibility: opencode
metadata:
  enabled_for: memory-scribe, orchestrator
---

# Memory Engram

## When to use
To persist decisions and discoveries that must survive across sessions/compactions, or to recall prior work before starting.

## Tools
- `mem_save` — write a memory (set a stable `topic_key` for evolving topics to upsert in place).
- `mem_search` — find relevant memories by keywords (returns truncated results).
- `mem_get_observation` — fetch full untruncated content by id (always follow a search with this).
- `mem_context` — fast recent-session context.

## SAVE (high signal)
- Architecture/ADR decisions — especially the WHY and the tradeoff.
- Verified bug fixes WITH root cause.
- Failed approaches and why they failed (so they are not retried).
- Domain invariants and business rules.
- Key verify/build/test commands for the repo.
- Fragile files and known gotchas.

## DO NOT SAVE
- Secrets, credentials, tokens, API keys, PII.
- Raw `.env` contents, large logs, full diffs.
- Unverified speculation or guesses.
- Obvious facts already plain in the code.

## Procedure
1. Recall: `mem_search` keywords → `mem_get_observation` on the best hit for full content.
2. Save: write a titled memory with What / Why / Where / Learned; reuse the `topic_key` to evolve a topic instead of duplicating.

## Rules
- The repository is the primary source of truth; memory is continuity, not a substitute.
- Save only AFTER verification or human confirmation — never persist unconfirmed claims.
- Keep entries short and high-signal; one decision/discovery per memory.
- Different topics never overwrite each other — same topic evolves via the same `topic_key`.
