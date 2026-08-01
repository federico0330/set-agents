# Feature 009 — self-application, contract 1.1.0

Status: drafted 2026-07-28 from defects observed while operating the harness on itself. **Challenged
2026-07-28** by an independent read-only `spec-challenger` on a different model than the writer: 11 findings,
5 raised as blockers, verdict `revision_required`. The amendments are written into the criteria below and
listed with their evidence in `## Registro de enmiendas` at the end.

## Contexto

Every defect in this contract has the same shape: **the harness declares a rule and does not enforce it on
itself.** They were not found by reading the code looking for problems. They were found by using the harness
to deliver features 006, 007 and 008 in a single day, and hitting each one.

That shape matters more than the individual bugs. A harness whose value proposition is *"every decision is
delegated, implemented and audited"* loses that value silently when its own declarations are inert, because
nothing fails — the instruction is simply ignored and the session continues looking correct.

### The four defects, all verified

**1. The knowledge layer is addressed at a path that does not exist.**
Ten canonical agent prompts instruct the agent to read `docs/ai/knowledge/<domain>.md` **FIRST if it exists**
(`grep -rl "docs/ai/knowledge" Global/_canonical/agents/ | wc -l` → 10). In this repository `docs/ai/` does
not exist at all.

The layer is **two tiers, and both are real** — the first draft of this contract mistook them for a duplicate
and was corrected. Commit `279c10e` ("per-domain department knowledge, **project layer + global layer**")
created them deliberately:

| Tier | Path the prompts name | Lives today at | Writer | How it reaches a project |
|---|---|---|---|---|
| Project | `docs/ai/knowledge/<dom>.md` | — | only `memory-scribe` | `bootstrap_project.py:130-138` seeds it from `PROYECTO/` |
| Cross-project | `docs/ai/knowledge/_global/<dom>.md` | `knowledge/<dom>.md` (repo root) | the human, promoting | `sync-project.sh:84-96` installs it read-only |

Their contents differ — headers, and `## Candidatos a global` exists only in the project tier — so neither is
redundant, and untracking either one breaks distribution to every project.

The irony is the diagnosis: `PROYECTO/docs/ai/knowledge/` **does exist**, so every project scaffolded by the
harness inherits a working memory layer that the harness itself does not have. The harness never gave itself
the project tier it gives its children, and its cross-project tier sits at a path no prompt names.
`memory-scribe` is declared the only writer of the project tier and has therefore never consolidated anything
here across five delivered features. The conditional *"if it exists"* is what makes the failure silent — the
instruction degrades to a no-op instead of an error.

**2. A feature can be delivered without ever existing in the state machine.**
Feature `006-execution-graph` shipped complete — spec, ADR-0009, code, a concurrent review panel, refutation,
two delta reviews, a final audit, 12 commits, 209 green tests — and `ai/state/features/` contains 002, 003,
004, 005 and **not 006**. `STATUS.md` does not list it and never will. Nothing required the state file to
exist: `feature-state.py init` is a manual orchestrator step with no gate behind it, so delivering outside the
state machine costs nothing and produces no signal.

**3. The review panel accepts members it will later reject, and lies about fixing it.**
Two distinct defects in one command, both hit while reviewing `007-P0`:
- `start-review-panel` without `--role` succeeds and registers a panel with fewer members than the
  orchestrator is about to spawn. The mismatch only surfaces when a subreview returns —
  `role architect is not part of active review panel` — i.e. *after* the spawn has already been paid for.
- `start-review-panel` with an already-existing `--panel-id` returns `ok: true` and **silently adds nothing**.
  A mutating command that reports success while doing nothing is the worst available failure mode: the caller
  believes it has corrected the problem.

**4. A finding that arrives after the panel closes has no channel at all.**
Consequence of (3): finalizing the panel moved the package to `PACKAGE_REPAIR`, from which `record-review` is
also refused. Five verified findings from an independent architect review had to be written to
`decisions-log.jsonl` instead of the package record, where a reader looking at the package will not find them.

## Alcance explícitamente excluido

- **Populating the knowledge layer with content.** This contract makes the organ exist and be reachable, and
  makes `memory-scribe`'s writes land where readers look. Filling it is the natural product of the next
  features closing, not a deliverable to be manufactured now — invented "accumulated invariants" would be
  worse than an empty file.
