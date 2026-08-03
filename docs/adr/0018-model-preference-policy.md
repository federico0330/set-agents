# ADR-0018 — Model preference policy: a closed role-class taxonomy, one tie-break sort-key
element, never a second decision-maker

- Estado: Accepted (2026-08-02). Feature `014-model-preference-policy`, contract 3.2.0 (four
  spec-challenge rounds, `approve-with-amendments`, user-approved 2026-08-02). Package
  `P1-model-preference-policy`.
- Context: `ai/scripts/routing_core/service.py` (`RoutingService.route()`'s candidate sort key),
  `ai/scripts/routing_core/domain.py` (`RouteDecision`, the new `resolve_bias_class` resolver),
  `ai/scripts/set_agents_app.py` (the sibling `model-preference.toml` config surface and its CLI),
  `roles.tsv` (`capability`/`duty` columns), `models.toml` (`[roles.<role>.tiers.*]`,
  `[areas.<duty>]`, governed by Accepted `ADR-0003`).

## Contexto

The user runs shifting model/provider subscriptions over time (today Anthropic + OpenAI, soon
Kimi Code, possibly OpenCode Go too) and wants which *kind* of work goes to which provider to be
biased by whichever subscriptions are *currently* active — credential-detected, never a manual
edit or a scheduled date — without bypassing the existing dynamic selector
(`RoutingService.route()`). This repo already tried a fixed role→provider preference once:
`007-quota-visibility`'s `P0-role-affinity`, reverted the same day it was reviewed
(`ai/state/decisions-log.jsonl:23`, slug `p0-role-affinity-reverted`) for two real defects — (1)
a preferred-but-unauthenticated provider could route a decision straight out of the dynamic
system by falling back to a static agent, and (2) nothing enforced the two hand-maintained
role-groups were disjoint from each other or the roster. Both are addressed by construction below,
not by discipline alone. `spec-challenge` additionally forced a hard precondition before any of
this could be designed: does a writer-role decision (`implementer`, `debugger`, …) flow through
`RoutingService.route()`'s sort key at all, or through the separate static
`models_config.resolve_role`/`[areas.<duty>]` mechanism `ADR-0003` governs? Reading the code
directly answered this — `RoutingService.route()` builds and sorts exactly one candidate list for
every `role_class` alike (`"writer"`, `"review"`, `"other"`), so a writer decision's candidate
*selection* is the identical sort this contract's other classes already use; `[areas.<duty>]`
governs a genuinely different, non-per-decision surface (the static, install-time-baked default
for unrouted delegation and session-start resolution). That finding is what makes the design below
possible without a second integration point.

## Decisión

1. **A closed, four-value, disjoint role-class taxonomy over `roles.tsv`'s existing `capability`/
   `duty` columns — `decision`, `grunt`, `build`, `unscoped` — resolved by one function,
   `resolve_bias_class` (`routing_core/domain.py`), reused everywhere it is needed rather than
   duplicated a second time.** `grunt` (`capability == "review-ro" AND duty IN {"audit","judge"}`)
   and `build` (`capability == "code-rw"`) are, by definition, the exact predicates
   `RoutingService._role_class` already computes as `"review"`/`"writer"` (`service.py:312-317`) —
   reused literally, not reconstructed as an equivalent compound condition. `decision`
   (`duty IN {"coord","docs"}`) is new: the user's own two named examples, `orchestrator` (the
   sole `coord`-duty role) and `architect`, generalized to the other four `docs`-duty roles by the
   same "any role that makes judgment calls" language the user's own request used, confirmed
   correct by the user directly. Every other role is `unscoped`. Membership: `decision`=7,
   `grunt`=6, `build`=7, `unscoped`=8, summing to the full 28-role roster, enforced by a
   disjoint-partition regression test — directly mitigating `P0`'s finding 2. An explicit
   `[role_override]` entry (see decision 2) takes precedence over the default predicate; the
   resolver never falls back to a role-by-role provider table, which would reopen `P0`'s exact
   flaw.
2. **A dedicated sibling config file, `~/.local/state/set-agentes/model-preference.toml`, never
   routed through the pre-existing `write_app_config`/`app_config()` pair.** `write_app_config` is
   a flat `key = value` serializer that corrupts a nested preference table into JSON object
   syntax `tomllib` cannot parse, and `app_config()` silently swallows any parse failure as `{}`,
   discarding every unrelated key already in the file — both failure modes this contract's own
   sibling file must never reproduce. Two closed-shape tables: `[preference]` (role-class ->
   ordered provider list, from the same closed vocabulary `_PAIR_COMMANDS` already probes:
   `openai-codex`, `anthropic`, `opencode-zen`, `opencode-go`) and `[role_override]` (role name ->
   one of the three named classes — `unscoped` is a resolution outcome, never a legal override
   target). A dedicated, purpose-built two-table serializer (not a general nested-TOML writer),
   written via the pre-existing `atomic_write` helper (temp file + `os.replace`, already
   established for the Claude settings JSON writer). The loader (`load_model_preference`) and the
   two CLI write paths (`cmd_model_preference_set`/`cmd_model_preference_role_override`) share the
   same small validator functions — a malformed provider/role/class token can never even be
   *written* by the CLI; a hand-edited file is the only way to reach the load-time `die()` path.
   Every malformed input fails closed via `ModelPreferenceError`, never a silent default.
