---
description: Read-only diff audit against active scope
agent: auditor
---
Read-only audit. Do not edit files. Scope: $ARGUMENTS

Inspect AGENTS.md, active spec/task/acceptance, git diff, and ai/state/verify.log. Return
"AUDIT_PASS: no concrete findings against the provided scope." or findings with the schema
(id, severity, file:line, evidence, impact, minimal_fix, verification).
