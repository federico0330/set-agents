# Feature 014 — model-preference-policy, contract 3.1.0

Status: `revision_required` after SPEC_CHALLENGE round 3 (8 findings, R3-F-01..R3-F-08, 2 blocking) — a
**correction pass, not a rescope**: round 3 found this contract's "real effect today" claim was overstated
(it inherited an "already silently defeated in production" framing from `015`'s own since-superseded round-1
draft, and separately overclaimed live effect for `implementer`/`debugger` on the primary lane without
verifying this machine's actual credential shape), plus six lower-severity citation/precision findings. All
eight are fixed here; no acceptance criterion, class, role count, or invariant confirmed clean in round 3 is
touched — see `## Historial de challenge` for the full disposition. This round also surfaces a genuinely good
update, not just corrections: `015-anthropic-dispatch-parity` was redesigned in parallel (now its own contract
**2.0.0**, `docs/specs/015-anthropic-dispatch-parity/spec.md`) around a cross-lane provider redirect that,
once shipped, gives `014` real effect on BOTH its `build` class AND its `grunt` class — not only `build`, as
round 2 believed. No package opened, `feature-state.py init` not run. Depends, non-blockingly, on
`008-dynamic-selection`'s P1 (`accepted` per `ai/state/features/008-dynamic-selection.json` →
`packages[] where package_id="P1-uninterrupted-delegation" → status="accepted"`, though `008/spec.md`'s own
header prose still reads "P1 contract drafted" — a stale status line in that file, not touched by this
contract, cited here only so this dependency claim is grounded in the real state machine, not stale prose) and
on `012-discovered-inventory`'s P1 (`accepted`, same state-file pattern,
`ai/state/features/012-discovered-inventory.json`). This is a **sibling** of `008-dynamic-selection`'s P3
sketch (budget-aware selection, scoped-not-contracted, blocked on `007-P2`), not an amendment to it — P3 stays
exactly as blocked as it already is; this contract does not touch `docs/specs/008-dynamic-selection/spec.md`
and has no dependency on `011-quota-failover`.

**Corrected this round, stated once here and precisely, not as a vague forward-pointer:** `014` has **zero
code dependency** on `015` — it never edits routing/doctrine, only a sort-key bias consulted strictly after
routing already happened, so nothing in this file's own mechanism requires `015` to exist. But `014`'s
**observable, real-world effect** on the primary `opencode` lane is a different question, and round 3 found it
was answered wrong in 3.0.0: verified live this session, `('opencode','anthropic')` probes to **zero** models
on this machine (`opencode auth list --pure` lists four credentials, none `Anthropic`; `opencode models
anthropic --pure` → `Error: Provider not found: anthropic`), so `014`'s mechanism has **zero live, observable
effect on the primary lane today, full stop — for all three classes alike, including `implementer`/`debugger`,
previously (3.0.0) claimed to be "the entire real, live, working scope."** This is `015`'s prerequisite gap,
not `014`'s bug — see `### Honest scope` for the exact per-lane, per-class breakdown (including the one real
exception, the `pi` lane, live-verified this round, not `[runtime].primary`) and the new `### Dependency on
015` subsection for what `015`'s contract 2.0.0 (pre-challenge as of this citation) concretely changes once it
ships, with its own real AC numbers. No other feature's approved contract is edited by this file, and
`Global/_canonical/**` and its three generated copies are never touched by this contract, in this round or any
other.

See `## Historial de challenge` at the end for what round 1 and round 2 found and how each finding was
resolved.

## Contexto

**The request, in the user's own terms (session, 2026-07-31).** The user runs two $100/month subscriptions
today (Anthropic/Claude, OpenAI/GPT). In roughly twelve days that mix changes: GPT is dropped, Kimi Code
($40/month) is added, possibly alongside OpenCode Go ($10/month) as a backup. The mix will keep changing —
this is not a one-time migration. The ask: which model/provider handles which *kind* of work should be
**biased by which subscriptions are currently active**, not fixed in code, and it must still flow through the
**existing** dynamic selector — this contract adds a configurable weight to that mechanism, it does not
replace or race it with a second decision-maker. Two work-classes were named: "decision-making" work
(orchestrator, and — the user's own words — "by extension any role that makes judgment calls, architect,
adversarial judges, etc.") biased toward whichever family is *currently* the trusted/premium option (GPT right
now, Claude once GPT is dropped); and "grunt work / adversarial-judge / bulk-verification" work biased toward
the cheaper, disposable option. The user separately named, twice, that credential detection (not a manual
config edit, not a scheduled date — both alternatives were offered and rejected this session) must drive which
subscriptions count as "currently active."

