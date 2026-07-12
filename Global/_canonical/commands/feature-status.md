---
description: Report package workflow state without mutation
agent: orchestrator
---
Report status for feature:
$ARGUMENTS

Read the compact state file and summarize: current phase, approved spec version/hash, packages, task states,
gates, attempts consumed, open findings, repairs, blockers, and next transition. Do not edit files or run gates.
