# Feature 008 — dynamic-selection, contract 1.4.0

Status: P1 contract drafted. P2 reverted 2026-07-30 to its original uncontracted scoping paragraph after
three spec-challenge rounds inside this document (19 → 8 → 4 findings, all resolved) reached
`ready_for_user_approval` and then hit a hard structural wall: `cmd_init`'s frozen `acceptance_criteria` list
on this feature's state file (`AC-01..AC-10`, P1's, with real accepted history) cannot host it without
`--force`, which would destroy that history. The fully challenged contract now lives in its own feature,
`docs/specs/012-discovered-inventory/spec.md` — see the one-line pointer in this file's P2 section and
`ai/state/decisions-log.jsonl` slug `p2-discovered-inventory-pasa-a-ser-su-propia-feature-012`. P3 remains
scoped but not contracted — P3 depends on `007-P2` and, for its provider-category layer, on
`012-discovered-inventory`.

## Contexto

The user's instruction, verbatim (2026-07-28):

> *"No quiero que exista ese 'excel' o base en donde el orquestador elija los modelos que ya están asociados
> a los agentes y subagentes en ese excel. Quiero que sea dinámico: que el orquestador analice la tarea, vea
> la lista de agentes o subagentes habilitados en el entorno, y elija el más conveniente, con el esfuerzo
> lógico asociado. Y que si el subagente se queda sin tokens en el plan (como puede pasar con Claude), el
> orquestador re-instancie el proceso con otro modelo."*

Three capabilities are being asked for, and they have different dependencies. This contract covers the one
that depends on nothing and hurts today.

### What is actually broken (verified, not assumed)

**The spare route is computed, persisted, and then made unreachable.** Every routing decision records a
fallback identity in its `dispatches` row. `mark_dispatched` (`ai/scripts/routing_core/store.py:805`,
citation corrected 2026-07-30, F-16: the file grew when `provider_exhaustions` landed under `011`, shifting
these lines) sets `fallback_window_open=0` in the same UPDATE that dispatches the run, and `consume_fallback`
(`store.py:812`) requires `state='authorized' AND fallback_window_open=1`. `consume_fallback` has **no
production caller** — `grep -rn "consume_fallback" --include=*.py .` outside `tests/` returns only its own
definition. So the fallback is reachable only in the window *before* dispatch, which is precisely not when a
provider runs out of tokens.

**The harness cannot tell "out of quota" from "failed".** Every in-turn error collapses into one bucket,
`PI_TURN_ERROR` (`ai/scripts/set_agents_spawn.py:281`). Plan exhaustion, a model refusing, a rate limit and a
bug in the task are indistinguishable. Without that distinction there is nothing to branch on: "re-instantiate
with another model" and "report the failure" cannot be told apart.

The exhaustion signature is on record and does not need to be guessed —
`docs/specs/004-adaptive-dispatch/evidence/P3-implementation.md:173` captured it live:
`400 {"type":"error","error":{"type":"invalid_request_error","message":"You're out of extra usage. …"}}`.

### The tension this contract does not resolve by deleting

The catalog is what makes routing auditable: each decision carries a `route_id`, and the service revalidates
that identity against a freshly built snapshot before every durable authorization
(`routing_core/service.py:177-181`). Free-form model choice has no identity to revalidate, so two identical
tasks could receive different models with no way to distinguish judgment from drift.

The legitimate half of the complaint is narrower and is accepted: today the catalog is a **hand-written
inventory of two providers** that does not reflect what is actually available where the harness is standing.
The resolution is that the inventory becomes **discovered** rather than declared (P2), and that selection over
that inventory is a recorded decision with a stated rationale — not that the record disappears.

Related, and stated so it is designed for rather than discovered later: an orchestrator asked whether a task
deserves more compute will answer yes. Budget must therefore be a ceiling enforced in code, never advice in a
prompt. That is why P3 depends on `007-P2` — a ceiling needs a measured spend to sit above.

## P1 — uninterrupted-delegation (doctrine)

Revised after SPEC_CHALLENGE (15 findings, 7 blocking) and the user's follow-up. The original P1 was an
automatic in-code failover; the challenge proved it cannot reach the case that motivated it, and the user
then named a second, larger problem. Two later amendments — the AC-05 scope correction and the AC-10 ADR
number — are recorded inline at the criterion each one changes, not in a separate log.

