---
description: Scalability / query-efficiency review
---

Before doing anything else, invoke `subagent({ agent: "package-reviewer", task: "<the request/arguments below>" })` to delegate this to the `package-reviewer` role — never handle it directly.

Read-only performance review of the current diff (or: $ARGUMENTS), focused on the scalability checklist:
SQL pagination (not in memory), N+1, AsNoTracking on reads, projection, indexes, magic numbers, bounded
work. Return findings with `category: scalability` and impact at scale, or note no concrete findings.
