---
description: Focused read-only diff audit against active scope
---

Before doing anything else, invoke `subagent({ agent: "package-reviewer", task: "<the request/arguments below>" })` to delegate this to the `package-reviewer` role — never handle it directly.

Read-only quick/focused audit (see package-reviewer's quick mode). Do not edit files. Scope: $ARGUMENTS

Inspect AGENTS.md, active spec/package/task/acceptance, git diff, and ai/state/verify.log. Return
"AUDIT_PASS: no concrete findings against the provided scope." or findings with the schema
(id, severity, category, file:line, evidence, impact, minimal_fix, verification), ending with `AUDIT_FAIL`.
