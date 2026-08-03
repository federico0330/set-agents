---
description: Architecture design + ADR before implementation
---

Before doing anything else, invoke `subagent({ agent: "architect", task: "<the request/arguments below>" })` to delegate this to the `architect` role — never handle it directly.

Design the technical approach for the active spec (or: $ARGUMENTS).

Identify core domain vs infrastructure, apply SOLID + Clean/Hexagonal, define transaction/concurrency
boundaries and failure modes, write an ADR per significant decision, and state the implementer contract.
