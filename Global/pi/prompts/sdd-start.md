---
description: Create SDD spec/plan/tasks/acceptance for an idea
---

Before doing anything else, invoke `subagent({ agent: "product-analyst", task: "<the request/arguments below>" })` to delegate this to the `product-analyst` role — never handle it directly.

Start Spec-Driven Development for:
$ARGUMENTS

Write docs/specs/<id>/{spec.md,plan.md,tasks.md,acceptance.md}. Make every requirement testable, mark the
first shippable slice, list explicit non-goals, and make money/identity/audit/concurrency rules explicit.
