---
description: Run the deterministic verification gate
---

Before doing anything else, invoke `subagent({ agent: "gate-runner", task: "<the request/arguments below>" })` to delegate this to the `gate-runner` role — never handle it directly.

Run ./ai/scripts/verify.sh and report the result. Args: $ARGUMENTS
If it fails, summarize the failure from ai/state/verify.log. Do not repair and do not weaken tests.
