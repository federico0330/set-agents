---
description: Report package workflow state without mutation
agent: orchestrator
---
Report status for feature:
$ARGUMENTS

Run:

```bash
python3 ai/scripts/feature-state.py status <feature_id>
```

Summarize only the persisted state: current phase, approved spec version/hash, packages, task states, gates,
budgets consumed, open findings, repairs, blockers, and next transition. Do not edit files, run gates, or infer
status from chat history.
