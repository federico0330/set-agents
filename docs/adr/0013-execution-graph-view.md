# ADR-0013 — Execution graph view: derived-in-read, closed edge vocabulary, fail-open commits

- Estado: Accepted (2026-07-30). Feature `006-execution-graph`, contract 1.2.0, package
  P3-graph-view, AC-20..AC-29. This is the first ADR for the graph surface; P1
  (false-edges) and P2 (finding-verification, ADR-0009) shipped before this package and
  are unaffected — this ADR only covers what P3 adds. Superseded in part by ADR-0014
  (2026-07-30): D1/D3's claim that spawn nodes are deferred to a future "P3.1" is
  superseded by `010-spawn-provenance`, which built that P3.1 and adds a `spawn` node type;
  every other decision below (D1's derive-in-read design, D2, D4, D5) is unaffected and
  this note changes nothing else in this file.
- Every file:line citation below was verified against the working tree on 2026-07-30
  (`ai/scripts/feature-state.py`, current at the time of writing — line numbers move as
  the file grows, the citation is to the function name they belong to as much as the
  number).
- Two decisions carried over verbatim from `docs/specs/006-execution-graph/spec.md`'s
  amendment log (second `SPEC_CHALLENGE` pass) rather than re-litigated here: `--commit`
  stays in scope (real caller from day one — `repair-agent` knows its own commit) and
  `--caused-by-spawn` is deferred to a future P3.1, gated on a doctrine decision (who
  mints a spawn's event id and how it reaches the three runtimes' canonical prompts) that
  is out of this package's scope. Recorded here because both are load-bearing for D2/D3
  below, not because either was reopened.

## Contexto

The delivery lifecycle already IS a graph — nodes are bounded assignments (findings,
reviews, verifications, repairs), edges are the data that crosses between them — but
nothing rendered it. A finding's provenance (who raised it, who verified or refuted it,
what repaired it, which commit) lived only inside `ai/state/features/<fid>.json`, legible
to `jq` and to nobody navigating by eye. Three constraints shaped the design, all
verified against the tree before anything was decided:

1. **The state files are already the source of truth for everything the graph would
   show.** A finding's severity, its verifier, its repair's `changed_files` — every field
   AC-27 needs for a navigable label already exists on `package["findings"]`,
   `package["verifications"]`, `package["repairs"]`. Building a second store that
   duplicates this is either always in sync (free, since it derives from the same read)
   or a second thing that can drift from the first (never free). The choice was never
   close.
2. **The joins the graph needs are structural, not temporal.** A finding's `produjo` edge
   is "this id appears in `review_panels[].subreviews[].findings`", not "this event and
   this finding share a timestamp" — the latter breaks the moment two records share a
   timestamp by construction (a blocker and the `history` event recorded in the same
   call, which happens on every `block_with_reason` call). AC-20 states this as a hard
   rule for exactly this reason.
3. **`record-repair` had no way to name the commit that closed a finding.** `changed_files`
   names paths, never a sha, so "the commit that repaired it" (this package's own scope
   line) was structurally unreachable before AC-21.

## Decisión

### D1 — Derived-in-read, no new store, no materialized index

`build_execution_graph(root, feature_ids)` (`ai/scripts/feature-state.py:1510`) walks
`<root>/ai/state/features/*.json` on every call and returns an in-memory `_GraphState`
(`:1304`) — nodes and edges built fresh from the JSON already on disk. There is no
`graph.json`, no cache, no incremental update path, and nothing new that
`accept-package`/`record-repair`/any mutating command has to keep in sync. The entire
feature is read-only against data every other command already owns and writes.

**Rejected: a materialized graph file regenerated on every `mutate()`.** Two independent
reasons, not one: it duplicates data that already has one writer per file (`owned_paths`
doctrine, unchanged here), and it makes every future field added to a finding/review/
repair a two-place change (the record, and the graph mirror of the record) instead of a
one-place change the graph function picks up automatically the next time it runs. The
derive-in-read cost is real (`build_execution_graph` re-parses every requested state file
per invocation) but bounded by the same thing that already bounds `render_notes` and
`render_status`: the number of features and packages a harness install tracks, not a
number that grows without limit.

### D2 — Mermaid emission is stdlib-only, validated by concrete structural assertions

