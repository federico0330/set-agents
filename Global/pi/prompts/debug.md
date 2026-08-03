---
description: Root-cause a failing gate and fix minimally
---

Before doing anything else, invoke `subagent({ agent: "debugger", task: "<the request/arguments below>" })` to delegate this to the `debugger` role — never handle it directly.

A gate failed. Args: $ARGUMENTS
Reproduce from ai/state/verify.log, find the ROOT cause, apply the minimal fix, add a regression test if
missing, re-run verify.sh. Stop with HUMAN_DECISION_REQUIRED if it repeats or is ambiguous.
