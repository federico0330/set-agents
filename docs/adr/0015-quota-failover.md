# ADR-0015 — Quota failover is a new linked dispatch, not fallback-window reuse

- Estado: Proposed (2026-07-30). Feature `011-quota-failover`, contract 1.1.0.

## Contexto

The Pi routing lane can observe a real provider failure after dispatch. A recognized quota exhaustion means an
attempt may already have consumed subscription usage, while its static fallback window is intentionally closed
once dispatch begins. Reopening that window or rewriting the dispatched row would make the audit record claim a
different execution than the one that ran.

The failure must also be distinguished from a rate limit and from unknown errors. An over-broad classifier
would silently send a task to another paid provider after a real application error. Finally, choosing another
model from the same exhausted provider rediscoveries the same quota boundary on every future selection.

## Decision

1. Recognize exhaustion only from the exact normalized, settled Pi/Anthropic API error: HTTP `400`,
   `invalid_request_error`, and `out of extra usage`. Rate limits, every other error, incomplete results, and Pi
   crashes do not enter failover or provider exhaustion state.
2. Close the expected dispatched original run terminally as `quota_exhausted` and persist its observed usage
   through Feature 007 when supplied; absent `usage_status` is valid. Do not assign any original `selected_*`,
   `actual_*`, `fallback_*`, `fallback_consumed*`, or `fallback_window_open` field. Only terminal outcome/state,
   timestamps, and usage fields may change.
3. Model a replacement with nullable `replacement_of_run_id` on its new dispatch row, self-referencing the
   original and protected by a unique non-null partial index. The link, rather than a narrative correlation,
   makes one replacement durable and idempotent.
4. Perform `close_exhausted_and_authorize_replacement` in one SQLite `BEGIN IMMEDIATE` transaction: validate
   the original row and exact signature; upsert the original provider into installation-global
   `provider_exhaustions`; obtain only the original's stored fallback identity; revalidate its provider is not
   exhausted; apply ordinary authorization; and atomically insert or return the one linked replacement. It must
   never run a new route selection.
5. Key `provider_exhaustions` by installation-global provider identity, never by model or project, with
   `expires_at` at the UTC start of the following day. All project selections exclude a live record inside their
   own immediate transaction; eligibility resumes at `expires_at`.
6. Preserve routed reviewer independence exactly. Exhaustion is not authority to select a reviewer that would
   otherwise be denied as `REVIEWER_INDEPENDENCE_UNAVAILABLE`.
7. Require an opt-in E2E proof with a controlled, genuinely exhausted subscription and a usable alternate when
   that controlled precondition is available. It must assert durable database state, not merely logs. If the
   precondition is unavailable, evidence is `BLOCKED` / `HUMAN_DECISION_REQUIRED`, never a passing skip.

## Rejected alternatives

- **Reopen and consume the original fallback window.** It turns a post-dispatch failure into a pre-dispatch
  fallback and rewrites the audit meaning of the original attempt.
- **Per-model exhaustion memory.** Quota belongs to the provider plan; it merely repeats a failed request on a
  sibling model.
- **Project-scoped exhaustion memory.** The same installation subscription can be consumed through another
  project, so isolating the record by project permits an immediately known-exhausted provider to be selected.
- **Re-run routing selection for the replacement.** It could silently choose a different route on retry and
  loses the originally stored fallback decision; authorization must be of that identity alone.
- **Retry rate limits and unknown failures as quota exhaustion.** This converts transient or product defects
  into silent cross-provider work and can add paid consumption.
- **Relax reviewer independence during failover.** Availability does not justify collapsing separation of
  duties.
- **Change paid budgets or provider inventory.** This feature reacts to observed failure only; billing and
  inventory policy stay outside its scope.

## Consecuencias

- History accurately shows the billed, failed original and its independently authorized replacement.
- Provider-wide, installation-global exclusion avoids repeated dead spawns across projects while remaining
  conservative: availability is reconsidered automatically at the next UTC boundary, not guessed from a local
  clock or opaque timeout.
- Failover is bounded. A replacement failure remains a real terminal outcome, avoiding a cascade that drains
  multiple subscriptions.
- The design adds routing state and concurrency obligations but no external dependency, provider catalog
  change, paid-budget action, or change to Feature 008's established state.
