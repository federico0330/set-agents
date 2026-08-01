# Integration evidence — 007-quota-visibility (contract 1.3.0)

Actor: integrator. Date: 2026-07-29. All three packages (P1-schema-normalize, P2-spawn-accounting,
P3-correct-record) were already `PACKAGE_ACCEPTED` before this pass; no package internals were reopened.
This note records what was checked at INTEGRATION and the one judgment call made (AC-19 vs the spec.md
prose that supports it).

## 0. Global gates (not re-run; orchestrator ran them directly)

`./ai/scripts/verify.sh` → `VERIFY_PASS` (284 tests) · `./build.sh --check` → `SELF_SCAFFOLD_SYNC_OK
files=2`. Not repeated here; no code was touched during this pass, so there is nothing new for those gates
to catch.

## 1. AC-by-AC confirmation against the working tree

Read `docs/specs/007-quota-visibility/spec.md` end to end (all 19 AC, all four amendment logs). For each AC,
confirmed the combination of P1+P2+P3 as they exist in the tree right now — not re-litigating what package
review already accepted, but checking the seams between packages and a handful of claims live against the
running system.

- **AC-01/AC-02/AC-03/AC-04/AC-05/AC-06/AC-07 (P1).** `_normalize_ddl()` (`store.py:192`) is the only
  normalizer, delimiter-aware over all four SQLite quoting forms, comments stripped before whitespace
  collapse. `SchemaDivergence` (`store.py:257`) carries `missing`/`altered`/`unexpected` and prints only
  canonical (compile-time) names. ADR-0005 carries the "version-drift/corruption detector, not tamper
  defence" amendment (`docs/adr/0005-trusted-routing-sqlite-lifecycle.md:129-131`). Confirmed live: the two
  real schema-4 backups on disk (`~/.local/state/set-agentes/routing-v2/backups/routing-v4-*.db`) are
  untouched (same size/mtime as recorded in prior package evidence) — P1 diagnoses them without recovering
  them, per the explicit non-goal in "Alcance explícitamente excluido".
- **AC-08 through AC-14 (P2, schema 5→6 and the migration chain).** This is the one true cross-package seam
  (P1's normalized-DDL comparison has to agree with P2's 5→6 `ALTER` output, or every post-migration open
  fails). Read `store.py:534-637` (`_migrate_4_to_5`, `_migrate_5_to_6`, `migrate()`): one `BEGIN EXCLUSIVE`,
  a single `_ddl_divergence` comparison against the *current* canonical DDL after the whole chain runs, never
  per-step — exactly what AC-14's coupling note requires, since an intermediate 4→5 check would compare a
  schema-5 database against schema-6 canonical and always fail.
  `tests/test_routing.py:test_routing_migrate_uses_harness_identity_and_test_store` builds a frozen schema-4
  fixture via `frozen_dispatches_script()` (P1's fixture generator) and drives it through `migrate()` to
  schema 6 in one CLI call, asserting `schema_version=6` and row-count preservation — i.e. a schema-4 base
  literally migrates through both packages' logic together and is proven in the suite, not just asserted in
  prose. `test_the_migration_banner_reports_the_versions_it_observed` additionally proves the banner is
  version-generic by running two different source schemas (4 and 5) through the same path and requiring the
  reported `from=` values to differ — a regression against the old hardcoded `from=4 to=5` (ADR-0008 D8,
  amended at `docs/adr/0008-two-roots-portability.md:461-464`).
  Confirmed live (not just in the test suite) against the real `routing.db` on this machine: schema 6, 1
  dispatch row, usage columns populated (`usage_input=3321, usage_output=5, usage_cache_read=NULL,
  usage_cache_write=NULL, usage_reasoning=0, cost_micros=3351, usage_status='ok'`) — NULL cache columns are
  correct per AC-08 ("Pi reports no cache, a written `0` would fabricate evidence"), not a degraded reading.
  `_authorize_issued`'s positional column list (AC-09's second half) still matches the widened table: a real
  spawn recorded through it without error.
- **AC-15.** `python3 ai/scripts/set_agents_app.py --routing-report` run live: returns both `p50_ms`/`p90_ms`
  (from `events`, machine-global) and a `tokens` block (from `dispatches`, per-project) with the scope
  sentence verbatim in the JSON (`"scope": "dispatches, per-project (this project_key only); unlike
  p50_ms/p90_ms and per_route above, which come from events..."`). Confirmed the two route-key sets are
  stated as not-subsets, matching the AC.