3. **One integration point, shared by all three in-scope classes, at one precise, narrow position
   inside `RoutingService.route()`'s existing candidate sort key — never a second decision-maker.**
   The resolved class's ordered preference list participates as one additional sort-tuple element,
   `_bias_rank`, inserted between the existing tier element and `curated_priority`:
   `(independence_boolean, tier_order, bias_rank, curated_priority, route_id)`. Never before the
   independence/tier boundary; never a change to the exclusion loop that builds `candidates`
   (`service.py:250-297`, untouched) — every existing hard exclusion
   (`PROVIDER_UNAUTHENTICATED`, `REVIEW_PROVIDER_CONFLICT`, `TIER_INSUFFICIENT`, …) fires exactly
   as before this weight is ever consulted, directly closing `P0`'s finding 1: a preferred-but-
   unauthenticated candidate can never fall back out of the dynamic system, because it never
   becomes a candidate in the first place. Never a change to `routes.v1.toml`'s
   `roles`/`tools`/`tier` membership — no role gains or loses eligibility because of this
   contract, unlike `P0`'s twelve duplicated rows. Absent configuration (no file, or the resolved
   class is `unscoped`, or the class has no `[preference]` entry) evaluates to one constant rank
   for every candidate, so ordering is byte-identical to today's four-element sort — no separate
   code branch preserves the unbiased default; it falls out of the same code path. A regression
   test pins the sort tuple's exact five-element shape so any future change — this contract's or
   another's — fails loudly, not silently.
4. **The preference tables reach `RoutingService` through the existing `config` dict parameter,
   under an internal-marker key, never a `routing.py` signature change.** `routing.py`'s
   `compose()`/`_compose_for_tests()` are the harness's one production/test composition facade and
   were out of this package's owned paths; extending their signature was rejected (see below).
   Instead, `set_agents_app.py` (which already loads `models.toml` into a plain dict before calling
   `routing.compose`) injects the sibling file's already-validated
   `{"preference": {...}, "role_override": {...}}` under `config["_model_preference"]` — the same
   underscore-prefixed, never-re-serialized internal-marker convention `models_config.py` already
   uses for `config["_source_schema"]`. `RoutingService.__init__` reads and strips this key;
   `RoutingService._for_tests` (the hermetic test seam) takes the same tables directly as two new,
   independently-defaulted keyword arguments, so every pre-existing call site of that seam stays
   byte-identical without updating its call.
