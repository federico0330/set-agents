# Context pack — 009-P3 `panel-integrity`

Delimited by structure, not by a file list: the surface is the **review-panel command family** of
`ai/scripts/feature-state.py` (and its byte-identical twin `PROYECTO/ai/scripts/feature-state.py`), plus the
two drifted records AC-11 names.

## The three defects, all found by using the cycle rather than reading it

Recorded live in `docs/notas/decisiones/2026-07-28 start-review-panel-silent-noop.md` and
`docs/notas/decisiones/2026-07-28 p0-architect-findings-outside-package-record.md`, while reviewing `007-P0`.

1. **A panel opens with nobody declared.** `cmd_start_review_panel` falls back to
   `args.role or ["package-reviewer"]`, so a panel registers fewer members than the orchestrator is about to
   spawn. The mismatch surfaces only when a subreview returns — `role architect is not part of active review
   panel` — i.e. after the spawn is already paid for.
2. **Correcting it reports success and does nothing.** A second `start-review-panel` against a live
   `panel_id` returns `{"ok": true, "changed": false}` and adds no role. A mutating command that reports
   success while doing nothing is the worst available failure mode: the caller believes it corrected the
   problem.
3. **A late reviewer has no door.** Finalizing the panel moves the package to `PACKAGE_REPAIR`, and
   `record-review` and `record-subreview` both hard-gate on `phase == "PACKAGE_REVIEW"` while
   `LEGAL_TRANSITIONS["PACKAGE_REPAIR"]` has no edge back. Five verified architect findings had to be written
   to `decisions-log.jsonl`, where a reader looking at the package will not find them.

## The fourth defect, which the contract did not know about

Measured during exploration and reproduced against a scratch state file before any fix:

`panel_id` defaults to `RP-{deep_review_cycles + 1:02d}`, derived from the counter this same command
increments. `record_event` deduplicates on `event_id` and returns `False`, and **every caller ignores that
return value**. So a retry of `start-review-panel` with the same `--event-id` and no explicit `--panel-id`:

- mints `RP-02` instead of colliding with `RP-01`,
- takes `deep_review_cycles` to 2 — the whole budget,
- strands `RP-01` `in_progress`, where `record-subreview`'s `reversed(...)` scan will never reach it again,
- writes the state with a bumped `revision` and **no history entry**,
- and makes the next legitimate panel open **block the feature** with `deep review budget exhausted`.

It only manifests under real timeouts, and no test covers it. It is the reason AC-09's fix is a replay
short-circuit placed **before** the phase gate, not an unconditional raise.

## Invariants the package must not break

- **The panel is one deep-review cycle no matter how it grows.** `extend-review-panel` must not touch
  `attempts.deep_review_cycles` or `metrics.package_reviews`.
- **`package["reviews"]` proves a deep review happened.** `package_accept_ready` reads it both as
  `reviews[-1].verdict` and as a non-empty existence check, and `check_transition` / `next_transition` read
  `reviews[-1]` too. A late review must therefore land in its own list, never there — otherwise the exception
  channel becomes a way to skip review entirely.
- **A finding must carry who raised it, and the filer must not get to choose it.**
  `cmd_record_verification` compares `finding["source_role"]` against the actor to stop someone refuting their
  own finding. An ingress that omits `source_role` becomes the one way to file a finding you are then allowed
  to kill yourself — and so does one that lets the filer supply it, which is why `source_role` sits in
  `FINDING_BOOKKEEPING` and is refused at birth rather than merely defaulted.
- **"This exact call already ran" is keyed on the command, not only on the id.** `replayed()` is the single
  definition, shared by `record_event` and by every updater that short-circuits, so the two can never disagree
  about whether a call is a retry. Keyed on the id alone, an `--event-id` reused across two different commands
  made the second one a silent no-op.
- **Findings enter through `normalize_findings` + `merge_finding`, never a blind append.** The first refuses a
  finding born terminal or carrying its own bookkeeping; the second archives a stale verdict into
  `verification_history` when a finding is re-raised.
- **Refusals go out as `{"ok": false, "error": …}` on stdout.** `argparse`'s `required=True` writes a usage
  dump to stderr instead, which neither the test suite nor any agent parsing this CLI can read.
- **The two `feature-state.py` copies stay byte-identical** (`./build.sh --check` → `SELF_SCAFFOLD_SYNC_OK
  files=2`), and the test suite drives the `PROYECTO/` one.

## Out of scope, recorded rather than fixed

The review cycle is not redesigned: the two-cycle cap, the concurrency rule and the verification node are
unchanged. Feature 006 is not backfilled. Four pre-existing defects found while tracing the call graph
(ignored `record_event` return value across ~15 commands, `record-delta-review` not setting `source_role`,
`next_transition` advising `DELTA_REVIEW` with nothing to repair, `--allow-missing` being all-or-nothing) are
logged as decisions, not repaired here.
