---
description: Global multi-feature status without mutation
---

Before doing anything else, invoke `subagent({ agent: "orchestrator", task: "<the request/arguments below>" })` to delegate this to the `orchestrator` role — never handle it directly.

Report the global development status.

Read `ai/state/STATUS.md` (regenerate it first with `python3 ai/scripts/feature-state.py render-status` if it is
missing or looks stale). Summarize in plain language: every feature with its mode, phase, current package,
budgets consumed, open findings and blockers, plus the recent quick-fixes. Flag anything BLOCKED or waiting on a
human decision first. Do not edit files, run gates, or infer status from chat history.