- **Retrieval beyond files.** No embeddings, no vector store, no reranker. The harness has zero external
  dependencies (`python3 ≥3.11`, no lockfile, CI installs nothing) and retrieval over a repository is
  lexical and agent-driven by design — an exact identifier match beats an approximate one for code.
- **Redesigning the review cycle.** The panel gets the guards it is missing; the two-cycle cap, the
  concurrency rule and the verification node are unchanged.
- **`docs/ai/memory-log.md` in the harness.** AC-01 creates `docs/ai/`, so the question is fair, and the
  answer is out of scope on purpose: `save_memory.py:19-20` does `mkdir(parents=True)` before appending, so
  the general log creates itself on first use and never dangles. No prompt names it, so AC-03's guard does
  not require it either. Creating it empty now would only manufacture a file nobody asked for.

## P1 — knowledge-home

- **AC-01** — the knowledge layer lives where the ten prompts already look, in the harness itself: reading
  `docs/ai/knowledge/<domain>.md` from within this repository resolves.
- **AC-02** — each tier has exactly one home, and both homes are the path the prompts name. The cross-project
  tier moves from `knowledge/` in the repo root to `docs/ai/knowledge/_global/`, its single consumer
  (`sync-project.sh:84`) follows it, and the harness gains the project tier it never had. What stops being
  tracked is the root `knowledge/` directory — not because it was redundant, but because it was the one tier
  living at a path no prompt looks at. `PROYECTO/docs/ai/knowledge/` is untouched: it is the template the
  harness seeds into its children, not a second copy of anything.
- **AC-03** — `verify.sh` fails when a canonical prompt names a path that does not resolve in the harness.
  Scope, so the guard is implementable and its blast radius is known: every backtick-quoted literal under
  `docs/`, `ai/`, `knowledge/`, `tests/`, `Global/`, `PROYECTO/`, `profiles/` in `Global/_canonical/**`;
  templated forms (containing `< > { } * ,`) are skipped because the agent fills them in at run time; every
  remaining path resolves or sits in a waiver set **with its reason written beside it**. A waiver without a
  reason is a hole, not a waiver. This is the guard that makes the class of defect impossible to reintroduce,
  not just this instance of it — and the proof is that it already found a second instance
  (`local-gate-runner.md:6` names `ai/state/002-local-uat-identities-and-feature-state.json`, gone since
  feature 002), which this package also repairs, because a guard that ships failing is not a guard.
- **AC-04** — every path `memory-scribe` is declared to write is a path the readers are declared to read, and
  all of them exist, proven by a test that parses the prompts rather than by inspection. The relation is
  **subset, never equality**: the readers' declared set is strictly larger by design, because each of them
  also reads the `_global/` tier that `memory-scribe.md:25` explicitly forbids the scribe to touch. Set
  equality is unsatisfiable by construction and an AC written that way could never pass.
- **AC-12** — what `save_memory.py --domain` writes is what `memory-scribe` is declared to write. Today
  `memory-scribe.md:18-19` demands entries prefixed `[YYYY-MM][feature-id]` under one of three named sections
  and `save_memory.py:21-22` appends a bare `- <date>: <entry>` to the end of the file. AC-04 cannot catch it
  — that is a path criterion and this is a format one. The layer is being switched on in this package;
  shipping its writer emitting a shape no reader expects would be born broken. Proven by a test that parses
  the resulting file's structure, not one that checks the target path exists.

## P2 — state-machine-required

- **AC-05** — delivering a feature outside the state machine becomes an error instead of silence: work under
  `docs/specs/<feature-id>/` that has reached package delivery while `ai/state/features/<feature-id>.json`
  does not exist fails a gate. **Where that gate lives is the design question this package answers**, the
  same way AC-10 answers its own — because the three candidates are not interchangeable and none of them is
  free. `verify.sh` has no notion of a commit at all; the existing `post-commit` hook cannot fail anything by
  construction (`post-commit:4` ends in `|| true`, and the commit object exists before it runs); a blocking
  `pre-commit` hook would be a class of enforcement this repository has never had. The package names its
  choice and accepts the consequence in writing.