- **AC-16.** `python3 ai/scripts/cost-report.py --project .` run live: lists a `pi` row
  (`. pi gpt-5.6-luna implementer 1 3.3k 5 ...`) beside the `claude-code`/`opencode` rows. `_pi_project_key`
  (`cost-report.py:221`) duplicates `project_key_for` rather than importing `routing_core`, per ADR-0005 —
  confirmed by reading both derivations side by side; a test pins their agreement
  (referenced in P2's evidence, not re-run here). `--help` and `TIPS-USO.md` (`:96,:106`) both state the
  coverage limit ("only spawns dispatched through set_agents_spawn.py").
- **AC-17.** `_compact_in` (`store.py:830-838`) only ever touches `events`; grepped the whole file for any
  `DELETE`/retention logic against `dispatches` after P2's schema-6 columns were added — none exists. The
  acknowledged unbounded growth is unchanged, not worsened.
- **AC-18.** `docs/adr/0010-spawn-accounting.md` exists and records design + rejected alternatives.
- **AC-19.** See §2 below — the one item that needed a judgment call.

No AC failed. No cross-package regression found in the seam that matters (schema chain + DDL comparison).

## 2. AC-19 / spec.md drift — decision

**What was checked.** Read `docs/notas/BUENOS-DIAS.md` in full, word-for-word, against the live state of
`routing.db` (queried directly: `schema_version=6`, 1 dispatch row, both real v4 backups untouched in
`backups/`). BUENOS-DIAS.md §3 ("¿Está listo para usar pi-agent...?") already carries an explicit
2026-07-29 correction: it states plainly that `routing.db` **exists**, in **schema 6**, created by P2's own
live verification spawn, and that the old `rm` remediation is withdrawn "no por lo que esta sección decía
antes" — i.e. it does NOT repeat spec.md's stale rationale ("no longer exists"), it states the current,
verified truth instead. This matches the routing.db state queried directly. **AC-19's actual deliverable
(the corrected note) is correct and fully satisfies the AC's stated intent: "replaced by what was
verified."**

**The drift is confined to spec.md's own supporting prose**, not to the deliverable: AC-19's clause in
`spec.md` reads "the `rm` remediation offered in that note is also withdrawn — the database it names no
longer exists and routing is not blocked." That was true when 1.3.0 was approved (2026-07-29T00:39z) and
became false about 10 hours later at 2026-07-29T10:10z, when P2's own mandated live-verification step (item
2 of the spec's "Verificación" section: "a real spawn through the openai-codex lane") recreated the file.
This is already fully diagnosed and registered by P3 itself: decision
`ac-19-rationale-drifted-mid-package-routing-db-recreated` (`ai/state/decisions-log.jsonl`,
2026-07-29T15:51:30z), which explicitly declined to edit `spec.md` from inside P3 (owned_paths scoping,
contract-hash integrity) and named INTEGRATION as the next checkpoint to evaluate the fix.

**Decision: defer (option b), do not edit spec.md.** Registered as a new decision,
`ac-19-spec-prose-amendment-deferred-past-integration` (see `ai/state/decisions-log.jsonl`), confirming and
narrowing the open debt for whoever next touches this contract. Reasoning:

1. The Integrator role is explicitly scoped to not change approved acceptance criteria. AC-19's disputed
   clause is inside the acceptance-criterion text itself, inside the hash-pinned approved spec
   (`approved_spec.hash = 31d6e65a...` in the state file) — not a code comment or a citation range. Editing
   it, however surgical, is editing approved contract text, and that is a category INTEGRATION does not own
   even when the edit is a pure fact-correction with no behavioural consequence.
2. There is no live tension to resolve under time pressure: the actual deliverable (BUENOS-DIAS.md) already
   states the truth and does not repeat the stale clause anywhere. A human or future package reading AC-19
   next to BUENOS-DIAS.md sees a correct note and a rationale clause that undersells its own result (the
   note is *more* correct than the AC that specified it) — this is confusing, not wrong, and it is exactly
   the class of "citation rot" this contract's own three prior amendment logs (1.0→1.1→1.2→1.3) treat as
   routine, always fixed by an authored amendment log entry with a re-approved hash, never by a downstream
   role editing in place.
3. This feature's own subject matter is "claims rot, verify before trusting" (P3 exists to correct exactly
   this kind of drift, twice, through adversarial repair rounds). Having INTEGRATION casually rewrite
   approved acceptance-criteria prose without the same SPEC_CHALLENGE-grade scrutiny the rest of this spec
   got would be inconsistent with the discipline the feature itself is teaching.
4. No packages remain open on 007 to carry a formal 1.3.0→1.4.0 amendment, and this feature has no more
   planned packages — a one-clause spec-prose amendment is real but small work, better done as a deliberate,
   named amendment (in the same style as the existing amendment logs) by whoever opens the next touch on this
   contract (a maintenance package, or folded into 008 if it ever needs to cite AC-19), than slipped in here.

**Net effect of choosing (b):** `spec.md`'s hash is untouched (no drift caused by this pass — the file was
not edited). The open item is: *AC-19's rationale clause is stale; the deliverable it describes is correct
regardless.* This is recorded, not hidden, and does not block `DONE`.

## 3. Other cross-package findings

None blocking. Two small, non-blocking observations, neither of which changes any AC or requires a repair:

- `cost-report.py --project .`'s `pi` row currently reports `actual_model=gpt-5.6-luna` under the
  `openai-codex` provider (the one real dispatch on this machine went through `openai-codex`, with
  `anthropic` recorded only as `fallback_provider`, never consumed) — this matches the spec's stated
  exclusion ("the router genuinely chose openai-codex at every tier") and is not a defect; noted only because
  it is the first time the `pi` lane has real data to look at, and it looks like what the spec predicted it
  would look like.
- `--routing-report`'s output carries a `warnings: ["LEGACY_ROUTING_STATE_PRESENT"]` entry unrelated to
  007 — pre-existing, out of this feature's scope, not investigated further here.

## 4. Verdict

Ready for `DONE`. All 19 AC hold against the working tree, the one real cross-package seam (P1's DDL
normalization + P2's 5→6 migration chain) is proven end-to-end both in the test suite and against the live
`routing.db` on this machine, and the AC-19/spec.md prose drift is a recorded, non-blocking documentation
debt rather than an unresolved defect.
