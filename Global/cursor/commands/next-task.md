---
description: Legacy task runner; prefer /feature-batch for package workflow
agent: orchestrator
---
Advance the active change. Argument (optional task id): $ARGUMENTS

Compatibility path only. If an approved feature can be packaged, switch to `/feature-batch` and package planning.
Never start deep audits after ordinary individual tasks.

If a feature state exists, run:

```bash
python3 ai/scripts/feature-state.py next <feature_id>
```

Then continue from the returned package workflow transition. For legacy quick-fix scope with no package state,
delegate implementation, local validation, deterministic gates, and only a focused audit when package workflow is
not applicable.