- **AC-06** — the gate does not fire on the pre-approval lifecycle, and it names the remedy when it does. A
  spec is legitimately written and revised during `SPEC_DRAFT` and `SPEC_CHALLENGE`, *before* the state file
  is supposed to exist — a naive check trips on every first draft, on every challenger revision, and on this
  very contract, and `feature-state.py init` is the actively wrong remedy at that moment because running it
  early is AC-13's defect. The gate distinguishes "not there yet" from "never going to be there", and when it
  fires it names the missing feature and the exact command. A guard that reports a violation without the
  remedy just moves the friction; one that reports violations that are not violations gets disabled.
- **AC-07** — feature 006 is **not** backfilled. Reconstructing transitions, spawns and reviews that were
  never recorded produces a record that looks authoritative and is not — the precise failure the file-first
  model exists to prevent. The gap stays visible, pointed at by the decision
  `feature-006-delivered-outside-state-machine`.
- **AC-13** — `init` cannot assert an approval that never happened. `PHASES` contains `REQUIREMENTS`,
  `SPEC_DRAFT`, `SPEC_CHALLENGE` and `USER_APPROVAL`, but `LEGAL_TRANSITIONS` has **no entry for any of
  them**, so `cmd_init:1204` writes `"from": "USER_APPROVAL"` as a label nothing verifies and jumps straight
  to `PACKAGE_PLANNING`. AC-05 closes the *too-late* failure mode — delivering with no record. This closes
  the *too-early* one — opening a record that claims a challenge and an approval that were never performed.
  They are the same defect facing opposite directions, and leaving one open means this feature ships a guard
  its own delivery already walked past: the state file for `009-self-application` carried
  `approved_at: 2026-07-28T13:28:24` while `spec.md:3` still read *"Not yet challenged"*, which is how the
  challenge that produced this criterion found it.

## P3 — panel-integrity

- **AC-08** — `start-review-panel` requires its members to be declared explicitly; a panel cannot be opened
  without naming who will review.
- **AC-09** — `start-review-panel` against an existing `panel_id` is an error, never a silent no-op. If
  extending an open panel is legitimate, it is a distinct operation that says so.
- **AC-10** — an independent review that returns after its panel closed has a sanctioned channel that lands
  on the package record. Which channel, and whether it consumes a deep-review cycle, is the design question
  this package answers — the concurrent panel is by rule *one* cycle, so counting a late member as a second
  cycle would misrepresent the process in the opposite direction. One dead end is named up front so the
  implementer does not spend a cycle rediscovering it: reusing `record-review` or `record-subreview` cannot
  work, because both hard-gate on `phase == "PACKAGE_REVIEW"` (`feature-state.py:1489`, `:1558`) and
  `LEGAL_TRANSITIONS["PACKAGE_REPAIR"]` has no edge back to it. A new phase is **not** required either: a
  phase-agnostic command that appends to `package.findings` is still backstopped by the `has_open_findings`
  check that `package_accept_ready` runs at the acceptance gate (`feature-state.py:435-438`).
- **AC-11** — pre-existing record drift found while tracing these defects is corrected:
  `docs/adr/0009-finding-verification.md` exists on disk but is absent from `docs/adr/README.md`, and
  `docs/specs/003-trusted-routing-pi-runtime/design.md:455` has asserted the opposite of the real exclusion
  behaviour since the FD-008 repair.

## Verificación