**A real, contradictory detail in the user's own two bullets, resolved explicitly below, not glossed
over:** "adversarial judges" is named once as an example of *decision-making* work (parenthetically, next to
"architect") and once, by its exact role name, as the flagship example of *grunt* work ("'grunt work' /
adversarial-judge / bulk-verification work"). Both cannot be true for the same role under a two-class model.
Resolved in AC-01 below, on real evidence (`adversarial-judge`'s actual shape in `roles.tsv` matches the
audit-duty review roles the second bullet calls grunt, not `architect`'s planning shape) — stated as a product
decision this draft makes, not a silent assumption; it is exactly the kind of pairwise conflict this repo's
own spec-writing discipline requires resolving before hand-off, and it is flagged again in the Audit for
`spec-challenger`/`USER_APPROVAL` to confirm or overturn.

### The scope-widening decision (round 1 → round 2, why this is contract 2.0.0 and not 1.1.0)

Round 1 (13 findings, `revision_required`) asked the user, directly, whether the two-class taxonomy
(`decision`/`grunt`, 13 of 28 roles) was the right scope, and separately raised (finding F-06) that the seven
`duty="implement"`/`capability="code-rw"` writer roles were structurally excluded from both classes and fell
into `unscoped`. The user's answers widen the contract, in the user's own verbatim words:

- *"Quiero que un rol no tenga hardcodeado ningun modelo, justamente, a eso apunta eliminar estas
  features."* — the taxonomy is not meant to cover only decision-making and grunt work; no role should have a
  model pinned by construction, full stop.
- *"También quiero influir en quién implementa."* — the bias must also reach the roles that do the actual
  implementation work: the seven writer/`code-rw` roles round 1 found excluded.

**This is a real, third role-class, not a wording change.** A new class, `build`, covers exactly the seven
`duty="implement"`/`capability="code-rw"` roles (`test-writer`, `implementer`, `frontend-engineer`,
`refactor-specialist`, `debugger`, `repair-agent`, `integrator` — `roles.tsv:11-17`, counted directly), using
the SAME mechanism already designed for `decision`/`grunt`: a configurable, credential-aware, weighted bias
inserted into `RoutingService.route()`'s existing candidate sort key — never a hardcoded override table, never
a second decision-maker, never bypassing an existing hard exclusion. The investigation below (required before
this class could be designed at all) confirms it is the *same* integration point, not a second one.

### The architectural question this widening forces, resolved by reading the real code (F-06)

Round 1 found `execution_enabled=True` (`service.py:216`, gated at `service.py:175`) is reachable only when
`role_class == "writer"` (`RoutingService`'s own internal `_role_class`, `service.py:221`) — and, separately,
this repo has an older, pre-existing static mechanism: `models.toml`'s `[areas.<duty>]` → `[roles.<role>]`
tables, resolved by `models_config.py`'s `resolve_role` (`models_config.py:238-264`, base→area→role merge),
governed by Accepted `ADR-0003`. Round 1 did not resolve which of these two mechanisms actually selects the
model for a writer-role decision today. It had to be resolved before the `build` class could be designed,
because the two mechanisms have opposite implications for AC-04's integration point — reusing it if writer
decisions flow through `RoutingService.route()`, or requiring a second, separately-justified integration point
if they do not.

**Finding, read directly from the code, not assumed:** they coexist, but at **different points in the
pipeline, for different purposes, and only one of them is a per-decision selector**.

1. **`RoutingService.route()` builds exactly one candidate list and runs exactly one `candidates.sort(...)`
   call (`service.py:135-171`), for every `role_class` value alike** — `"writer"`, `"review"`, and `"other"`
   all go through the identical exclusion loop and the identical sort. `role_class` is computed once, early
   (`service.py:113`), and is consulted only *after* the sort to decide (a) whether independence exclusions
   apply (`role_class == "review"`, lines 115-126) and (b) whether the terminal branch returns a
   non-executable report or mints a durable authorization (`role_class == "writer"` and not `simulate`, lines
   175-216). **`candidates[0]` — the actual selected route — is decided by the SAME sort key regardless of
   which of the three `role_class` values applies.** A writer-role decision's candidate selection is not a
   parallel code path; it is the identical sort this contract's `decision`/`grunt` classes already insert into.
2. **This is not hypothetical or test-only.** `cmd_route_decide` (`set_agents_app.py:385-...`) accepts any
   `role` from `roles.tsv`, including the seven `duty="implement"` roles, computes its own `_role_class_of`
   (`set_agents_app.py:230-233`, the verbatim-duplicated twin of `service.py`'s predicate, already named as a
   pre-existing duplication this contract does not fix) and calls `service.route(...)` with it — writer roles
   are routed through this exact CLI today. `008-dynamic-selection`'s own accepted P1 doctrine states directly
   that `--route-decide` is **runtime-agnostic** and used across all four `SELECTED_RUNTIMES`
   (`docs/specs/008-dynamic-selection/spec.md:116-123`, citing `domain.py:20` and
   `set_agents_app.py:390`), and `set_agents_spawn.py`'s own module docstring (the pi-lane CLI-subprocess
   spawner) states its lifecycle runs over *"the SAME dispatch CLI the OpenCode lane uses"* — confirming
   `--route-decide` is the harness's one dynamic per-decision selector, not a pi-only or review-only mechanism.
3. **`models_config.py`'s `resolve_role`/`[areas.<duty>]` is a genuinely separate mechanism, at a different
   point in the pipeline: it sets the STATIC, install-time-baked DEFAULT model for a role** — consumed by
   `generate.py`'s own `load_roles` wrapper to bake a model into every generated native-runtime agent
   definition (the frontmatter a native Claude Code/OpenCode subagent invocation falls back to when no routed
   `--route-decide` decision is in play), and by `codex_orchestrator()` (`models_config.py:373-380`) for the
   orchestrator's own Codex CLI session-start model. It never runs per-decision, never observes live
   credentials, and never reorders anything — it assigns one fixed value per area, resolved once at generation
   time (or session start), full stop. `008-dynamic-selection`'s own P1 doctrine names exactly this seam:
   *"delegation that carries no routing decision: non-tiered roles... and sessions driven by the shared
   doctrine with no `--route-decide` in play"* (`008/spec.md:129-130`) is the surface `[areas.<duty>]` still
   governs untouched, distinct from the surface this contract's sort-key bias reaches.

**Conclusion for the `build` class's design:** it reuses AC-04's existing, single integration point —
the same sort-key position `decision`/`grunt` already use — because writer-role candidate selection, whenever
it flows through the routed `--route-decide` dispatch, runs through the identical code this contract already
modifies. No second integration point is designed or needed. What the `build` class's bias does **not** reach
is the static `[areas.<duty>]` default consumed for untiered/ad hoc delegation and session-start resolution —
that surface is untouched, named explicitly in Non-goals, and is not a gap this contract silently leaves: it
is the same "unrouted delegation keeps its doctrine-only default" behavior `008-dynamic-selection`'s own P1
already established and did not change either.

### Design decision — reconciling with `ADR-0003` (F-04/F-08 resolution, not deferred to a later ADR)

`ai/state/decisions-log.jsonl:22` (finding F-08 of the P0 architect-findings entry, `p0-role-affinity-reverted`
/`p0-architect-findings-outside-package-record`) named the precedent objection this contract must answer, now
more pressing than in round 1 because the widened scope explicitly covers writer roles `[areas.implement]`
already partially governs: *does a duty-keyed role partition compete with `models.toml`'s `[areas.<duty>]`
table (governed by Accepted `ADR-0003`) as a second, hand-maintained source of truth?*

**Answer: coexistence at two genuinely different, non-overlapping points of the pipeline — not a second
source of truth in the sense F-08 warned about, for three concrete reasons, not an assertion:**

1. **Narrower surface, by construction.** This contract's role-class bias only ever reorders the six curated
   `routes.v1.toml` candidates that already survived every hard exclusion in `RoutingService.route()`, and
   only for decisions that flow through `--route-decide`. It never assigns a model to an area, never creates
   or removes a candidate, and is a complete no-op for any role this contract does not cover or any decision
   made outside the routed dispatch. `[areas.<duty>]` remains the ONLY mechanism that assigns a default model
   to an area — this contract never writes, reads as authoritative, or duplicates that assignment.
2. **Keyed by the same signal, not an independently hand-maintained table.** P0's real defect (the objection
   F-08 raised) was a hand-written, per-role provider table disconnected from any existing structure. This
   contract's classes are not that: `grunt` is, by definition, the exact predicate `RoutingService._role_class`
   already computes as `"review"` (`service.py:222`); the new `build` class is, by definition, the exact
   predicate the same function already computes as `"writer"` (`service.py:221`); `decision` and `unscoped`
   are the two ways of splitting what that same function already buckets as `"other"` (`orchestrator` +
   `duty="docs"` vs. everything else not otherwise classed). Every one of this contract's four classes is
   derived from `roles.tsv`'s own `capability`/`duty` columns — the same axis `ADR-0003`'s own `[areas.<duty>]`
   table is keyed by — never an independent taxonomy invented for this feature.
3. **A tie-break, never an assignment, never consulted before the hard-exclusion loop.** P0's actual, panel-
   proven defect was that its preference was consulted *before*, and independently of, whether the preferred
   option was live — letting a stale preference exit the dynamic system entirely (`decisions-log.jsonl:23`,
   finding 1). This contract's bias is a sort-key element evaluated strictly *after* every hard exclusion
   (AC-04); it can only choose among candidates that already exist and are already authorized to be selected.

This reconciliation is written directly into the spec, as this repo's own precedent for a design decision that
does not yet need a dedicated ADR file allows (see AC-09): `012-discovered-inventory`'s own accepted contract
wrote its design reconciliation in-file and required its ADR (`docs/adr/0016-discovered-inventory.md`) as an
acceptance criterion of the package itself (AC-12), not as a pre-`USER_APPROVAL` document — the same pattern
`008-dynamic-selection`'s P1 AC-10 used for `docs/adr/0011-uninterrupted-delegation.md`. AC-09 below follows
the identical pattern for this contract.

### The precedent this contract must not repeat, read from the real record (not guessed)

`007-quota-visibility` briefly carried a package literally named **`P0-role-affinity`**, opened after the user
first asked for "sonnet building, gpt auditing." It was implemented as a **fixed provider preference by
role**, hand-written directly into `ai/catalogs/routes.v1.toml` as **twelve duplicated route rows** (one set of
six per role-group instead of the shared six). It was reverted the same day it was reviewed. The full record
survives in three places, all read directly this session: `ai/state/decisions-log.jsonl:23` (slug
`p0-role-affinity-reverted`), its narrative twin `docs/notas/decisiones/2026-07-28
p0-role-affinity-reverted.md`, and `docs/specs/007-quota-visibility/spec.md:100-111` (the in-file retraction,
including index row `A-01` at `:314`: *"P0 `role-affinity` is a package of this feature (AC-20/21/22) —
Reverted the same day for contradicting the reformulated goal; the scope moved to feature 008."*).

**What the review panel actually found — two real defects, not one vague "fixed preference is bad":**

1. **High — the fixed preference could route a decision straight out of the dynamic system.** On the primary
   OpenCode lane, an `anthropic`-preferred decision that had no live OpenCode-authenticated Anthropic route
   available **fell back to a static agent, discarding the tiered/dynamic selection entirely** for that
   decision. The fixed preference was consulted *before* — and independently of — whether the preferred
   option was actually live, so a stale or momentarily-unauthenticated preference didn't just pick a worse
   *tier*, it exited the dynamic mechanism altogether.
2. **High — nothing enforced the two role-groups were disjoint.** `ai/state/decisions-log.jsonl:22` (finding
   F-07, from the architect's independent review, folded into the same P0 record after a separate harness
   defect blocked it from entering the panel's own record — see `p0-architect-findings-outside-package-record`
   in the same log): a role duplicated in both the "writer" and "auditor" preference groups tied on
   `curated_priority=10` against itself, and the tie was silently broken by a hash of `route_id` — an
   unaudited, non-deterministic-looking resolution nobody had designed for.

**The full architect record from the same log entry, all five findings, engaged explicitly (F-05 resolution —
round 1 only engaged F-07):**

- **F-07 (high)** — the disjointness gap above. Directly mitigated by AC-01's own enumeration test.
- **F-08 (medium)** — the second-source-of-truth objection. Answered above, in `### Design decision`.
- **F-09 (medium)** — `brainstormer` is generative, not evaluative, but P0's hand-made grouping put it in the
  audit/grunt bucket for being merely read-only. **Already correctly resolved by this contract's own design,
  cited here as a real strength, not a new fix**: `brainstormer` (`roles.tsv:3`, `capability=review-ro`,
  `duty=analysis`) fails AC-01's `grunt` predicate (`duty IN {"audit","judge"}` — `analysis` is neither) and
  is `unscoped`, exactly as it should be.
- **F-10 (medium)** — the audit-group priority inversion was inert for all six review roles, because
  `REVIEW_PROVIDER_CONFLICT` decides the provider before `curated_priority` is ever read. This is the same
  shape as round 1's own F-01/F-10 finding about `grunt`-class inertness today — resolved explicitly below (the
  user chose to keep `grunt` anyway, and the inertness is now a stated, tested fact, not a silent gap).
- **F-11 (low)** — without post-dispatch failover, exhausting a provider's quota mid-spawn is a terminal
  failure, and concentrating "decision-making" work onto one premium provider raises exposure to it. Accepted
  explicitly below (Non-goals) — the same risk exists today without this feature, only made somewhat more
  likely, not created.

**The user's own reformulation, read directly from the decision record (not paraphrased into a convenient
narrative):** *"que el orquestador elija el modelo y el effort entre TODO lo disponible en el harness donde
corre, siendo crítico sobre responsabilidad, tokens y tiempo restante de sesión."* A fixed role→provider table
is the literal opposite of that: it removes from the selector exactly the decision the user wants it to keep
making. Two-thirds of what P0 promised were already true without it — `models.toml`'s `[areas.implement]
claude="sonnet"` / `[areas.audit] claude="opus"` (`/home/federico/SET-AGENTES/models.toml:81,93`, unchanged
since) already governed the Claude Code lane, and `REVIEW_PROVIDER_CONFLICT` (`service.py:166`) already forced
a reviewer onto a different provider than the writer's.

**Why this contract's design is not the same shape, stated precisely, not just asserted:**

- P0 wrote its preference **into `routes.v1.toml` itself**, duplicating rows and, by construction, changing
  *which candidates exist* and *which roles they serve* — a change to route **eligibility**. This contract
  (AC-04) never edits `routes.v1.toml`'s `roles`/`tools`/`tier` membership and never adds or removes a
  candidate; it only ever reorders **already-eligible, already-authenticated** candidates that survived every
  one of `RoutingService.route()`'s existing hard exclusions (`service.py:136-169` — identity, exhaustion,
  authentication, role compatibility, tools, context, and all three review-independence checks). A preference
  that happens to name a currently-unauthenticated provider can never cause a fallback out of the dynamic
  system, because an unauthenticated provider produces no candidate at all — the exact failure mode of P0's
  finding 1 is structurally unreachable here, not merely avoided by discipline.
- P0's two preference groups were hand-maintained, parallel, and never checked for disjointness against each
  other or against the roster. This contract's three role-classes (AC-01) are a closed, exhaustive partition
  over `roles.tsv`'s own existing `capability`/`duty` columns, and AC-01 requires a regression test that
  enumerates the full 28-role roster and asserts every role maps to exactly one of `{decision, grunt, build,
  unscoped}` — a direct, named mitigation of P0's finding 2, not a hope that it will not recur.
- P0's preference table, being routes, participated in `curated_priority` — a route-level field with no
  concept of "the human asked for this bias, on purpose, right now." This contract's weight is a **new,
  separate, explicitly-configured** input, inserted into the *existing* sort key at a fixed, narrow position
  (AC-04) — never a second parallel decision path the orchestrator or the routing service could disagree with
  each other about.

### What already exists, read from the real code and data this session (not inherited)

**`roles.tsv`'s `capability`/`duty` columns already partition the 28-role roster** (`roles.tsv:2-29`,
confirmed by direct count) along an axis close to, but not identical to, what the user described. Verified
live: `capability="review-ro" AND duty IN {"audit","judge"}` selects exactly six roles — `spec-challenger`,
`package-reviewer`, `delta-reviewer`, `security-auditor`, `finding-verifier`, `adversarial-judge`
(`roles.tsv:9,20-24`) — and this is **not a new observation this contract invents**: it is the *exact*
predicate `RoutingService._role_class` (`ai/scripts/routing_core/service.py:218-223`) already computes,
today, for an unrelated purpose (deciding which decisions may carry a `review_of_run_id` and be checked for
writer-independence) — and the identical predicate is duplicated verbatim as `_role_class_of`
(`ai/scripts/set_agents_app.py:230-233`), a pre-existing, small, un-shared duplication this contract notes but
does not fix (out of scope; named so a future reader does not wonder whether it was missed).
`capability="code-rw"` (the same function's `"writer"` branch) selects exactly seven roles — `test-writer`,
`implementer`, `frontend-engineer`, `refactor-specialist`, `debugger`, `repair-agent`, `integrator`
(`roles.tsv:11-17`) — this contract's new `build` class (see the scope-widening section above). No equivalent
existing code concept selects "judgment-call" roles the way the user described `orchestrator`+`architect`:
`capability="coord-ro"` selects exactly one role (`orchestrator`, `roles.tsv:2`); `duty="docs"` selects six
roles (`product-analyst`, `project-bootstrapper`, `architect`, `agent-factory`, `ux-ui-designer`,
`package-planner`, `roles.tsv:4-8,10`, of which `architect` is the user's own second named example) but
nothing in the existing code currently treats `coord`+`docs` as one combined class — AC-01 states this
generalization explicitly as a product decision, not a rediscovered existing rule.

**Today's tie-break is already a single, static, GLOBAL number — uniform across every role, not
role-class-scoped at all.** `ai/catalogs/routes.v1.toml` has exactly six rows (confirmed:
`grep -c '^\[\[routes\]\]'` → 6), `provider ∈ {"openai-codex","anthropic"}` only (confirmed:
`grep '^provider = '` → both values, no third). Every `openai-codex` row carries `curated_priority = 10`;
every `anthropic` row carries `curated_priority = 20` (`routes.v1.toml:14,24,34,44,54,64`, all six checked
directly). Because `candidates.sort(...)` (`service.py:171`) orders ascending by `curated_priority` as its
third key, **`openai-codex` (GPT) already wins every tie today, for every role, at every tier, whenever both
providers are simultaneously authenticated** — this is not a hypothetical this contract introduces; it is the
literal, already-shipped behavior, uniform across `orchestrator`, `adversarial-judge`, and `implementer` alike.
The user's "GPT 5.6 Sol for orchestrator right now" is therefore *already* the default outcome for
`orchestrator` specifically today (`gpt-5.6-sol` is the `balanced`-tier `openai-codex` row,
`routes.v1.toml:26-34`) — but so is GPT for every other role, including the ones the user wants biased toward
the cheap/disposable option, or toward whichever provider actually implements. **This is the concrete gap this
contract closes: a role-class-scoped bias, replacing one undifferentiated global number.**

**The live per-decision credential check the new bias must reuse, not duplicate.** `RoutingService.route()`
excludes a candidate with `reason="PROVIDER_UNAUTHENTICATED"` (`service.py:145`) whenever `route.model` is
absent from `self.inventory.get((facts.selected_runtime, route.provider), frozenset())` — `self.inventory` is
built, on every `RoutingService` construction, from `probe_inventory(config, ...)`
(`routing_core/catalog.py:426`), which only ever probes the closed `(runtime, provider)` pairs in
`_PAIR_COMMANDS` (`catalog.py:133-140`): `("codex","openai-codex")`, `("claude-code","anthropic")`, four
`("opencode", <provider>)` pairs (`openai-codex`, `anthropic`, `opencode-zen`, `opencode-go`), and two `("pi",
<provider>)` pairs. **This means "is a given provider currently authenticated" is already computed, live, on
every routing decision, for exactly these four providers** — a stale user-declared preference naming a
provider that has since lost its credentials produces zero eligible candidates for that provider and is
therefore automatically inert, with no separate "detect the subscription changed" step required. This is the
concrete mechanism (AC-03) that satisfies the user's own explicit choice this session — automatic credential
detection, not a manual edit and not a scheduled date — for the four providers already known to the router.

**Standalone "Kimi Code" is not one of those four providers, verified live, not assumed.** Read this session,
read-only, keys only, never values (same discipline as `pi_auth_provider_keys()`, `catalog.py:243-258`):
`~/.pi/agent/auth.json`'s key set is exactly `{"anthropic","openai-codex"}`. `opencode auth list --pure`
reports exactly four credentials on this machine: `OpenCode Go`, `OpenAI`, `GitHub Copilot`, `OpenCode Zen` —
no standalone `Kimi` entry. `/home/federico/SET-AGENTES/models.toml`'s `[catalog].opencode_zen` and
`[catalog].opencode_go` allowlists (`models.toml:26-27`) both already list `kimi-k2.5`, `kimi-k2.6`,
`kimi-k2.7-code`, `kimi-k3` — but strictly as model ids reachable *through* the `opencode-zen`/`opencode-go`
subscriptions, which already have their own probe pairs and their own billing-kind entries
(`PROVIDER_BILLING_KIND = {"opencode-zen": "metered", "opencode-go": "subscription"}`, `catalog.py:148`).
(Note, so nobody confuses the two: `tests/fixtures/models.toml` is an unrelated test fixture with its own
independent, smaller content — every citation in this contract to `models.toml` bare or with a line number
means the real file at `/home/federico/SET-AGENTES/models.toml`, never the fixture. **Same disambiguation
applies to `roles.tsv` — round 3, R3-F-08(a):** `tests/fixtures/roles.tsv` is a separate, smaller decoy fixture
(confirmed live, `find . -iname roles.tsv` returns both); every citation in this contract to `roles.tsv` bare
or with a line number means the real file at `/home/federico/SET-AGENTES/roles.tsv`, never the fixture.) **What could not be
verified, stated plainly: whether the user's actual $40/month "Kimi Code" product is (a) a standalone
credential surface this repo has never seen — in which case it needs a brand-new provider onboarding (new
`_PAIR_COMMANDS` pair, new probe-response parser, new billing-kind entry, new `routes.v1.toml` rows — the same
shape of work `012-discovered-inventory`'s AC-01/AC-02 did for `opencode-zen`/`opencode-go`), a real, named,
external dependency this contract does **not** deliver — or (b) informally the user's name for the Kimi models
already reachable through `opencode-go`'s existing, already-probed subscription. No trace of (a) exists on
this machine today; this draft does not guess between the two and names the ambiguity for `USER_APPROVAL`
rather than fabricating a detection mechanism for a credential surface that may not exist.** Either way, a
second, independent, deeper blocker applies regardless of which reading is correct — see the next paragraph.

**A structurally deeper blocker than credentials: Kimi-hosted models are not routable at all today, regardless
of any credential question.** `012-discovered-inventory`'s own accepted contract states this as an explicit
non-goal, read directly this session: *"No curated `routes.v1.toml` rows for the new models — this contract
makes them probeable, not routable; a route row still needs a human to pick its roles/tools/tier/priority/
family"* (`docs/specs/012-discovered-inventory/spec.md:432-435`). `routes.v1.toml` has exactly six rows, none
with `provider ∈ {"opencode-zen","opencode-go"}` (verified above). `RoutingService.route()`'s candidate list is
built by iterating `self.snapshot.routes` (`service.py:136`), itself built from that same file
(`build_snapshot(catalog_path, roster, config)`, `catalog.py:503`) — **a provider absent from `routes.v1.toml`
can never produce a candidate, and therefore can never be reordered by anything this contract adds, no matter
how the preference or the credential check resolve.** This contract's "grunt-work bias toward the cheap/
disposable option" and "build-work bias toward the currently-implementing option" are therefore, as specified,
**inert for every Kimi-hosted model on this machine today** — stated here as a real, load-bearing limitation
(see Non-goals), not discovered later as a surprise.

### Honest scope — which of the three classes have real, live effect today, verified directly against
`models.toml`, per-lane and per-class (round 3 correction — R3-F-01, blocking; supersedes round 2's own
"2 real roles" claim, which did not verify the primary lane's actual credential shape)

Round 2 (9 findings, `revision_required`) found something round 1 never checked: this contract's role-class
bias only ever fires for a role whose candidate selection is **dynamically tiered** — i.e. a role that has its
own `[roles.<role>.tiers.fast/balanced/frontier]` tables in `models.toml`, the structure
`models_config.load_role_tiers` reads to build the per-tier `RoutingService` candidate set at all. A role
without those tables never reaches a state where this contract's sort-key element has anything to reorder,
regardless of which of AC-01's four classes it is placed in. **Re-verified directly this round, not carried
over from round 2's summary:** `grep -n '^\[roles\.' models.toml` shows exactly six roles carry
`.tiers.<tier>` tables — `debugger` (`models.toml:151,154,157`), `delta-reviewer` (`:160,163,166`),
`finding-verifier` (`:169,172,175`), `implementer` (`:184,187,190`), `package-reviewer` (`:199,202,205`),
`security-auditor` (`:226,229,232`). No other role in the 28-role roster has a `.tiers.*` table. These six,
and only these six, are "tiered" in the sense this contract's mechanism requires.

**Precision on WHY only these six roles ever reach `RoutingService.route()`'s sort key at all — an operational
doctrine gate, not a structural code-level exclusion, verified directly rather than assumed.** It is tempting
to assume `routes.v1.toml`'s per-route `roles` field is what limits candidate production to these six — it is
not: every one of the six curated routes lists all 28 roles in its `roles` array (`ai/catalogs/routes.v1.toml`,
all six `roles = [...]` lines checked directly), so `RoutingService.route()` would happily produce candidates
for any of the 28 roles if it were ever invoked for them. **The real gate is the shipped orchestrator doctrine
itself, byte-identical across all three generated copies**
(`Global/_canonical/agents/orchestrator.md:157-158`, verbatim: *"`implementer`, `debugger`, `package-reviewer`,
`delta-reviewer`, `security-auditor`, and `finding-verifier` are **tiered roles**: before spawning one of them,
follow the decide→spawn protocol below"*): the orchestrator's own spawn protocol only ever invokes
`--route-decide` for these six named roles; for every other role, it spawns the BASE static agent directly,
without calling `--route-decide` at all. This is consistent with, and independently corroborates,
`models.toml`'s `.tiers.*` table roster (the same six roles) — the doctrine names them as "tiered roles" in
prose, `models.toml` backs that same set with real per-tier OpenCode variant data (`load_role_tiers`,
`models_config.py:308-366`, which builds the multiple `<role>@<tier>` OpenCode variant files the doctrine's
"Match by MODEL" step spawns). Both signals agree; neither is guessed from the other's name.

Crossed against AC-01's three in-scope classes, role by role:

- **`decision` (7 roles: `orchestrator`, `product-analyst`, `project-bootstrapper`, `architect`,
  `agent-factory`, `ux-ui-designer`, `package-planner`) — ZERO of the six tiered roles are members.** This is
  not "reduced effect" — it is **no reachable effect at all, full stop.** The orchestrator's own doctrine never
  invokes `--route-decide` for any of these seven roles (they are not named in the "tiered roles" sentence
  above); every one of them is spawned as the BASE static agent directly, governed exclusively by the static
  `[areas.<duty>]`/`[roles.<role>]` resolution
  (`models_config.resolve_role`) baked at generation time, exactly as it is today, with or without this
  contract. A configured `decision`-class preference is legal to write (AC-02) and produces byte-identical
  observable behavior to no preference at all, on every one of these seven roles, unconditionally — not
  "usually," not "on today's catalog," unconditionally, because the mechanism these seven roles use has no
  concept of a per-decision sort at all.
- **`grunt` (6 roles: `spec-challenger`, `package-reviewer`, `delta-reviewer`, `security-auditor`,
  `finding-verifier`, `adversarial-judge`) — 4 of 6 are tiered (`package-reviewer`, `delta-reviewer`,
  `security-auditor`, `finding-verifier`); 2 of 6 are not (`spec-challenger`, `adversarial-judge`, which
  behave exactly like `decision`-class roles above — no reachable effect, full stop, for a second,
  independent reason).** For the 4 that ARE tiered, **corrected this round (R3-F-01/R3-F-03) from "one
  provider survives, nothing to reorder" to the actual mechanism on the real, live primary-lane credential
  shape:** on `opencode` (`[runtime].primary`), `PROVIDER_UNAUTHENTICATED` (`service.py:145`) excludes every
  `anthropic` candidate first (`('opencode','anthropic')` probes to zero models, verified live this round —
  see the corrected header claim above), and `REVIEW_PROVIDER_CONFLICT` (`service.py:166`) separately excludes
  every `openai-codex` candidate that shares the writer's provider — leaving **ZERO** survivors, not one, and
  the decision returns `REVIEWER_INDEPENDENCE_UNAVAILABLE`, a hard refusal (shipped doctrine's own
  `Global/_canonical/agents/orchestrator.md:199-205` HARD DENIAL branch: HALT, raise `HUMAN_DECISION_REQUIRED`
  — see Non-goals for the corrected framing). There is nothing to reorder because there is nothing left to
  sort, a stronger and different claim than "one survivor already decided the outcome." **This still makes
  the AC-01 byte-identical-`RouteDecision` regression test true** (a configured `grunt`-class preference
  cannot change a decision with zero candidates either way) — but the test's own assertion must check the
  actual `reason_codes` (`("REVIEWER_INDEPENDENCE_UNAVAILABLE",)`), not merely `RouteDecision` equality, so a
  future reader sees the moment this shape changes (once this lane gains a real Anthropic credential, the
  shape becomes the ORIGINAL "one survivor, tiered-but-inert" case round 1/2 described; once `015` ships and
  redirects the effective runtime for `anthropic` candidates, the shape changes again — see `### Dependency on
  015` below). **`spec-challenger`/`adversarial-judge`** are *not tiered at all* (doctrine never invokes
  `--route-decide` for them), unchanged from round 2's finding.
- **`build` (7 roles: `test-writer`, `implementer`, `frontend-engineer`, `refactor-specialist`, `debugger`,
  `repair-agent`, `integrator`) — 2 of 7 are tiered and doctrine-invoked (`implementer`, `debugger`); 5 of 7
  are not tiered at all (`test-writer`, `frontend-engineer`, `refactor-specialist`, `repair-agent`,
  `integrator`, governed solely by `[areas.implement]`'s static default, no reachable effect from this
  contract).** **Corrected this round (R3-F-01, the round's headline blocking finding):** round 2 claimed
  `implementer`/`debugger` were "the entire honest, real, live scope of this contract as it now ships" — this
  is **wrong on the primary lane, verified live, not assumed.** `implementer`/`debugger` are writer-class
  decisions (`role_class == "writer"`), so `REVIEW_PROVIDER_CONFLICT` never applies to them — but
  `PROVIDER_UNAUTHENTICATED` still excludes all three `anthropic` tier rows on `opencode` today, leaving
  exactly **ONE** surviving candidate (`openai-codex`) at every tier. A sort key with exactly one candidate to
  sort has nothing to reorder: `candidates[0]` is fixed regardless of any configured `build`-class preference.
  **`implementer` and `debugger` therefore have ZERO observable effect from this contract on the primary lane
  today too — the same bottom line as every other role in the roster, for a narrower, code-level reason
  (single-survivor, not doctrine non-invocation) rather than the wide-reaching, honest exception round 2
  believed they were.** A regression test that asserts this must inject an inventory shaped like this
  machine's real live probe (no `("opencode","anthropic")` key), not a more generous test fixture — the same
  faithfulness requirement `015`'s own AC-01 states explicitly for its own tests, adopted here for the same
  reason (see Verificación).

**R2-F-03's predicate fix, verified, does not change this membership.** Round 2 found `AC-01`'s `build`
predicate (`duty == "implement" AND capability == "code-rw"`) was not provably identical to the code it
claimed to reuse — the real predicate, `RoutingService._role_class` (`service.py:221`), is the single-conjunct
`capability == "code-rw"` alone, with no `duty` conjunct (verified directly, `service.py:218-223`, reproduced
in `### The architectural question` above). Re-checked against `roles.tsv:11-17` directly: every one of the
seven `capability == "code-rw"` rows also carries `duty == "implement"` — there is no row with `code-rw` and a
different duty, and no row with `duty == "implement"` and a different capability. **The two predicates select
the exact same seven roles on the current roster; membership is unchanged, only the predicate's stated
definition is corrected** to the literal, single-conjunct form `capability == "code-rw"`, matching `grunt`'s
already-correct pattern of reusing `_role_class`'s output literally rather than reconstructing an equivalent
compound condition. AC-01 below is corrected accordingly.

**The `[areas.implement]` question, resolved precisely, not assumed (round 2's open question on R2-F-05).**
For the two real tiered `build` roles, does `[areas.implement]`'s static default (`models.toml:80-84`,
`claude = "sonnet"`) play any role once a decision is fully routed through `--route-decide`? **Read directly
from the shipped doctrine, byte-identical across all three generated copies
(`Global/claude-code/agents/orchestrator.md:199-201`, `Global/opencode/agents/orchestrator.md`, and
`Global/codex/agents/orchestrator.toml:192-194`, none touched by this contract): yes, but only on one specific,
named path — the "off-lane model" legitimate-degrade branch.** When a routed decision comes back
`ok=true, execution_enabled=true` but `data.provider != "openai-codex"` (i.e. the decision named `anthropic`),
the doctrine closes that run as abandoned and spawns the **BASE static agent** instead — and the BASE agent's
baked-in model is exactly `[areas.implement]`'s static default (`resolve_role`, consumed by `generate.py`'s
`load_roles` at generation time). **On a decision that stays on-lane (`provider == "openai-codex"`),
`[areas.implement]` plays no role whatsoever** — the spawned variant is matched by the routed decision's own
`model:` line, verbatim, never falling back to the static default. So: for `implementer`/`debugger`, this
contract's `build`-class bias and `[areas.implement]`'s static default are **not two competing sources of
truth for the same decision** — they govern two disjoint outcomes of the SAME routed decision (on-lane spawn
vs. off-lane degrade), never both at once, and neither is silently overridden by the other. There is no
composition/precedence question left to resolve for this pair; R2-F-05 is closed by this precise reading, not
by further design.

