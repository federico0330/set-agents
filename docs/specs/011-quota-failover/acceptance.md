# Feature 011 — quota-failover acceptance

## AC-01 — Classify only recognized quota exhaustion

Given Pi reports a settled, normalized Anthropic API error with HTTP `400`, `type=invalid_request_error`, and
the marker `out of extra usage`,
when its terminal result is handled,
then the run is classified `quota_exhausted`.

Given a rate-limit signature, another provider error, an unrecognized/malformed error, or a Pi process crash,
when its terminal result is handled,
then it keeps its distinct rate-limit or generic failure outcome, no provider exhaustion is written, and no
replacement is authorized.

## AC-02 — Preserve the failed attempt

Given a recognized quota-exhausted dispatched run with a provider usage payload,
when it is closed,
then the original row is terminally failed as `quota_exhausted` and retains the observed usage under the
Feature 007 accounting rules.

Given a recognized quota-exhausted dispatched run without `usage_status`,
when it is closed,
then the close remains valid and no usage value is invented.

And no `selected_*`, `actual_*`, `fallback_*`, `fallback_consumed*`, or `fallback_window_open` field on that
original row is assigned, rewritten, or reopened; only terminal state/outcome, timestamps, and usage fields may
change.

## AC-03 — Authorize one linked replacement

Given the original dispatched run closes with the exact recognized quota signature and its stored fallback
identity is eligible and not exhausted,
when failover executes,
then exactly one new dispatch is authorized under that stored identity, linked by
`replacement_of_run_id`, and dispatched under its own identity without a fresh selection.

Given the same close/failover operation is retried after a process crash or a caller retry,
when it reaches the transaction again,
then it returns the existing replacement linked to that original and the unique non-null replacement link
prevents a second dispatch.

Given the stored fallback provider became exhausted before replacement authorization,
when failover executes,
then it does not reselect another route and no replacement is created.

Given that replacement also exhausts or fails,
when it closes,
then no third dispatch is authorized by this feature.

## AC-04 — Exclude an exhausted provider atomically

Given provider A is classified exhausted in project X at UTC instant T,
when the close/exhaustion transaction commits,
then `provider_exhaustions` records provider A without a project key and with `expires_at` at the start of the
next UTC day, and every subsequent selection in project X or project Y before that instant excludes all
provider-A routes, regardless of model.

Given concurrent selectors race with that transition,
when their transactions complete,
then none can authorize provider A after the exhaustion transaction commits.

Given the captured UTC time reaches `expires_at`,
when a new selection is made,
then provider A is eligible again unless another normal routing rule excludes it.

## AC-05 — Keep reviewer independence hard

Given the only eligible replacement would violate routed reviewer independence,
when replacement authorization is evaluated,
then routing returns the existing hard denial and no compromised reviewer dispatch is created.

## AC-06 — Prove the live failure path

Given an explicitly enabled test environment with one controlled, genuinely exhausted subscription and another
usable provider,
when the opt-in E2E scenario runs a minimal Pi task,
then it observes the real provider exhaustion response, not a mock, records the failed original with observed
usage when supplied (or validly absent `usage_status`), authorizes one linked replacement, and completes the
task through that replacement.

And inspecting the routing database proves both rows, their unique linkage, the installation-global provider
exclusion through `expires_at`, and no paid budget, quota balance, or provider inventory was altered by test
setup.

Given no controlled exhausted subscription is available,
when the opt-in E2E gate is evaluated,
then it records `BLOCKED` / `HUMAN_DECISION_REQUIRED`; an unavailable live precondition is not a passing,
skipped, or waived E2E result.