`./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → `SELF_SCAFFOLD_SYNC_OK files=2` ·
`python3 -m unittest discover -s tests -v` · `git diff --check` · ownership vs baseline. The test count never
falls from its value at the start of the package's work, and no test is skipped. It is deliberately not
pinned to a number here: the first draft said "rises from 209", which was already stale on the day it was
written — 007 and 008 had moved the baseline to 211 — and a hardcoded historical figure invites the reader to
verify against the wrong thing.

The proof that matters is adversarial, not confirmatory: for each AC that adds a guard, the guard must be
shown **failing** on the defect it was written for before it is shown passing on the fixed tree. A guard only
demonstrated green proves nothing about what it catches.

## Secuenciación

`check-owned-paths.py` validates one package's diff against **its own** declared paths and nothing else —
there is no cross-package or cross-feature collision detection anywhere in this repository, so concurrent
editing of one physical file by two open features has no automatic guard at all. Three other features sit at
`PACKAGE_ACCEPTED` while this one is planned (003, 005, 008) and a fourth at `PACKAGE_PLANNING` (007). The
two files this contract contends for are `ai/scripts/verify.sh` (P1 and P2) and `ai/scripts/feature-state.py`
(P3, plus its byte-identical twin `PROYECTO/ai/scripts/feature-state.py` that `./build.sh --check` keeps in
sync). `005-P1-portable-core` owns both and is `accepted` with `integrated: true`, so it is done editing them
and the collision is latent rather than live. The rule this contract adopts: **P1, P2 and P3 ship strictly in
order**, and no package here begins while another open feature has an unaccepted package declaring the same
file.

## Registro de enmiendas

Contract 1.0.0 → 1.1.0, from an independent read-only challenge on 2026-07-28. Findings the challenge raised
that changed the contract, each verified against the code before it was accepted:

| # | What it attacked | Verified how | Amendment |
|---|---|---|---|
| F-01 | AC-04's "the same paths" | `memory-scribe.md:25` forbids the scribe to touch `_global/`, while `spec-challenger.md:39` and `security-auditor.md:56` declare reading it | AC-04 rewritten as subset over the project tier; set equality is unsatisfiable by construction |
| F-04 | AC-05 named no enforcement point | `verify.sh` takes no commit argument; `post-commit:4` ends in `\|\| true` and runs after the commit object exists; no `pre-commit` hook exists | AC-05 states the outcome and defers the mechanism to the package, the precedent AC-10 already sets here |
| F-05 | AC-05/06's premise | `PHASES` (`:22-26`) contains the four pre-approval phases; `LEGAL_TRANSITIONS` (`:41-54`) has no entry for any of them | **AC-13 added.** The too-early failure mode was wide open, and this feature's own state file had already walked through it |
| F-06 | AC-06's remedy | a spec is legitimately committed during `SPEC_DRAFT`/`SPEC_CHALLENGE`, before `init` is supposed to run | AC-06 now requires the gate to distinguish "not there yet" from "never going to be there" |
| F-08 | silence about `docs/ai/memory-log.md` | `save_memory.py:19-20` calls `mkdir(parents=True)` before appending | named in the exclusions, with the reason it cannot dangle |
| F-09 | no AC covered the write format | `memory-scribe.md:18-19` demands `[YYYY-MM][feature-id]` under a named section; `save_memory.py:21-22` appends `- <date>: <entry>` at end of file | **AC-12 added.** AC-04 reasons about paths and could never catch a format defect |
| F-10 | AC-10's design space | `cmd_record_review:1489` and `cmd_record_subreview:1558` hard-gate on `PACKAGE_REVIEW`; `package_accept_ready` still checks `has_open_findings` at `:435-438` | the dead end is named, and so is the fact that no new phase is needed |
| F-11 | "test count rises from 209" | the suite runs 211 today | pinned to "never falls from its value at package start" instead of a stale number |
| F-07 | nothing sequenced the packages | `check-owned-paths.py` compares one package against its own paths only; 003, 005 and 008 sit at `PACKAGE_ACCEPTED` | new `## Secuenciación` section; `005-P1` owns both contended files but is `integrated: true`, so the collision is latent |

Two findings were planning-artifact defects rather than contract defects, and were fixed in the package plan
when the state file was rebuilt — recorded here because they would each have blocked the package that owns
the criterion:

- **F-03** — P1 declared `owned_paths: ["ai/scripts/verify.sh", "knowledge"]`. `check-owned-paths.py:26` uses
  bare `fnmatch`, and `fnmatch("knowledge/security.md", "knowledge")` is `False`: the pattern matched not one
  file inside the directory it named. P1 could not legally have touched its own AC-01/AC-02 targets.
- **F-02** — P3 did not declare `docs/specs/003-trusted-routing-pi-runtime/design.md`, the file AC-11
  requires it to edit.

The two prior findings that prompted the challenge are recorded where they landed rather than duplicated
here: the two-tier correction is written into defect #1 and AC-02, and the guard's measured blast radius into
AC-03.