**The one real, live exception today — the `pi` lane, verified this round, and precisely scoped so it is not
mistaken for the contract's main claim.** `_PAIR_COMMANDS` (`catalog.py:133-140`) audits `("pi","anthropic")`
and `("pi","openai-codex")` as two separate, independent pairs from the `opencode` ones. Live-probed this
session (`pnpm dlx --package @earendil-works/pi-coding-agent@0.81.1 pi --list-models`, the exact probe
`_PAIR_COMMANDS` runs): **both pairs return real, populated model lists** — 15 `anthropic` models (`claude-*`)
and 6 `openai-codex` models (`gpt-5.*`) — confirming `~/.pi/agent/auth.json`'s `anthropic`/`openai-codex` keys
(both OAuth-shaped: `type`/`refresh`/`access`/`expires`) are live-authenticated credentials, not stale ones.
**This means a `RoutingService.route()` call made with `facts.selected_runtime == "pi"` genuinely has BOTH
providers' candidates surviving `PROVIDER_UNAUTHENTICATED` today** — a `grunt`-class preference on the pi lane
would face `REVIEW_PROVIDER_CONFLICT`'s single-survivor exclusion exactly as round 1/2 originally described
(one survivor, tiered-but-inert, not zero), and a `build`-class preference on the pi lane would have TWO
surviving candidates with something real to reorder. **Stated precisely, not overclaimed: this is a real
exception to "zero effect everywhere today," but it is not this contract's main claim** — `pi` is not
`[runtime].primary` (`models.toml:36`, still `opencode`), and the pi-lane's own end-to-end delegation doctrine
(`013-pi-interactive-target`) was still `PACKAGE_PLANNING`, not shipped, as of this session — so whether any
current, real delegation flow actually issues a `--route-decide` call with `selected_runtime="pi"` for a
`grunt`/`build`-class role today is a separate, not-fully-verified operational question this contract does not
resolve. The mechanism-level fact (the probe pairs are live) is confirmed; the doctrine-level fact (whether
that lane's real delegation path reaches this contract's sort key today) is not, and is named here as an open
question rather than assumed either way.

**Why this doesn't make the contract pointless, stated plainly.** The mechanism is correct, uniform, and fully
specified for all three classes (proven by the mechanism-correctness tests in Verificación, which inject a
synthetic inventory rather than depend on any lane's live credential state) — it simply has **zero observable
effect on the primary `opencode` lane today, for every class, full stop**, corrected from round 2's belief that
`implementer`/`debugger` were a working exception. `decision` in full, `grunt` in full, and `build` in full are
kept in the taxonomy anyway — never removed — for exactly the reason round 1 already established: no role
should be pinned to a hardcoded model by construction, ready with zero further code change the moment more
roles become tiered, the primary lane gains a real Anthropic credential, or (see `### Dependency on 015`
immediately below) `015` ships its cross-lane redirect. Their current, observable, real-world effect on the
primary lane is stated here as **zero, for all 20 in-scope roles, no exceptions**, with a regression test
proving it — not a silent gap, an audited fact.

### Dependency on `015` — precisely, with real AC numbers, not a vague forward-pointer (round 3, resolves the
open question round 3's challenge raised: does `014` target the lane `015` is designing toward, ship gated on
an external prerequisite, or wait for `015`?)

**Answer: `014` ships as specified now — its mechanism is complete and correct — and its real-world effect on
the primary lane is contingent on `015`, an external prerequisite `014` does not deliver and does not need to
wait for**, because `014` never edits routing/doctrine and needs zero code change once `015` lands. `015` was
completely redesigned in parallel this session (now its own contract **2.0.0**, pre-challenge as of this
citation, `docs/specs/015-anthropic-dispatch-parity/spec.md`) around a cross-lane provider redirect: **AC-01**
("Provider-aware effective-runtime resolution") makes `RoutingService.route()` resolve a route's
authentication against an **effective runtime** — `facts.selected_runtime` for `openai-codex` (unchanged), or
`claude-code` for `anthropic` (the one redirect `015` configures) — "for both writer and review decisions"
(`015/spec.md` AC-01, verbatim). **AC-04** ("Review-independence gap closed via the redirect") adds an explicit
orchestrator-doctrine branch so the everyday verified-review shape spawns via the redirect instead of hitting
`REVIEWER_INDEPENDENCE_UNAVAILABLE`, while `015`'s own AC-04 second regression test explicitly preserves the
`REVIEWER_INDEPENDENCE_UNAVAILABLE` HALT when no redirect exists anywhere (ADR-0011 D4 untouched).

**Concretely, for `014`, once `015` ships (both, per `015`'s own AC-01 wording, "for both writer and review
decisions"):**
- `014`'s **`build` class** (`implementer`, `debugger`, its only 2 tiered roles) gains real effect: `anthropic`
  candidates stop being excluded by `PROVIDER_UNAUTHENTICATED` on the primary lane (the effective runtime
  becomes `claude-code`, which is already live-authenticated, `015` §C), restoring the second candidate this
  contract's sort key needs to have anything to reorder.
- `014`'s **`grunt` class** (its 4 tiered roles: `delta-reviewer`, `finding-verifier`, `package-reviewer`,
  `security-auditor`) *also* gains real effect — not just `build`, correcting round 2's belief that only
  `build` would benefit. Once the redirect resolves an `anthropic` reviewer candidate against `claude-code`'s
  live credential, it survives `PROVIDER_UNAUTHENTICATED` and — being a different provider than an
  `openai-codex` writer — survives `REVIEW_PROVIDER_CONFLICT` too, so a real, non-empty candidate set (not a
  `REVIEWER_INDEPENDENCE_UNAVAILABLE` refusal) reaches this contract's sort-key element for the first time on
  the primary lane.
- `014`'s **`decision` class** (0 tiered roles) **stays permanently inert under both scenarios, worth stating
  plainly since it is the one class `015` can never help**: the reason `decision`'s seven roles have no
  reachable effect is not a credential/exclusion problem `015` fixes — it is that the shipped orchestrator
  doctrine never invokes `--route-decide` for any of them at all (see the `decision` bullet above). `015`'s
  redirect only ever changes which candidates a `--route-decide` call produces; it has no effect on whether
  `--route-decide` is invoked in the first place.

**No code change to `014` is required for either of the above** — this contract's own sort-key element
(AC-04) already reorders whatever candidates the exclusion loop leaves standing; `015`'s change happens
entirely upstream of it, inside the exclusion loop itself. This dependency is named here as the accurate
answer to round 3's open question, not resolved by shipping `014` gated on `015`, nor by waiting for `015` to
land first: `014`'s own spec, taxonomy, config surface, and mechanism are complete and correct today,
independent of `015`'s timeline.

## Alcance

In scope: a configurable, role-class-scoped tie-break weight, consulted at one precise point inside the
already-accepted dynamic selector (`RoutingService.route()`), plus the configuration surface, its CLI writer,
and the role-class taxonomy that feed it. **Corrected this round (R3-F-01, blocking) — stated once here,
prominently, and never contradicted below: on the primary `opencode` lane, today, this mechanism has ZERO
observable, live effect for ALL 20 in-scope roles, across all three classes alike, no exceptions —
`implementer`/`debugger` included.** `('opencode','anthropic')` probes to zero models on this machine, so
`PROVIDER_UNAUTHENTICATED` excludes every `anthropic` candidate on this lane; `build`'s two tiered roles are
left with exactly one surviving candidate (nothing to reorder) and `grunt`'s four tiered roles are left with
zero surviving candidates (`REVIEWER_INDEPENDENCE_UNAVAILABLE`, a hard refusal). This is a real, verified,
observable-effect claim about the primary lane today — not a hypothetical — and it is `015`'s prerequisite gap
(cross-lane Anthropic dispatch), not a defect of this contract's own design; see `### Dependency on 015`
(Contexto) for exactly how, and for which classes, that changes once `015` ships, with zero code change to
`014`. The one real exception is the `pi` lane (not `[runtime].primary`), where both `anthropic` and
`openai-codex` probe live today — named precisely, not as this contract's main claim, in `### Honest scope`.
Every in-scope role is legal to configure (AC-02) and the taxonomy is kept in full regardless, for the same
"no role hardcoded by construction" reason round 1 established — but its real, current, observable effect on
the primary lane is zero, proven by regression test, not merely asserted. See `### Honest scope` in Contexto
for the full, verified, per-lane breakdown.

- A closed, three-class, disjoint role taxonomy (`decision`, `grunt`, `build`) over `roles.tsv`'s existing
  `capability`/`duty` columns, with every other role explicitly `unscoped` (AC-01) — kept in full even though
  most of it is currently inert, for the same "no role hardcoded by construction" reason round 1 established.
- A single, real, per-harness-install configuration surface declaring, per role-class, an ordered provider
  preference list, plus a per-role override to move a specific role between classes, written through a new,
  dedicated CLI subcommand rather than a hand-edited file (AC-02).
- Reuse (not reinvention) of the existing live per-decision credential/authentication check for the four
  already-known providers; an explicit, named dependency — not delivered here — for onboarding a standalone
  "Kimi Code" provider if that turns out to be a real, separate credential surface (AC-03).
- The exact integration point inside `RoutingService.route()`'s candidate sort key, shared by all three
  in-scope classes, and the invariants that keep it from becoming a second, competing decision-maker (AC-04).
- The role→class resolution function and its override precedence (AC-05).
- Explicit non-goals restated as testable negative assertions (AC-06).
- The named, largely-moot-given-honest-scope composition point with `008-dynamic-selection`'s P3 sketch (AC-07).
- Observability of the resolved role-class and applied preference on the decision output itself, under a field
  name that does not collide with the existing, differently-valued `role_class` envelope key (AC-08).
- The ADR that records this design, required as a delivery criterion of the package, not before
  `USER_APPROVAL` (AC-09).

**Explicitly out of scope, stated once here and restated in Non-goals:** fixing the pre-existing, system-wide
gap that currently discards any routed decision naming `anthropic` in all three lanes (separate feature `015`);
widening which roles are dynamically tiered (a static-roster fact this contract observes, never edits); and the
future "gateway" model idea (see `## Future work`).

## Non-goals (explicit, so a later package does not assume them included)

- **No change to `008-dynamic-selection`'s P1 accepted doctrine** (`AC-01..AC-10`, `ai/state/features/
  008-dynamic-selection.json`) or to the text generated from it into any of the three runtimes. This contract
  neither edits `docs/specs/008-dynamic-selection/spec.md` nor reopens any of P1's accepted acceptance
  criteria.
- **No change to `[areas.<duty>]`'s static, install-time-baked default model resolution**
  (`models_config.py`'s `resolve_role`, governed by `ADR-0003`). This contract's bias only ever reaches a
  decision that flows through `--route-decide`'s dynamic dispatch; the static default consumed for untiered/ad
  hoc delegation and session-start resolution (`codex_orchestrator()`) is untouched, exactly as
  `008-dynamic-selection`'s own P1 already established for that seam. See `### The architectural question`
  above for the full reasoning.
- **No genuine per-project configuration layer.** `models.toml`/`roles.tsv` are `HARNESS_HOME`-owned per
  Accepted `docs/adr/0008-two-roots-portability.md` (`ROOT = Path(__file__).resolve().parents[2]` in
  `models_config.py` resolves to the harness install root, confirmed live, not a project root) — there is no
  real "per-project" layer to build on for model routing, and the user explicitly declined building one when
  this was raised. This contract's one real configuration layer is per-harness-install (AC-02); "per-user" and
  "per-harness-install" name the same physical location and trust domain in this repo (both are the
  operator's own `$HOME`, both already trusted per `ADR-0008`'s own table) and are used interchangeably below.
