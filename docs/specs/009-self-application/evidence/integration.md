# Integration evidence — 009-self-application (contract 1.1.0)

- Integrator run: 2026-07-29T16:58:19+00:00
- Packages integrated: P1-knowledge-home, P2-state-machine-required, P3-panel-integrity (all `PACKAGE_ACCEPTED`,
  `integrated: true` in `ai/state/features/009-self-application.json`)
- Global gates already run by the orchestrator before this pass and re-confirmed here at the targeted-test level
  (not re-run in full, per instructions): `./ai/scripts/verify.sh` → `VERIFY_PASS` (284 tests, includes
  `GLOBAL_PORTABILITY_OK`, `CANONICAL_PATHS_OK`, `FEATURE_STATE_OK`); `./build.sh --check` →
  `SELF_SCAFFOLD_SYNC_OK files=2`.

## What was checked

1. Read the approved spec (`docs/specs/009-self-application/spec.md`, contract 1.1.0, 13 ACs) and the full
   package history/findings/repairs/verifications in the state file end to end (all three packages, all
   findings — `closed` or `refuted`, none left `open`).
2. Read the actual code for the three seams most likely to hide a cross-package defect no single package's
   review would catch:
   - `ai/scripts/verify.sh` (order of the two new guards: `check-canonical-paths.py` then
     `check-feature-state.py`, both P1/P2 territory).
   - `ai/scripts/check-canonical-paths.py` (P1's AC-03 guard) and `ai/scripts/check-feature-state.py` (P2's
     AC-05/06 gate) — whether the state-machine gate's commit-history scan is affected by P1 moving
     `knowledge/` → `docs/ai/knowledge/_global/` (it is not: the gate keys on `docs/specs/<id>/` directories
     and commit subjects, never on the knowledge tree).
   - `cmd_init` (P2's AC-13 spec-hash verification) against `cmd_record_late_review` / `cmd_extend_review_panel`
     / `cmd_start_review_panel` (P3's AC-08/09/10 verbs) and the shared `replayed()` helper P3 introduced as the
     single replay-detection definition — confirmed `init` and the panel verbs don't share any state field or
     guard that could interact, and that `replayed()` is used consistently by `record_event` and all four
     updaters that short-circuit (P3's own F-01 repair), so nothing P2 added to `init` could desync from it.
   - `record-late-review`'s explicit refusal on an already-`accepted` package (`"raise this against the
     integration or block the feature"`) — this is the live door I would have had to use had I found a
     genuine defect; confirmed it resolves to the CLI's own `block` verb, matching P3's own refuted F-04.
3. Ran the 10 tests that most directly exercise these seams together (not the full ~7-minute suite, since the
   orchestrator already ran it green): all pass.
   ```
   python3 -m unittest tests.test_harness.HarnessTests.{test_knowledge_write_and_read_targets_agree,\
   test_save_memory_writes_the_format_the_scribe_declares,test_domain_knowledge_is_wired_through_the_canon,\
   test_canonical_path_guard_fails_on_a_dangling_reference,test_init_refuses_to_attest_a_spec_it_did_not_verify,\
   test_feature_state_gate_fails_when_a_delivered_feature_has_no_state_file,\
   test_the_delivery_commit_convention_is_declared_where_the_gate_reads_it,\
   test_start_review_panel_requires_declared_members,\
   test_a_late_finding_cannot_be_refuted_by_the_role_that_filed_it,\
   test_replay_detection_has_exactly_one_definition}
   -> Ran 10 tests, OK
   ```
4. Checked for leftover cruft: `docs/notas/features/009-self-application/*.md` (P1/P2/P3 notes + the hub
   `bitacora.md`), every finding in the state file (all `status: closed` or `status: refuted`, none `open`,
   none deferred as "fix in integration" — every deferral is a `log-decision` entry with an explicit "not
   repaired, out of this package's criteria" reasoning), and the P3 context pack
   (`docs/specs/009-self-application/context/P3-panel-integrity.md`), which no longer contains the false
   "reachable only through record-late-review" claim F-03 flagged — confirmed removed.
5. Confirmed `docs/ai/knowledge/` on disk: 5 project-tier files + `docs/ai/knowledge/_global/` with 5
   cross-project files, and no `knowledge/` directory left at the repo root (`git status` shows the five moves
   as renames, `R`, to `docs/ai/knowledge/_global/*`).
6. Confirmed AC-11's two record-drift repairs are actually on disk: `docs/adr/README.md` has the ADR-0009 row,
   and `docs/specs/003-trusted-routing-pi-runtime/design.md` no longer asserts the inverted exclusion-counting
   behaviour.

## AC-by-AC confirmation

- **AC-01** — `docs/ai/knowledge/<domain>.md` resolves inside this repo (5 files present). Pass.
- **AC-02** — `docs/ai/knowledge/{security,data,architecture,algorithms,frontend}.md` (project tier) and
  `docs/ai/knowledge/_global/*.md` (cross-project tier) both exist; `knowledge/` at the repo root is gone;
  `sync-project.sh:84` points at the new `_global` path. Pass.
- **AC-03** — `check-canonical-paths.py`, run inside `verify.sh` after `build.sh --check`, fails on any
  concrete literal a canonical prompt names that doesn't resolve, with a 3-entry waiver set, each reason
  naming its real producer/file:line. Pass (and it is itself covered by a regression test, per the F-02
  repair — a guard whose failing path nothing drives was P1's own review finding).
- **AC-04** — `test_knowledge_write_and_read_targets_agree` parses the canonical prompts (brace expansion
  included) and asserts the scribe's declared write set is a subset of every reader's declared read set. Pass.
- **AC-05** — `check-feature-state.py`, wired into `verify.sh`, fails `FEATURE_STATE_MISSING` when a
  `docs/specs/<id>/` directory has a matching `Feature <n> P<m>` delivery commit and no
  `ai/state/features/<id>.json`. The mechanism (verify.sh only, not a git hook) is decided and logged. Pass.
- **AC-06** — the gate is silent during `SPEC_DRAFT`/`SPEC_CHALLENGE` (no `P<n>` token yet) and its output
  names the exact `feature-state.py init ...` remedy, including the real sha256 of the spec. Pass.
- **AC-07** — `006-execution-graph` is not backfilled; it's a named, reasoned waiver in
  `check-feature-state.py`'s `WAIVED` dict pointing at the `feature-006-delivered-outside-state-machine`
  decision. Pass.
- **AC-08** — `start-review-panel` without `--role` is rejected before any spawn is paid for
  (`test_start_review_panel_requires_declared_members`). Pass.
- **AC-09** — a duplicate `--panel-id` is a hard error; `extend-review-panel` is the distinct, named verb for
  adding a member to an open panel. Pass.
- **AC-10** — `record-late-review` is a phase-agnostic verb that lands findings on `package["findings"]`,
  which `package_accept_ready`'s `has_open_findings` already reads — no new phase, no deep-review-cycle
  consumption. It correctly refuses against an already-`accepted` package and names `block` as the escalation
  path. Pass.
- **AC-11** — `docs/adr/README.md` carries the ADR-0009 row; `docs/specs/003-trusted-routing-pi-runtime/design.md`
  no longer asserts the inverted exclusion behaviour. Pass.
- **AC-12** — `save_memory.py --domain` requires `--section`, matches the heading as a whole line
  (`^## {section}$`), and refuses `UNKNOWN_SECTION`/`MISSING_KNOWLEDGE_FILE` without appending — the shape
  `memory-scribe.md` declares. Pass.
- **AC-13** — `cmd_init` verifies `sha256(spec_path)` against the supplied hash and refuses
  `SPEC_HASH_MISMATCH`/`SPEC_NOT_FOUND` without writing state; `--approved-by` is required and recorded in the
  init event alongside `spec_hash_verified: true`. Pass.

All 13 ACs hold in the integrated tree, not just in each package's own review record.

## Cross-package findings (reported, not acted on — none block DONE)

Everything below was already found, argued, and explicitly deferred as debt by the packages' own review panels
and finding-verifiers (recorded in `ai/state/decisions-log.jsonl` / rendered under `docs/notas/decisiones/`,
none phrased as "will fix in integration"). Re-surfacing them here only because the integrator brief asked for
anything relevant even if minor/cosmetic and out of scope:

1. **`cmd_record_review` is the one door into `PACKAGE_TESTING` that never checks `has_open_findings`**
   (unlike `finalize-review-panel` and `record-delta-review`). This is the root of P3's F-03 (which was
   repaired only in its false code comment, not in the underlying asymmetry) and is explicitly out of P3's AC
   scope — every package in flight uses `record-review`, so changing it would be exactly the kind of
   drive-by refactor the harness rules forbid mid-package. Decision:
   `docs/notas/decisiones/2026-07-28 las-cinco-deudas-del-ciclo-de-review-que-p3-nombro-y-no-reparo.md`.
2. **`record-delta-review --new-finding` never stamps `source_role`**, so a finding filed through delta review
   has no author and the anti-self-refutation guard (the same invariant AC-10's F-02 repair hardened for
   `record-late-review`) cannot fire on it. Same decision note as above, item 2. Pre-existing, not introduced
   by 009, and not a defect in any of the three packages' own criteria.
3. **`done_ready` checks whether `data['blockers']` is empty, not whether any entry is unresolved** —
   `cmd_reopen` stamps `resolved_at`/`resolved_by`/`resolved_reason` but never removes the blocker, so a
   feature that was legitimately blocked and reopened can never reach `DONE` without a hand-edit. Verified
   pre-existing (not introduced by P3) and explicitly out of P3's AC-08–11 scope. **Not applicable to
   009-self-application itself** — this feature's `blockers` array is empty, so nothing here stops 009 from
   reaching `DONE`. Flagged only because it is exactly the class of silent-failure defect this feature exists
   to close, and it lives one layer below what 009 touched. Decision:
   `docs/notas/decisiones/2026-07-28 una-feature-bloqueada-y-reabierta-no-puede-llegar-nunca-a-done.md`.
4. **The state machine cannot amend an already-created package** (`owned_paths`, `tasks`,
   `acceptance_criteria`, `objective` are immutable after `create-package`) or retire a superseded one. All
   three packages in 009 hit a live instance of this — each was created with an incomplete `owned_paths` list
   and had to route the gap through `approved_exceptions` instead of amending the package record directly (P3
   alone needed 9 exceptions). Logged as a decision rather than fixed here, correctly: fixing it is a
   state-machine change with a much larger blast radius than any of P1–P3's criteria, and none of AC-01–13
   asks for it. Decision:
   `docs/notas/decisiones/2026-07-28 estado-no-sabe-amendar-un-contrato-revisado.md`.
5. **Unrelated, observed only in passing**: while checking `git status` for 009 cruft, `ai/state/features/003-trusted-routing-pi-runtime.json` shows an uncommitted `block` transition ("spawn budget exhausted") timestamped identically to this integrator's spawn event. That belongs to feature 003, not 009 — not investigated further, not touched, flagged only so the orchestrator is aware there is concurrent activity on another feature's state file in the same working tree.

None of the above are regressions introduced by P1/P2/P3, none are required by any of the 13 ACs, and none
were left as an unresolved "TODO" inside the 009 package records — every one is a logged decision with its own
note. I did not modify any file to address them, per the integrator's scope (no re-opening accepted packages
for out-of-scope findings).

## Verdict

**Ready for DONE.** The sum of P1-knowledge-home + P2-state-machine-required + P3-panel-integrity, as they
exist in the working tree, satisfies all 13 acceptance criteria of contract 1.1.0. No interaction seam between
the three packages produces a defect: P1's file move doesn't confuse P2's commit-history gate, P2's spec-hash
verification in `init` doesn't interact with P3's panel/late-review verbs beyond sharing the same file (kept
byte-identical with `PROYECTO/ai/scripts/feature-state.py` via `build.sh --check`), and P3's replay-detection
refactor (`replayed()`) is used uniformly across every short-circuiting updater, including the ones P1 and P2
did not touch. No orphaned notes, no dangling "fix in integration" markers, no open findings anywhere in the
state file.
