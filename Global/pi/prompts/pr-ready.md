---
description: Aggregate gates and decide PR readiness
---

Before doing anything else, invoke `subagent({ agent: "orchestrator", task: "<the request/arguments below>" })` to delegate this to the `orchestrator` role — never handle it directly.

Decide if the active change is PR-ready. Args: $ARGUMENTS
Confirm: verify.sh PASS, required domain audits PASS (security/db/perf as applicable), no weakened tests,
secrets-hygiene clean, scope matches the spec. List any blockers or output the go-ahead with the gate summary.
