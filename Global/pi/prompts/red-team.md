---
description: Authorized offensive+defensive security review (read-only)
---

Before doing anything else, invoke `subagent({ agent: "security-auditor", task: "<the request/arguments below>" })` to delegate this to the `security-auditor` role — never handle it directly.

Authorized, read-only offensive review of the current diff (or: $ARGUMENTS).
Enumerate entry points, attempt authz bypass/IDOR, tampering, injection, races, replay, business-logic abuse.
Minimal PoC only; no destructive payloads/DoS. For each attack path found, also return its mitigation plan.
Return SECURITY_PASS or ranked findings (SEC- schema: attack_path + mitigation together).
