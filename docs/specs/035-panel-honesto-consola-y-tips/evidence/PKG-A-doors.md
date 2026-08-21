# PKG-A · T-001 — Door audit: every way a package can end up in `PACKAGE_TESTING`

> Feature `035-panel-honesto-consola-y-tips`, spec hash
> `296e051fccfd0cea2f222cc7061987f6b66507d9ed2b10539d7e58ea3169331c`.
> Role: `architect`. Measured 2026-08-20 by direct read of `ai/scripts/**`.
> Deliverable of T-001 (`tasks.md:27-47`). **This audit reports; it closes nothing.**

## How completeness is established (not asserted)

`data["phase"]` is the ONLY field that carries the feature phase. Command run:

```
$ rg -n '\["phase"\] *=|\['"'"'phase'"'"'\] *=|update\(\{[^}]*phase' ai/scripts
```

28 hits, of which **26 are assignments** and 2 are `==` comparisons the pattern also catches
(`cli_repair.py:65`, `cli_lifecycle.py:352`). No `.update()`/`setdefault` write of `phase`
anywhere. Of those 26 assignments, **7 can land on `PACKAGE_TESTING`**: five write the
literal (`cli_review.py:55`, `cli_repair.py:281`, `cli_repair.py:338`,
`cli_reporting.py:497`, `feature-state.py:867`), two write a variable
(`args.to_phase` at `cli_lifecycle.py:273`, `to_phase` at `cli_reporting.py:429`) whose
`PACKAGE_TESTING` value is legal per `LEGAL_TRANSITIONS` (`model.py:41-43`). Every one of
the seven is in the table below. The other 19 assignments target `PACKAGE_REPAIR`,
`DELTA_REVIEW`, `PACKAGE_REVIEW`, `PACKAGE_RUNTIME_QA`, `PACKAGE_ACCEPTED`,
`PACKAGE_PLANNING` or `BLOCKED`. `model.py`, `transitions.py`, `cli_modules.py`,
`cli_integration.py` and `render_status.py` write `phase` nowhere.

`ai/scripts/**` and `PROYECTO/ai/scripts/**` are line-for-line identical on all four
modules involved (verified with `rg -n PACKAGE_TESTING` over both trees: same file, same
line numbers). Every `file:line` below therefore applies to both copies, which is what
AC-A.7 requires and what makes the golden suite (`tests/test_harness.py:32`, which runs the
`PROYECTO/` binary) able to see the change.

## The seven doors

| # | door (verb / call site) | `file:line` that sets `PACKAGE_TESTING` | checks `has_open_findings`? | checks panel membership? | this slice |
|---|---|---|---|---|---|
| 1 | `record-review --verdict pass` | `feature_state_lib/cli_review.py:55` | **NO** | **NO** | **CLOSED HERE** (AC-A.1, AC-A.4) |
| 2 | `finalize-review-panel --verdict pass` | `feature_state_lib/cli_review.py:161` | **YES** — `:159-160`, `{critical, high, medium}` | **YES**, at two points: panel open rejects a panel missing a required role (`feature-state.py:576-583`), finalize rejects missing subreviews (`cli_review.py:136-138`) | unchanged |
| 3 | `record-delta-review --verdict pass` | `feature_state_lib/cli_repair.py:338` | **YES** — `:335-336`, same three severities | n/a (the panel that produced the findings already ran) | unchanged |
| 4 | `record-repair --skip-delta` | `feature_state_lib/cli_repair.py:281` | **NO** — the guard at `:246-253` inspects only `repaired`, i.e. the findings named by `--finding-id` on *this* call; an open finding that was never repaired travels through untouched | n/a | **NAMED NO-GOAL 12** — stays open by decision, `docs/notas/decisiones/2026-08-20 035-skip-delta-fuera-del-slice.md` |
| 5 | `transition --to-phase PACKAGE_TESTING` | `feature_state_lib/cli_lifecycle.py:273`, gated by `transitions.check_transition` (`transitions.py:33-38`) | **YES** — `:37-38`, same three severities | **indirectly**: `:35-36` requires `package["reviews"]` non-empty with a last verdict of `pass`/`repair_required`, and `reviews[]` has exactly two writers — `cli_review.py:45` (`record-review`) and `cli_review.py:147` (`finalize-review-panel`). Once door 1 is closed for FULL panels, the only way to populate `reviews[]` on a FULL package is the panel itself | unchanged (closes derivatively — see below) |
| 6 | `record-verification` all-refuted fast path | `feature-state.py:867`, guarded at `:862` | **YES, AND STRICTER** — `has_open_findings(package)` with `severities=None`, which by `model.py:751-757` returns `True` for a non-terminal finding of *any* severity, `low` included. The branch fires only when the open set is empty | n/a (this door is downstream of a review that already happened; it also requires `_repair_entered_from_review`, `cli_review.py:223-252`) | unchanged — **newly enumerated, see "Not a HUMAN_DECISION_REQUIRED" below** |
| 7 | `run_dry_workflow` synthetic self-demonstration | `feature_state_lib/cli_reporting.py:497` (and `:429` via `check_transition`) | n/a | n/a | **not a door.** It builds an in-memory `base_state(feature_id, ..., "dry-run")` at `:422` and never loads or writes a real `ai/state/features/*.json`; its findings are literals it wrote itself at `:460-463`. It is a self-test of the lifecycle, not a mutation surface |

