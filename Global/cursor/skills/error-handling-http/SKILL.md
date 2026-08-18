---
name: error-handling-http
description: HTTP error-handling & contract checklist — correct status codes (409 conflict, 404 not found), one global exception middleware mapping typed domain exceptions, never leak stack traces, verb/cache semantics (GET cacheable, POST not), and idempotency keys for retried mutations. Load when touching API error handling, HTTP responses, or retryable actions.
license: MIT
compatibility: opencode
metadata:
  enabled_for: package-reviewer, security-auditor, architect, implementer
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
6. **Verb & cache semantics** — GET is safe/idempotent/cacheable; PUT/DELETE are idempotent; POST is neither.
   Never hide a mutation behind a GET. Set `Cache-Control` to match, and never cache authenticated/private
   responses in a shared cache.
7. **Idempotency keys** — any mutation that can be retried (network retry, at-least-once queue, and **especially
   an agent-triggered action**) carries a unique idempotency key so a replay is a no-op, not a double-charge or
   duplicated side effect. Name where the key is persisted and its dedup window.

## Verification ideas
Force a conflict → response is 409 with a clean body (no stack). Force an unhandled error in prod config →
client sees generic message + id; full detail only in server logs. One middleware owns the mapping. Replay the
same mutation with the same idempotency key → the side effect happens once, not twice.
