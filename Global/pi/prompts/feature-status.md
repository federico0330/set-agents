---
description: Report package workflow state without mutation
---

Before doing anything else, invoke `subagent({ agent: "orchestrator", task: "<the request/arguments below>" })` to delegate this to the `orchestrator` role — never handle it directly.

Report status for feature:
$ARGUMENTS

Run:

```bash
python3 ai/scripts/feature-state.py status <feature_id>
```

Summarize only the persisted state: current phase, approved spec version/hash, packages, task states, gates,
budgets consumed, open findings, repairs, blockers, and next transition. Do not edit files, run gates, or infer
status from chat history. For the quick multi-feature overview (all features plus recent quick-fixes) point the
user to `/status`, backed by `ai/state/STATUS.md`.
