---
name: error-handling-http
description: HTTP error-handling checklist — correct status codes (409 conflict, 404 not found), one global exception middleware mapping typed domain exceptions, never leak stack traces to clients. Load when touching API error handling or HTTP responses.
license: MIT
compatibility: opencode
metadata:
  enabled_for: auditor, security-auditor, architect, implementer
---

# HTTP Error Handling

## When to use
Any API/controller/middleware change, or when mapping domain errors to HTTP responses.

## Inputs
`git diff`, controllers/handlers, exception types, the global error middleware, the API contract/spec.

## Outputs
`PASS` or findings (`id, severity, file:line, evidence, impact, minimal_fix, verification`).

## Checklist
1. **Correct status codes** — concurrency/already-taken ⇒ `409 Conflict`; missing resource ⇒ `404`;
   bad input ⇒ `400`/`422`; unauthorized ⇒ `401`/`403`. Don't collapse everything into 500 or a generic 400.
2. **Typed domain exceptions** — `ConflictException`, `NotFoundException`, etc., mapped in ONE place.
3. **Global exception middleware** — a single mapper type→status, instead of try/catch repeated per controller.
4. **Never leak internals** — no stack trace / framework detail to the client in production; return a generic
   message + correlation id; log the detail server-side only.
5. **Consistent error body** — same shape across endpoints (`{ code, message, correlationId }`).

## Verification ideas
Force a conflict → response is 409 with a clean body (no stack). Force an unhandled error in prod config →
client sees generic message + id; full detail only in server logs. One middleware owns the mapping.