**Why this package is prose and not code.** `ai/scripts/set_agents_spawn.py` is the harness's only spawner
and it is pi-only: `route_and_spawn` pins `selected_runtime: "pi"` (`:329`) and builds `pi_pinned_argv`
(`:243`). For OpenCode, Claude Code and Codex there is no harness-controlled subprocess — nothing to
classify an error in, nothing to re-launch. The user's actual pain (a Claude Code subagent running out of
plan tokens) lives entirely outside the code path. The lever that exists there is the orchestrator's own
behaviour, which is doctrine.

The contract: a long session stays walkable. The harness's promise is that every decision is delegated,
implemented and audited without the developer typing "dale, continuá".

### The three defects this closes

1. **Pauses that ask for nothing.** Observed by the user in OpenCode: the orchestrator finishes a subagent,
   reports, and stops with *"necesito de vos: NADA"*. `CLAUDE.md` already forbids asking about routine test
   failures, gate reruns, required repairs, or continuing approved package work — the doctrine exists and is
   not being followed, because nothing states the rule in the negative: **a turn that has nothing to ask must
   not end.**
2. **A dead subagent ends the work.** With no spawner to intercept, only the orchestrator can notice a
   subagent that died on quota and relaunch it.
3. **One unusable provider stops the review pipeline entirely.** Reviewer independence requires the reviewer
   not share the writer's provider (`service.py:149,155`, citation corrected 2026-07-30, F-16); with two
   providers and one gone, *no* reviewer is
   routable, so `PACKAGE_REVIEW` halts for every package, not just the failed spawn.
   **Corrected 2026-07-28 (RP-01 verification):** "gone" here means *absent from the inventory*, not
   *exhausted*. `probe_inventory` (`routing_core/catalog.py:305`) observes credentials and binaries, never
   quota, so an exhausted-but-authenticated provider stays routable and the exhaustion surfaces as a **dead
   spawn**, not as a decide-time denial. Defect 3 is therefore real for a provider that is logged out or
   unreachable; for an exhausted plan the live path is defect 2. Both are closed here, by different rules.

- **AC-01** — the orchestrator never ends a turn to report progress. A turn ends only when it has a question
  only the human can answer (per the `CLAUDE.md` question policy), when the work is done, or when it is
  blocked with `HUMAN_DECISION_REQUIRED`. "Here is what happened, shall I continue?" is a defect, not a
  courtesy.
- **AC-02** — when a delegated subagent dies from provider quota exhaustion, the orchestrator relaunches it
  once, with a different model, without asking. The relaunch and its cause are recorded
  (`log-narrative`), so the session record shows what happened without the session stopping to say it.
- **AC-03** — the relaunch is bounded at one per assignment. A second exhaustion of the same assignment is a
  real blocker and is reported as one.
- **AC-04** — when only one provider remains usable, the harness **warns once and keeps working**, selecting
  models within the surviving provider. Degraded is not stopped. The warning is recorded in state, not only
  printed, so it survives the session.
- **AC-05** — reviewer independence is redefined around the guarantee that actually holds. **The primary
  guarantee is a clean context**: a reviewer that never saw the implementation reasoning cannot defend it,
  cannot carry its sunk cost, and cannot approve work because it is its own. Cross-provider review remains
  preferred, but its absence no longer halts the pipeline.
  **Scope, corrected 2026-07-28 after review panel RP-01 (finding F-01, critical, upheld under adversarial
  refutation).** The first version of this note drew the boundary by *runtime* — "the pi lane keeps its hard
  denial, the other three relax" — and that boundary does not exist. `--route-decide` is runtime-agnostic:
  it defaults `selected_runtime` to `opencode` and accepts all four (`ai/scripts/routing_core/domain.py:20`,
  `ai/scripts/set_agents_app.py:390`), and the independence exclusion (`routing_core/service.py:149,155`,
  citation corrected 2026-07-30, F-16) fires wherever a recorded writer run is offered as `review_of_run_id`,
  in any lane —
  `tests/test_routing.py:554-571` drives `selected_runtime="claude-code"` and asserts exactly
  `REVIEWER_INDEPENDENCE_UNAVAILABLE`. So the discarded version would have relaxed, in prose, a rule the
  routing service still enforces in the very lanes it named.

  The boundary is drawn by **mechanism**: a `--route-decide` decision returning
  `REVIEWER_INDEPENDENCE_UNAVAILABLE` stays a HARD DENIAL that halts, in **every** runtime, exactly as
  `Tiered dispatch` step 3c states (asserted at `tests/test_harness.py:1333-1336`, inside
  `test_orchestrator_doctrine_branches_on_route_decide_reason_taxonomy`). This AC governs delegation
  that carries **no** routing decision: non-tiered roles, the benign `REVIEW_IDENTITY_UNVERIFIED` path, and
  sessions driven by the shared doctrine with no `--route-decide` in play. Making a *routed* reviewer degrade
  instead of halt is a routing-service change and is deferred to P1b/P2.
