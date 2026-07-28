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

## Amendment log (1.0.0 → 1.1.0, post-review)

The concurrent review panel (`package-reviewer` + `security-auditor`) returned `repair_required` with 13
consolidated findings, and the `finding-verifier` — this ADR's own node, applied to itself — upheld **all 13**
after attempting genuine refutation on six. The pattern behind them: the ceremony was written into the prose
and the CLI was left soft. Four decisions are amended and two are added.

### D1 amended — the actor gate (SEC-001 / PV-01)

`record-verification` accepted any `--actor`. Reproduced end to end: `--actor implementer` refuted a
`critical`/`security` finding against its own diff, the package moved to `PACKAGE_TESTING`, and it then
accepted with `repairs=[]` and `delta_reviews=[]`. `NON_ACCEPTING_ACTORS` was being enforced one step
downstream of the verb that defeats the gate, which is not enforcement.

Now: `REFUTING_ACTORS = {"finding-verifier"}` — only the verifier may refute; `upheld` verdicts and the waiver
stay open to the coordinator. A refutation is also rejected when the actor equals the finding's `source_role`.
`--actor` is required explicitly (no default), because `verified_by` IS the independence attribution.

### D4 amended — a waiver must live inside the command it waives (OBS-5)

`--skip-delta` is checked inside `record-repair`; `--skip-reason` guarded a step nothing required, so skipping
verification entirely was free and left no trace. The node was mandatory in prose and optional in code.

Now: `record-repair` refuses to run while the package has no verification record and any open finding is above
`low`, and refuses any individual finding above `low` that carries no `verified_verdict`.

### D6 amended — evidence, not presence (SEC-002)

`not (reason and evidence)` is a truthiness check: `True`, `{"k": "v"}` and `"   "` all passed and retired
`critical` security findings. And `verdict_evidence` was persisted but rendered nowhere, so the human-facing
audit trail this ADR leans on was empty exactly when it mattered.

Now: both fields must be non-empty strings after `strip()`, capped at 2000 chars; `evidence` has a minimum
length and must match one of the three shapes the brief enumerates (`file:line`, a `$` command with output, or
an `AC-\d+`). Both the reason AND the evidence are rendered in the package note, with the verifier's name.

### D7 (new) — `upheld` is terminal for verification, and the pass is budgeted (PV-02)

`upheld` left the finding `open`, so the terminal-status guard never fired on a second pass: verify `upheld`,
then verify again as `refuted`, repeatable without limit. A retry-until-you-win loop in a harness that caps
every other loop. Now a finding carrying `verified_verdict == "upheld"` cannot be re-verified, and
`max_verifications_per_package` (2 for feature/scoped, 1 for quick-fix/incident) blocks the package when
exhausted. The budget is validated with a default, so state files written before it stay valid.

### D8 (new) — the auto-transition is gated on why the package is in repair (PV-04)

`PACKAGE_REPAIR` has four entry points: review, delta review, a failed testing run and a failed runtime QA.
Keying the skip-to-testing transition on the finding set alone meant refuting an unrelated `low` finding after
a red test marked the package testing-ready with the red test never addressed. Now
`_repair_entered_from_review` inspects the last history event that set the phase, and only the review paths
qualify.

### D7 corrected (delta review, DR-01) — the budget is a backstop, not the control

Sized at 2 per package, `max_verifications_per_package` was smaller than the flows the other budgets already
allow. Reproduced inside every declared budget: two review cycles with a delta-review regression in each end
in `BLOCKED`; in `quick-fix`/`incident` a *single* delta-review regression became unrepairable. That defeats
`max_deep_review_cycles` and turns "the delta reviewer found a regression" into a routine human escalation —
exactly what the question policy forbids.

The anti-retry control is `verified_verdict` stickiness, not the counter. The counter is a runaway backstop
and is now dimensioned against the flows it must not block: 6 for feature/scoped, 3 for quick-fix/incident.
Two further corrections: the budget is evaluated **after** the waiver branch, because blocking a package for
taking the cheap path is absurd; and a waiver increments its own `attempts["verification_waivers"]` rather
than the budgeted counter — V-12 asked for the waiver to be *visible*, not for it to consume a scarce
resource, and counting it in the budget made the waiver unreachable at the ceiling through a second door.

### D8 corrected (delta review, DR-02) — an intra-phase event is not an entry

