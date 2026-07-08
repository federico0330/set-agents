---
description: Pick and route the next task through the loop
agent: orchestrator
---
Advance the active change. Argument (optional task id): $ARGUMENTS

Read specs/tasks, pick the next task, delegate the smallest implementation (driven by the spec/design, NOT by
tests), then run the implement⇄audit loop until the auditor returns no findings; write regression tests once it
converges and route the right gates (verify + domain audits). Report phase, gate results, and the next step or
human decision.
