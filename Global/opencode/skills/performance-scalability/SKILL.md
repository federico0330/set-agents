---
name: performance-scalability
description: Scalability checklist — paginate in SQL not memory, kill N+1, AsNoTracking on reads, project needed columns, index filters, no magic numbers, bounded work. Load on list endpoints, queries, loops over data, or hot paths.
license: MIT
compatibility: opencode
metadata:
  enabled_for: performance-auditor, architect, implementer, debugger
---

# Performance & Scalability

## When to use
List/search endpoints, queries, loops over data, pagination, batch jobs, or any path that grows with data
volume or traffic.

## Inputs
`git diff`, the query/ORM code and its callers, entity/index definitions, expected data volumes.

## Outputs
`PERF_PASS` or findings (`id, severity, file:line, evidence, impact_at_scale, minimal_fix, verification`).

## Checklist
1. **Paginate in the database** — `Skip/Take` / `LIMIT/OFFSET` / keyset runs in SQL, not after materializing
   the whole table in memory. Return `{data, total, page, pageSize}` so the client can render "Page X of Y".
2. **No N+1** — one query with join/`Include`/projection, not one query per row inside a loop.
3. **AsNoTracking on reads** — pure read/GET queries don't track entities; only track when you will mutate+save.
4. **Project only needed columns** — avoid overfetch on hot paths.
5. **Indexes** — exist for the filters, sorts and joins the diff introduces.
6. **No magic numbers** — page sizes, TTLs, timeouts are named constants/config, defined once.
7. **Bounded work** — no unbounded loops/fan-out/allocations driven by untrusted input.

## Verification ideas
Estimate cost at 10×/100×/1000× rows. `EXPLAIN` shows index seek, not full scan. Query count is O(1) per
request, not O(n). Pagination query returns a fixed small page regardless of table size.