- **No dependency on `011-quota-failover`.** This contract's weight consults only the existing
  `PROVIDER_UNAUTHENTICATED` live-inventory exclusion (`service.py:145`); it never reads `provider_exhausted`
  (conditionally consulted at `service.py:143` only when `self.store is not None` — never on the
  simulate/explain lane — and backed by `011`'s `provider_exhaustions` table) and behaves identically whether
  `011` is ever accepted or stays `BLOCKED`.
- **No cost model, no daily-USD ceiling, no metered-vs-subscription comparison of any kind.** This contract
  carries no dollar figure and makes no `PROVIDER_BILLING_KIND` (`catalog.py:148`) comparison. That axis
  belongs to `008-dynamic-selection`'s P3 sketch; the relationship between the two is named, not resolved, in
  AC-07.
- **No new `routes.v1.toml` rows for `opencode-zen`/`opencode-go`.** Kimi-hosted models stay exactly as
  non-routable as `012-discovered-inventory` left them. This contract's `grunt`- and `build`-class bias has
  **no observable effect** on any Kimi-hosted model until a separate, later change gives `opencode-zen`/
  `opencode-go` real route rows — named here as a real limitation of this contract's own scope, not a defect
  discovered after shipping.
- **No new standalone "Kimi Code" provider onboarding** (new `_PAIR_COMMANDS` pair, probe parser, billing-kind
  entry). If the user's actual subscription turns out to need one, that is separate, prerequisite work, named
  as an external dependency in Contexto, not delivered by this contract.
- **No change to the session-window/context-budget problem** (the "5h window, ~2.5h usable" report). Explicitly
  out of scope per the user's own instruction this session; this contract's design is not influenced by it.
- **No quick-fix to the orchestrator's current default model shipped ahead of the rest of this contract.** The
  full system ships as one coherent contract, per the user's own explicit instruction this session.
- **The quota-exhaustion-exposure risk of concentrating "decision"-class work on one premium provider is
  accepted as-is, not mitigated here.** A `decision`-class bias toward a premium provider raises exposure to
  mid-spawn quota exhaustion, with `011-quota-failover` still `BLOCKED` and no automatic post-dispatch
  failover yet. The user accepted this explicitly this session: the risk already exists today, without this
  feature; this contract makes it somewhat more likely (decisions can now concentrate deliberately on one
  provider) but does not create a new failure mode. It closes automatically once `011` is ever accepted, with
  no action needed from this contract.
- **The `grunt` class's current live inertness on the two-provider catalog is accepted, kept, and proven, not
  removed.** See AC-01.
- **Absent configuration at every layer (no file, or the role is `unscoped`) produces byte-identical candidate
  ordering to today's** — the default behavior of `008-dynamic-selection`'s P1-accepted selector is unbiased
  and unchanged (AC-04, AC-06).
- **No widening of which roles are dynamically tiered.** `models.toml`'s `[roles.<role>.tiers.*]` tables
  (verified this round: exactly `debugger`, `delta-reviewer`, `finding-verifier`, `implementer`,
  `package-reviewer`, `security-auditor`, `models.toml:151-232`) are a pre-existing, static-roster fact this
  contract only ever reads, never edits, never adds to. This is the concrete, verified reason `decision`'s
  seven roles, `grunt`'s two non-tiered roles (`spec-challenger`, `adversarial-judge`), and `build`'s five
  non-tiered roles (`test-writer`, `frontend-engineer`, `refactor-specialist`, `repair-agent`, `integrator`)
  have zero observable effect from this contract today — not a defect of this contract's design, a fact about
  which roles the rest of the harness has chosen to route dynamically at all. Widening that roster is real,
  separate, prerequisite work this contract does not scope or deliver. See `### Honest scope` in Contexto.
- **No fix to the pre-existing, cross-lane gap that excludes every `anthropic` candidate on the primary
  `opencode` lane today — corrected this round (R3-F-02, blocking): this is a fail-CLOSED availability/liveness
  problem, not a fail-open security defeat, and `014` neither causes nor fixes it (`015`'s prerequisite, see
  `### Dependency on 015`, Contexto).** `014`'s own prior draft (contract 3.0.0) imported an "already silently
  defeated in practice, today... the common case, not an edge case" framing from `015`'s own round-1
  (contract 1.0.0) draft — round 3 found `015`'s own round-1 challenge already corrected this before `014`'s
  3.0.0 was written, and `014` had not picked up the correction. The real, verified behavior, read from `015`'s
  current spec (`docs/specs/015-anthropic-dispatch-parity/spec.md` §D.1, a live hermetic reproduction, not a
  hypothetical) and from the shipped doctrine's own text (`Global/_canonical/agents/orchestrator.md:199-205`,
  byte-identical across all three generated copies): on this machine, today, a routed review decision that
  would need `anthropic` for provider-diversity does **not** silently degrade to a same-provider reviewer — it
  hits **zero** surviving candidates (`PROVIDER_UNAUTHENTICATED` excludes the `anthropic` side,
  `REVIEW_PROVIDER_CONFLICT` excludes the `openai-codex` side) and returns `REVIEWER_INDEPENDENCE_UNAVAILABLE`,
  which the shipped doctrine's own fail-closed HARD DENIAL branch treats as a HALT requiring
  `HUMAN_DECISION_REQUIRED` (`Global/_canonical/agents/orchestrator.md:199-205`, explicit in its own text: "the
  routing brain actively REFUSING the request... do not spawn anything... Stop and raise
  `HUMAN_DECISION_REQUIRED`"). **This is a real availability problem — reviews cannot run at all when only one
  provider is available — not a silent bypass of the independence guarantee.** Two distinct, both pre-existing,
  neither caused nor fixed by `014`:
  1. **Writer-side (`build`-class relevant).** Read directly, byte-identical across all three generated copies
     of the shipped orchestrator doctrine (`Global/claude-code/agents/orchestrator.md:199-201`,
     `Global/opencode/agents/orchestrator.md`, `Global/codex/agents/orchestrator.toml:192-194` — none touched by
     this contract): whenever a routed decision comes back `ok=true, execution_enabled=true` with
     `data.provider != "openai-codex"`, the doctrine treats it as a legitimate "off-lane model" degrade, closes
     the run, and spawns the BASE static agent instead, for every lane alike. **On the primary lane today, this
     branch is structurally unreachable for `014`'s `build`-class roles anyway** — a routed decision can never
     name `anthropic` in the first place, because `PROVIDER_UNAUTHENTICATED` already excludes it from the
     candidate list before the sort key runs (see `### Honest scope`, Contexto).
  2. **Reviewer-side (`grunt`-class relevant) — a hard, fail-closed HALT, not a fail-open degrade, corrected
     this round from 3.0.0's wrong framing.** `015`'s own §D investigation (`docs/specs/015-anthropic-
     dispatch-parity/spec.md:156-176`, a live-executed hermetic reproduction against this machine's real
     credential shape, not a static trace) found the doctrine never reaches the ambiguous shape 1.0.0's
     original trace worried about (`ok=true`, `data.provider="anthropic"`, `execution_enabled=false`) — that
     shape assumed `('opencode','anthropic')` was authenticated, which it is not on this machine. The real
     shape is `REVIEWER_INDEPENDENCE_UNAVAILABLE`, a hard denial the doctrine's own HARD DENIAL branch (3c)
     halts on unconditionally. **This is directly the same mechanism this contract's own `grunt`-class
     inertness proof (AC-01) rests on** — `PROVIDER_UNAUTHENTICATED` and `REVIEW_PROVIDER_CONFLICT` together
     narrow the candidate list to **zero survivors** on the primary lane today (corrected from 3.0.0's "at most
     one survivor" — R3-F-03), before this contract's sort-key element is ever consulted, which is why a
     `grunt`-class preference has zero effect on `RouteDecision` regardless. Severe (it blocks every ordinary
     review's throughput today, requiring a human every time), but a fail-closed severity, not a fail-open one.
  **Neither manifestation is caused by `014`, and `014` fixes neither** — `015` (its own contract 2.0.0,
  pre-challenge as of this citation) addresses both, per its own AC-01/AC-04 (see `### Dependency on 015`,
  Contexto, for the exact mechanism and which of `014`'s classes benefit). **Corrected this round: `014`'s own
  `decision`/`grunt`/`build`-class preferences toward `anthropic` are fully specified but, on the primary lane
  today, do NOT genuinely reorder anything toward `anthropic`** — an `anthropic` candidate is excluded from the
  candidate list entirely by `PROVIDER_UNAUTHENTICATED` before this contract's sort key ever runs, so there is
  nothing for the preference to reorder toward, on any class, today (this corrects 3.0.0's claim that the
  sort-key mechanism "genuinely reorders `RouteDecision.provider` toward `anthropic` when so configured" — that
  claim was only ever true against a synthetic test inventory with `anthropic` authenticated, never against
  this machine's real, live credential shape). See `### Honest scope` and `### Dependency on 015` in Contexto,
  and the Verificación section's rewritten fixture-that-would-fool-it test.
- **No unset/remove CLI mechanism for the sibling `model-preference.toml` file (round 3, R3-F-04(e)).**
  `--model-preference-show` (read-only, AC-02) is delivered by this contract; removing or clearing an existing
  `[preference]`/`[role_override]` entry is not — that is separate, deferred, follow-up work. Until it lands,
  the user must hand-edit the sibling file to remove an entry, a real, named tension against this contract's
  own "CLI, not hand-edited" framing (R2-F-04's user decision), stated here honestly rather than hidden behind
  the show command's existence.
- **No lightweight "gateway" routing model.** See `## Future work` below — named so the idea is not lost, not
  designed or scoped here.

## Future work (explicitly out of scope, recorded so it is not lost — not designed here)

The user floated, this same session, a bigger idea while discussing why so few roles are currently tiered: a
future, lightweight "gateway" agent that fronts every role and dynamically hands off to whichever real target
model should actually do the work, so that only **one** agent in the entire system ever has a hardcoded model
assignment (today, every non-tiered role still has one, baked at generation time via `[areas.<duty>]`/
`[roles.<role>]`). This is a real, coherent direction — a possible "V2" of this contract's own goal ("no role
should have a model pinned by construction") taken to its logical conclusion — but it is a materially different
shape of system (a routing indirection layer, not a sort-key tie-break) and is **explicitly deferred, not
designed, not scoped, and not built by this contract.** Recorded here only so a future spec author does not
have to rediscover it from a chat transcript.

## Acceptance Criteria

- **AC-01 — a closed, disjoint, three-class taxonomy derived from `roles.tsv`'s real columns, with the
  adversarial-judge contradiction resolved explicitly, and — new this round, replacing round 2's blended
  "inertness" claims — a precise, per-class, per-role statement of which of the taxonomy's 20 in-scope roles
  have real, live, observable effect TODAY and which do not, and why (round 2 → round 3, R2-F-02).** Three
  in-scope classes, cross-checked directly this round against `models.toml`'s `[roles.<role>.tiers.*]` tables
  (`models.toml:151-232` — the closed, six-role universe of dynamically-tiered roles: `debugger`,
  `delta-reviewer`, `finding-verifier`, `implementer`, `package-reviewer`, `security-auditor`; no other role
  has a `.tiers.*` table):
  - **`decision`** = `duty == "coord"` (the sole role `orchestrator`) **UNION** `duty == "docs"` (`architect`,
    `product-analyst`, `project-bootstrapper`, `agent-factory`, `ux-ui-designer`, `package-planner` —
    `roles.tsv:4-8,10`). Seven roles total. `orchestrator` and `architect` are the user's own two named
    examples; the other four `duty="docs"` roles are swept in by the same generalization ("by extension any
    role that makes judgment calls") the user's own prose already invoked — stated here as an explicit product
    decision, flagged for `USER_APPROVAL`, not a rediscovered rule.
    **Real-effect statement (honest scope, this round): ZERO of these seven roles are dynamically tiered, and
    the reason is operational, not a `RouteDecision`-level code exclusion — stated precisely so the claim is
    not overstated in either direction (round 2 → round 3 self-correction, verified by re-reading the code, not
    carried forward from an earlier draft's phrasing).** `RoutingService.route()`/`--route-decide` is itself
    role-agnostic: `routes.v1.toml`'s six curated routes each list all 28 roles in their `roles` field
    (verified directly, every `roles = [...]` line in `ai/catalogs/routes.v1.toml` checked), so if `--route-decide`
    were ever invoked for `orchestrator` or any other `decision`-class role, this contract's sort-key element
    WOULD apply and WOULD reorder `RouteDecision.provider` exactly like it does for a tiered role — that is by
    design, not a bug, and this contract's own AC-04 mechanism-correctness test relies on exactly this
    uniformity. **The real reason `decision`'s seven roles have zero real-world effect is that the shipped
    orchestrator doctrine, byte-identical across all three generated copies, never invokes `--route-decide` for
    any of them at all**: its own delegation step names exactly six roles as "tiered roles" requiring the
    decide→spawn protocol (`Global/_canonical/agents/orchestrator.md:157-158`, verbatim: *"`implementer`,
    `debugger`, `package-reviewer`, `delta-reviewer`, `security-auditor`, and `finding-verifier` are **tiered
    roles**"*) — every other role, including all seven `decision`-class roles, is spawned as the BASE static
    agent directly. `orchestrator` itself never even reaches a delegation step for its own model — its
    session-start model comes from `codex_orchestrator()` (`models_config.py:373-380`), a wholly separate,
    static, non-per-decision mechanism. This is a **documentation/operational fact, verified by direct
    citation of the shipped doctrine, not a Python-level regression-testable claim** — a hermetic unit test
    that called `RoutingService.route()` for `role="orchestrator"` directly WOULD show the preference taking
    effect (correctly — see AC-04), so no such test is written or required for this class; the "zero real
    effect" claim rests on the doctrine citation above, not on a byte-identical-`RouteDecision` assertion,
    which would be false if attempted. See Verificación for how AC-01's regression coverage is split
    accordingly between the mechanism-correctness proof (all 28 roles, all four classes alike) and the
    real-world-reachability proof (doctrine citation, for the 22 non-tiered roles; code-level hard-exclusion
    test, for `grunt`'s 4 tiered-but-inert roles).
  - **`grunt`** = `capability == "review-ro" AND duty IN {"audit", "judge"}` — `spec-challenger`,
    `package-reviewer`, `delta-reviewer`, `security-auditor`, `finding-verifier`, `adversarial-judge`
    (`roles.tsv:9,20-24`). Six roles total. **This is the exact predicate `RoutingService._role_class` already
    computes as `"review"` (`service.py:222`)** — reused by definition, not re-derived.
    **`adversarial-judge` is placed here, definitively, resolving the contradiction named in Contexto:**
    its real `roles.tsv` shape (`temperature=0.0`, `capability=review-ro`, `duty=judge`) is structurally
    identical to the other five roles the user's own second bullet named as the grunt/bulk-verification
    archetype, and has nothing in common with `architect`'s shape (`temperature=0.2`, `capability=docs-rw`,
    `duty=docs`) — the parenthetical mention of "adversarial judges" alongside "architect" in the user's first
    bullet is read as a drafting slip, not a deliberate reclassification of the review pipeline.
    **Real-effect statement, corrected this round (R3-F-03, mechanical) to state TWO distinct, independent
    reasons instead of one blended claim — and to correct which kind of proof applies to each, and the actual
    survivor count on the primary lane today:** (a) `package-reviewer`, `delta-reviewer`, `security-auditor`,
    `finding-verifier` — 4 of 6 — ARE dynamically tiered (named in the doctrine's own "tiered roles" sentence,
    `Global/_canonical/agents/orchestrator.md:157-158`, and `--route-decide` genuinely IS invoked for them in
    real operation), but are *tiered-yet-inert-by-hard-exclusion*. **Corrected this round: on the primary
    `opencode` lane today, the mechanism is not "one provider survives" — it is ZERO survivors.**
    `PROVIDER_UNAUTHENTICATED` (`service.py:145`) excludes every `anthropic` candidate first (verified live,
    `('opencode','anthropic')` probes to zero models on this machine), and `REVIEW_PROVIDER_CONFLICT`
    (`service.py:166`, see AC-04's corrected attribution) separately excludes every `openai-codex` candidate
    that shares the writer's provider — together leaving no candidate at all, and the decision returns
    `REVIEWER_INDEPENDENCE_UNAVAILABLE` (a hard refusal the shipped doctrine halts on,
    `Global/_canonical/agents/orchestrator.md:199-205` — see Non-goals), before this contract's preference is
    ever consulted. **This is still provable by a byte-identical-`RouteDecision` regression test** (a
    configured preference cannot reorder a candidate list of length zero either way), **but the test's own
    assertion must check the actual `reason_codes`** — `assertEqual(decision.reason_codes,
    ("REVIEWER_INDEPENDENCE_UNAVAILABLE",))` — not merely `RouteDecision` equality, so a future reader can see
    this test's meaning change the day this lane gains a real Anthropic credential (the shape reverts to the
    ORIGINAL "one survivor, tiered-but-inert" case, still byte-identical but for a different reason) or the day
    `015` ships its cross-lane redirect (the shape changes again — see `### Dependency on 015`, Contexto — and
    the test must then assert the preference DOES change `RouteDecision.provider`, no longer byte-identical).
    It becomes observably active the moment a third provider gains real `routes.v1.toml` rows OR `015` ships,
    with zero further code change to `014` either way. (b) `spec-challenger`, `adversarial-judge` — 2 of 6 —
    are **not dynamically tiered at all**, the same operational reason `decision`'s seven roles are inert (the
    doctrine never invokes `--route-decide` for them either) — **not** provable by a byte-identical-
    `RouteDecision` test (that would be false if attempted, for the same reason explained under `decision`
    above: the sort key would genuinely reorder their candidates if the CLI were invoked directly); proven
    instead by the same doctrine-citation argument. Both facts are named, precisely, with the correct proof
    mechanism for each, not blended into one claim or one test.
  - **`build`** (scope-widened in round 1, predicate corrected this round — R2-F-03) = **`capability ==
    "code-rw"`** — the literal, single-conjunct predicate `RoutingService._role_class` already computes as
    `"writer"` (`service.py:221`), reused by definition, the same way `grunt` reuses `"review"` — **not**
    `duty == "implement" AND capability == "code-rw"` as previously stated, which round 2 found was not
    provably identical to the code it claimed to reuse. Re-verified directly against `roles.tsv:11-17`: every
    `code-rw` row also carries `duty == "implement"` and vice versa, so **membership is unchanged** —
    `test-writer`, `implementer`, `frontend-engineer`, `refactor-specialist`, `debugger`, `repair-agent`,
    `integrator`. Seven roles total, same as before, now defined by the literal predicate rather than a
    compound one asserted to be equivalent. See `### The architectural question` in Contexto for why this
    class shares AC-04's integration point unchanged, and `### Design decision` for why this does not recreate
    a second source of truth against `[areas.implement]`.
    **Real-effect statement — corrected this round (R3-F-01, blocking; this is the round's headline finding,
    reversing round 2's own headline claim): 2 of 7 are dynamically tiered and doctrine-invoked — `implementer`,
    `debugger` (both named in the doctrine's own "tiered roles" sentence,
    `Global/_canonical/agents/orchestrator.md:157-158`) — but on the primary `opencode` lane today, they have
    the SAME zero observable effect as every other role in the roster, for a third, distinct reason.** Unlike
    `grunt`'s reviewer decisions, no independence exclusion applies to a writer-class decision — so
    `PROVIDER_UNAUTHENTICATED` (`service.py:145`) is the ONLY exclusion in play, and it excludes all three
    `anthropic` tier rows on this lane (verified live, `('opencode','anthropic')` probes to zero models),
    leaving exactly **ONE** surviving candidate (`openai-codex`) at every tier. A sort key with one candidate to
    sort has nothing to reorder: `candidates[0]` is fixed regardless of any configured `build`-class preference.
    **Round 2's claim that these two roles were "the entire real, live, working scope of this contract as it
    now ships" did not verify this machine's actual credential shape and is retracted** — a hermetic regression
    test using `tests/test_routing.py`'s own more generous default fixture (which DOES include an authenticated
    `('opencode','anthropic')` key) would have gone green on that claim even though it is false against the
    real, live catalog; this contract's own real-effect tests must instead inject an inventory shaped like this
    machine's real probe (no such key), the same faithfulness requirement `015`'s own AC-01 states for its
    tests. The other 5 — `test-writer`, `frontend-engineer`, `refactor-specialist`, `repair-agent`,
    `integrator` — remain not dynamically tiered at all, the same operational reason as `decision`'s seven
    roles: the doctrine never invokes `--route-decide` for them, spawning the BASE static agent directly,
    governed solely by `[areas.implement]`'s static default. **Not provable by a byte-identical-`RouteDecision`
    test** (as with `decision`'s roles and `grunt`'s two non-tiered roles, the sort key would genuinely reorder
    their candidates if `--route-decide` were invoked for them directly — the mechanism is uniform by design);
    proven instead by the same doctrine-citation argument used for `decision`'s roles (see Verificación). See
    `### Dependency on 015` (Contexto) for the concrete, cited mechanism by which `implementer`/`debugger`
    regain real effect once `015` ships.
  - **Every other role (8 of 28: `brainstormer`, `image-describer`, both `gate`-duty roles,
    `github-release-manager`, `memory-scribe`, `app-runner`, `runtime-verifier`) is `unscoped`** — untouched by
    this contract's configuration or code path, exactly today's behavior. (Round 1's `unscoped` set of 15 loses
    the seven roles that now form `build`; 15 − 7 = 8, arithmetic checked directly.)
  - **The taxonomy itself is not narrowed by any of the above** — the user's explicit "honest scope" decision
    this round (verbatim: *"Por el momento me conformo con los 2 roles reales con modelos Hardcodeados... si es
    que lo ves bien asi"*) keeps all four classes exactly as defined; only the STATED real-world effect of
    every class changes, from "live for `implementer`/`debugger`, inert elsewhere" (round 2's framing,
    retracted — R3-F-01) to "zero on the primary lane today, for every class, for two distinct code-level
    reasons (`grunt`: zero survivors, a refusal; `build`'s two tiered roles: one survivor, nothing to reorder)
    plus one operational reason (`decision` and the non-tiered roles: doctrine never invokes `--route-decide`),
    contingent on `015` for `build`/`grunt` once it ships, or on the tiered roster widening, or on this lane
    gaining a real Anthropic credential" (this round's corrected, honest framing — see `### Honest scope`,
    Contexto). Widening which roles are tiered is real, separate, out-of-scope work (Non-goals); the user
    separately floated, and explicitly deferred, a bigger "gateway" redesign — see `## Future work`.
  - **Disjointness is enforced, not assumed** — directly mitigating `007-P0`'s finding 2
    (`decisions-log.jsonl:22`, F-07): a regression test enumerates the full 28-role roster from `roles.tsv` and
    asserts every role maps to exactly one of `{decision, grunt, build, unscoped}`, never two, and that the
    `decision`/`grunt`/`build` sets found by this contract's own resolver equal the sets named above by direct
    enumeration (a change to `roles.tsv` that silently shifts any set fails the test instead of silently
    drifting). **New this round, two more enumeration checks, code-level and doctrine-level respectively:**
    (i) a second regression test cross-checks the same 28 roles against `models.toml`'s `.tiers.*` universe
    (Python-readable, code-level) and asserts the tiered-vs-not partition named above (7 `decision` = 0 tiered;
    6 `grunt` = 4 tiered + 2 not; 7 `build` = 2 tiered + 5 not) matches exactly, so a future change to
    `models.toml`'s tiered roster (widening or narrowing it) fails this test loudly instead of silently
    invalidating this AC's own prose; (ii) a doctrine-consistency check — **corrected this round (R3-F-06):
    round 2/3.0.0 checked only the CANONICAL orchestrator file, but the zero-reachability proof for the 21
    non-tiered roles depends on what is actually SHIPPED in all three generated copies too, not only the
    canonical source** — so this check reads the exact six role names in the "tiered roles" sentence from ALL
    FOUR files (`Global/_canonical/agents/orchestrator.md:157-158`, `Global/claude-code/agents/orchestrator.md`,
    `Global/opencode/agents/orchestrator.md`, `Global/codex/agents/orchestrator.toml` — the same four-file
    universe `find Global -iname orchestrator.md -o -iname orchestrator.toml` returns, verified live this round,
    canonical included) and asserts all four match `models.toml`'s `.tiers.*` six-role set byte-for-byte. This
    reuses, rather than reinvents, the existing precedent test `tests/test_harness.py`'s
    `test_orchestrator_doctrine_branches_on_route_decide_reason_taxonomy` (`:2864-2895`) already establishes for
    checking the SAME three generated copies for a different string (`generate.py` copies the canonical body
    verbatim, per that test's own comment, `:2872`) — this AC's own check follows the identical read-all-copies
    pattern, adding the canonical file as a fourth, so a future edit to either the doctrine's prose or
    `models.toml`'s tiered roster that silently diverges the two — in the canonical source OR in a stale
    generated copy that `./build.sh` was never re-run for — is caught mechanically, even though this contract
    does not own or edit the doctrine file itself (Non-goals).
- **AC-02 — one real, per-harness-install configuration surface, with a dedicated writer that does not corrupt
  the existing shared app config, and every currently-undefined resolution state given a stated, testable
  rule.** A new sibling file inside the same private, already-established directory `write_app_config` uses
  (`STATE_DIR = Path.home() / ".local/state/set-agentes"`, `set_agents_app.py:39`) — e.g.
  `STATE_DIR / "model-preference.toml"` — with its **own dedicated writer**, never routed through
  `write_app_config` (`set_agents_app.py:704-716`). **Why a sibling file, not a new table inside the existing
  `config.toml` written by `write_app_config` (round-1 finding F-02, blocking):** `write_app_config` is a flat
  `key = value` serializer (`f"{key} = {json.dumps(value)}"` per line, `set_agents_app.py:711`); round 1 proved
  live that writing a nested preference table (e.g. `{"decision": ["anthropic", "openai-codex"]}`) through it
  emits `json.dumps`'s `{"decision": [...]}"` syntax — JSON object syntax, not TOML inline-table syntax (which
  requires `=`, not `:`, and unquoted bare keys) — which `tomllib.loads` in `app_config()` then fails to parse,
  and `app_config()` (`set_agents_app.py:693-697`) silently swallows *any* parse failure as `{}`, discarding
  **every** unrelated key already in the file, not only the new one. A sibling file with its own dedicated,
  genuinely nested-table-capable TOML writer avoids this failure mode entirely and never touches the
  pre-existing single-writer discipline `write_app_config`'s own `AC-15` establishes for `config.toml` — chosen
  over teaching `write_app_config` real nested-table serialization because it is strictly less code, touches
  zero call sites that already depend on `write_app_config`'s current flat-only contract, and needs no new
  regression coverage on a shared writer other unrelated features already rely on. **Required regression test:**
  a round-trip write-then-read of the new sibling file, asserting (a) a nested preference table survives intact
  and (b) an unrelated key already present in `config.toml` before the write is untouched — proving the
  isolation, not merely asserting it. [UNVERIFIED for architecture: the exact file name/module the dedicated
  writer lives in — the requirement is a genuine nested-TOML round-trip, isolated from `write_app_config`'s own
  file, not this literal choice.]

  **Schema.** Two tables in the sibling file: `[preference]`, keyed by role-class (`decision`/`grunt`/`build`),
  each value an ordered list of provider tokens from the same closed vocabulary `routes.v1.toml`/
  `_PAIR_COMMANDS` already use (today `"openai-codex"`, `"anthropic"`; extensible, forward-compatible with
  `"opencode-zen"`/`"opencode-go"` once/if they gain route rows); and `[role_override]`, keyed by role name,
  each value one of the three class names, moving that one named role into a different class than AC-01's
  default (never a role-by-role provider table — that would reopen `007-P0`'s exact flaw).

  **Precedence — genuinely TWO real levels (round-1 finding F-03, blocking, resolved by the user accepting
  "per-harness-install" scope, not a real per-project layer — see Non-goals):** (1) this one per-harness-install
  file, if present — a role named in `[role_override]` resolves to the class named there (feeding AC-05); the
  resolved class's ordered list, if the file declares one in `[preference]`, governs the sort-key rank (AC-04).
  (2) the built-in default — no bias — whenever the file is absent, or the resolved class has no `[preference]`
  entry in it. There is no third or fourth layer; round 1's original "project-role-override > project-class >
  user-class > default" four-level chain is retired as inaccurate — `models.toml`/`roles.tsv` are
  `HARNESS_HOME`-owned (Accepted `docs/adr/0008-two-roots-portability.md`), so no genuine per-project layer
  exists to place above this one.

  **Three previously-undefined resolution states, now defined (round-1 finding F-07, medium):**
  1. **A provider absent from a configured preference list** ranks tied/neutral: it sorts after every provider
     explicitly named in that list, at a fixed rank equal to the list's length (so any two unlisted providers
     tie with each other too) — never excluded, never crashes, simply unranked among the ranked.
  2. **A malformed/unknown provider token** (e.g. a typo, or a value outside the closed provider vocabulary) in
     `[preference]` fails closed at config-load time. **Precedent corrected this round (R2-F-08(d) originally,
     re-corrected R3-F-08(b) — the sub-condition count was still off by round 2's own fix):** the cited
     precedent, `models_config.load_config`'s `_normalize_schema2`, does set a fail-closed rule for
     `[routing].enabled_providers` (`models_config.py:197-201`, the `if` at `:197-200` and its `die(...)` at
     `:201`) — but that single `die("models.toml: invalid [routing] values")` call is coarser than round 1/2
     implied, and finer-grained than round 2's own recount: it is one generic message covering **ten boolean
     sub-conditions across five fields**, re-counted directly this round (`enabled_providers`: not-a-list,
     empty, non-string-or-non-enum member, duplicate member — four sub-conditions on one field;
     `xhigh_benchmarked`'s bool-ness; `max_enabled`'s fixed-`False` requirement; `single_writer`'s bool-ness;
     `fallback_limit`'s int-ness, non-bool-ness, and fixed-`1` requirement — three sub-conditions on one field;
     ten total, `or`-chained into one `if`, `models_config.py:197-200`), with no per-token message. This
     contract does **not** reuse that exact message (it would be actively less useful here, hiding which token
     was wrong). Instead, this contract's own config-load validation is new, small, and well-scoped, producing
     a **per-token** message: `die(f"model-preference.toml: [preference].{class_name}
     contains unknown provider {token!r}")` — naming the offending class table and the exact bad token, not a
     blended message covering unrelated fields. The *shape* of the precedent (fail closed, `die()`, never a
     silent default) is reused; the *granularity* is this contract's own, deliberately finer.
  3. **A `[role_override]` entry naming a role absent from `roles.tsv`** fails closed the same way, reusing the
     exact existing precedent `models_config.load_roles` already sets for an unknown `[roles.<name>]` entry in
     `models.toml` (`models_config.py:274-276`, `die(f"models.toml: [roles.{name}] does not match any role in
     roles.tsv")`) — this contract's own loader raises the equivalent, per-role-named message: `die(f"model-
     preference.toml: [role_override].{role} does not match any role in roles.tsv")`, not a new error shape.
  4. **A `[role_override]` entry naming a class outside `{"decision", "grunt", "build"}`** (the fourth value,
     `"unscoped"`, is a resolution OUTCOME, never a legal override target — a role cannot be manually assigned
     to "no class") fails closed the same way: `die(f"model-preference.toml: [role_override].{role} names
     unknown class {token!r}")`.

  **New this round (R2-F-04, resolves the user's own decision this session: a CLI subcommand, not a
  hand-edited file) — the write path.** Two new flags on the existing single flat `argparse` parser
  (`set_agents_app.py:2521-...`, matching this repo's existing convention — see e.g. `--auto-update {on,off}`,
  `--mcp-on/--mcp-off NAME` + `--harness`, `--plugin-on/--plugin-off NAME`, `--route-terminal RUN_ID OUTCOME`
  via `nargs=2`, `--feature-id` via `action="append"` for an ordered repeatable value):
  - **`--model-preference-set CLASS`** (`metavar="CLASS"`, `choices=("decision", "grunt", "build")`) combined
    with one or more **`--provider NAME`** (`action="append"`, order of appearance on the command line IS the
    ordered preference list — the same repeatable-ordered idiom `--feature-id` already establishes elsewhere in
    this file) — writes/replaces `[preference].<CLASS>` with the given ordered provider list, leaving every
    other key in the sibling file untouched (the round-trip regression test above already proves this
    isolation). Example: `set-agents --model-preference-set build --provider anthropic --provider
    openai-codex`. Backing function `cmd_model_preference_set(class_name, providers)`, printing
    `MODEL_PREFERENCE_SET class=<CLASS> providers=<p1>,<p2>,...` on success (exit 0), matching this file's
    existing single-line uppercase confirmation idiom (`PLUGIN_SET ...`, `AUTO_UPDATE=...`).
  - **`--model-preference-role-override ROLE CLASS`** (`nargs=2`, `metavar=("ROLE", "CLASS")`, mirroring
    `--route-terminal`'s existing two-positional-value idiom) — writes/replaces `[role_override].<ROLE> =
    "<CLASS>"`. `CLASS` is validated against the same three-value closed vocabulary. Prints
    `MODEL_PREFERENCE_ROLE_OVERRIDE role=<ROLE> class=<CLASS>` on success.
  - **Validation is shared, not duplicated, between the CLI write path and the config-load path**: both call
    the same small validator functions this AC's resolution-states already define (point 2/4 above for
    provider/class tokens, point 3 for role names), so a malformed value can never even be written by this CLI
    to begin with — a hand-edited file is the only way to reach the load-time `die()` path at all.
  - **Should the command warn when the configuration has no observable effect on the current roster/catalog?
    Yes — corrected this round (R3-F-01 changed the answer, not just the wording): the write still proceeds
    always (the taxonomy is deliberately kept live-but-inert, per the user's own "no role hardcoded"
    principle), but `cmd_model_preference_set`/`cmd_model_preference_role_override` print an additional,
    non-blocking line to stderr whenever the resolved class/role currently has zero observable effect — which,
    per this round's corrected honest scope, is **every** in-scope class/role on the primary lane today,
    `implementer`/`debugger` included, not only `decision`/`grunt`/`build`'s five non-tiered roles as round 2
    believed.** `MODEL_PREFERENCE_NOTE class=<CLASS> has no observable effect on the primary lane today (see
    docs/specs/014.../spec.md ### Honest scope)` — so a user who configures anything is told immediately, at
    write time, not left to discover it by reading this spec. [UNVERIFIED for architecture: whether this check
    is purely structural (doctrine-invocation — the same static, `--build.sh`-time-stable fact used throughout
    this spec, cheap and always available at CLI-write time) or additionally re-probes live credentials to
    detect the day this lane gains a real Anthropic key (in which case the note for `build`'s two tiered roles
    would correctly stop firing without a `014` code change, matching how the mechanism itself already behaves)
    — the requirement is that the note is truthful about today's real effect, not which of the two checks
    implements it.]
  - **Why a small, purpose-built serializer for this file closes R2-F-04's "unscoped general TOML writer"
    concern, stated explicitly:** this sibling file's schema is fully closed and fully owned by this contract —
    exactly two tables (`[preference]`, `[role_override]`), each a flat mapping to either a list of closed-
    vocabulary strings or a single closed-vocabulary string. This is NOT "hand-roll a general nested-TOML
    serializer" (round 2's concern about an unscoped writer) — it is a small, fixed-shape emitter for a schema
    this contract itself defines and fully controls, with no arbitrary user TOML, no unknown key shapes, and no
    generality beyond these two tables. [UNVERIFIED for architecture: the exact function name/module for the
    shared validator and the CLI-flag backing functions — the requirement is the flag interface, the shared
    validation, and the closed-schema serializer described above, not their literal file location.]

  **Five previously-undefined CLI write/read states, now defined (round 3, R3-F-04, mechanical — the read/write
  path's own undefined states, distinct from the three config-load states above):**
  (a) **A parse failure on the sibling preference file at load time must fail closed**, `die()` with a clear
  message — never silently swallow. **This is the exact defect class the sibling-file design exists to avoid,
  and it must not be reproduced one file over:** `app_config()`'s own existing bug (`set_agents_app.py:693-697`,
  `except (OSError, tomllib.TOMLDecodeError): return {}`) silently discards a parse failure as an empty config,
  the same failure shape round 1's F-02 already condemned for `write_app_config`'s corruption risk. This
  contract's own sibling-file loader must not call that function or reuse its silent-swallow behavior; a
  malformed `model-preference.toml` fails the `set-agents` invocation loudly, with `die(f"model-preference.toml:
  {exc}")` or equivalent, never degrading to "as if the file were absent."
  (b) **`--model-preference-set CLASS` with zero `--provider` values is an error** — a preference with no
  providers is meaningless (there is nothing to rank); `argparse` (or the backing function) rejects it before
  any write is attempted, with a clear message naming the missing `--provider`.
  (c) **`--provider` given without `--model-preference-set` is an argparse-level error.** Verified this round:
  the two flags are independent `argparse` arguments today with no built-in collision — this AC makes them
  co-required (e.g. `argparse`'s own mutually-inclusive-group idiom, or a post-parse check that `die()`s with a
  named message), so `--provider anthropic` alone (no target class) fails immediately rather than being
  silently ignored.
  (d) **Duplicate `--provider` tokens on the same `--model-preference-set` invocation are rejected**, following
  this repo's own existing precedent for duplicate-rejection: `models_config.py`'s `_normalize_schema2`
  (`models_config.py:198`, `len(routing["enabled_providers"]) != len(set(routing["enabled_providers"]))`, one
  of the sub-conditions folded into the `[routing]` validation `if` at `models_config.py:197-201` — see AC-02's
  own citation correction below, R3-F-08(b)) already treats a duplicated `enabled_providers` entry as invalid.
  This contract's own CLI validator applies the same length-vs-set-length check to the ordered `--provider`
  list before writing, `die()`-ing on a duplicate rather than silently collapsing or silently keeping the first
  occurrence's rank.
  (e) **No unset/remove/show path exists in round 2's design — named honestly rather than hidden, not silently
  left as a gap.** This contract adds **`--model-preference-show`** (read-only, prints the sibling file's
  current, fully-resolved `[preference]`/`[role_override]` contents, or a clear "no preferences configured"
  line if the file is absent) as part of this AC's delivery — a read path was always implied by "CLI, not
  hand-edited" and its absence would have been a real, silent gap. **Removal/unset is different: deferred
  explicitly to a follow-up package, not delivered here** — until that lands, the user must hand-edit the
  sibling file (deleting a key) to remove a `[preference]`/`[role_override]` entry, which is named here as a
  real, honest tension against "CLI, not hand-edited," not hidden behind the show command's existence. See
  Non-goals.
  **Atomic write required, not a plain `write_text`.** `write_app_config`'s current write mechanism
  (`set_agents_app.py:714`, a direct `APP_CONFIG.write_text(...)` call, no temp file, no rename) is the
  anti-pattern to avoid — a crash or concurrent write mid-`write_text` can leave a truncated or
  interleaved-with-another-writer file. This contract's own sibling-file writer must write to a temp file in
  the same directory and `os.replace()`/`Path.rename()` it into place, so a write either fully lands or leaves
  the previous, valid file untouched — never a partially-written one.
- **AC-03 — credential/availability detection is reused for the four already-known providers, and named as an
  explicit external dependency for anything else — never fabricated.** For `openai-codex`, `anthropic`,
  `opencode-zen`, `opencode-go` (the closed universe of `_PAIR_COMMANDS`, `catalog.py:133-140`), this
  contract's weight consults **no new credential probe**: the ranked preference in AC-02 only ever reorders
  candidates that already survived `RoutingService.route()`'s existing exclusions — unconditionally,
  `PROVIDER_UNAUTHENTICATED` (`service.py:145`); conditionally, only when `self.store is not None` (never on
  the simulate/explain lane), `PROVIDER_EXHAUSTED` (`service.py:143`) — this contract's preference reorders
  whatever the exclusion loop leaves standing either way, never bypassing or duplicating either check. This is
  also the whole mechanism by which "no manual reconfiguration needed when the subscription mix changes" (the
  user's own explicit choice this session, over a manual edit or a scheduled date) is satisfied for real,
  **for every in-scope class including `build`**: a provider that has lost its credentials produces zero
  candidates, so a stale preference entry naming it is automatically inert — no polling, no "detect the mix
  changed" step, nothing to keep in sync. **A standalone "Kimi Code" credential surface is not discoverable
  on this machine today** (verified live, read-only, key-presence-only, same discipline as
  `pi_auth_provider_keys()`: `~/.pi/agent/auth.json` keys = `{"anthropic","openai-codex"}`; `opencode auth
  list --pure` = `OpenCode Go, OpenAI, GitHub Copilot, OpenCode Zen`, no `Kimi` entry). This contract does
  **not** invent a probe for it — onboarding a new provider (a new `_PAIR_COMMANDS` pair, parser, billing-kind
  entry, per `012-discovered-inventory`'s AC-01/AC-02 precedent) is named as a real, external, blocking
  dependency for the weight to have any effect on a standalone Kimi Code subscription specifically, not
  delivered by this contract (see Non-goals).
- **AC-04 — one integration point, shared by all three in-scope classes, at one precise, narrow position
  inside the existing sort key, never a second decision-maker.** Round 1's F-06 investigation (see Contexto)
  established that `RoutingService.route()` builds and sorts its candidate list exactly once, for every
  `role_class` alike (`"writer"`, `"review"`, `"other"`) — so `decision`, `grunt`, and `build` share this single
  integration point; no second one is designed. **Precision correction this round (R2-F-08(a)) — "`role_class`
  is consulted only after the sort" is imprecise as a blanket claim and is now stated per `role_class`
  instead:** `role_class` itself is computed once, early, for every decision alike (`service.py:113` region).
  For `role_class == "writer"` (this contract's `build` class) and `role_class == "other"` (this contract's
  `decision` class and `unscoped`), that early computation genuinely has no further consequence before the
  sort — `writer` (the local variable holding the prior-run's writer identity) stays `None` for both, no
  pre-sort branch keys off `role_class` again, and the sort key element this contract adds is the first place
  `role_class`'s classification has any effect on candidate ORDER. For `role_class == "review"` (this
  contract's `grunt` class), by contrast, `role_class` genuinely IS consulted before the sort: it gates the
  `if role_class == "review":` branch (`service.py:115-126`) that resolves the prior writer's identity via
  `self.store.implementation_identity(review_of_run_id)` — and that resolved `writer` identity then feeds BOTH
  the hard exclusion `REVIEW_PROVIDER_CONFLICT` (`service.py:166`, inside the exclusion loop, before the sort
  runs) AND sort-tuple position 1 (`(x[0].provider == writer.provider) if writer else False`, `service.py:171`)
  — two genuinely pre-sort, `role_class`-gated consultations that do not exist for `"writer"`/`"other"`. This
  contract's own new sort-key element (position 3, all three classes alike) is unaffected either way — it is
  always inserted after the existing sort key's independence/tier elements regardless of which `role_class`
  produced them — but the CLAIM "`role_class` is only consulted post-sort" is corrected to hold exactly for
  `build`/`decision`, not for `grunt`, whose hard-exclusion/position-1 pre-sort machinery this AC's point 1
  below already relies on and correctly attributes. Inside `RoutingService.route()`, the class-scoped ranked
  preference from AC-02 participates **only** as one additional element of the existing candidate sort key
  (`candidates.sort(key=lambda x: (...))`, `service.py:171`), inserted **between** the existing
  `TIER_ORDER[route.tier]` element (position 2) and the existing `curated_priority` element (today's position
  3, shifting to 4): `(independence_boolean, tier_order, role_class_preference_rank, curated_priority,
  route_id)`. Non-negotiable, and each clause a direct, named mitigation of the `007-P0` failure modes in
  Contexto:
  1. **Never before position 1 (writer/reviewer-independence guard) or position 2 (tier sufficiency).** The
     tier-sufficiency ordering is untouched, unconditionally, by any configuration this contract adds.
     **Corrected attribution (round-1 finding F-10, low-medium):** position 1
     (`(x[0].provider == writer.provider) if writer else False`) does **not itself** prevent a same-provider-
     as-writer candidate from winning — every candidate reaching the sort has already had that exact case
     hard-excluded by `REVIEW_PROVIDER_CONFLICT` (`service.py:166`), so position 1 evaluates to the constant
     `False` for every surviving candidate on every decision, review or not, and is vestigial for this specific
     guarantee. The real guarantee — no same-provider-as-writer reviewer candidate can ever be selected — is
     attributed correctly to the hard exclusion at `service.py:166`, which this contract's new element (at
     position 3, after position 1) can never reorder past or bypass, exactly as it could never reorder past or
     bypass any other hard exclusion.
  2. **Never a change to the exclusion loop that builds `candidates`** (`service.py:136-169`) — every existing
     `reason=...` exclusion (`RUNTIME_UNAVAILABLE`, `PROVIDER_EXHAUSTED`, `PI_SIMULATION_ONLY`,
     `PROVIDER_UNAUTHENTICATED`, `ROLE_INCOMPATIBLE`, `TOOLS_MISSING`, `CONTEXT_MISSING`,
     `REVIEW_FAMILY_CONFLICT`, `REVIEW_MODEL_CONFLICT`, `REVIEW_PROVIDER_CONFLICT`, `TIER_INSUFFICIENT`) fires
     exactly as it does today, before this contract's weight is ever consulted — directly closing `007-P0`'s
     finding 1 (a preferred-but-unauthenticated candidate can never fall back out of the dynamic system,
     because it never becomes a candidate in the first place).
  3. **Never a change to `routes.v1.toml`'s `roles`/`tools`/`tier` membership** — no role gains or loses
     eligibility for any route because of this contract, unlike `007-P0`'s twelve duplicated rows.
  4. **Absent configuration (no file, or the role is `unscoped`) evaluates to a constant** for every candidate,
     so ordering is byte-identical to today's `(independence, tier, curated_priority, route_id)` sort — no
     separate code branch is needed to preserve the unbiased default; it falls out of the same code path.
  5. **Forward-compatibility tripwire (round-1 finding F-11-tripwire, medium):** AC-07 leaves the composition
     with `008-dynamic-selection`'s future P3 sketch undecided, on purpose. A regression test pins the current
     sort key's exact element count and order (five elements after this contract lands: independence, tier,
     role-class-preference-rank, curated_priority, route_id) so that ANY future change to that tuple's shape —
     P3 or otherwise — fails loudly, not silently, the moment it lands without updating both contracts' authors.
     The composition question itself stays open (AC-07); only its silent-drift failure mode is closed here.
  [UNVERIFIED for architecture: whether the resolved preference tables are retained on the `RoutingService`
  instance at construction time (`_seal`, `service.py:85-94`, which does not currently retain `config`) or
  threaded per-call — the requirement is the sort-key position and the five invariants above, not this
  implementation choice.]
- **AC-05 — role→class resolution is one function, reused, not duplicated a third time.** Default resolution
  per AC-01's `capability`/`duty` predicates; override precedence per AC-02's single per-harness-install layer
  (role named in `[role_override]` resolves to that class; otherwise AC-01's default applies). The resolved
  class is one of exactly four closed values (`"decision"`, `"grunt"`, `"build"`, `"unscoped"`) — never a
  role-by-role provider list, which would reopen `007-P0`'s exact flaw of an unaudited, hand-maintained,
  per-role table disconnected from a class model. **Named explicitly so it is not repeated a third time:** this
  repo already has one small, un-shared duplication of an adjacent role-class predicate (`_role_class`,
  `service.py:218-223`, vs. `_role_class_of`, `set_agents_app.py:230-233`, verbatim-identical bodies, two
  independent definitions) — this contract's own role→class resolver must be written once and consumed
  everywhere it is needed, not copied a second time the way that pre-existing pair already was. [UNVERIFIED for
  architecture: whether this resolver lives in `models_config.py` alongside `resolve_role`'s existing
  base→area→role merge, or as a new, separate module — the requirement is a single, testable, single-source
  function, not its file location.]
- **AC-06 — non-goals restated as testable negative assertions** (see Non-goals above for the full list):
  no change to `008-P1`'s accepted doctrine or generated text; no change to `[areas.<duty>]`'s static default
  resolution or to `codex_orchestrator()`; no genuine per-project configuration layer; no dependency on
  `011-quota-failover` (`provider_exhausted`, `service.py:143`, is never read unconditionally by this
  contract's own code); no cost/USD-ceiling logic of any kind; no new `routes.v1.toml` rows and no new
  provider onboarding (both named as external dependencies, not delivered here); no change to the
  session-window/context-budget problem; no quick-fix shipped ahead of the full contract; **new this round**:
  no widening of which roles are dynamically tiered, and no fix to the pre-existing cross-lane anthropic-degrade
  gap (`015`'s scope, not `014`'s); the quota-exhaustion-exposure risk, the `grunt`-class inertness, and (new
  this round) the `decision`-class and non-tiered-`build`-role inertness are all accepted and tested, not
  mitigated further. **R2-F-06's coverage gap closed:** every one of these negatives now has an explicit
  Verificación bullet (see `## Verificación` below) rather than being asserted only in prose here — each was
  individually re-checked this round for whether it is actually mechanically verifiable (all are: either a
  byte-identical-output regression test against a real code path, or a source-level absence-of-reference check,
  never an unfalsifiable "and nothing else changed" claim).
- **AC-07 — the named composition point with `008-dynamic-selection`'s P3 sketch, now much narrower given
  honest scope (R2-F-06).** P3's own two-layer model (`docs/specs/008-dynamic-selection/spec.md:240-267`:
  layer 1, any `subscription`-billed provider with quota wins with no cost comparison, gated on
  `011-quota-failover`'s `provider_exhaustions`; layer 2, a `metered` provider only below a daily USD ceiling)
  and this contract's role-class preference are **orthogonal axes over the same candidate-sort position** —
  both are soft, post-hard-exclusion tie-break inputs. **Given honest scope (`### Honest scope`, Contexto),
  what's actually left to compose is narrow, stated precisely rather than left as a blanket "undecided"
  claim:** `decision` and `grunt` have no live sort-key participation today regardless of P3, so there is
  nothing for P3 to compose with for those 13 roles; the composition question has real substance only for
  `build`'s two live roles, `implementer`/`debugger` — if P3 ever lands, ITS sort-key element and THIS
  contract's `build`-class rank would both be live, simultaneously, for exactly these two roles, and this
  contract still does **not** decide their relative order (e.g., `independence > tier > [P3 layer] > [014
  role-class rank] > curated_priority > route_id`, or some other order) — it names this as the concrete open
  integration question for whichever of the two packages lands second. AC-04's point 5 tripwire test guarantees
  this silent-drift risk is caught mechanically for all classes alike, not left to memory, even though only
  `build` currently has anything real to drift.
- **AC-08 (new, round-1 finding F-08, medium; field renamed this round, R2-F-09) — the resolved role-class and
  applied preference are observable on the decision output itself, under a name that does not collide with an
  existing, differently-valued field in the same JSON envelope.** `RouteDecision`
  (`routing_core/domain.py:165-178`, corrected line range this round — R2-F-08(c); the dataclass body runs from
  the `class RouteDecision:` line to its `to_dict()` method, inclusive) is a frozen dataclass; every existing
  construction site is inside `service.py` only (checked directly this round — **14 call sites, corrected from
  round 2's "13" — R2-F-08(b)**, all positional, none passing `independence_verified` positionally, all
  stopping before it or omitting it and relying on its default), so it is the sole file needing a call-site
  change. Two new fields are added at the end, both defaulted, so every existing call site stays valid
  unmodified: **`bias_class: str | None = None`** (renamed this round from `preference_class` — round 2's
  R2-F-09 found the previous name landed in the same JSON envelope as an existing, differently-valued
  `role_class` key emitted by `cmd_route_decide`, `set_agents_app.py:440`, `data["role_class"] = role_class`,
  drawn from `_role_class_of`'s three-value vocabulary `{"writer", "review", "other"}` — a near-homonym to a
  new four-value field, `{"decision", "grunt", "build", "unscoped"}`, would confuse a future reader parsing one
  envelope with two similarly-named-but-disjoint-vocabulary fields. `bias_class` is deliberately not "role
  class" at all in its name, stated here explicitly so the two fields' coexistence — same envelope, same
  decision, two independent classifications of the same role, disjoint vocabularies — is documented, not
  discovered by confusion later) — one of the four AC-01/AC-05 closed values, independent of whether a route
  was actually found (the class assignment does not depend on route availability). **Precision corrected this
  round (R3-F-05, mechanical — round 2's "populated whenever `facts.role` resolved successfully... except the
  early `FACTS_INCOMPLETE`/`REVIEW_IDENTITY_INVALID` refusals" blended two refusal shapes with different
  timing under one label, and understated a third):** `role_class` (the service's own internal 3-value
  classification, which AC-05's role→class resolver piggybacks on the same `facts.role` lookup to compute) is
  computed at exactly one line, `service.py:113`, immediately after the request/facts shape checks and before
  any review-identity or conflict check. **`bias_class` is `None` only for the two refusals that fire strictly
  BEFORE that line** — both currently carrying `reason_codes=("FACTS_INCOMPLETE",)` (`service.py:107` — the
  issuer/consume guard — and `service.py:112` — the request-risk/required-tools shape guard). **`bias_class` IS
  populated for every refusal reachable only AFTER `service.py:113`**, a strictly larger set than round 2's
  text implied: both `REVIEW_IDENTITY_INVALID` refusals (`service.py:119` — no `review_of_run_id` offered and
  not `unverified_review` — and `service.py:125` — a `review_of_run_id` offered but rejected by
  `self.store.implementation_identity`) fire only after `role_class` is already known, contrary to being
  grouped with the "early, pre-resolution" refusals; **and a third, previously-uncounted refusal** — the
  `conflicts` check (`service.py:127-130`) — also fires only after `service.py:113`, yet returns the exact
  same `reason_codes=("FACTS_INCOMPLETE",)` as the two early guard clauses. **`reason_codes` alone therefore
  cannot predict whether `bias_class` is populated**: two `RouteDecision`s with byte-identical
  `reason_codes=("FACTS_INCOMPLETE",)` can differ in `bias_class` (`None` for the early guard-clause refusal,
  populated for the later `conflicts` refusal) depending only on control-flow position relative to
  `service.py:113` — the regression test for this AC (Verificación) must exercise all four refusal sites
  (`:107`, `:112`, `:119`, `:125`, plus the `:130` `conflicts` path) individually, not infer that the two
  `FACTS_INCOMPLETE`-reason-code sites are interchangeable; and
  `preference_configured: bool = False` (name unchanged — no collision) — true only when AC-02's config
  supplied a non-default (non-empty `[preference]`) entry for the resolved class, false when the class fell
  back to the built-in unbiased default (absent file, or class present in `[role_override]` / AC-01's default
  but absent from `[preference]`). Reusing `reason_codes` was considered and rejected: it is a closed
  vocabulary of terminal/refusal reasons (`FACTS_INCOMPLETE`, `PROVIDER_UNAUTHENTICATED`, etc.) consumed by
  `_decide_status`'s own reason→exit-code table (`set_agents_app.py:246-250`) — folding an informational,
  always-present field into it would blur a vocabulary other code already branches on. **`to_dict()` — citation
  corrected this round (R3-F-08(d)): `def to_dict(self):` is at `domain.py:177`, its `return
  dataclasses.asdict(self)` body at `:178`; cited together as `domain.py:177-178`** — is `dataclasses.asdict`-
  based and picks up both new fields automatically, with no separate serialization code to maintain.
- **AC-09 (new, round-1 finding F-04, blocking — architectural design decision, now answered in-spec) — the
  design is recorded in a dedicated ADR, required as a delivery criterion, not before `USER_APPROVAL`.**
  Mirroring `008-dynamic-selection`'s P1 AC-10 (`docs/adr/0011-uninterrupted-delegation.md`) and
  `012-discovered-inventory`'s AC-12 (`docs/adr/0016-discovered-inventory.md`) — both wrote their ADR as part of
  the package's own delivery, not as a precondition of spec approval — this contract requires a new ADR
  recording: the three-class taxonomy and its reuse of `_role_class`'s existing predicates (AC-01); the single
  shared integration point and the F-06 investigation that established it (AC-04); and the `### Design
  decision` reconciliation with `ADR-0003` above (that this contract coexists with, and does not replace or
  compete with, `[areas.<duty>]`). **ADR number is deliberately not pinned now:** `0017` is explicitly claimed
  by `013-pi-interactive-target`'s own AC-14 (`docs/specs/013-pi-interactive-target/spec.md:361-362`, naming
  `docs/adr/0017-pi-interactive-target.md`) even though that file does not yet exist on disk (`013` is still
  `PACKAGE_PLANNING` as of this session) — so the next unclaimed number at spec-writing time is `0018`, but
  whoever writes this contract's ADR must re-check `docs/adr/README.md` live at that time rather than assume
  `0018` still is: a hole (an unclaimed number becoming claimed by something else first) is recoverable, a
  collision on the same number is not, the same distinction `008-dynamic-selection`'s own P1 AC-10 note
  already established for this repo. **Re-confirmed live this round, not carried over stale:** `docs/adr/README.md`
  still lists `0002..0016` as the highest materialized entries (`0016-discovered-inventory.md`, `Accepted`,
  `2026-07-31`); `0017` is still claimed-not-materialized by `013`; `0018` is still the next unclaimed number
  AT THIS SPEC-WRITING MOMENT — restated, not re-decided, because this fact can only ever be trusted live, at
  ADR-write time, never from any spec's prose (this one's prior round included). **R2-F-06's coverage gap
  closed:** the Verificación section below now states explicitly, as a required package-acceptance-time check
  (not a unit test — this is a documentation-existence fact, not code behavior), that (a) the ADR file exists
  on disk at whatever path/number was actually claimed, (b) `docs/adr/README.md` carries a matching row with
  `Status = Accepted`, and (c) the ADR number was re-verified live against `docs/adr/README.md` at the moment
  the ADR was actually written, not assumed from this spec's `0018` note.

### Audit (self-review)

- **Universe named, for every claim in this contract:** the 28-role roster (`roles.tsv:2-29`, counted
  directly); the 4-way partition over it (`decision`=7, `grunt`=6, `build`=7, `unscoped`=8, summing to 28,
  checked directly); the closed 4-provider universe `_PAIR_COMMANDS` already probes (`catalog.py:133-140`); the
  six real `routes.v1.toml` rows and their two providers (counted and enumerated directly, not assumed from an
  earlier summary); the four real credentials `opencode auth list --pure` reports on this machine today; the
  two keys present in `~/.pi/agent/auth.json` today. **New this round:** the closed, six-role universe of
  dynamically-tiered roles read directly from `models.toml`'s `[roles.<role>.tiers.*]` tables
  (`models.toml:151-232` — `debugger`, `delta-reviewer`, `finding-verifier`, `implementer`, `package-reviewer`,
  `security-auditor` — a `grep -n '^\[roles\.'` sweep of the whole file, not a sample); **the four-file
  universe of orchestrator-doctrine copies — corrected this round (R3-F-08(c)): `find Global -iname
  orchestrator.md -o -iname orchestrator.toml` returns FOUR files, not three** — the canonical source
  (`Global/_canonical/agents/orchestrator.md`) plus its three generated copies
  (`Global/claude-code/agents/orchestrator.md`, `Global/opencode/agents/orchestrator.md`,
  `Global/codex/agents/orchestrator.toml`), all four read directly this round, byte-identical on every cited
  passage (the "tiered roles" sentence, the HARD DENIAL branch). Round 2/3.0.0's "three-lane universe" framing
  undercounted by omitting the canonical file the other three are generated from — fixed here and in AC-01's
  doctrine-consistency check (R3-F-06). No claim in this contract is stated over "however many happen to exist"
  without that count taken live this session.
- **Absence-of-record behavior, defined for every case this contract introduces:** a role absent from any
  configured preference (no file, or classified `unscoped`) is unbiased — AC-04's constant-key fallback, not a
  silent skip with undefined ordering. A provider named in a preference list that currently has no valid
  credentials produces zero candidates upstream of this contract's own code (AC-03) — never a crash, never a
  "provider not found" branch this contract needs to write, because the existing exclusion loop already owns
  that case. A role reclassified by override exits or enters this contract's code path exactly as its new
  class dictates. A provider preference naming `opencode-zen`/`opencode-go` today has a defined, stated
  outcome: legal configuration, zero observable effect, because no candidate of that provider currently exists
  to reorder (Contexto, Non-goals) — not an unstated gap discovered later. A provider absent from a configured
  list, a malformed provider token, and a `[role_override]` entry naming an unknown role all now have a
  stated, precedent-reusing rule (AC-02, resolving round-1's F-07).
- **Data source proven to carry the signal, not paraphrased from an inherited summary:** every code citation
  (`service.py`, `catalog.py`, `set_agents_app.py`, `models_config.py`, `domain.py`, `routes.v1.toml`,
  `roles.tsv`, `models.toml`) was opened and read directly this session, this round included. The `007-P0`
  precedent was read from its three surviving records (`decisions-log.jsonl:21-23`, the matching
  `docs/notas/decisiones/` file, and `007-quota-visibility/spec.md`'s own in-file retraction), not
  reconstructed from memory or a title alone — all five architect findings (F-07..F-11) from the same log entry
  are read and reconciled this round, not only F-07 as in round 1. The credential-surface claims (no standalone
  Kimi Code on this machine) were checked live, read-only, key-presence-only — never a value read or logged.
  The F-06 architectural question (does a writer-role decision flow through `RoutingService.route()`'s sort
  key) was answered by reading `service.py`'s actual control flow line-by-line, `set_agents_app.py`'s
  `cmd_route_decide`, `set_agents_spawn.py`'s own module docstring, and `008-dynamic-selection/spec.md`'s own
  AC-05 evidence — not assumed from either mechanism's name. **New this round, all four of round 2's citation
  findings re-verified live, not copied from round 2's own summary (R2-F-08):** `RouteDecision(` is constructed
  at exactly 14 call sites in `service.py` (`grep -c` this round, corrected from round 2's carried-forward
  "13"); the `RouteDecision` dataclass body runs `domain.py:165-178` (from `class RouteDecision:` through its
  `to_dict()` method, corrected this round from a prior draft's off-by-one citation of `:179`); `models_config.py`'s cited fail-closed
  precedent (`_normalize_schema2`, `models.toml: invalid [routing] values`, `models_config.py:197-201`) was
  re-read in full this round and re-counted precisely (R3-F-08(b), correcting round 2's own "six" recount):
  **ten boolean sub-conditions across five fields** (`enabled_providers`, `xhigh_benchmarked`, `max_enabled`,
  `single_writer`, `fallback_limit`) blended under one message, not a per-token one — the precedent's *shape*
  is reused, its coarse granularity is not (see AC-02); `set_agents_app.py:440` (not
  round 2's approximate "442") is the exact line writing the pre-existing `role_class` envelope key AC-08's
  renamed field must not collide with.
- **Pairwise conflict pass:** (1) `decision` vs. `grunt` vs. `build` — enforced pairwise-disjoint by AC-01's
  own test, directly mitigating `007-P0`'s finding 2. (2) This contract's new sort-key element vs. `008-P3`'s
  future layer-1/layer-2 model — both soft, same tie-break region; the composition is named, not silently
  decided, in AC-07, and AC-04's point 5 tripwire test catches any silent shape change mechanically. (3) This
  contract's weight vs. the three review-independence hard exclusions
  (`REVIEW_FAMILY_CONFLICT`/`REVIEW_MODEL_CONFLICT`/`REVIEW_PROVIDER_CONFLICT`, `service.py:149,160,166`) and
  the writer-independence sort element (position 1, now correctly attributed as vestigial for this purpose, see
  AC-04 point 1) — AC-04 states plainly these are never reordered or bypassed; a `grunt`-class preference can
  never place a same-provider-as-writer reviewer candidate ahead of a cross-provider one, because the hard
  exclusion at `service.py:166` already removed it from the candidate list before the sort runs at all. (4) A
  role in `decision`/`build` class whose only live candidates are also under `TIER_INSUFFICIENT` for the task's
  required tier — AC-04 confirms tier sufficiency (position 2) is evaluated before this contract's preference
  (position 3), so a "premium" preference can never promote a candidate whose tier is too low for the task; it
  can only choose among candidates that already clear the tier bar. (5) `build`-class preference (biasing which
  candidate becomes the writer's authorized identity) vs. `grunt`-class preference (biasing which candidate a
  later reviewer of that same work prefers) — no conflict: `REVIEW_PROVIDER_CONFLICT` still hard-excludes any
  reviewer candidate sharing the writer's provider regardless of what either preference ranks among the
  survivors, so the two configured biases can coexist, even point at overlapping providers, without ever
  weakening independence — this is the same "independence first, preference second" invariant AC-04 point 1
  already states, now confirmed across two configured axes instead of one.
- **UNVERIFIED-for-architecture tags, collected:** AC-02's exact file name/module for the sibling config
  writer, the CLI-flag backing functions (`cmd_model_preference_set`/`cmd_model_preference_role_override`
  named as a proposal, not a pin), and the shared validator functions those two paths both call; AC-04's exact
  code site for retaining resolved preference tables on `RoutingService`; AC-05's exact module for the
  role→class resolver; AC-09's exact ADR number, to be re-checked live at ADR-write time rather than assumed
  now (`0018` is the next unclaimed number at spec-writing time, re-confirmed live this round too, but `0017`
  being claimed-not-yet-materialized by `013` means this must be re-verified, not assumed, when AC-09 is
  actually done) — left to `architect`.
- **What I could not verify, stated plainly rather than omitted:** (1) whether the user's actual "Kimi Code"
  $40/month product is a standalone credential surface this repo has never seen, or an informal name for the
  Kimi models already reachable through `opencode-go`'s existing subscription — named as a real open question
  for `USER_APPROVAL`, not resolved by guessing (Contexto, AC-03). (2) The `decision`-class generalization from
  `orchestrator`+`architect` to all six `duty="docs"` roles is this draft's own product decision, not something
  the user stated for the other five roles by name — flagged for confirmation, not silently assumed settled;
  round 2/3's finding that this whole class is currently zero-effect does not change this open question, it
  only lowers the immediate stakes of getting it wrong. (3) The `adversarial-judge` classification (AC-01)
  resolves a real contradiction in the user's own two bullets on the evidence available; it is this draft's
  call, not a re-statement of something the user explicitly disambiguated themselves. (4) Whether the widened
  `build`-class scope changes the user's own intuition about which providers should appear in
  `[preference].build`'s ordered list (e.g., should `build` default toward the SAME premium provider as
  `decision`, or toward the cheaper option, or toward whichever is "currently implementing" in some sense this
  contract does not define) — the user's two verbatim quotes state that the mechanism must exist and must
  reach writer roles, not what the actual preference ORDER should be; this draft leaves the list's actual
  contents fully user-configured (AC-02), not defaulted to any particular provider, and flags this as worth
  confirming explicitly at `USER_APPROVAL` so nobody assumes a default that was never stated. **(5) New this
  round: whether the user wants the CLI's non-blocking `MODEL_PREFERENCE_NOTE` inertness warning (AC-02) to
  ever become a hard `--yes`-gated confirmation instead of a pure stderr note — this draft's own call, proposed
  as the least surprising default (never block a legal, future-proofing configuration), flagged for
  confirmation, not assumed settled. **(6) Corrected this round (R3-F-07): round 2/3.0.0 said whether `015`'s
  eventual fix changes anything about this contract's own acceptance criteria was "not verified against a spec
  that does not exist yet" — that framing was already an internal contradiction by the time it was written
  (`015`'s spec.md file existed, per round 3's own finding) and is now definitively stale: `015`'s spec.md
  exists, is real, and was read directly this round (`docs/specs/015-anthropic-dispatch-parity/spec.md`,
  contract 2.0.0).** Whether `015`'s fix changes anything about `014`'s own acceptance criteria remains
  answered "no, by design" (`014` never depends on `015`'s internals, only on the pre-existing routing/doctrine
  boundary already described, per `### Dependency on 015`, Contexto) — the real residual uncertainty, restated
  precisely, is that `015`'s own design was still in-flight/pre-challenge at the time of this citation (its
  spec exists and was read, but has not yet been through `SPEC_CHALLENGE`, so its AC numbers/content could
  still shift before its own `USER_APPROVAL`) — not that the file itself was hypothetical.**

## Verificación

`./ai/scripts/verify.sh` → `VERIFY_PASS` · `python3 -m unittest discover -s tests -v` — test count measured at
package-planning time (not asserted here as a stale number, following `008-dynamic-selection`'s own precedent
for the same reason: this repo's suite grows fast enough that a number pinned at spec-writing time would be
stale before implementation starts) — must rise, never fall, no test skipped, to cover at minimum:

- **AC-01.** The disjoint-partition enumeration test over the real 28-role roster across all four classes; the
  `models.toml`-`.tiers.*`-cross-check enumeration test (tiered-vs-not partition, code-level); the
  doctrine-consistency check, corrected this round (R3-F-06) to read all FOUR orchestrator-doctrine files
  (canonical plus its three generated copies) and assert the six doctrine-named "tiered roles" match
  `models.toml`'s `.tiers.*` six-role set byte-for-byte in each. **Real-effect proofs, split by which kind of
  proof actually applies, and corrected this round (R3-F-01/R3-F-03) to reflect the real, live primary-lane
  credential shape rather than a more generous test fixture:** (i) a regression test reproducing `grunt`'s four
  tiered roles' real mechanism on the primary lane — **using an inventory shaped like this machine's real live
  probe (no `("opencode","anthropic")` key), not `tests/test_routing.py`'s own more generous default fixture**
  — asserting `reason_codes == ("REVIEWER_INDEPENDENCE_UNAVAILABLE",)` with vs. without a configured
  preference (byte-identical either way, since zero candidates survive: `PROVIDER_UNAUTHENTICATED` excludes
  `anthropic`, `REVIEW_PROVIDER_CONFLICT` excludes `openai-codex`, `service.py:145,166`); a SEPARATE test,
  using a fixture WITH `("opencode","anthropic")` authenticated (the original, hypothetical "one survivor"
  shape round 1/2 described), asserts the byte-identical-`RouteDecision` claim for that shape too, so both are
  proven, not conflated; (ii) a **mechanism-correctness** test (not a "zero effect" test — the opposite claim)
  proving the sort-key element genuinely reorders `RouteDecision.provider` when `RoutingService.route()` is
  invoked directly, with a synthetic multi-provider-authenticated inventory, for a role in ANY of the four
  classes alike, including `decision`'s roles, `grunt`'s two non-tiered roles, and `build`'s roles — this is
  expected, correct, uniform behavior (AC-04), not a defect to hide; (iii) the real-world zero-reachability
  claim for `decision`'s seven roles, `grunt`'s two non-tiered roles, and `build`'s five non-tiered roles rests
  on the doctrine-citation evidence above (all four orchestrator-doctrine files never naming these 14 roles as
  "tiered"), not on a Python regression test; (iv) **new this round (R3-F-01) — `build`'s two tiered roles**
  (`implementer`, `debugger`) get their OWN real-world zero-effect proof, distinct from (iii)'s doctrine-
  citation argument, because `--route-decide` genuinely IS invoked for them: a regression test, using the same
  live-machine-shaped inventory as (i) (no `("opencode","anthropic")` key), asserts a configured `build`-class
  preference produces byte-identical `RouteDecision` output to no preference configured, because
  `PROVIDER_UNAUTHENTICATED` leaves exactly one surviving candidate (`openai-codex`) regardless — this is the
  test that would have caught round 2's overclaim had it been written against the real credential shape instead
  of a synthetic one with `anthropic` authenticated. Stated explicitly so a future reader does not go looking
  for a byte-identical-output test for (iii)'s 14 roles that was never written because it would be false there,
  while correctly expecting one for (i)/(iv)'s roles because a real, code-level mechanism forces it.
- **AC-02.** The two-level precedence resolution (role-override-in-file > class-default-in-file > built-in
  default) exercised with the sibling file present and absent; the round-trip write+read test proving no
  corruption of unrelated `config.toml` keys and of unrelated `[preference]`/`[role_override]` keys already in
  the sibling file; the three fail-closed resolution states (unranked provider, malformed provider token,
  unknown-role override) each with their own per-token `die()` message asserted, not just a generic failure;
  the new CLI subcommand's write path — `--model-preference-set`/`--model-preference-role-override` — exercised
  end-to-end (flags → validated write → file on disk matches the schema) and its shared validator functions
  asserted to be the SAME functions the config-load path calls (single-source-of-truth, not two copies); the
  `MODEL_PREFERENCE_NOTE` inertness warning — **corrected this round (R3-F-01 changed the expected assertion,
  not just its wording)** — asserted present on stderr for every write today, `decision`/`grunt`-class writes,
  all seven `build`-class roles including `implementer`/`debugger` alike, since all 20 in-scope roles have zero
  observable effect on the primary lane today (`### Honest scope`, Contexto); the five new CLI write/read
  states (R3-F-04): the parse-failure-fails-closed test, the zero-`--provider` rejection, the
  `--provider`-without-`--model-preference-set` argparse-level rejection, the duplicate-`--provider`-token
  rejection, and `--model-preference-show`'s read-only output, each with its own dedicated test; the atomic
  write (temp file + rename) asserted by simulating an interrupted write and confirming the prior valid file
  survives untouched.
- **AC-03.** A preference naming a currently-unauthenticated provider produces the same candidate set as no
  preference at all (no crash, no special-cased branch), exercised for `decision`, `grunt`, and `build` alike.
- **AC-04.** Via `RoutingService._for_tests`'s existing hermetic seam (`service.py:76-83`): (a) the new sort-key
  element never reorders across the independence/tier boundary; (b) a hard-excluded candidate is never made
  eligible by any configuration; (c) absent configuration produces byte-identical `RouteDecision` output to the
  current, unmodified sort key on the same fixture inputs; (d) the point 5 tripwire test pinning the sort
  tuple's exact element count/order; (e) **new this round (R2-F-08(a))** — a dedicated test confirms
  `role_class`'s pre-sort consultation is exactly as scoped: for a `role_class == "review"` decision, the
  `writer` identity is resolved and feeds both `REVIEW_PROVIDER_CONFLICT` and sort position 1 before this
  contract's own element is ever reached; for `"writer"`/`"other"`, no such pre-sort branch exists.
- **AC-05.** The single-resolver-reused-not-duplicated assertion (one function, multiple call sites, same
  object identity or equivalent single-source-of-truth proof, not two independently maintained copies) over all
  four closed class values.
- **AC-06 (new this round, R2-F-06 — was entirely uncovered before).** Each restated negative gets its own
  explicit, individually falsifiable check, not a single blended "nothing else changed" assertion: no change to
  `008-P1` doctrine/generated text (a diff of the three generated orchestrator copies against their
  pre-package-start content, outside this contract's own changed files, stays empty); no change to
  `[areas.<duty>]`'s static resolution (`models_config.resolve_role`'s return value for a fixed
  role/profile/config is asserted byte-identical whether or not this contract's sibling config file is present
  — proving presence of a `model-preference.toml` file has literally zero effect on the OLD mechanism, the
  mirror image of AC-04(c)'s proof that absence of one has zero effect on the sort); no change to
  `codex_orchestrator()`'s return value under the same before/after sibling-file-presence check; no
  unconditional read of `provider_exhausted` (a test asserts this contract's own new code path never calls
  `self.store.provider_exhausted` directly — only the pre-existing conditional call at `service.py:143`,
  untouched, does); no `PROVIDER_BILLING_KIND` reference anywhere in this contract's own new module(s) (a
  source-inspection assertion, not a behavioral one — grep-equivalent, asserting the string is absent from the
  new files' source); no new `routes.v1.toml` rows (a checksum/row-count assertion: the file's row count and
  provider set are unchanged by this package's diff); the `grunt`-class and (new this round) `decision`-class
  and `build`'s-five-non-tiered-roles inertness are covered by AC-01's own tests above, not re-asserted here.
- **AC-07 (R2-F-06 — narrowed given honest scope, and now has an explicit bullet instead of none).** There is
  no additional runtime test beyond AC-04(d)'s tripwire — `008-P3` does not exist as code yet, so there is
  nothing to compose against today. What IS verified: the tripwire test's sort-tuple-shape pin (AC-04(d)) is
  confirmed to cover `build`'s live pair (`implementer`/`debugger`) specifically, since that is the only
  in-scope class where a future `008-P3` element would ever coexist with a LIVE `014` element on the same
  decision — for `decision`/`grunt`, the tripwire still fires on any shape change (protecting future-tiered
  roles too), but there is no current live interaction to additionally prove.
- **AC-08.** The new `bias_class`/`preference_configured` `RouteDecision` fields, asserted present and
  correctly populated on both an executable and a non-executable decision; **new this round (R2-F-09)** — a
  dedicated test asserts `bias_class` and the pre-existing `role_class` envelope key
  (`set_agents_app.py:440`) are both present, simultaneously, in the same `cmd_route_decide` JSON envelope,
  with their independently correct, disjoint-vocabulary values (`{"decision","grunt","build","unscoped"}` vs.
  `{"writer","review","other"}`) — proving the coexistence is intentional and non-colliding, not merely that
  the rename avoided a string clash by luck. **New this round (R3-F-05)** — a dedicated test exercises all four
  early-refusal sites individually (`service.py:107`, `:112`, `:119`, `:125`, plus the `:130` `conflicts`
  path) and asserts `bias_class is None` for exactly the two before `service.py:113`
  (`:107`, `:112`) and populated for the other three (`:119`, `:125`, `:130`) — including the two
  `reason_codes=("FACTS_INCOMPLETE",)` sites (`:112` and `:130`) asserted to differ in `bias_class` despite
  sharing the identical reason code, so the test cannot be satisfied by branching on `reason_codes` alone.
- **AC-09 (R2-F-06 — was implicit, now explicit).** Not a unit test — a required package-acceptance-time
  checklist item, re-verified live, not assumed from this spec's prose: (a) the ADR file exists on disk at
  whatever path/number was actually claimed at ADR-write time; (b) `docs/adr/README.md` carries a matching row
  with `Status = Accepted`; (c) the ADR number cited in (a)/(b) was confirmed against `docs/adr/README.md`'s
  live state at the moment the ADR was written, not copied from this spec's `0018`-at-spec-writing-time note.

`git diff --check` · ownership vs. baseline.

**Test isolation (round-1 finding F-09, medium — fixed):** every new test in this contract follows the same
hermetic pattern `tests/test_routing.py` already establishes for `RoutingStore` (`tempfile.TemporaryDirectory()`
+ `RoutingStore._for_tests(root)`, never the real `~/.local/state/set-agentes/`) and for `RoutingService`
(`routing._compose_for_tests`/`RoutingService._for_tests`, real on-disk `routes.v1.toml` + injected, not
live-probed, inventory — `ai/scripts/routing.py:31-40`). This contract's own sibling config file gets the same
treatment: every test that reads or writes it does so against a `tempfile.TemporaryDirectory()` path
substituted for `STATE_DIR` (monkeypatch or an explicit-path parameter, mirroring how `RoutingStore._for_tests`
takes an explicit root rather than trusting an environment default), so no test run ever reads, writes, or
depends on the real machine's actual sibling file or `config.toml`.

**This feature's own fixture-that-would-fool-it, named explicitly per the faithfulness rule — rewritten again
this round (R3-F-01, because round 2's own version of this section was itself fooled by exactly the fixture
class it warns about).** A hermetic test that only exercises `RoutingService._for_tests`'s synthetic
snapshot/inventory (never the real `routes.v1.toml`/`models.toml`) would go green on every AC above even if the
real, on-disk `routes.v1.toml` still only carried two providers — proving the sort-key mechanics without ever
proving the mechanism has any effect on this machine's real, current candidate set. **Round 3's own correction
is a second, sharper instance of this exact failure mode, and is named honestly here rather than only in the
Historial:** round 2's version of this section (quoted and retracted below) claimed a `build`-class preference
"measurably changes `implementer`'s selected route... live, on the real catalog" — that claim was true only
against a synthetic test inventory with `("opencode","anthropic")` authenticated (mirroring
`tests/test_routing.py`'s own generous default fixture), never against this machine's real, live probe result.
**Corrected fixture-that-would-fool-it rule, going forward: any test backing a "real-world effect" claim in
this spec must use an inventory shaped like this machine's actual live probe (no
`("opencode","anthropic")` key), never `tests/test_routing.py`'s own default `setUp` fixture** — the same
faithfulness requirement `015`'s own AC-01 states explicitly for its own tests, adopted here for the identical
reason.

- **What CAN be honestly proven, live, against the real catalog today:** **mechanism correctness across all
  four classes alike, and nothing more** — a `decision`-class preference for `"anthropic"` measurably changes
  `orchestrator`'s selected route at the `balanced` tier **when tested against a synthetic inventory with both
  providers authenticated** (today's default order is `openai-codex` first, per Contexto), observed in the
  returned `RouteDecision` when `RoutingService.route()` is invoked directly for `role="orchestrator"`. **This
  is real and correctly demonstrates the sort-key mechanism works uniformly — it is explicitly captioned as a
  mechanism-correctness proof, not a real-world-effect proof**, both because the shipped orchestrator doctrine
  never invokes `--route-decide` for `orchestrator` in actual operation, AND — new this round — because even a
  role for which `--route-decide` genuinely IS invoked (`implementer`, `debugger`) shows the SAME
  synthetic-inventory dependency: against this machine's real, live credential shape, neither role's
  `RouteDecision` changes at all (see AC-01(iv)). **There is no role, of 28, for which this contract's
  preference measurably changes a `RouteDecision` computed against the real, live primary-lane catalog today —
  round 2's claim that `implementer` was such a role is retracted (R3-F-01).**
- **What CANNOT be honestly proven today, restated and sharpened (this round corrects round 2's own R2-F-07
  resolution, which itself rested on the now-retracted claim):** no test in this contract's Verificación can
  honestly claim a real, live `RouteDecision`-level change on the primary lane today, for any class — this is a
  stronger, more honest statement than round 2's "the `RouteDecision` boundary is proven, only the spawn layer
  isn't." Both boundaries are unproven live today: the `RouteDecision` layer, because `PROVIDER_UNAUTHENTICATED`
  removes every `anthropic` candidate before the sort key runs, leaving nothing to reorder (AC-01); and the
  spawned-agent layer, for the same downstream reason round 2 already identified (the shipped doctrine's
  off-lane/hard-denial handling — see Non-goals) — which is moot today anyway, since the `RouteDecision` layer
  never even produces an `anthropic` result to hand it. **Conclusion, stated precisely: this contract's proof
  obligation today is exactly the mechanism-correctness proof (synthetic inventory, all four classes, uniform
  behavior) plus the real-world zero-effect proof (live-machine-shaped inventory, byte-identical output) — both
  fully deliverable and required by AC-01/AC-04's own tests — and nothing claiming more than that.** The
  moment `015` ships (`### Dependency on 015`, Contexto), `build`'s two tiered roles and `grunt`'s four tiered
  roles gain a real `RouteDecision`-level proof obligation this contract's own tests do not yet need to (and
  today, honestly, cannot) satisfy — named here as the concrete trigger for revisiting this section, not left
  implicit.

## Historial de challenge

### Round 1 — `revision_required` (13 findings, F-01..F-13)

Verdict: `revision_required`. This was a MAJOR revision, not a refinement — one of the user's own answers to a
round-1 open question widened the contract's scope (a new `build` role-class covering the seven writer roles,
using the same mechanism), which is why this file bumps to contract **2.0.0**, not a 1.x patch. Disposition of
every finding:

- **F-01/F-10 (blocking + medium, `grunt`-class inertness)** — user decision: keep `grunt` exactly as scoped,
  documented as provably inert on today's two-provider catalog, and proven inert by a dedicated regression
  test rather than left as a silent gap. See AC-01, AC-06.
- **F-02 (blocking, correctness/data-loss bug)** — fixed by moving the per-user config to a dedicated sibling
  file with its own genuine nested-TOML writer, never routed through `write_app_config`'s flat-only serializer,
  with a required round-trip regression test. See AC-02.
- **F-03 (blocking, architecture)** — user decision: accept "per-harness-install" scope, not a genuine
  per-project layer (`models.toml`/`roles.tsv` are `HARNESS_HOME`-owned per Accepted `ADR-0008`). Precedence
  chain corrected from four levels to two real ones. See AC-02, Non-goals.
- **F-04 (blocking, architecture — absent design decision)** — resolved in-spec via `### Design decision`
  (Contexto) reconciling this contract with `ADR-0003`, plus a new AC-09 requiring a dedicated ADR as a
  delivery criterion, mirroring `008-P1`'s AC-10 and `012`'s AC-12 precedent.
- **F-05 (medium, evidence-integrity)** — all five architect findings (F-07..F-11) from the same
  `decisions-log.jsonl` entry are now read and reconciled explicitly in Contexto, not only F-07.
- **F-06 (medium, superseded by the scope-widening)** — investigated and resolved: writer-role decisions flow
  through `RoutingService.route()`'s exact same sort key as `decision`/`grunt` decisions; the `build` class
  reuses AC-04's single integration point unchanged. See Contexto `### The architectural question`, AC-04.
- **F-07 (medium, undefined states)** — all three states defined with reused, cited fail-closed precedents.
  See AC-02.
- **F-08 (medium, observability)** — new AC-08, two new `RouteDecision` fields, additive and backward-compatible.
- **F-09 (medium, flaky test risk)** — test isolation pinned to the existing `tempfile.TemporaryDirectory()` +
  `_for_tests` hermetic seam precedent, extended to this contract's own sibling config file. See Verificación.
- **F-10-attribution (low-medium, wrong causal claim)** — AC-04 point 1 corrected to attribute the
  same-provider-as-writer guarantee to the `service.py:166` hard exclusion, not to the (vestigial) sort-tuple
  position 1.
- **F-11/F-05-quota-risk (blocking-ish, accepted by user)** — quota-exhaustion-exposure risk stated explicitly
  in Non-goals as accepted, unchanged from today, closing automatically once `011` lands.
- **F-11-tripwire (medium, forward-compatibility)** — AC-04 point 5, a regression test pinning the sort tuple's
  exact shape, added.
- **F-12 (low, citation)** — `roles.tsv:3-8` corrected to `roles.tsv:4-8,10` everywhere it appeared.
- **F-13 (low, precision)** — `PROVIDER_EXHAUSTED`'s `self.store is not None` condition now stated explicitly
  wherever cited; `models.toml` cited with its real full path everywhere, with an explicit note distinguishing
  it from the decoy `tests/fixtures/models.toml`.

**The scope-widening itself, stated once more, plainly:** the user's own words — *"Quiero que un rol no tenga
hardcodeado ningun modelo"* and *"También quiero influir en quién implementa"* — moved this contract from a
two-class taxonomy covering 13 of 28 roles to a three-class taxonomy covering 20 of 28 roles, adding the
`build` class and its own AC-01 bullet, its own share of AC-02/AC-03/AC-04's invariants, and its own
fixture-that-would-fool-it proof in Verificación. Everything round 1 confirmed correct and listed under "Verified
clean" stands untouched: the 007-P0 precedent's representation; the real (pre-insertion) sort tuple structure
(4 elements, independence boolean at position 1); AC-01's original `decision`/`grunt` arithmetic (28 roles, 7
decision, 6 grunt); the dependency claims on 008-P1/012-P1; the three already-confirmed product decisions from
before round 1 (Kimi out of scope; `adversarial-judge` → `grunt`; `decision` = all six `duty=docs` roles).

### Round 2 — `revision_required` (9 findings, R2-F-01..R2-F-09) — a real DESCOPING, not a refinement

Verdict: `revision_required`, 2 of 9 findings blocking (R2-F-01, R2-F-02). **Stated as plainly as round 1's own
widening was stated: this round is the mirror image of round 1.** Round 1 widened the contract (13→20 roles,
new `build` class) because the user asked for more. Round 2 found that, of the 20 roles the taxonomy now
covers, only **2** — `implementer` and `debugger` — have real, live, observable effect on today's roster and
catalog; every other covered role is either structurally unreachable (not dynamically tiered, per the shipped
orchestrator doctrine's own "tiered roles" list) or tiered-but-provably-inert (`grunt`'s four tiered roles,
hard-excluded by `REVIEW_PROVIDER_CONFLICT`). This file bumps to contract **3.0.0**, not a 2.x patch, because
the user's own resolution changes what the contract is honestly claimed to deliver, not merely how it is
worded — exactly the same bar round 1's own 1.0.0→2.0.0 bump used, applied in the opposite direction. **Three
user decisions this session reshaped scope**, resolving the two blocking findings and reframing the rest:

1. **On R2-F-01 (no anthropic-backed spawnable variant exists in any of the 3 lanes today — the shipped
   doctrine discards any routed decision with `provider != "openai-codex"`):** the user spun this off as a
   separate, urgent feature, **`015-anthropic-dispatch-parity`** (spec-drafted in parallel this same session,
   by a different agent). `014` does not fix this gap and is rewritten not to depend on it being fixed — its
   own anthropic-directed preferences are fully specified and functional as of this contract, and will start
   having real, spawn-level effect the moment `015` ships, with zero code change to `014`, because `014` never
   edits routing/doctrine, only a sort-key bias consulted strictly after routing already happened. **Learned
   after round 2 closed, while this revision was already underway (from `015`'s own parallel investigation,
   `docs/specs/015-anthropic-dispatch-parity/spec.md:154-229`):** the gap is worse and more urgent than round
   2's framing suggested — the reviewer-independence guarantee `REVIEW_PROVIDER_CONFLICT` exists to provide is
   **already silently defeated in production today**, not a future risk tied to the subscription mix changing
   in twelve days; corrected everywhere this file discusses it (Non-goals, Contexto, Verificación). See
   Non-goals for the full finding.
2. **On R2-F-02 (only 6 of 28 roles are dynamically tiered — flow through `RoutingService.route()`'s sort at
   all in real, shipped operation — everything else is spawned as a static BASE agent, per the orchestrator
   doctrine's own "tiered roles" list, never touching this contract's mechanism):** the user chose **"honest
   scope"**, verbatim: *"Por el momento me conformo con los 2 roles reales con modelos Hardcodeados, si es que
   lo ves bien asi"* — the taxonomy (`decision`/`grunt`/`build`/`unscoped`) is NOT narrowed, kept in full for
   the same "no role hardcoded by construction" reason round 1 already established, but its real, current,
   observable effect is now stated precisely, prominently, and per-role, not blended into one "grunt is inert"
   claim the way round 1 left it. See `### Honest scope` (Contexto) and the rewritten AC-01. **Re-verified this
   round, and found MORE PRECISE than round 2's own summary implied** (see AC-01): the "only 6 roles reachable"
   fact is an OPERATIONAL/doctrine fact (the shipped orchestrator doctrine never invokes `--route-decide` for
   the other 22 roles), not a code-level `RoutingService.route()` restriction (the CLI/service are role-agnostic
   by design and would reorder any role's candidates if invoked) — this contract's own regression coverage is
   split accordingly between a mechanism-correctness proof (all 28 roles, uniform) and a real-world-reachability
   proof (doctrine citation for 21 roles; `service.py:166` hard-exclusion test for `grunt`'s 4 tiered-inert
   roles) — a more precise, more defensible claim than a single blended "byte-identical for everyone" assertion
   would have been. **A second idea the user floated and explicitly deferred, not built now:** a future
   lightweight "gateway" agent fronting every role so only one agent in the system ever has a hardcoded model —
   recorded in `## Future work`, not designed here.
3. **On configuration (R2-F-04, blocking — the config-writing mechanism was entirely unspecified):** the user
   chose a new CLI subcommand, not a hand-edited file. `AC-02` now specifies `--model-preference-set CLASS
   --provider NAME [--provider NAME ...]` and `--model-preference-role-override ROLE CLASS`, backed by a small,
   purpose-built, closed-schema TOML serializer (not a general nested-TOML writer — R2-F-04's actual concern —
   because this file's two-table schema is fully owned and controlled by this contract), sharing its validator
   functions with the config-load path so a malformed value can never even be written, and emitting a
   non-blocking `MODEL_PREFERENCE_NOTE` when the configured class/role is currently inert.

**Every other round-2 finding, disposition:**

- **R2-F-03 (medium, `build`'s predicate wasn't provably identical to the code it claimed to reuse)** — fixed:
  `build` is now defined by the literal, single-conjunct predicate `capability == "code-rw"` (`service.py:221`),
  matching `grunt`'s already-correct pattern; membership unchanged (verified: every `code-rw` row also carries
  `duty == "implement"` and vice versa, `roles.tsv:11-17`). See AC-01.
- **R2-F-05 (the composition-with-`[areas.<duty>]` question)** — simplified to near-nothing by honest scope: no
  composition question exists for the 21 roles this contract never reaches (their static default is the ONLY
  thing that ever governs them). For the 2 real `build` roles, resolved precisely, not assumed: `[areas.implement]`
  plays a role ONLY on the off-lane-degrade fallback path (spawn the BASE agent when the routed decision names
  `anthropic`) — on an on-lane decision, the spawned variant is matched by the routed decision's own model,
  never falling back to the static default. The two mechanisms govern disjoint outcomes of the same decision,
  never both at once. See `### Honest scope`, Contexto.
- **R2-F-06 (medium, AC-09's ADR requirement and AC-06/AC-07's negative assertions had no Verificación
  coverage)** — fixed: Verificación now has explicit, individually falsifiable bullets for AC-06 (each negative
  restated as its own testable check, not one blended assertion), AC-07 (narrowed to what's actually left to
  verify given honest scope — nothing beyond the existing tripwire, since `008-P3` doesn't exist as code yet),
  and AC-09 (a required package-acceptance-time checklist item: ADR file exists, `docs/adr/README.md` row
  matches, ADR number re-checked live, not assumed from spec-writing time).
- **R2-F-07 (low-medium, the anti-fooling test measured the wrong layer — green even when the actually-spawned
  agent's model is unchanged)** — resolved, not merely carried forward: rewritten to distinguish what CAN be
  honestly proven today (the sort-key mechanism correctly reorders `RouteDecision` — for `build`'s live pair,
  this IS the closest thing to a real-world-effect proof, since `--route-decide` genuinely is invoked for them
  in shipped operation) from what CANNOT (a genuinely different SPAWNED model for an `anthropic`-directed
  preference, blocked today by the same pre-existing, `015`-owned gap regardless of this contract). This
  contract's own proof obligation now stops precisely at the `RouteDecision` boundary, stated as a conclusion,
  not left as an unresolved caveat. See Verificación.
- **R2-F-08 (low, four citation/precision errors)** — all four fixed: (a) "`role_class` consulted only after
  the sort" restated per `role_class` — true for `"writer"`/`"other"` (`build`/`decision`), false for
  `"review"` (`grunt`), which pre-sort-consults `role_class` to resolve the writer identity feeding both
  `REVIEW_PROVIDER_CONFLICT` and sort position 1 (AC-04). (b) `RouteDecision(` call-site count corrected to 14
  (re-counted live). (c) `RouteDecision` dataclass range corrected to `domain.py:165-178`. (d) the
  `models_config.py` fail-closed precedent for AC-02 restated accurately (one generic message covering ~6
  unrelated validations, `models_config.py:197-201`) with this contract's own new validation specified as
  small, per-token, and well-scoped instead — not a reuse of that generic message.
- **R2-F-09 (low, naming collision)** — fixed: AC-08's new field renamed `preference_class` → `bias_class`,
  with the coexistence with the pre-existing `role_class` envelope key (`set_agents_app.py:440`,
  `{"writer","review","other"}`) stated explicitly and covered by a dedicated regression test, not merely
  avoided by luck.

**What round 2 independently confirmed correct, unchanged by this round:** the core `RoutingService.route()`
mechanism claim (one candidate list, one sort — now correctly scoped per `role_class` for the pre-sort
consultation nuance, R2-F-08(a)); the 28-role partition arithmetic structure; AC-04's corrected F-10
attribution; AC-08's dataclass-safety claim (now under its new field name); the honest `## Historial de
challenge` framing — this round keeps being honest, and says so plainly: this is a real descoping to what is
honestly deliverable today, not a refinement, not a widening, and not a retreat from the taxonomy itself (which
stays exactly as wide as round 1 left it, for the same reason). Not re-litigated, per the assignment's own
instruction: Kimi-out-of-scope, `adversarial-judge`→`grunt`, and the six-role `decision`-class definition — all
still stand as taxonomic definitions, even though `decision`'s real-world effect is now stated as currently
zero, precisely and for the right reason (operational non-invocation, not a code-level defect).

### Round 3 — `revision_required` (8 findings, R3-F-01..R3-F-08, 2 blocking) — a correction pass, not a
rescope, that also surfaces a genuinely good update

Verdict: `revision_required`, 2 of 8 findings blocking (R3-F-01, R3-F-02). **Stated as plainly as round 1's
widening and round 2's descoping were both stated: this round is neither.** It is a **correction pass** — every
acceptance criterion, class definition, role count, and invariant round 3's own challenge confirmed clean is
left untouched (see the "do not touch" list below); what changed is that two of this contract's own factual
claims about its real-world effect were wrong, inherited from an earlier, since-superseded draft of a sibling
feature, and never independently re-verified against this machine's actual live state before being asserted
here. This file bumps to contract **3.1.0**, not a 3.x-only wording pass and not a new major version — no
scope was added, removed, or rescoped; only what is TRUE about the mechanism's current, real-world reach was
corrected.

**The two blocking findings, disposition:**

1. **R3-F-01 — round 2's "2 real roles" claim (`implementer`/`debugger` have real, live effect today) is FALSE
   on the primary lane, verified live, not guessed.** `('opencode','anthropic')` probes to zero models on this
   machine (`opencode auth list --pure` / `opencode models anthropic --pure`, both re-run live this round). On
   `opencode` (`[runtime].primary`), `PROVIDER_UNAUTHENTICATED` excludes every `anthropic` candidate for EVERY
   role at EVERY tier, so `candidates[0]` is fixed to the sole surviving `openai-codex` candidate regardless of
   this contract's sort-key bias — **zero live effect on the primary lane today, for all three classes, no
   exceptions.** Fixed in the header, `### Honest scope`, the new `### Dependency on 015` subsection, Alcance,
   AC-01's `grunt`/`build` bullets, and the Verificación/fixture-that-would-fool-it sections (all rewritten to
   require an inventory shaped like this machine's real probe, not a more generous test fixture). **The genuinely
   good news this finding surfaces, not just a correction:** `015-anthropic-dispatch-parity` was completely
   redesigned in parallel this session (now its own contract **2.0.0**,
   `docs/specs/015-anthropic-dispatch-parity/spec.md`, pre-challenge as of this citation) around a cross-lane
   provider redirect whose own AC-01 states it applies "for both writer and review decisions" — meaning once
   `015` ships, `014`'s `build` class (`implementer`/`debugger`) AND `014`'s `grunt` class (its 4 tiered roles)
   BOTH gain real effect, not just `build` as round 2 believed, with zero code change to `014`. `014`'s
   `decision` class (0 tiered roles) stays permanently inert regardless, since the reason it is inert is
   operational (doctrine never invokes `--route-decide` for it), not credential-related — `015` cannot help it.
   The one live, real, verified-this-round exception to "zero everywhere today" is the `pi` lane (not
   `[runtime].primary`): both `('pi','anthropic')` and `('pi','openai-codex')` probe live (verified by directly
   running the same probe command `_PAIR_COMMANDS` uses), named precisely as a real-but-out-of-the-main-path
   exception, not the contract's headline claim.
2. **R3-F-02 — the "already silently defeated in production" claim `014` imported from `015`'s own round-1
   draft is confirmed WRONG and outdated; `015`'s own round-1 challenge already corrected this before `014`'s
   3.0.0 was written.** Read directly from `015`'s current spec (`docs/specs/015-anthropic-dispatch-
   parity/spec.md` §D.1, a live hermetic reproduction) and from the shipped doctrine's own text
   (`Global/_canonical/agents/orchestrator.md:199-205`): a routed review decision needing `anthropic` for
   provider-diversity does not silently degrade to a same-provider reviewer — it hits zero candidates and
   returns `REVIEWER_INDEPENDENCE_UNAVAILABLE`, which the doctrine's own fail-closed HARD DENIAL branch HALTS
   on, raising `HUMAN_DECISION_REQUIRED`. Fixed in all four places the wrong framing appeared (header, Non-goals,
   Contexto's `### Honest scope`/AC-01 cross-references, and the `### Honest scope` "grunt" bullet) — restated
   as the real, verified, fail-CLOSED availability/liveness problem it is (reviews cannot run when only one
   provider is available), not a fail-open security defeat.

**The six lower-severity findings, all mechanical, all fixed:**

- **R3-F-03** — AC-01's `grunt`-class mechanism description ("one provider survives, nothing to reorder")
  corrected to the real, live shape on the primary lane today (zero survivors, `REVIEWER_INDEPENDENCE_
  UNAVAILABLE`, a refusal); the regression test's assertion strengthened to check `reason_codes` explicitly,
  not just `RouteDecision` equality, so a future reader sees the day this shape changes.
- **R3-F-04** — AC-02's five previously-undefined CLI write/read states defined: config-load parse failures
  fail closed (never `app_config()`'s silent-`{}` pattern); `--model-preference-set` with zero `--provider`
  values is an error; `--provider` without `--model-preference-set` is an argparse-level co-required error;
  duplicate `--provider` tokens are rejected, reusing `models_config.py:198`'s existing duplicate-rejection
  precedent; `--model-preference-show` (read-only) added, with removal/unset explicitly deferred and named as
  a real, honest tension in Non-goals rather than hidden. Atomic write (temp file + rename) required, replacing
  the plain-`write_text` anti-pattern `write_app_config` currently uses.
- **R3-F-05** — AC-08's `bias_class` population precision corrected: `role_class` is computed at exactly
  `service.py:113`; `bias_class` is `None` only for the two refusals strictly before that line (`:107`, `:112`,
  both `FACTS_INCOMPLETE`); it IS populated for every refusal reachable only after it, including both
  `REVIEW_IDENTITY_INVALID` refusals (`:119`, `:125`) AND a previously-uncounted third refusal, the `conflicts`
  check at `:130` (also `FACTS_INCOMPLETE`, but post-resolution) — so `reason_codes` alone cannot predict
  `bias_class`'s presence.
- **R3-F-06** — AC-01's doctrine-consistency check extended from the canonical file alone to all FOUR
  orchestrator-doctrine files (canonical plus its three generated copies), reusing the same read-all-copies
  pattern the existing `tests/test_harness.py:2864-2895`
  (`test_orchestrator_doctrine_branches_on_route_decide_reason_taxonomy`) precedent already establishes for a
  different string, rather than inventing a new check shape.
- **R3-F-07** — the Audit's "not verified against a spec that does not exist yet" self-contradiction fixed:
  `015`'s spec.md exists and was read directly; the real residual uncertainty restated as "`015`'s design was
  in-flight/pre-challenge at the time of citation," not that the file was hypothetical.
- **R3-F-08** — four citation fixes: (a) `roles.tsv` citations disambiguated with its real full path
  `/home/federico/SET-AGENTES/roles.tsv`, matching how `models.toml` was already disambiguated from its own
  `tests/fixtures/` decoy; (b) AC-02's "six conditions OR'd into one `if`" corrected to the actual count, ten
  boolean sub-conditions across five fields; (c) the Audit's `find Global -iname orchestrator.md -o -iname
  orchestrator.toml` sweep corrected from "three-lane universe" to the real four-file count (canonical
  included); (d) `to_dict()`'s citation corrected — `def to_dict(self):` is at `domain.py:177`, its `return`
  body at `:178`, cited together as `:177-178`.

**What round 3 confirmed correct, untouched by this round (the "do not touch" list, respected in full):** the
sort-key integration point and its five invariants (AC-04); the `build`-class predicate fix from round 2
(`capability=="code-rw"` alone, `service.py:221`); the 28-role partition arithmetic (`decision`=7, `grunt`=6,
`build`=7, `unscoped`=8); AC-08's dataclass safety and the `bias_class` rename (only R3-F-05's precision was
fixed, the field and its rename stand); AC-02's sibling-file architectural premise (only R3-F-04's undefined
states were fixed, the file mechanism itself stands); the "gateway V2" forward note (`## Future work`);
Kimi-out-of-scope; `adversarial-judge`→`grunt`; the six-role `decision`-class definition.
