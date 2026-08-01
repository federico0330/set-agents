# Feature 011 — quota-failover design

## Lifecycle

`normalized Anthropic/Pi response → exact classification → terminally close original + persist observed usage
when present + mark provider exhausted globally → authorize one stored-identity linked replacement → dispatch`.

The durable transition is one SQLite `BEGIN IMMEDIATE` transaction named
`close_exhausted_and_authorize_replacement`. It validates the exact eligible error and expected dispatched
original, records the terminal reason and provider-wide exclusion, then authorizes a new dispatch using the
original's stored fallback identity. It does not perform a second route decision. The replacement is linked
back to the original and protected by a single-replacement constraint.

## Classification

Classification is a pure, narrow allowlist over bounded/redacted normalized error facts. The only
`quota_exhausted` result in scope requires all of: Pi's settled API error, Anthropic provider identity, HTTP
`400`, `invalid_request_error`, and marker `out of extra usage`. It has three outcomes:

- `quota_exhausted`: the exact recognized Anthropic quota signature; eligible for this feature's one failover.
- `rate_limited`: recognized rate limit; terminal/retry behavior remains outside this feature.
- `unknown_failure`: every other error; no model/provider inference and no failover.

Rate limits, unknown errors, malformed/partial terminal payloads, and Pi process crashes classify outside
`quota_exhausted`; none writes a provider exhaustion row or authorizes a replacement. Raw provider output,
prompts, credentials, and task content are not persisted.

## Durable schema and idempotency

`routing_runs.replacement_of_run_id` is nullable and self-references `routing_runs.run_id`; only replacement
rows set it. A unique partial index on non-null `replacement_of_run_id` enforces at most one linked replacement
per original. The transaction resolves a repeated call by first reading that link and returning the same
replacement; a uniqueness race is resolved by rereading it, not by creating a new route.

`provider_exhaustions` has no project identifier. Its primary key is the installation-global provider identity,
and `expires_at` is the UTC start instant of the following calendar day. This state is therefore shared by
projects using the installation and expires by comparison to the single UTC instant captured in the transaction.

## Atomic exclusion

Exhaustion state is keyed by installation-global provider identity, never by model or project. The immediate
transaction captures UTC time once, upserts `expires_at` to the start of the next UTC day for the original
provider, revalidates the stored fallback provider is not live-exhausted, and atomically inserts the
replacement. Ordinary routing selection captures UTC time inside its own immediate transaction and filters
providers with a live exhaustion record before selecting or authorizing a route. This prevents a post-commit
selector in any project from selecting an exhausted provider; a selector that committed before the exhaustion
transition remains an already-authorized independent attempt.

The next UTC date automatically falls outside the exclusion predicate. No background timer, local timezone, or
inventory mutation is introduced.

## Independence and accounting

Replacement authorization is not selection: it consumes only the already stored fallback identity and fails if
that identity is now exhausted or violates ordinary authorization. It does not bypass writer/reviewer provider
or family checks; `REVIEWER_INDEPENDENCE_UNAVAILABLE` remains a hard denial. Usage belongs to the original
attempt if observed there, including a failure that was billed; absent `usage_status` is valid. A replacement
records its own observed usage separately.

## E2E boundary

The real-provider test is intentionally opt-in and is mandatory where a controlled exhausted subscription is
available and an alternate provider is usable. It sends a minimal task, captures only redacted evidence, and
asserts database rows, exact linkage/index invariants, installation-global exhaustion, and stored-identity
authorization behavior. If the controlled prerequisite is unavailable, it reports `BLOCKED` /
`HUMAN_DECISION_REQUIRED`; it cannot pass by being skipped. It does not purchase quota, change account limits,
alter credentials, or edit the discovered/static provider inventory.
