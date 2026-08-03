---
description: Offensive + defensive security review of the diff
---

Before doing anything else, invoke `subagent({ agent: "security-auditor", task: "<the request/arguments below>" })` to delegate this to the `security-auditor` role — never handle it directly.

Read-only OWASP-aligned security review of the current diff (or: $ARGUMENTS).
Check authZ/IDOR, tenant scoping, input/SQL/XSS, secrets, error leakage, PII in logs, dependency risk, and
attempt exploitability like an attacker. Return SECURITY_PASS or findings (SEC- schema), each with its
mitigation plan attached.