5. **`RouteDecision` gains two new, additive, defaulted fields: `bias_class` and
   `preference_configured` — never colliding with the pre-existing, differently-valued
   `role_class` envelope key `cmd_route_decide` already emits.** `role_class` is
   `RoutingService`'s own internal three-value classification (`{"writer","review","other"}`);
   `bias_class` is this contract's four-value classification
   (`{"decision","grunt","build","unscoped"}`) — same envelope, same decision, two independent,
   disjoint-vocabulary classifications of the same role, deliberately not named as near-homonyms.
   `bias_class` is `None` only for the two refusals that fire strictly before `role_class` itself
   is computed (`service.py`'s issuer/consume guard and its request-shape guard); it is populated
   for every refusal reachable only after that point, including two refusals that share the
   identical `reason_codes=("FACTS_INCOMPLETE",)` tuple as one of the early guards yet differ in
   `bias_class` — proving `reason_codes` alone cannot predict population. Both fields are added at
   the end of the frozen dataclass, so all 14 pre-existing `RouteDecision(` construction sites in
   `service.py` stay valid, and `to_dict()` (`dataclasses.asdict`-based) picks up both fields for
   free.
6. **Coexistence with `ADR-0003`'s `[areas.<duty>]`, not a second, competing source of truth — three
   concrete reasons, not an assertion.** Narrower surface by construction: this contract only ever
   reorders the six curated `routes.v1.toml` candidates that already survived every hard exclusion,
   and only for decisions routed through `--route-decide`; it never assigns a model to an area,
   never creates or removes a candidate. Keyed by the same signal, not an independently
   hand-maintained table: every one of the four classes is derived from `roles.tsv`'s own
   `capability`/`duty` columns — the same axis `[areas.<duty>]` is keyed by. A tie-break, never an
   assignment, never consulted before the hard-exclusion loop: `P0`'s actual defect was a
   preference consulted *before*, and independently of, whether the preferred option was live; this
   contract's weight is evaluated strictly *after* every hard exclusion and can only choose among
   candidates already authorized to be selected.

## Rejected alternatives

- **A hand-written role→provider table, `P0`'s exact shape.** Directly reopens both of `P0`'s
  proven defects (finding 1: dynamic-system bypass on a stale preference; finding 2: unaudited,
  non-disjoint role grouping). Rejected outright, restated as the precedent this contract must not
  repeat.
- **Widening `write_app_config` to serialize nested tables correctly, instead of a sibling file.**
  Strictly more code, touches every call site that already depends on `write_app_config`'s current
  flat-only contract, and needs new regression coverage on a writer other, unrelated features
  already rely on — for one feature's own two-table schema. A dedicated sibling file with its own
  small, fixed-shape serializer is strictly less code and needs no shared-writer regression risk.
- **A genuine per-project configuration layer, above the per-harness-install file.**
  `models.toml`/`roles.tsv` are themselves `HARNESS_HOME`-owned (Accepted `ADR-0008`), so there is
  no existing per-project layer to place this preference above; the user separately accepted
  per-harness-install scope during spec-challenge.
- **Extending `routing.py`'s `compose()`/`_compose_for_tests()` signatures to carry the preference
  tables explicitly.** `routing.py` was outside this package's owned paths. The `config` dict
  channel (decision 4) achieves the same result — the resolved tables reaching
  `RoutingService.__init__` — with a strictly smaller diff and zero signature change to a shared
  composition facade other features also call.
- **Reusing `reason_codes` to carry `bias_class`/`preference_configured`.** `reason_codes` is a
  closed vocabulary of terminal/refusal reasons `_decide_status`'s own reason→exit-code table
  branches on; folding an always-present, purely informational field into it would blur a
  vocabulary other code already depends on for control flow.

## Accepted residual risk

`decision`'s seven roles, and fourteen of `grunt`/`build`'s thirteen non-`decision` roles, have no
reachable real-world effect today — not a credential gap this contract's mechanism could close, but
because the shipped orchestrator doctrine (`Global/_canonical/agents/orchestrator.md:157-158`,
byte-identical across all three generated copies) only ever invokes `--route-decide` for six named
"tiered roles". This is accepted, not mitigated further, and tested: a doctrine-consistency
regression check reads the exact six role names from all four orchestrator-doctrine files
(canonical plus its three generated copies) and asserts they match `models.toml`'s own
`[roles.<role>.tiers.*]` six-role universe byte-for-byte, so a future doctrine or tiered-roster
drift fails loudly instead of silently invalidating this ADR's own claim. `015-anthropic-dispatch-
parity` (Accepted `ADR-0019`) closed the credential half of this picture for the six tiered roles
specifically — `grunt`'s four and `build`'s two now have real, live, observable effect on the
primary `opencode` lane via the `_PROVIDER_RUNTIME_REDIRECTS` redirect, verified against the live
effective-runtime inventory — but this contract needed zero code change for that to become true,
and the fourteen non-tiered `grunt`/`build` roles plus all seven `decision` roles remain unaffected
by any future credential change, for the same operational (doctrine-invocation) reason.

Onboarding a standalone "Kimi Code" credential surface (verified live, not present as any
`_PAIR_COMMANDS` pair or on-machine credential today) and widening which roles are dynamically
tiered are both real, external, non-goal dependencies for this contract's mechanism to reach
further — named here, not silently assumed.

A further, honest limitation of today's two-provider (`anthropic`/`openai-codex`) catalog, not
mitigated further and recorded as a durable decision (`docs/notas/decisiones/`, slug
`ac-01i-grunt-no-flip-en-verified-review-2-proveedores`): `REVIEW_PROVIDER_CONFLICT` already forces a
verified reviewer decision onto the one provider that differs from the writer's, so with only two
providers authenticated a configured `grunt` preference can never additionally choose a *different*
provider for that decision — it can only be proven to make the `anthropic` candidate *survive*
(`PROVIDER_UNAUTHENTICATED`/`REVIEW_PROVIDER_CONFLICT`) where it previously did not. Genuine
cross-provider reordering by `grunt`'s own preference is proven instead, uniformly across all four
classes, on the `unverified_review` shape (no forced writer identity to reorder against).

## Consecuencias

- The routing service's candidate sort key gains exactly one new element, uniformly consulted for
  every role and every class alike; no second decision-maker exists anywhere in this contract, and
  none of `RoutingService.route()`'s existing hard exclusions, tier ordering, or reviewer-
  independence guarantees can ever be reordered past or bypassed by a configured preference.
  `008-dynamic-selection`'s future `P3` sketch (budget-aware selection, still `BLOCKED`/scoped-not-
  contracted) would share this same sort-key region if it ever lands; the tripwire test that pins
  today's five-element shape is this contract's own forward-compatibility guarantee against a
  silent shape drift either package could introduce.
- A future package that wants to widen which roles are dynamically tiered, or onboard a new
  provider, needs zero change to this contract's taxonomy, resolver, config schema, or sort-key
  integration — the mechanism is uniform and already exercises every class; only the operational
  doctrine and `models.toml`'s tiered roster would need to move.
- `resolve_bias_class` (`routing_core/domain.py`) is now the second role-classification predicate
  in this codebase, alongside the pre-existing, deliberately-not-deduplicated
  `RoutingService._role_class`/`set_agents_app._role_class_of` pair — a future reader should not
  assume the two are the same function or the same vocabulary; they are disjoint by design (see
  decision 5).
