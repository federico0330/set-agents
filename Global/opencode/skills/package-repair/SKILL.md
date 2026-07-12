---
name: package-repair
description: Repair all accepted package review findings in a consolidated pass, preserving finding-to-change-to-verification traceability and retry budgets.
license: MIT
compatibility: opencode
metadata:
  enabled_for: repair-agent, debugger, implementer
---

# Package Repair

## Procedure
1. Parse the complete findings set.
2. Reject vague findings lacking evidence.
3. Group findings by root cause and files.
4. Apply the smallest safe changes.
5. Run finding-specific checks and package gates.
6. Update state with finding -> files changed -> verification.

## Stop
Stop as `blocked` for secrets/prod access, irreversible operations, product conflicts, or repeated failure after
retry budget. Never weaken tests or acceptance criteria.
