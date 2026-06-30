---
name: red-team-playbook
description: Authorized, read-only offensive review of the change under test — authz bypass/IDOR, parameter tampering, injection, race conditions, token replay, mass assignment, path traversal, business-logic abuse — ranked by real impact with minimal PoC. Load when adversarially probing a feature or diff for exploitable weaknesses.
license: MIT
compatibility: opencode
metadata:
  enabled_for: red-team, security-auditor
---

# Red Team Playbook

## When to use
Authorized adversarial review of code/endpoints in scope, to surface exploitable paths a defender missed. Read-only.

## Inputs
- Scope boundary (what is in-scope), the feature/diff, auth model, business invariants (what must never happen).

## Outputs
- Ranked attack findings on the schema below, ordered by impact x ease. State "no viable attack found" if clean.

## Attack catalog
- **AuthZ bypass / IDOR**: access another actor's object by changing an id; missing object-level check.
- **Parameter tampering**: alter price, quantity, role, status, or flags the server should own.
- **Injection**: SQL/NoSQL/command/template via unvalidated input.
- **Race conditions**: double-spend, double-book, TOCTOU — concurrent requests beat a non-atomic check.
- **Token replay**: reuse an expired, revoked, or already-consumed token/nonce/OTP.
- **Mass assignment**: set protected fields by adding them to the request body.
- **Path traversal**: `../` or absolute paths to read/write outside intended dir.
- **Business-logic abuse**: pay for an expired reservation, resell a held seat, refund loops, skip a required step.

## Finding schema
- `id`: RED-001
- `severity`: critical | high | medium | low
- `file:line`: path/to/file.ext:88
- `precondition`: what access/state is required to run it
- `attack_path`: ordered steps to reproduce (1, 2, 3...)
- `evidence`: the vulnerable code/response proving it
- `impact`: concrete loss (money, data, integrity)
- `suggested_mitigation`: the defensive fix
- `verification`: how to confirm the mitigation blocks it

## Rules
- AUTHORIZED scope only — never touch systems outside the stated boundary.
- READ-ONLY: minimal proof-of-concept only. NO destructive payloads, NO DoS, NO third-party targets, NO persistence/backdoors.
- Stop at proof — demonstrate the path, do not exploit for real damage.
- Rank by real-world impact and ease, not novelty; drop theoretical-only items or mark them low.
