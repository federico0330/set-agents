---
name: package-review
description: Deep independent review of a complete package diff against approved spec, package criteria, gates, integration behavior, and relevant risk surfaces.
license: MIT
compatibility: opencode
metadata:
  enabled_for: package-reviewer, delta-reviewer, adversarial-judge
---

# Package Review

## Inputs
Approved spec/version, package plan, diff, gate results, assumptions, and known risks.

## Checks
- Correctness against covered acceptance criteria.
- Integration with existing contracts.
- Architecture and maintainability with real impact.
- Security/data/performance surfaces when touched.
- Failure paths and edge cases.
- Test gaps that would leave accepted behavior unprotected.

## Cadence
One deep review per integrated package. A second pass is focused on repair delta. Full re-review only when repair
changes architecture, public contracts, or risk surface substantially.

## Long-running commands you run yourself
Never pipe a gate/suite you are verifying through a `tail -N` pipe while waiting — silence trips the
runtime's stall watchdog. Run it as `ai/scripts/heartbeat-run.py --interval N -- <command>` (ADR-0041, see
`spawn-prompt/SKILL.md`).
