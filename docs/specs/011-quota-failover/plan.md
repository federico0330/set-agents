# Feature 011 — quota-failover plan

1. Confirm Feature 007-P2's usage schema and add `replacement_of_run_id` (self FK plus unique non-null partial
   index) and installation-global `provider_exhaustions(provider identity, expires_at)` with no project key.
   Do not reinitialize Feature 008.
2. Implement only the exact normalized settled Pi/Anthropic `400` + `invalid_request_error` + `out of extra
   usage` classifier and close the expected dispatched original without rewriting its identity/fallback fields.
3. Add `close_exhausted_and_authorize_replacement` as one immediate transaction: upsert the original provider's
   UTC-next-day exhaustion, use only the stored fallback identity, revalidate it is not exhausted, preserve the
   reviewer-independence denial, atomically insert one linked replacement, and return it on retry.
4. Add deterministic tests for all non-matching/PI-crash failures, absent usage status, no rewrite, cross-project
   exclusion, stored-identity/no-reselection, atomic concurrent selection, UTC expiry, crash/retry idempotency,
   linkage uniqueness, and reviewer denial.
5. Run the opt-in real-provider E2E when a controlled exhausted subscription and alternate are available;
   inspect all database invariants. Otherwise record `BLOCKED` / `HUMAN_DECISION_REQUIRED`, not pass.

## Decision points

- Store `expires_at` as the UTC start instant of the next day; the selection predicate compares against the one
  UTC instant captured inside its transaction.
- The linkage is `replacement_of_run_id` on the replacement row, with self-FK and unique non-null partial index;
  this is durable/queryable and cannot mutate the original dispatch.
- No fallback re-selection is allowed. Authorization may use only the pre-stored fallback identity and must
  revalidate its provider has no live exhaustion record.
- The exact Pi/Anthropic signature is fixed for this feature. Any other message or process failure is ordinary
  failure.

## Risks and mitigations

- Provider wording drift: maintain narrow exact fixtures and fail closed to generic failure.
- Concurrent routing: use the existing SQLite immediate-transaction boundary for both status and selection.
- E2E availability: when a controlled exhausted subscription is unavailable, record
  `BLOCKED` / `HUMAN_DECISION_REQUIRED`, never a fabricated pass or waiver.