`_repair_entered_from_review` scanned history for the last event with `to == "PACKAGE_REPAIR"`, but
`record_event` writes `to = data["phase"]` for anything that does not move the phase. Two commands poisoned
it: `record-spawn`, which orchestrator doctrine makes **mandatory before every delegation**, and
`record-verification` itself when a verifier splits verdicts across calls. Reproduced: the same two
refutations reach `PACKAGE_TESTING` in one call with no spawn, and stay stuck in `PACKAGE_REPAIR` with the
spawn — degrading into an empty repair pass plus a full delta review for a package with zero surviving
findings. The thesis of this ADR silently stopped holding in its own documented flow.

Now the scan skips any event whose `from == to`. Both regressions are pinned by tests that fail without the
fix; the absence of a spawn in the original test fixture is precisely what let this ship green.

### D7 corrected again (second delta review, DR-05/DR-06) — one default, and the waiver is a loop too

Raising the command's default from 2 to 6 left `validate_state`'s default at 2. The key is **optional** —
every state file written before it omits it — so for all four existing features the command authorised a pass
that `fail_if_invalid` then rejected. The failure shape got *worse*, not better: where there had been a
governed `BLOCKED` with a recorded blocker, there was now an ungoverned `StateError`, no blocker, and `next`
still recommending `DELTA_REVIEW`. That is precisely what this decision exists to prevent, surviving on the
flank the fix did not look at.

`DEFAULT_MAX_VERIFICATIONS = 6` is now the single source for all three readers (`validate_state`,
`base_state`, `cmd_record_verification`). An optional budget key with more than one default is a drift waiting
to happen.

And the waiver counter, given its own dimension to keep the cheap path reachable, was left uncapped — the only
loop in the harness without a ceiling, in a file whose own comment says it caps every loop. It now shares the
same budget value against its own counter: same ceiling, separate dimension, no second key to drift. Both are
`block_with_reason`, never a raise.

Verified by the reviewer and not repaired, because it is correct: the waiver cannot launder a `medium+`
finding into repair. `record-repair`'s per-finding `verified_verdict` guard holds regardless of how many
waivers were recorded, so N waivers are no worse than one.

### D1/D2 corrected (auditoría final) — la invariante vivía en un comando, no en el modelo

La auditoría final (panel de seguridad + arquitectura sobre la feature entera) devolvió el diagnóstico que
las tres rondas anteriores no habían visto, porque cada una miró su propio diff: **la invariante "un hallazgo
`medium+` no sale del conjunto abierto sin veredicto" se instaló en `record-repair`, no en el modelo de
hallazgos.** Las tres fugas estaban afuera de los dos comandos endurecidos, en las puertas que ningún diff
tocaba:

1. **`record-delta-review --closed-finding` no tenía ninguna guarda.** Ni severidad, ni veredicto, ni
   reparación, ni actor — la única de las cuatro rutas de escritura terminal sin control. Reproducido: un
   hallazgo `critical` de seguridad sale del conjunto abierto sin cambio de código y sin registro, y el
   paquete se acepta. Ahora exige veredicto **y** reparación previa: un delta review **confirma** que una
   reparación cerró un hallazgo, no puede ser lo que lo cierra.
2. **Un hallazgo re-levantado heredaba el veredicto del ciclo anterior.** `existing.update(finding)` sólo
   pisa las claves entrantes, así que `verified_verdict` sobrevivía sobre un hallazgo que volvía a estar
   abierto: una credencial reutilizable que autorizaba la reparación del ciclo 2 con un juicio emitido contra
   otro diff. El eje de verificación ahora se archiva en `verification_history` y se resetea (`merge_finding`).
3. **`--new-finding` con un id existente appendeaba un duplicado.** Todos los lookups son first-match, así que
   la copia nueva era invisible para todo comando y visible sólo para `has_open_findings`: el paquete quedaba
   sin salida por CLI, sólo `block` + edición manual del JSON. Ahora mergea, y `validate_state` reporta ids
   duplicados como ya hacía con `package_id`.

Y la de seguridad, que es de la misma familia y peor: **`normalize_findings` saneaba `status` y nada más.**
`verified_verdict` y `repair_attempts` — los campos que las guardas nuevas **leen** — eran asignables al nacer.
Un `upheld` pre-seteado vuelve el hallazgo permanentemente irrefutable (le saca al verificador su única razón
de existir, elegida por quien levanta el hallazgo); un `repair_attempts` negativo hace que
`max_repairs_per_finding` no dispare nunca. Se cierra por **whitelist**: `FINDING_BOOKKEEPING` es propiedad
del ciclo de vida, nunca de quien archiva. Blacklistear una clave por vez es exactamente lo que hicieron las
tres rondas anteriores.

