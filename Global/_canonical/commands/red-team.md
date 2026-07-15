---
description: Authorized offensive+defensive security review (read-only)
agent: security-auditor
---
Authorized, read-only offensive review of the current diff (or: $ARGUMENTS).
Enumerate entry points, attempt authz bypass/IDOR, tampering, injection, races, replay, business-logic abuse.
Minimal PoC only; no destructive payloads/DoS. For each attack path found, also return its mitigation plan.
Return SECURITY_PASS or ranked findings (SEC- schema: attack_path + mitigation together).
