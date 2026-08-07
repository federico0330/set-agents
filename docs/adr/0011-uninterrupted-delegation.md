# ADR-0011 — Uninterrupted delegation: when a turn may end, and what independence really buys

- Estado: Accepted (2026-07-28). Feature `008-dynamic-selection`, package P1-uninterrupted-delegation.
- Amends the orchestrator's conversational contract and the reviewer-independence doctrine **on the lanes the
  orchestrator delegates on directly** (Claude Code, OpenCode, Codex). Does NOT amend the routing service, the
  dispatch state machine, the two-cycle deep-review budget, the spawn soft cap, or the Question policy — no
  item was removed from the latter.
- Numbered 0011 and not the next free 0010: `docs/adr/0010-spawn-accounting.md` is already reserved by the
  `007-P2` package record. This package lands first, so the index carries a temporary hole at 0010 that
  `007-P2` fills. A hole is recoverable; a collision on one ADR number is not.
- Every file:line citation was verified against the working tree on 2026-07-28.

## Contexto

The harness promises that every decision is delegated, implemented and audited without the developer having to
drive it. In practice a session stopped on its own several times per feature, and the user named it:

> *"El orquestador delega, termina el subagente y me dice 'el subagente devolvió …, sigue delegar …, necesito
> de vos: NADA'. Esos parones son innecesarios, quiero evitarlos completamente."*

The cause was in the doctrine, not in the model. `orchestrator.md` mandates a fixed end-of-turn block whose
last line is literally `Necesito de vos: <decisión concreta pendiente, o "nada">`, and adds *"Never end a turn
without it"*. What it never stated is the complementary half: **under what conditions a turn is allowed to
end**. With the obligation stated and the condition missing, "an instance came back" reads as a turn boundary,
the block is emitted, and the user pays for the pipeline's progress by typing "dale, continuá".

Two further stops were verified in the tree and are closed here:

1. **A dead subagent ended the work.** `ai/scripts/set_agents_spawn.py` is the harness's only spawner and it is
   pi-only — `route_and_spawn` pins `selected_runtime: "pi"` (`:329`) and builds `pi_pinned_argv` (`:243`).
   For Claude Code, OpenCode and Codex there is no harness-controlled subprocess, so nothing but the
   orchestrator can notice a subagent that died on quota and relaunch it. The lever that exists there is
   doctrine.
2. **One unusable provider stopped every review.** Reviewer independence removes every route sharing the
   writer's provider before any preference is consulted (`routing_core/service.py:148,154`). With two
   providers and one gone, no reviewer is routable at all — so `PACKAGE_REVIEW` halts for every package, not
   just for the spawn that failed.
   Read "gone" as *absent from the inventory*, never as *exhausted*: `probe_inventory`
   (`routing_core/catalog.py:305`) observes credentials and binaries, not quota, so an exhausted-but-logged-in
   provider stays routable and its exhaustion surfaces on the path in (1). D4 develops this; the distinction
   is stated here because a reader who stops at the motivating narrative would otherwise carry away the
   conflation D4 exists to correct.

## Decisión

### D1 — A turn ends for three reasons, and reporting progress is not one of them

A turn ends only when there is a question the Question policy authorizes, when the requested work is finished,
or when a `HUMAN_DECISION_REQUIRED` blocker is being recorded. The operational test is the block itself: if
`Necesito de vos` would read `nada`, the turn is not over.