- **AC-06** — under single-provider operation the reviewer must use a **different model within that
  provider** than the one that implemented. Same provider is a weakened guarantee; same provider *and* same
  model is the weakest available and is not accepted while an alternative exists. This recovers part of the
  decorrelation for free.
- **AC-07** — a review performed without cross-provider independence is recorded as such on the package,
  permanently and visibly, with the reason. The cost of the degradation is that correlated blind spots
  survive: the same model family tends to make the same errors and to find the faulty reasoning natural. That
  is a real loss, it is accepted deliberately to keep the session moving, and it must be legible to whoever
  reads the package later.
- **AC-08** — exhaustion of *every* provider is `HUMAN_DECISION_REQUIRED`. That is the one stop this package
  keeps, because there is nothing left to delegate to.
- **AC-09** — the doctrine is generated into all three runtimes, not written once in the canonical prompt and
  lost. `./build.sh --check` proves the rule reached `Global/{opencode,claude-code,codex}`.
- **AC-10** — `docs/adr/0011-uninterrupted-delegation.md` records the design and, explicitly, the
  independence trade-off of AC-05..AC-07 and its reversal threshold, plus the pi-lane deferral of AC-05.
  (`0011` and not the next free number `0010`: `0010-spawn-accounting.md` is already reserved by the
  `007-P2` package record. This package lands first, so the index carries a temporary hole at 0010 that
  `007-P2` fills — a hole is recoverable, a collision on the same ADR number is not.)

## P1b — quota-failover (pi lane, code) — deferred

The original P1, kept for the lane where the harness does own the process. Deferred behind 007 for a concrete
reason found by the challenge: `store.py`, `set_agents_spawn.py`, `set_agents_app.py` and
`docs/adr/0005-*.md` are all claimed by live `007` packages, and `close_run` accepts no terminal reason
today, so expressing "closed because the plan ran out" requires editing `set_agents_app.py`, which `007-P2`
also edits. Sequencing beats a merge conflict in the audit state machine.

**Corrected 2026-07-30 (P2 spec-challenge, F-17).** This "deferred" framing is still literally accurate, and
must stay stated that way: the separately tracked feature `011-quota-failover` was opened and its code
landed (`provider_exhaustions` table, `store.py:410,698`; `close_exhausted_and_authorize_replacement`,
`store.py:709`), but per `docs/adr/0015-quota-failover.md` (`Estado: Proposed`, 2026-07-30) and the package's
own gate status it is **BLOCKED**, not `ACCEPTED` — the coordinator confirmed this directly. Nothing in `011`
supersedes or completes this P1b section; the code existing is not the same as the deferral being resolved. Any
later mention of `011` elsewhere in this document (see P2) must carry the same qualifier, not a bare "shipped."

The challenge also corrected three things this package must carry when it is written:
- Reopening `fallback_window_open` on a dispatched row is **not** forbidden by the `CHECK` at `store.py:404`
  (citation corrected 2026-07-30, F-16) — that CHECK constrains terminal states only. The real prohibitions
  are `consume_fallback`'s `WHERE` (`store.py:815`) and the decision in ADR-0005 (`:86-87`).
- Review decisions are never persisted as runs (`service.py:164`, citation corrected 2026-07-30, L-02), so a
  reviewer can never exhaust quota mid-spawn; the original AC-06 described an impossible scenario.
- The exhausted attempt was still billed (`docs/specs/004-adaptive-dispatch/evidence/P3-implementation.md:180`),
  so a failover silently doubles spend unless the failed attempt's usage is attributed — which needs `007-P2`.

### Original P1 contract (superseded)

