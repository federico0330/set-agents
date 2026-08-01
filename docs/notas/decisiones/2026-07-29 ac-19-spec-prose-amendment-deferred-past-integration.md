# AC-19's stale spec.md rationale clause stays unedited past integration too

<!-- notas:auto -->
- fecha: 2026-07-29 · actor: integrator
- alcance: [[features/007-quota-visibility|007-quota-visibility]] · [[features/007-quota-visibility/P3-correct-record|P3-correct-record]]

## Contexto

P3's decision ac-19-rationale-drifted-mid-package-routing-db-recreated diagnosed that AC-19's clause in spec.md ('the database it names no longer exists and routing is not blocked') was true at 1.3.0 approval (2026-07-29T00:39z) and became false about 10 hours later when P2's own mandated live-verification spawn recreated routing.db in schema 6 (2026-07-29T10:10z) -- and named INTEGRATION as the checkpoint to evaluate a 1.3.0->1.4.0 fix. At integration, docs/notas/BUENOS-DIAS.md was re-read word-for-word against the live routing.db (queried directly: schema_version=6, 1 dispatch row) and confirmed already correct -- it states the database exists in schema 6 and withdraws the rm remediation for the real, current reason, not for spec.md's stale one. AC-19's deliverable is therefore fully satisfied; only spec.md's own supporting prose is stale.

## Decisión

Do not edit spec.md from INTEGRATION. AC-19's disputed clause is acceptance-criterion text inside the hash-pinned approved spec (approved_spec.hash=31d6e65a...), and the Integrator role does not own changing approved acceptance criteria even for a pure fact-correction with no behavioural consequence. The deliverable (BUENOS-DIAS.md) is correct and does not repeat the stale clause, so nothing user-facing is wrong -- only the AC's own rationale undersells its result. Left as open, named debt for whoever next opens a package on this contract (a 007 maintenance package, or a 1.3.0->1.4.0 amendment authored with the same rigor as the existing 1.0->1.1->1.2->1.3 amendment logs), rather than slipped in unilaterally here.

## Consecuencias

spec.md is byte-identical to what P3 left it; approved_spec.hash in ai/state/features/007-quota-visibility.json still matches the file, so no re-init or re-approval is forced by this pass. A future reader of AC-19 must cross-check it against this decision and ac-19-rationale-drifted-mid-package-routing-db-recreated rather than trust the clause literally. Feature 007 proceeds to DONE with this as recorded documentation debt, not a blocker.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
