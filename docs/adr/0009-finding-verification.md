# ADR-0009 — Adversarial refutation of review findings before repair

- Estado: Accepted (2026-07-27). Feature `006-execution-graph`, package P2-finding-verification.
- Amends the review→repair edge of the package lifecycle. Does NOT amend the review-cycle budget
  (ADR-independent, `MODE_BUDGETS` in `feature-state.py`), the routing tier model (ADR-0004/0006), nor the
  separation-of-duties invariant — it extends the latter one step further.
- Every file:line citation was verified against the working tree on 2026-07-27.

## Contexto

The harness already enforces that **the implementer never approves its own work**: reviewers are read-only,
`NON_ACCEPTING_ACTORS` blocks the mutating roles from `accept-package`, and the routing store keeps a reviewer
independence index. It does **not** enforce that a reviewer's finding is true.

Verified in the tree before this ADR:

1. `orchestrator.md` step 9 read, verbatim: *"If findings exist, `repair-agent` repairs them in a
   consolidated pass."* Nothing sits between the panel and the repair.
2. `feature-state.py` had exactly two terminal finding statuses — `closed` (set by `record-repair`) and
   `accepted`. **There was no way to retire a finding without patching code.** A reviewer who is wrong forces
   a code change.
3. A false finding costs four things, not one: a `repair-agent` pass, a `delta-reviewer` pass, a real code
   change made for no reason, and one of the **two** deep review cycles the budget allows
   (`feature-state.py:1407,1446`, `MODE_BUDGETS`).

This is the same asymmetry the harness already accepted for implementation, applied to review: the party that
produced the artifact is not the party that certifies it.

## Decisión

### D1 — One verifier, batched, between panel and repair

A new read-only role `finding-verifier` (`roles.tsv`: `subagent / 0.0 / review-ro / audit`) receives the
**whole** consolidated findings list in ONE spawn with the inverted brief: try to refute each finding.

Rejected: *N independent skeptics per finding* (the pattern the source material recommends). It multiplies
cost 3–9× and breaks the `~12 spawns per package` soft cap that `orchestrator.md` already declares. Escalation
for the dangerous cases is handled by D5 instead, which costs nothing extra.

Rejected: folding refutation into `delta-reviewer`. Delta review runs **after** repair; the entire value here
is killing the finding **before** the code changes.

Rejected: cross-refutation inside the review panel (each member refutes the others). It creates a real data
dependency between panel members and would destroy the concurrent panel established in `006-P1-false-edges`.

### D2 — `refuted` is a terminal finding status, and the finding is never deleted

`TERMINAL_FINDING_STATUSES = {"closed", "accepted", "refuted"}` (`feature-state.py`), applied at the three
sites that share the identical open-set predicate: `has_open_findings`, the STATUS.md counter, and the
bitácora counter.

A refuted finding **stays in `package["findings"]`** carrying `status=refuted`, `verdict_reason`,
`verdict_evidence`, `verified_by`, `verified_at`. It is rendered in the package note with its grounds. This is
the point: the record must show what was killed and why, or the verifier becomes a way to make findings
disappear. The `adversarial-judge` sees refutations in the final bundle.

`record-repair` raises on a `--finding-id` whose status is `refuted` — repairing it would change code for a
defect shown not to exist.

### D3 — Verification is not a review cycle

`record-verification` never touches `deep_review_cycles`. The only two increments stay where they were
(`record-review`, `start-review-panel`). Verification is an edge **inside** the cycle the panel already
counted; charging for it would make the correct behaviour cost budget.

Consequence for the panel filter (`finalize-review-panel`): `refuted` joins `closed` in the "still live"
predicate, so a finding killed in cycle 1 cannot reappear in the cycle-2 panel. **Dedup runs against
everything seen, not against what survived** — otherwise refuted findings resurface every round.
`accepted` keeps its previous treatment there unchanged.

### D4 — The cost gate is a physical waiver, not prose

The verifier is spawned only when the consolidated panel left ≥1 finding of severity `medium|high|critical`.
An all-`low` bundle skips it with `record-verification --skip-reason <reason>`, and the CLI **refuses the
waiver if anything above `low` is open**. Same doctrine as the `--skip-delta` waiver: the decision lands in
the state file, never in a chat log.

Rationale: an audit-tier spawn costs more than the repairs a `low` finding would trigger. Verifying
everything is defensible on quality and indefensible on the quota history that produced the spawn economy
rules in the first place.

### D5 — Escalation is a routing decision, not a second role

A `critical`/`high` finding, or any finding of category `security`, does not get a different verifier: it gets
a different **tier**. The orchestrator classifies the verification spawn `risk=high` in those cases and
`routes.v1.toml` selects from there. This composes with feature 004 instead of duplicating it, and adds zero
new routing prose.

### D6 — The asymmetry is `upheld`

A finding the verifier cannot refute survives, unchanged. A false negative (killing a real defect) is strictly
worse than a false positive (one unnecessary repair), so the default under uncertainty is written explicitly
into the agent brief and enforced by the CLI: `normalize_verdicts` rejects a `refuted` verdict that lacks both
`reason` and `evidence`. Re-rating severity is not refutation. The verifier may not add findings — an
observation is routed by the orchestrator, because a finding smuggled in through the verifier would skip the
review-cycle count.

## Consecuencias

- **+1 spawn per package**, of audit tier, only when the bundle warrants it. Measured against real package
  cost before the pattern is extended anywhere else.
- **Possible saving of a whole repair cycle**: if every finding is refuted, `record-verification` moves the
  package straight to `PACKAGE_TESTING` — no repair, no delta review.
- **New failure mode: an overconfident verifier.** Mitigated by D6 (default `upheld`, evidence mandatory) and
  by D2 (refutations are visible in the record and in the judge's bundle), not eliminated. If refutations of
  real defects show up in practice, the fix is the tier, not the removal of the node.
- `roles.tsv` and `ai/catalogs/routes.v1.toml` must stay in sync: `routing_core/catalog.py:387` requires
  `union(route.roles) == roster_names` exactly. A role added to the roster and missing from any route row
  raises `CATALOG_INVALID` and takes down routing harness-wide — not just for that role.