- **OLD-AC-01** — provider quota exhaustion is classified as its own terminal reason, distinct from a generic
  turn error and distinct from a rate limit. A rate limit means *retry the same model later*; exhaustion means
  *this model is done for now* — conflating them either wastes retries or discards a working model.
- **OLD-AC-02** — classification is driven by the observed provider signature, and an unrecognized error stays a
  generic failure. Guessing "this looks like quota" from an unknown message is how a real bug gets silently
  retried on a second model and charged twice.
- **OLD-AC-03** — a run that terminates on exhaustion is followed by a fresh authorized run carrying the fallback
  identity, and the original run is closed honestly as a failure with its real reason. History is not
  mutated: the record must show that model A ran out and model B took over, not that model B was chosen all
  along. Reopening `fallback_window_open` on a dispatched run is explicitly rejected — the CHECK at
  `store.py:404` (citation corrected 2026-07-30, F-16) forbids it and rewriting a dispatched row erases the
  fact the audit trail exists to keep.
- **OLD-AC-04** — the exhausted provider is remembered for the rest of the session, so the next spawn does not
  select it again. Without this, every subsequent dispatch burns one failed spawn rediscovering the same
  exhaustion. The memory has an expiry and is per-provider, never per-model — a plan runs out, not a model.
- **OLD-AC-05** — the failover is bounded: one re-instantiation per run. A second exhaustion is a terminal
  failure the orchestrator reports, not a third attempt. Unbounded failover across providers is how both
  subscriptions get drained by one runaway task.
- **OLD-AC-06** — the separation-of-duties invariants survive the failover. In particular a reviewer
  re-instantiated after exhaustion must still not share the writer's provider or family
  (`service.py:149,155`, citation corrected 2026-07-30, F-16); if the only remaining provider is the writer's,
  the correct outcome is `REVIEWER_INDEPENDENCE_UNAVAILABLE`, not a review by a compromised reviewer.
- **OLD-AC-07** — the linkage between the failed run and its replacement is recorded. If that requires a schema
  column it is deferred to ride with `007-P2`'s schema change rather than opening a competing migration; in
  that case the linkage lives in the feature-state narrative for now and the deferral is stated in the ADR,
  not left implicit.
- **OLD-AC-08** — `docs/adr/0011-quota-failover.md` records the design, the rejected alternatives (window
  reopening; unbounded failover; per-model rather than per-provider memory), and the reversal threshold.

## Frameworks: why none of them

An outside review (2026-07-28) proposed LangGraph, CrewAI, Haystack, LlamaIndex and a vector database. All
are rejected on one invariant that predates this feature and is not negotiable inside it: **the harness has
zero external dependencies** — no `requirements.txt`, no `pyproject.toml`, no lockfile; `python3 ≥3.11` is the
whole requirement and the three CI platforms install nothing. Adopting any of them breaks "a guest clones it
and it works", which is feature 005's thesis. It is the same argument that rejected Claude Code's `Workflow`
in feature 006: the graph is expressed in harness data, never in a vendor's tooling.

Two of those proposals are also already satisfied, which is worth recording so they are not re-proposed:
the explicit state graph exists as `feature-state.py`'s phase machine with transitions declared as data and
persisted on disk (it outlives the process, which an in-memory graph does not), and planner/worker separation
exists as `package-planner` + `implementer` + a read-only orchestrator.

One proposal is actively worse than what exists: **Self-RAG**, where an agent grades and corrects its own
answer, is the failure mode this harness is built against — the implementer never approves its own work, and
`finding-verifier` (feature 006) goes further by requiring an independent role to *refute* findings with its
own evidence.

## P2 — discovered-inventory (scoped, not contracted)

Replace the hand-written provider rows with an inventory probed from the environment: what is authenticated
and reachable where the harness is standing, including OpenCode's own models (`kimi-k2.7-code`, `glm-5.2`,
and the free tiers) which the router cannot represent today because `ai/catalogs/routes.v1.toml` knows only
`openai-codex` and `anthropic`. Effort becomes a variable of the decision rather than a property of the tier
row. Selection stays a recorded decision with a stated rationale.

The full contract (AC-01..AC-12), already through three spec-challenge rounds and `ready_for_user_approval`,
was split out 2026-07-30 into its own feature — `docs/specs/012-discovered-inventory/spec.md` — because
`cmd_init`'s frozen `acceptance_criteria` list on this feature's state file cannot be extended without
destroying P1's accepted history (`ai/state/decisions-log.jsonl`, slug
`p2-discovered-inventory-pasa-a-ser-su-propia-feature-012`).

