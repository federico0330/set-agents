---
description: Aggregate gates and decide PR readiness
agent: orchestrator
---
Decide if the active change is PR-ready. Args: $ARGUMENTS
Confirm: verify.sh PASS, required domain audits PASS (security/db/perf as applicable), no weakened tests,
secrets-hygiene clean, scope matches the spec. List any blockers or output the go-ahead with the gate summary.
