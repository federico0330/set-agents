---
name: quality-gates
description: Define and run deterministic gates in a reproducible order for package and final integration verification without inventing unavailable commands.
license: MIT
compatibility: opencode
metadata:
  enabled_for: gate-runner, package-planner, repair-agent, integrator, test-writer
---

# Quality Gates

## Gate order
Use real project commands only:
1. format check
2. lint
3. compile/typecheck
4. focused unit/contract tests
5. package integration tests
6. applicable security/static checks
7. regressions
8. final global suite

## Rules
- Do not invent commands. Discover scripts from project files.
- Prefer `./ai/scripts/verify.sh` when present.
- Record command, exit status, and log path in feature state.
- A failed gate inside scope is repaired without asking the user.