## P3 — budget-aware selection (scoped, blocked on 007-P2)

The orchestrator weighs task responsibility against remaining session budget, and picks *"el subagente
indicado, con el modelo dentro de todos los que existan disponibles, con mayor probabilidad de ejecutar esa
tarea lo mejor posible al costo de tokens/tiempo/calidad más eficiente"* (user, 2026-07-28).

Three dependencies, all real:

- **Cost.** No provider reports remaining quota to the harness, so "remaining" is necessarily a declared
  budget minus measured spend — which is what `007-P2` builds. The ceiling is enforced in code, never as
  advice in a prompt, because an orchestrator asked whether a task deserves more compute answers yes.
- **Quality.** `metric_rollups` already accumulates per-model outcome counts and **nothing outside
  `store.py` reads them** (verified 2026-07-28). Selecting for "best result per token" needs that signal
  connected; today it is written and rots. `007` names this gap and deliberately does not close it.
- **Provider category.** `012-discovered-inventory`'s `subscription`/`metered` provider-keyed map (AC-08,
  renumbered when that contract split out of this file's P2 section — see the pointer there) is the input to a
  two-layer selection model, decided with the user 2026-07-30 (`decisions-log.jsonl`, slug
  `opencode-zen-go-billing-model-distinto-no-mismo-pool`) and not implemented by any package before this one:
  **layer 1** — any provider marked `subscription` with available quota (per `011-quota-failover`'s
  `provider_exhaustions`, once `011` is accepted — it is `BLOCKED` today, not accepted) wins with no cost
  comparison against any other candidate, because its marginal cost is already sunk; **layer 2** — a
  `metered` provider is only considered when no `subscription` provider has quota, and only up to a
  user-declared daily USD ceiling (not monthly — a metered provider's marginal cost cannot be compared
  against a subscription's amortized monthly cost without favoring the subscription every time, which is why
  layer 1 and layer 2 are not weighed against each other on the same axis). Hitting the daily ceiling means
  waiting for a `subscription` provider's quota to reset, not continuing to spend. This paragraph is the
  sketch `012-discovered-inventory`'s AC-08 points to; implementing it is this package's work, not
  `012`'s.

Until all three exist, "most efficient" has no operand and the selection degenerates into whatever the model
rationalises in the moment.

## Verificación

`./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → `SELF_SCAFFOLD_SYNC_OK files=2` ·
`python3 -m unittest discover -s tests -v` · `git diff --check` · ownership vs baseline. Test count rises
from **473** (corrected 2026-07-30, P2 spec-challenge F-12: the "209" baseline this line previously carried
was stale; re-measured both statically — `grep -rhoE "^\s*def test_" tests/*.py | wc -l` — and by a full live
`python3 -m unittest discover -s tests` run, `Ran 473 tests`, one unrelated pre-existing `tempfile` cleanup
flake outside `routing_core`/`catalog` scope, not touched by this contract), never falls, and no test is
skipped.

**P1b's** end-to-end proof is a real exhaustion, not a mocked one: drive a spawn against a provider whose plan
is exhausted, and show the run closing with the exhaustion reason and a second run completing the work on the
other provider — with both rows present in the routing database. That obligation belongs to the code package;
P1 is prose and touches no `routing_core` path, so it has no dispatches rows to show. (Stated explicitly
because the paragraph predates the P1/P1b split and read as an open obligation of the prose package.)

**P1's** proof is that the doctrine reaches all three runtimes and constrains meaning rather than wording:
each new rule is asserted by `test_turn_continuity_doctrine_reaches_all_three_harnesses` and
`test_shared_doctrine_covers_turn_continuity`, and each assertion was shown failing on the pre-change tree
before it was shown passing.

**P2's** proof (the two-part credential-translation unit test plus the credential-gated `P2 local live-parity
gate`) moved together with the rest of its contract into `docs/specs/012-discovered-inventory/spec.md`'s own
`## Verificación` section on 2026-07-30 — see the pointer in this file's P2 section for why. Nothing in this
file's own gates changes because of that move; the generic gate line above still governs P1/P1b/P3.
