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
4. Separate true product questions from safe implementation defaults.
5. Return one consolidated review.

## Output
Use `revision_required` only for blocking gaps. Use `ready_for_user_approval` when issues are optional or safely
documented as assumptions.
