---
name: bounded-implementation
description: Implement package work packets with local validation per task while deferring deep independent review until the integrated package is ready.
license: MIT
compatibility: opencode
metadata:
  enabled_for: implementer, frontend-engineer, refactor-specialist, repair-agent
---

# Bounded Implementation

## Rules
- Work only inside the assigned package and ownership paths.
- Run local validations after each coherent task.
- Keep the package buildable or record the exact partial state.
- Do not call reviewers or mark the package approved.
- Do not ask the user for routine failures; repair in scope or return a structured blocker.

## Local validation
Compile/typecheck, lint touched files, focused unit/contract tests, smoke checks, ownership checks, and a quick
self-diff review for scope.