`render_mermaid` (`:1610`) emits plain text via string formatting — no `mermaid-py`, no
templating library, no new dependency in `requirements`/`pyproject`. "Valid mermaid" is
not asserted by the unfalsifiable phrase; `validate_mermaid_structure` (`:1550`) checks
five concrete things the spec names (AC-22): first non-empty line is exactly
`flowchart TD`; every node id matches `[a-z0-9_]+` and avoids mermaid's reserved words
(`end`, `graph`, `subgraph`, `o`, `x`); every `subgraph` has a matching `end`; labels are
quoted with `"`, `[`, `(`, and newlines escaped (`_mermaid_escape`, `:1294`); and no
`subgraph` id ever equals a node id — guaranteed structurally by drawing subgraph ids from
a disjoint `sg_` prefix (`:1610`-`1631`) rather than asserted after the fact and hoped for.
`render_mermaid` calls this validator on its own output before returning
(`:1636`-`1641`) — a bug in the generator surfaces as a loud `StateError` against the
generator's own test suite, never as silently-shipped broken mermaid a human discovers in
Obsidian.

**Rejected: a mermaid library.** Nothing in this repo's dependency set renders diagrams
today, and mermaid's own grammar for what this package needs (nodes, nested subgraphs,
labelled edges) is small enough that hand-emitting it with an escaping function and a
validator is less code and less supply chain than a dependency whose validation surface
(does it escape the way THIS repo's tests assert) still has to be written regardless.

### D3 — A closed, five-member edge vocabulary; spawn nodes explicitly out of scope

`GRAPH_EDGE_TYPES = ("produjo", "verificó", "refutó", "reparó", "bloqueó")` (`:1283`) is
closed by construction: every edge `_add_package_findings`/`_add_feature_to_graph`
(`:1362`, `:1479`) emits uses one of these five literal strings, and
`validate_mermaid_structure` rejects any edge label outside the set. Direction is fixed
per type and stated once here rather than left to be re-derived from the code on every
read: `produjo`/`verificó`/`refutó`/`reparó` run FROM the record that did the work (review,
verification, repair) TO the finding (and, only for `reparó` with a declared `--commit`,
onward from the repair to a second, sibling `commit` node — "reparó stops at the finding"
per AC-21 describes exactly the case where that second edge is simply absent, not a
special-cased shorter chain). `bloqueó` runs FROM the container (`package` when the
blocker's `package_id` matches a known package, `feature` in the other three cases AC-26
names explicitly) TO the blocker — spec'd this direction explicitly in AC-26, the one edge
type whose direction is not "producer to finding".

Spawn nodes are named in P3's own scope line (the "bounded assignment" metaphor that
motivates the whole feature) but never built: **P3.1, not P3, and only after a
prerequisite decision.** The challenger's second `SPEC_CHALLENGE` pass measured this
directly — zero of the eight non-006 features in this repo, and P3 itself, pass an
`--event-id` to `record-spawn` today, across all three runtimes' orchestrator doctrine.
`--caused-by-spawn` would be a flag with no real caller, exercised only by fixtures
invented for the purpose. Building it now would be scope creep the spec explicitly
declined twice (first and second amendment log entries). It stays deferred until a
separate package decides who mints a spawn's event id and how it reaches the three
runtimes' canonical prompts — a doctrine change, not a graph change, and not this
package's to make unilaterally.

### D4 — `--commit`: format-gated, then fail-open against a possibly-unusable git

`record-repair --commit <sha>` (`ai/scripts/feature-state.py:2634`) accepts an optional
sha, gated on format BEFORE any git lookup (`COMMIT_SHA_RE`, `:2590`, 7-40 hex —
git's own abbreviation floor and the full sha length; `abcd` is well-formed hex but
rejected on format alone, never reaching git). Past the format gate,
`validate_commit_ref` (`:2602`) is deliberately **fail-open**: it checks
`git rev-parse --is-shallow-repository` first, and only treats a `cat-file -e` failure as
a real rejection when git is a full, non-shallow, answerable repository. Absent git,
a non-repo cwd, or a shallow clone all mean "git cannot answer this question", which is a
different claim from "the sha does not exist" — the exact posture
`ai/scripts/check-feature-state.py:79-90` already documents and this package reuses
rather than reinvents. `_git_answer` (`:2593`) is the one shared read-only-subprocess
helper both checks route through.

**The tension is named, not accidental.** Under fail-open with git unavailable, any
well-formed 7-40 hex string becomes a `commit` node in the graph — narrower than AC-20's
general promise ("missing data means a missing edge, never a fabricated one") for this one
case specifically. The alternative — fail closed when git cannot answer — was rejected
because it repeats the exact defect `check-feature-state.py`'s own history documents: a
shallow CI clone or a repo checked out without `.git` (a packaged release, a worktree
export) would then block a legitimate `repair-agent` call from ever recording its own
commit, for a reason that has nothing to do with whether the repair happened. The graph
never distinguishes a verified commit node from an unverified one visually — only
present/absent — so a caller inspecting the rendered graph cannot be misled into thinking
an unverified commit was checked; the state file itself does not record verification
status either, only the sha.

