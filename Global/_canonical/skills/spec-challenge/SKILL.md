---
name: spec-challenge
description: Read-only pre-approval challenge of a Feature Contract for contradictions, missing acceptance criteria, undefined states, risks, edge cases, and product decisions.
license: MIT
compatibility: opencode
metadata:
  enabled_for: spec-challenger, product-analyst, architect
---

# Spec Challenge

## Procedure
1. Check each acceptance criterion is observable.
2. Search for conflicts between spec, acceptance, design, non-goals, and constraints.
3. Identify missing failure states, permissions, data ownership, limits, and recovery behavior.
4. Check the three named architecture axes (`system-design-decisions`): data store type — including vector
   vs relational —, API Gateway, and deploy platform. A surface that plausibly needs one of these with no
   ADR addressing it is a blocking gap, not a safe default to assume past.
5. Separate true product questions from safe implementation defaults — the architecture axes above are never
   a safe default when unaddressed.
6. Return one consolidated review.

## Output
Use `revision_required` only for blocking gaps. Use `ready_for_user_approval` when issues are optional or safely
documented as assumptions.
