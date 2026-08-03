---
description: Consolidated package repair for concrete findings
---

Before doing anything else, invoke `subagent({ agent: "repair-agent", task: "<the request/arguments below>" })` to delegate this to the `repair-agent` role — never handle it directly.

Repair ONLY the concrete findings for the active package in ai/state/features/<feature_id>.json,
ai/state/audit-findings.md, or: $ARGUMENTS.

Make a consolidated minimal repair pass, preserve finding -> change -> verification traceability, do not change
acceptance criteria or weaken tests, run focused verification then package gates, and hand back to
`delta-reviewer`.
