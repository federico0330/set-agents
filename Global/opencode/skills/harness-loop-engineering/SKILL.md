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
task → implement → audit(read-only, vs spec/design/acceptance) → repair(findings) → audit → … until no findings
     → regression tests(test-writer) → verify(gate) → memory → stop
```
The **read-only audit against the spec/design is the primary gate**, not tests: a passing test does not prove the
code returns what the spec expects. Regression tests are written only after the audit loop converges, as proof of
the already-correct behavior — never as a guardrail to implement, and never weakened to pass.
Rules that make it safe:
- `MAX_ITER` cap (default 4).
- Deterministic verification (`ai/scripts/verify.sh`) runs build/lint each iteration and, once regression tests
  exist, runs them too — but the auditor, not a green suite, decides convergence.
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