**Rejected: guessing the commit from `git log` against `changed_files`.** AC-21 states
this explicitly and this ADR restates the reasoning: a repair's `changed_files` list can
match several commits (a shared file touched by an unrelated change) or none (a repair
whose commit was later rebased/squashed), and a guessed commit that happens to be wrong is
strictly worse than an absent one — it actively misdirects a reader tracing a finding to
its fix. The `reparó` chain stops at the finding when no `--commit` was declared, full
stop; nothing downstream of that is inferred.

### D5 — Plain `reviews[]` actor: stamped on the record, positional join only as a
### backward-compatible fallback, and only when it cannot mislead

Every source `_add_package_findings` (`:1391`) joins for a `produjo` edge label carries its
own actor/role directly on the record it reads, **except** the plain `record-review` path
(`reviews[]` entries with no `panel_id`) — that record originally had no actor field, so
the label was built by pairing `plain_reviews[index]` with `review_events[index]`
(the same-named `record-review` history events for that package) **by position**, relying
on both lists being appended in the same call order.

That assumption broke for one real call shape: `cmd_record_review` with `verdict:
"blocked"` appends the review to `reviews[]` and then returns via `block_with_reason`
**before** its own `record-review` history event is ever emitted (`:2141` region — a
`block` event is recorded instead). The two lists permanently diverge in length at that
point, and every plain review recorded after a blocked one pairs against the wrong history
event — a security-auditor PoC (two `record-review` calls, one `blocked` then one
`repair_required`) confirmed the second review's actor was attributed to the first, and the
first showed no actor at all. A fabricated attribution is worse than a missing one: AC-20
promises "missing data means a missing edge, never a fabricated one," and the same
principle extends to node labels, not only edges.

**Fix, in order of preference:**
1. `cmd_record_review` now stamps `"actor": args.actor` directly on the record it appends
   to `reviews[]` — additive, so no reader of the existing keys breaks. This is the
   record's own actor from here on; no join is needed for anything written from this point
   forward.
2. The positional join against `record-review` history events is kept **only** as a
   fallback for reviews that predate the stamp (real feature state files already on disk)
   and **only** when `len(plain_reviews) == len(review_events)` for that package. When the
   two lists have diverged — the exact shape the `blocked` early-return produces — the
   join is skipped entirely rather than paired against a plausible-but-wrong index: the
   label degrades to the verdict alone, actor omitted.

This was not previously named as a risk anywhere in this ADR; the original D1-D4 drafting
did not anticipate that an early `return` inside a command could desynchronize two lists
the join logic assumed were structurally locked together. The general lesson generalizes
beyond `reviews[]`: any future source added to this join whose actor is read by pairing
with a SEPARATE list (rather than carried on the record itself) inherits the same risk
class, so new sources should prefer stamping the actor on their own record, per (1) above,
over inventing a new positional pairing.

## Consecuencias

- Every future field added to a finding/review/verification/repair/blocker record is
  visible in the graph automatically the next time `graph`/`sync-notes` runs, with zero
  changes to any mutating command — the derive-in-read design (D1) is what makes this
  free.
- `set-agents --graph` (AC-25, `ai/scripts/set_agents_app.py:cmd_graph`) and
  `render_notes`'s `grafo.md` (AC-24) both call the exact same
  `build_execution_graph`/`render_mermaid` pair `feature-state.py graph` uses — there is
  exactly one place the join logic lives, so a fix or an added edge type lands in three
  surfaces at once instead of needing to be ported.
- A `record-repair --commit` call against a shallow clone or a git-less environment
  silently accepts an unverified sha (D4's named tension). This is discoverable only by
  reading the state file's `repairs[].commit` field directly against a real git host —
  the graph itself gives no visual signal. Tracked as an accepted risk, not a defect: the
  alternative (fail closed) actively blocks legitimate repairs, which is worse.
- Spawn nodes remain absent from every graph this package renders, including for features
  with heavy spawn activity (e.g. 009-self-application). A reader following a finding
  cannot yet see which spawn raised the review that produced it — only the review record
  itself. This is P3.1's opening, not a defect in P3: recorded in
  `docs/specs/006-execution-graph/spec.md`'s amendment log and in
  `ai/state/decisions-log.jsonl` (`log-decision`, this package), not left as an implicit
  gap someone has to rediscover.
- `feature-state.py` gains no new third-party dependency (D2): mermaid emission is
  ~150 lines of stdlib string handling plus its own validator, not a library integration.
