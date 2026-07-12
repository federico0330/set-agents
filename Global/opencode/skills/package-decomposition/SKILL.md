---
name: package-decomposition
description: Decompose an approved spec into coherent implementation packages, each with several related work items, ownership paths, risks, gates, and done conditions.
license: MIT
compatibility: opencode
metadata:
  enabled_for: package-planner, orchestrator, integrator
---

# Package Decomposition

## Package definition
A package is a reviewable unit that produces observable behavior: a vertical slice, related acceptance criteria,
API plus integration, UI plus API, or a stable subsystem contract.

## Heuristic
Prefer 3-7 work items per package when cohesive. Do not split by file/function count. Cohesion beats number.

## Required fields
`package_id`, objective, ACs covered, tasks, dependencies, ownership paths, risks, local validations, package
gates, done conditions, and high-risk checkpoints.

## Early checkpoints
Only for auth, authorization, tenant isolation, payments, secrets, crypto, destructive migrations/deletes,
incompatible public contracts, system permissions, or untrusted code execution. The checkpoint is focused on the
risk; the full review remains package-level.
