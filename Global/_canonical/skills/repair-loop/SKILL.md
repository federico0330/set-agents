---
name: repair-loop
description: Turn consolidated package/delta review findings into minimal fixes, re-verify, and route to focused delta review without expanding scope or weakening tests.
license: MIT
compatibility: opencode
metadata:
  enabled_for: orchestrator, repair-agent, implementer, debugger
---

# Repair Loop

## When to use
After package review or delta review produced concrete findings.

## Inputs
Findings set, approved spec, package plan, current diff, gate output, retry budget.

## Outputs
Minimal repair diff, finding-specific verification, package gate result, and delta-review handoff.

## Procedure
1. Parse findings; reject vague ones lacking evidence.
2. Group findings by root cause and files.
3. Make only minimal fixes. Batch related repairs; avoid unrelated cleanup.
4. Run finding-specific checks, then the package/full gate available in the project.
5. Route to `delta-reviewer` in a fresh read-only context.
6. Stop after retry budget or repeated state -> `BLOCKED`.

## Rules
- Never modify acceptance criteria or weaken tests.
- The repair agent cannot mark a finding resolved without delta review.
- A finding that reappears after budget is a terminal blocker, not an invitation to loop.
