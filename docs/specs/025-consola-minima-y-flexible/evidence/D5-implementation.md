# D5 implementation continuation — incremental checkpoint

Base verified: `8a9f62bb5fa7dc1ed3f4275a1261de7c88ea9208`.

## Partial checkpoint (2026-08-17)

- Applied only to `ai/scripts/set_agents_spawn.py` and `ai/scripts/claude_code_spawn.py`:
  - Pi sends `vault_block` via subprocess stdin, retaining the original task as argv's final positional.
  - Vault lookup has explicit no-vault/degraded notes; transient lookup failures are written to a protected routing-store JSONL sink and are not cached.
  - Claude's child routing environment honors `None` as an unset `SET_AGENTS_PROJECT`; an explicit `spawn_cwd` requests that scrub.
- Not yet applied: equivalent degradation/scrub changes in `codex_spawn.py` and `opencode_spawn.py`, or the four shared doctrine fences. No tests were run before the mandatory cut.
- Next steps: finish the symmetric Codex/OpenCode ports, add/adjust focal tests for all four lanes, run the requested focused RED→GREEN commands through `heartbeat-run.py`, then run `git diff --check` and commit the completed package.