## Verbs checked and confirmed NOT to be doors

- `record-late-review` (`feature-state.py:683-774`). Appends to `late_reviews[]` (`:754`),
  never to `reviews[]`, and emits its event with `data["phase"], data["phase"]` (`:769`) —
  the phase is unchanged by construction. Worth stating explicitly because the comment
  this slice rewrites (`transitions.py:101`) records that an earlier version of that branch
  blamed exactly this verb and was wrong.
- `next_transition` (`transitions.py:58-133`), including the advisory branch at `:95-109`.
  It returns a recommendation dict and mutates nothing.
- `record-testing` (`cli_repair.py:359-397`) reads `PACKAGE_TESTING` as a precondition
  (`:363`) and leaves it (`:374`, `:388`); it never enters it.

## No unforeseen door — and why door 6 is not one

T-001's stop condition (`tasks.md:42-47`) is an unforeseen door, i.e. one that lets a
package sit in `PACKAGE_TESTING` with a blocking finding open and that this contract did
not anticipate. **Door 6 was not in the spec's enumeration** (`spec.md:545-552` lists four
verbs; the audit finds six real ones plus one synthetic), so it is reported here as new —
but it is **not a hole**, and inventing a guard for it would be inventing a guard for an
invariant that already holds more strictly than the one PKG-A is installing:

- The target invariant is "no `{critical, high, medium}` finding open".
- Door 6's guard is "no finding open at *any* severity" (`model.py:755`, `severities is
  None` branch). That is a strict superset of the target: every state door 6 admits is a
  state doors 2, 3 and 5 would also admit.

So the honest report is: **six real doors, five guarded, one (`record-repair
--skip-delta`) deliberately left open by DEC-SKIP-DELTA-OUT.** No `HUMAN_DECISION_REQUIRED`
is raised, and no guard is invented outside `record-review`.

Two consequences the implementer must carry, both load-bearing for T-007:

1. **`PACKAGE_TESTING` + open blocking finding stays reachable** after this slice, through
   door 4. The advisory branch at `transitions.py:96-109` therefore stays alive and its new
   comment must name door 4 (`cli_repair.py:246-253` + `:280-282`) and cite
   `docs/notas/decisiones/2026-08-20 035-skip-delta-fuera-del-slice.md`. A comment claiming
   unreachability would be false on the day it is written.
2. **Door 5 needs no new code.** Its membership closure is *derived* from door 1's, not
   independent of it: `reviews[]` has two writers and both will be membership-aware after
   PKG-A. This derivation is stated so nobody later "hardens" `check_transition` on the
   belief that it is a second hole — it is the same hole, seen from downstream. It is also
   the reason `package_accept_ready` (`model.py:800-827`) is deliberately left alone: see
   `design.md` § "Where the predicate lives".

## Commands run for this audit

```
$ rg -n "PACKAGE_TESTING" ai/scripts
$ rg -n '\["phase"\] *=|\['"'"'phase'"'"'\] *=' ai/scripts
$ rg -n 'setdefault\("reviews"|\["reviews"\]\.append|late_review' ai/scripts
$ rg -n "PACKAGE_TESTING" PROYECTO/ai/scripts/feature_state_lib/{cli_review,cli_repair,transitions}.py PROYECTO/ai/scripts/feature-state.py
```
