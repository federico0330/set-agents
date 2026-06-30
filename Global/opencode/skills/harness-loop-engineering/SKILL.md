---
name: harness-loop-engineering
description: The meta-skill — how this whole system works. Harness = the verifiable process around the model (agents, permissions, gates, memory). Loop = a controlled cycle implement→verify→audit→repair with hard stops. Load to understand or orchestrate the workflow.
license: MIT
compatibility: opencode
metadata:
  enabled_for: orchestrator, architect, debugger
---

# Harness & Loop Engineering

## Idea
**Harness engineering** = designing the verifiable scaffolding around the model (roles, prompts, permissions,
skills, commands, deterministic scripts, audits, gates). The goal is not "ask the model nicer" but to box it
into a process that proves its own output. **Loop engineering** = controlled cycles with hard stop conditions.

## The canonical loop
```
task → implement → verify(gate) → audit(read-only) → repair(findings) → verify → audit → memory → stop
```
Rules that make it safe:
- `MAX_ITER` cap (default 4).
- Deterministic verification (`ai/scripts/verify.sh`) decides gates — not the model's opinion.
- The auditor is a DIFFERENT agent/run than the implementer (separation of duties).
- Findings must be actionable (`id, severity, file:line, evidence, impact, minimal_fix, verification`).
- Stop if the same failure/audit state repeats (hash the state and compare).
- Stop and emit `HUMAN_DECISION_REQUIRED` when a human must decide.
- Save durable memory at the end of a verified iteration.

## Roles vs pieces
- **Agent/subagent**: a role with prompt, permissions, model. **Skill**: a reusable procedure loaded on demand.
- **Command**: an invocable prompt (`/audit`). **MCP**: external tool (docs, memory). **Memory**: durable
  continuity (not primary truth). **Gate**: an objective pass/fail condition.

## Golden rule
Whoever implements does not approve. Cheap models implement; capable models design and audit. State lives in
files, so any session (or harness) can resume from the repository, not from chat.

## When to use
At the start of any non-trivial change, when designing a new loop, or when a process keeps producing churn.
