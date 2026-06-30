---
name: security-review
description: Defensive OWASP-aligned security checklist — authZ/object-level access, tenant scoping, input validation, output encoding, secrets, PII, dependency risk, rate-limiting — with actionable findings on a strict schema. Load when reviewing a diff or feature for security defects before declaring it done.
license: MIT
compatibility: opencode
metadata:
  enabled_for: security-auditor, auditor, architect, implementer
---

# Security Review

## When to use
After implementation, before a task or PR is declared done, to find defensive security defects. Read-only.

## Inputs
- Diff/changed files, the spec or feature intent, auth/tenancy model, data classification (what is PII/secret).

## Outputs
- Ordered findings (highest severity first) on the schema below. State "no findings" explicitly if clean.

## Checklist
- **AuthN/AuthZ**: every protected route checks identity AND permission. Verify object-level authorization — the actor owns/may access THIS record (no IDOR via guessable/sequential IDs).
- **Tenant scoping**: every query filters by tenant/org server-side; never trust a client-supplied tenant id.
- **Input validation**: validate/allowlist all external input. Parameterized queries only — no string-concatenated SQL/NoSQL/shell.
- **Output encoding**: context-correct encoding for HTML/attr/JS/URL to prevent XSS; no `dangerouslySetInnerHTML` on untrusted data.
- **Secrets**: never committed, never logged, never echoed to clients; loaded from env/secret store.
- **Errors**: no stack traces or internal detail to clients in prod; generic messages outward, detail to server logs.
- **PII in logs**: no emails, tokens, full records, or sensitive fields written to logs/telemetry.
- **Dependencies**: flag new/updated deps with known CVEs, unmaintained, or excessive scope.
- **Rate-limiting/abuse**: auth, payment, and expensive endpoints have rate limits/lockout against brute force and abuse.

## Finding schema
- `id`: SEC-001
- `severity`: critical | high | medium | low
- `file:line`: path/to/file.ext:42
- `evidence`: the exact vulnerable code or pattern
- `impact`: what an attacker gains
- `minimal_fix`: smallest change that closes it
- `verification`: how to confirm the fix holds (test/command/manual step)

## Rules
- Read-only — propose fixes, do not apply them.
- Severity by real exploitability and blast radius, not theory.
- Every finding cites concrete `file:line` evidence — no vague "could be insecure".
- Prefer server-side, deny-by-default fixes over client-side mitigations.
