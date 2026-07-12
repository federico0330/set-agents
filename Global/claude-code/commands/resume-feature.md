---
description: Resume a package-based feature from persisted state
agent: orchestrator
---
Resume feature:
$ARGUMENTS

Read `ai/state/features/<feature_id>.json`, approved spec, package plan, latest gates, findings, and repairs.
Continue from the next deterministic state transition. Do not restart from requirements unless state/spec is
missing or invalid. Consolidate any questions into one orchestrator question only if a real blocker exists.