Dos correcciones menores de la misma ronda: `next` recomendaba `DELTA_REVIEW` desde `PACKAGE_REPAIR` aunque el
comando que ese consejo implica ahora se niegue a correr (y el `reason` era literalmente falso); y el brief del
verificador enumeraba seis causales de refutación mientras el CLI acepta evidencia para tres — las dos
sobrantes producían citas fabricadas, síntoma que ya estaba en el propio repo con números de línea inventados.

### Repairs outside the state machine

- **`_short` is a trust boundary** (SEC-003). `merge_note` splits on the FIRST `NOTES_AUTO_END` with
  `maxsplit=1`, so a `verdict_reason` carrying that marker permanently promoted agent-authored text plus a
  stale findings snapshot into the human-owned region of `docs/notas/`, re-promoted on every regeneration.
  `_short` now neutralizes both markers for every state-derived field, and `merge_note` neutralizes the body
  as defense in depth.
- **Findings cannot be born terminal** (PV-03). `normalize_findings` accepted a caller-supplied `status`, so a
  `critical` finding could be created already `refuted` — bypassing every evidence check. It is now rejected
  on ingress; terminal statuses belong only to the commands that own them.
- **Replay is a no-op** (PV-08), **duplicate verdicts in one batch are rejected** (PV-09), the waived
  verification **counts against its budget** and a `verifications` **metric** exists (PV-10).
- **`PROYECTO/prompt.md` and `PROYECTO/AGENTS.md`** teach the node (PV-05). They were still instructing
  findings straight to repair, so a scaffolded project got the CLI without the doctrine. Note the reviewer's
  correction: agent doctrine is installed from `Global/`, not scaffolded from `PROYECTO/`, so this was a
  contradiction between the starter template and the installed prose rather than total inertness — and the
  drift is systemic, not specific to this line.
- **D5 is no longer inert** (SEC-004 / PV-06). `models.toml` now carries `[roles.finding-verifier.tiers.*]`,
  so the OpenCode variants exist and tier escalation can actually be applied. `routes.v1.toml` membership was
  necessary for catalog validity but never sufficient for tiering.
- **The dry run demonstrates the node** (PV-11), refutation shape included.

## Consecuencias

- **+1 spawn per package**, of audit tier, only when the bundle warrants it. Measured against real package
  cost before the pattern is extended anywhere else.
- **Possible saving of a whole repair cycle**: if every finding is refuted, `record-verification` moves the
  package straight to `PACKAGE_TESTING` — no repair, no delta review.
- **New failure mode: an overconfident verifier.** Mitigated by D6 (default `upheld`, evidence mandatory) and
  by D2 (refutations are visible in the record and in the judge's bundle), not eliminated. If refutations of
  real defects show up in practice, the fix is the tier, not the removal of the node — and after the D5
  amendment that fix can actually be applied on every runtime.
- **`_short` escaping is repo-wide and does not heal the past** (delta review, DR-03). It now rewrites a
  literal `-->` in EVERY state-derived field, so an ASCII arrow inside a narrative renders as `--›` —
  cosmetic, confined to the machine-owned block, and zero occurrences in current repo state. And
  `merge_note` escapes the generated body, not `existing`: a note that already carried an injected
  `NOTES_AUTO_END` from before this repair keeps it, and its stale tail stays in the human region. The vector
  never fired here (all four state files are clean), so this is a documented limit, not a live defect.
- **`refuted` is irreversible today.** `reopen` only applies from `BLOCKED` and does not touch finding
  statuses, so a wrongly refuted finding can be undone only by hand-editing the state JSON. Accepted for now:
  the actor gate plus mandatory evidence make a wrong refutation expensive to produce, and an
  `--reopen-finding` path is a distinct decision about who may un-retire a finding. Recorded here so it is a
  known limit rather than a discovery.
- `roles.tsv` and `ai/catalogs/routes.v1.toml` must stay in sync: `routing_core/catalog.py:387` requires
  `union(route.roles) == roster_names` exactly. A role added to the roster and missing from any route row
  raises `CATALOG_INVALID` and takes down routing harness-wide — not just for that role.
