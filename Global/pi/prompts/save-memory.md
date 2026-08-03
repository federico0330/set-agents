---
description: Persist durable, high-signal learning
---

Before doing anything else, invoke `subagent({ agent: "memory-scribe", task: "<the request/arguments below>" })` to delegate this to the `memory-scribe` role — never handle it directly.

Save durable memory for: $ARGUMENTS
Only after verification. What/Why/Where/Learned. Use a stable topic_key. Never save secrets, PII, raw logs,
or full diffs.
