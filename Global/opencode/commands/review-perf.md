---
description: Scalability / query-efficiency review
agent: performance-auditor
---
Read-only performance review of the current diff (or: $ARGUMENTS).
Check SQL pagination (not in memory), N+1, AsNoTracking on reads, projection, indexes, magic numbers,
bounded work. Return PERF_PASS or findings (PERF- schema) with impact at scale.