The end-of-turn block is **kept verbatim**. It is how the user follows the thread without opening state files,
and `tests/test_harness.py` asserts `"Necesito de vos:"` reaches all three runtimes. This ADR adds the missing
condition; it does not remove the report. (Template wording later updated by ADR-0033 — the sentinel line and
this stopping rule are unchanged; "verbatim" protects the rule, not the report's phrasing.)

Rejected: *deleting or weakening the block*. The block was never the defect — the absence of a stopping rule
was. Removing it would trade an unnecessary pause for an opaque session.

Rejected: *"ask for confirmation only on expensive steps"*. Every step in an approved package is already
authorized by the approved package; a second confirmation adds no information and re-introduces the pause under
a different name.

### D2 — Quota exhaustion is not task failure, and is budgeted separately

`Spawn economy` grants one focused retry per phase for an agent that failed, timed out, or returned unusable
output. An instance killed by plan exhaustion did none of those: it returned nothing because its plan ran out.
It therefore **does not consume the retry budget**, and it is relaunched once with a **different** model,
without asking, with the relaunch and its cause persisted via `log-narrative`.

The relaunch is bounded at one per assignment. Two budgets, both bounded — this is explicitly not a licence for
the `_retry2` / `_finish` spawn chains the same section already bans.

Rejected: *folding exhaustion into the existing retry budget*. Retrying the same model against an exhausted
plan is the one move that is always wrong, and spending the failure budget on it means a genuine failure later
in the phase has none left.

Rejected: *unbounded failover across providers*. That is how one runaway task drains both subscriptions.

### D3 — Independence is redefined around the guarantee that actually holds

The primary guarantee is a **clean context**. A reviewer that never saw the implementation reasoning cannot
defend it, cannot carry its sunk cost, and cannot approve the work because it is its own. That holds whether or
not the provider differs. Cross-provider review remains preferred; its absence no longer halts the pipeline.

Under single-provider operation the reviewer must run on a **different model** than the writer — a different
`<role>@<tier>` variant in OpenCode, a different model on the delegation call in Claude Code. Same provider is
a weakened guarantee; same provider *and* same model is the weakest available and is not accepted while an
alternative exists.

**The trade-off, stated plainly.** What is lost is decorrelation. One model family tends to make the same
mistakes twice and to find its own faulty reasoning natural, so a same-provider review has blind spots that a
cross-provider review would not. That loss is accepted deliberately, to keep a session moving rather than
halting an entire feature on a quota boundary. It is not accepted silently: every review that ran without
cross-provider independence states so in its own evidence — `record-subreview --evidence` for the degraded
member, `finalize-review-panel --evidence` for the panel — so the degradation lands in the package's review
record and stays legible to whoever reads the package later.

Rejected as the channel: `update-package --exception`. It reads like a general package annotation and it is
not one — `feature-state.py:1321-1326` rejects anything that is not `{"path": …, "status": "approved"}`, and
the entries exist to be consumed by `check-owned-paths.py` as path-ownership waivers. Recording a review
caveat there would have corrupted the ownership gate's input. This was caught by attempting it during this
package's own delivery.

**Known limit of that mechanism.** `--evidence` on `record-subreview` and `finalize-review-panel` is a free
-text field with `default=""` and **no non-empty or shape validation** (`feature-state.py:1575`, `:1613`,
`:2499`, `:2508`) — the only evidence-touching logic is a fallback string on the `blocked` branch. So a
degraded review *can* be finalized with empty evidence, and the disclosure is a discipline, not a guarantee.
ADR-0009 hit the same class of gap for refutation evidence and closed it with a length-and-shape requirement
(`normalize_verdicts`, `MIN_EVIDENCE_LEN`, `EVIDENCE_SHAPES`). Extending that guard to review evidence is the
obvious follow-up and is deliberately not done here; it is registered rather than assumed away.

**Reversal threshold.** If a defect reaches `PACKAGE_ACCEPTED` through a review recorded as degraded — that
is, a same-provider review passes work that a cross-provider review would plausibly have caught — the
degradation is no longer worth its cost, and the correct response is to make `PACKAGE_REVIEW` block on
independence again and treat one usable provider as a hard stop. The review-evidence entries make **half** of
that trigger mechanical: whether the accepting review ran degraded is readable from the package record
(assuming the evidence was populated at all — see the limit above). The other half, whether a cross-provider
review *would* have caught it, is an irreducible judgment call that no artifact in the tree computes. Saying
this makes the threshold "measurable rather than a matter of opinion" would overstate it: it makes the factual
predicate checkable and the counterfactual legible, which is less, and is what is actually on offer.

### D4 — The scope boundary is drawn by mechanism, not by runtime

**This decision was rewritten after review panel RP-01. The first version was wrong, and the way it was wrong
is worth keeping.** It read: "the pi lane keeps the hard denial; D3 governs the other three lanes, where no
independence check ever ran." That took one true, narrow fact — the subprocess *spawner*
`ai/scripts/set_agents_spawn.py` is pi-only (`:329`, `:243`) — and overgeneralized it into a claim about
*routing decisions*, which are a different axis. Both panel members reached the finding independently and it
survived adversarial refutation.

What the tree actually says. `--route-decide` is runtime-agnostic: `SELECTED_RUNTIMES`
(`routing_core/domain.py:20`) holds `opencode`, `claude-code`, `codex` and `pi`, and `set_agents_app.py:390`
defaults an absent `selected_runtime` to `opencode`. The independence exclusion
(`routing_core/service.py:148,154`) keys on role class, never on runtime, and fires wherever a recorded writer
run is offered as `review_of_run_id`. `tests/test_routing.py:554-571` drives `selected_runtime="claude-code"`
through a single-provider inventory and asserts exactly `REVIEWER_INDEPENDENCE_UNAVAILABLE`. So the discarded
boundary would have relaxed, in prose, a rule the routing service still enforces in the very lanes it named —
and `Tiered dispatch` step 3c, which is runtime-agnostic and sits ~200 lines earlier in the same prompt, would
have won on being read first.

The boundary that holds: **a `--route-decide` decision returning `REVIEWER_INDEPENDENCE_UNAVAILABLE` halts, in
every runtime, unchanged.** D3 governs delegation that carries **no** routing decision — non-tiered roles, the
benign `REVIEW_IDENTITY_UNVERIFIED` path, and sessions driven by the shared doctrine with no `--route-decide`
in play, which is the D6 case and where the observed pause happened. Making a *routed* reviewer degrade
instead of halt is a routing-service change, deferred to `008-P1b` / `008-P2`.

**A consequence worth stating, found during the same verification.** `probe_inventory`
(`routing_core/catalog.py:305`) observes credentials and binaries, never quota. An exhausted-but-authenticated
provider therefore stays in the inventory: the decision comes back ok and the **spawn dies**. Quota exhaustion
is thus normally met on D2's path, not as a decide-time independence denial — and a decide-time denial means
the other provider is *absent*, not exhausted. Conflating the two would send the orchestrator looking for a
relaunch where the correct answer is a halt.

### D4b — Lesson recorded, because it generalizes

Spawner scope and routing-decision scope are different axes. A doctrine that carves out by *lane* while the
mechanism it carves around dispatches by *reason code* carves out nothing. Any future change that relaxes a
`--route-decide` outcome must add the exception at `Tiered dispatch` step 3c itself, or lose to it.

### D5 — Total exhaustion is the one stop that survives

When every provider is exhausted there is nothing left to delegate to, so the correct outcome is
`HUMAN_DECISION_REQUIRED`. This is the only stop D1 preserves beyond the Question policy.

### D6 — The doctrine ships to the global instruction files, not only to the orchestrator prompt

The pause the user hit was in OpenCode, where `Global/_shared/AGENTS.opencode.md` is the doctrine loaded in
every session even when no orchestrator is driving. A rule living only in `agents/orchestrator.md` never
reaches that case, so the same contract is stated in all three shared files
(`AGENTS.opencode.md`, `CLAUDE.md`, `AGENTS.codex.md`).

`AGENTS.opencode.md` had no `## Human decision required` section at all — its `HUMAN_DECISION_REQUIRED`
sentence sat as the last bullet of `Execution discipline`, unlike the other two files. That sentence was moved
into a dedicated section rather than duplicated, which also brings the three files back into structural parity.

### Scale / Data / Security

D3 is a **security-posture change**: it redefines what the reviewer-independence control guarantees, from
"different provider" to "context that never saw the implementation reasoning". No data, migration, money or
identity path is touched — this package writes prose and tests only. The security consequence is stated in D3
and bounded by its reversal threshold; the accountability mechanism's known weakness is stated there too.
Section kept labelled, per the `docs/adr/0008-*.md` precedent, so a reader scanning for security-relevant
decisions finds this one.

## Consecuencias

- A session runs to the end of the approved work without the user re-authorizing each link. The failure mode
  moves from "stops too often" to "runs further than intended".
- **The blast radius of one turn is now the scope of the last `USER_APPROVAL`, not one package.** The first
  draft of this section claimed the package boundary still bounds it; that is wrong, and this ADR is what
  makes it wrong — finishing a package with the next one already approved is "reporting progress", which D1
  forbids as a reason to stop. The spawn cap is per-package (`orchestrator.md`, "~12 spawns per package") and
  does not bound a multi-package session either. What remains as a bound is the approved spec itself, the
  Question policy, and `HUMAN_DECISION_REQUIRED`. That is the trade the user asked for; it is named here
  rather than hidden behind a boundary this decision removes.
- Reviews may now be same-provider. Every such review states the degradation in its own review evidence, and
  those entries are the (partial, see D3) evidence base for the reversal threshold.
- Routed reviewer decisions behave exactly as before, in every runtime.
- Nothing here measures quota. The orchestrator learns a provider is exhausted by a spawn dying, which costs
  one failed spawn per discovery. Measuring spend is `007-P2`; selecting against a budget is `008-P3`.
