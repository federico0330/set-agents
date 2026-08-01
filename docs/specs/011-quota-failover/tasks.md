# Feature 011 — quota-failover tasks

## P1 — Routing state and failover

1. Define additive schema/state changes for `quota_exhausted`, observed usage,
   `replacement_of_run_id` (self-FK and unique non-null partial index), and installation-global
   `provider_exhaustions` with UTC `expires_at`. Validate migration and legacy behavior. (AC-02–AC-04)
2. Implement only the exact normalized settled Pi/Anthropic `400` / `invalid_request_error` /
   `out of extra usage` classifier and terminal processing. Do not route rate limits, unknown errors, malformed
   results, or Pi crashes through failover. (AC-01, AC-02)
3. Implement `close_exhausted_and_authorize_replacement` as one immediate transaction with strict original-row
   validation, no original identity/fallback-field rewrite, provider-exhaustion upsert, stored-fallback-only
   authorization, revalidation, and idempotent linked insertion. Preserve reviewer-independence invariants.
   (AC-02–AC-05)
4. Add focused deterministic tests, including transaction/concurrency, cross-project exclusion, absent usage
   status, no-rewrite, stored-identity/no-reselection, and crash/retry idempotency assertions. (AC-01–AC-05)
5. Add a separately invoked, credential-gated real exhausted-provider E2E runner and evidence format. It must
   assert database invariants, use no mocks or paid budget/inventory mutation, and report unavailable controlled
   exhaustion as `BLOCKED` / `HUMAN_DECISION_REQUIRED`, never pass. (AC-06)

## Required checks

- Migration and routing unit/integration suite.
- Repository verification and diff whitespace check.
- Independent package review of the complete state-machine change, including schema, concurrency, accounting,
  review independence, and E2E evidence.
