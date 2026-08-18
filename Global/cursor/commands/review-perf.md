---
description: Scalability / query-efficiency review
agent: package-reviewer
---
Read-only performance review of the current diff (or: $ARGUMENTS), focused on the scalability checklist:
SQL pagination (not in memory), N+1, AsNoTracking on reads, projection, indexes, magic numbers, bounded
work. Return findings with `category: scalability` and impact at scale, or note no concrete findings.
