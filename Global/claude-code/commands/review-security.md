---
description: Defensive security review of the diff
agent: security-auditor
---
Read-only OWASP-aligned security review of the current diff (or: $ARGUMENTS).
Check authZ/IDOR, tenant scoping, input/SQL/XSS, secrets, error leakage, PII in logs, dependency risk.
Return SECURITY_PASS or findings (SEC- schema). Coordinate with @red-team and @blue-team.
