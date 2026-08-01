# Feature 011 — quota-failover, contract 1.1.0

Status: draft for SPEC_CHALLENGE. This is a new, separately tracked feature. It does not reinitialize,
rewrite, or change the approved/history-bearing state of `008-dynamic-selection`.

## Problem

The Pi lane owns a subprocess and can observe its provider error and usage payload. Today a quota-exhausted
attempt is indistinguishable from a rate limit or an unknown task/runtime error. Retrying indiscriminately can
lose the real failure, consume another paid attempt, and repeatedly select an exhausted provider.

## Scope and invariants

- The only exhaustion signature in scope is a **settled, normalized Pi API error from Anthropic** with HTTP
  `400`, `type=invalid_request_error`, and the normalized marker `out of extra usage`. All three facts are
  required. Rate limits, unknown provider errors, malformed/partial Pi results, and a Pi process crash are
  never exhaustion and never trigger failover.
- The original dispatch closes as a terminal failure with its observed usage persisted through the Feature 007
  accounting path when usage is present. `usage_status` being absent is valid and must not prevent the close
  or authorize invented usage. It is never relabelled as success or replaced in place.
- At most one replacement is created. It is a newly authorized dispatch linked to the original failed run;
  it must not consume, reopen, or rewrite the original dispatch's fallback window or select a new target.
- A recognized exhaustion excludes the provider, not merely the model or project, from all future routing
  selections through the next UTC day. The exclusion is installation-global, and recording it together with
  replacement authorization is atomic, so concurrent selectors cannot authorize the just-exhausted provider
  after the exhaustion transaction commits.
- Existing routed reviewer independence remains a hard requirement. Failover must not select a reviewer that
  violates `REVIEWER_INDEPENDENCE_UNAVAILABLE` merely because another provider was exhausted.
- The acceptance proof includes an opt-in end-to-end run against a genuinely exhausted provider and a usable
  replacement provider. Mocked provider errors are insufficient for this proof.

## Explicit non-goals

- No modification of paid-plan limits, subscriptions, quota balances, provider credentials, or catalog
  inventory/discovery behavior.
- No automatic retry for rate limits or unknown failures.
- No multi-hop failover: exhaustion of the replacement is terminal.
- No relaxation of reviewer independence, fallback-window lifecycle, audit retention, or 008 doctrine.
- No assumption that quota is observable before a real provider response.

## Contracts

1. Classification is a fixed, fail-closed Anthropic/Pi predicate over the normalized settled error: HTTP `400`,
   `invalid_request_error`, and `out of extra usage`. It occurs before terminal close and records no raw
   provider output. No other provider or Pi failure is in this feature's exhaustion scope.
2. The additive schema is explicit:
   - A replacement dispatch has nullable `replacement_of_run_id` referencing the original dispatch's `run_id`
     (self foreign key). A unique partial index on non-null `replacement_of_run_id` enforces one replacement per
     original. Ordinary/original dispatches retain `NULL`.
   - `provider_exhaustions` is keyed solely by installation-global provider identity (no project key) and stores
     `expires_at` as the UTC instant at the start of the next UTC day. Its validity predicate is
     `expires_at > captured_utc_now`.
3. `close_exhausted_and_authorize_replacement` is one SQLite `BEGIN IMMEDIATE` transaction. It validates that
   the original is the expected dispatched row and that the exact known quota signature was normalized; then it
   closes the original as `quota_exhausted` and persists observed usage if supplied. It must not assign or
   rewrite **any** original `selected_*`, `actual_*`, `fallback_*`, `fallback_consumed*`, or
   `fallback_window_open` field. The only permitted original mutations are terminal state/outcome, timestamps,
   and Feature-007 usage fields.
4. The same transaction upserts the installation-global exhaustion record, reads the already stored fallback
   identity from the original, revalidates that that replacement provider is not exhausted at the captured UTC
   instant, applies ordinary authorization (including reviewer independence), and atomically inserts the linked
   replacement. It never runs a fresh route selection or selects a different identity. Repeating the operation
   after a crash/retry returns the already linked replacement, protected by the unique link, rather than
   creating another one.
5. Every ordinary selection transaction captures UTC time inside its own immediate transaction and excludes
   providers with a live `provider_exhaustions` row. Eligibility resumes automatically after `expires_at`.
6. The feature's E2E gate is opt-in but required when a controlled exhausted subscription and a usable
   alternate are available. It proves both durable rows, linkage, installation-global exclusion, and database
   invariants after a real exhausted-provider response. If that controlled precondition is unavailable, the
   E2E criterion is `BLOCKED` / `HUMAN_DECISION_REQUIRED`, never a passing or waived result.

## Dependencies and risks

- Depends on Feature 007-P2 usage persistence and its schema migration discipline.
- Touches routing lifecycle and concurrency; all status mutation and selection exclusion must share a database
  transaction boundary.
- A provider's public error wording can change. Signatures must be narrow, versioned/allowlisted, and unknown
  wording must fail as unknown rather than guessing quota exhaustion.

## Verification

Focused unit/integration tests cover the exact three-part Anthropic/Pi signature; every out-of-scope failure;
terminal usage persistence with and without `usage_status`; original no-rewrite invariants; one-replacement
linkage across crash/retry; stored-identity authorization without reselection; UTC expiry; cross-project,
installation-global exclusion; concurrent selector exclusion; and unchanged reviewer denial. An explicit,
credential-gated E2E test uses an actually exhausted provider and asserts the durable database state rather
than stubbing an error response. When its controlled precondition is absent, it records `BLOCKED` /
`HUMAN_DECISION_REQUIRED`. Standard repository gates, including `./ai/scripts/verify.sh` and
`git diff --check`, remain required.
