# ADR-0014 — Spawn provenance node: a package-scoped mint, not a rename of `run_id`

- Estado: Accepted (2026-07-30). Feature `010-spawn-provenance`, contract 1.0.0, package
  P1-spawn-provenance, AC-01..AC-05. Supersedes in part: `docs/adr/0013-execution-graph-view.md`
  D1 and D3, only for the single claim "spawn nodes are out of P3's scope, deferred to a
  future P3.1" — every other decision in ADR-0013 (D1's derive-in-read design, D2's
  stdlib-only mermaid emission, D4's fail-open commit, D5's actor-join fallback) stands
  unchanged and this ADR does not touch them. The deferred work ADR-0013 D3 named as
  "P3.1" is this feature, `010-spawn-provenance` — not a package of `006-execution-graph`
  (see "Origen" in `docs/specs/010-spawn-provenance/spec.md` for why it could not be).

## Contexto

`006-execution-graph`'s P3 built `build_execution_graph`/`render_mermaid`
(`ai/scripts/feature-state.py`) as a derive-in-read view over every record a package
already owns — findings, reviews, verifications, repairs, blockers — but named spawn
nodes as a deliberate gap: "P3.1, not P3, and only after a prerequisite decision" (ADR-0013
D3). That decision was **who mints a spawn's event id and how it reaches the three
runtimes' canonical prompts** — a doctrine change across `Global/opencode`,
`Global/claude-code`, `Global/codex`, and this feature's own `SPEC_CHALLENGE` history
(inherited from an earlier attempt to open this same work as `006-P3.1`) rejected making
that change twice, because `--caused-by-spawn` — the edge the doctrine change would
enable — would ship with zero real callers across all eight non-006 features in this
repo. This ADR records the smaller decision that IS in scope now: minting `spawn_id` as
its own first-class identity, so the graph can show a package's spawn spend today, and so
the doctrine work (if it ever happens) has a join key already waiting for it instead of
having to invent one under time pressure.

A second question this ADR has to answer directly, because it is the obvious thing to get
wrong: does `spawn_id` replace, wrap, or relate to `run_id`
(`ai/scripts/routing_core/store.py`)? They look similar (both are minted, package/run-scoped
identifiers attached to a delegation-shaped event) and it would be easy to assume one
subsumes the other. It does not, and the reasons are structural, not incidental.

## Decisión

### D1 — `spawn_id` mints a NEW identity; it does not replace, wrap, or read `run_id`

`spawn_id = f"SPAWN-{attempts['spawns']:03d}"` (`cmd_record_spawn`,
`ai/scripts/feature-state.py`) is a deterministic, package-scoped counter minted inside
`ai/state/features/<fid>.json` — the JSON state file every package-workflow command
already owns and writes. `run_id = "run1_" + secrets.token_hex(16)` (`store.py:311`) is a
cryptographically random, globally unique key inside `routing_core`'s own SQLite
`dispatches` table (`ai/scripts/routing_core/store.py`), governing a completely different
lifecycle: provider/model/route selection, fallback windows, and terminal outcomes for one
Pi-lane dispatch (ADR-0005/ADR-0007/ADR-0008).

These are not two names for the same fact:

- **Different scope.** `spawn_id` is scoped to one package inside one feature's state file
  — `SPAWN-001` in `010-spawn-provenance`'s `P1-spawn-provenance` package means nothing
  compared against `SPAWN-001` in a different package's `spawns[]`; only `(feature_id,
  package_id, spawn_id)` together is a unique key, and the graph's own `add_node` already
  disambiguates on exactly that tuple (`_GraphState.add_node`). `run_id` is globally unique
  by construction (32 random hex bytes) with no feature or package in its own identity —
  `routing_core` does not know what a "package" is.
- **Different write path and different failure model.** `spawn_id` is minted by a single
  Python process appending JSON via `atomic_write` (temp file + `os.replace`), guarded by
  `replayed()` against a retried `--event-id`. `run_id` is minted and persisted through
  SQLite's own transactional guarantees (`BEGIN IMMEDIATE`, `CHECK` constraints on the
  column itself), because the Pi lane needs concurrent-dispatch safety this JSON file was
  never built for and does not need.
- **Different question each answers.** A `spawn_id` answers "which delegation, inside
  which package, produced this review/finding/repair" — a bookkeeping and (eventually)
  provenance question for the package-workflow state machine. A `run_id` answers "which
  provider/model/route did this ONE routing decision actually dispatch to, and what did it
  cost" — an operational question for the routing/cost-accounting subsystem. Collapsing
  them into one identifier would force one system to answer a question that is not its own
  either by faking data (a `spawn_id` field bolted onto `dispatches`, or a `run_id` bolted
  onto `spawns[]`) or by taking a hard runtime dependency neither had before (the graph
  render, which is pure Python reading JSON files, would need a live SQLite connection to
  render a package's spawn history).

**Rejected: `spawn_id` IS `run_id`, reused verbatim.** Every real spawn does not
necessarily open a Pi-lane dispatch — the earlier `SPEC_CHALLENGE` pass measured this
directly: zero of the eight non-006 features in this repo pass an `--event-id` derived
from a live `run_id` into `record-spawn` today. Requiring one would mean `record-spawn`
either fabricates a `run_id`-shaped value that never went through `routing_core`'s own
authorization path (a fabricated identity, the exact defect class ADR-0013 D5's actor-join
fix was written to eliminate for a different field) or blocks recording a spawn at all
absent a live Pi dispatch — which would make `record-spawn` (mandatory before every
delegation, per ADR-0011) newly dependent on a runtime the harness treats as optional.

**Rejected: `spawn_id` wraps/embeds `run_id` as a substring or foreign key.** This assumes
every spawn has exactly one corresponding dispatch, which is false today (a spawn can be a
non-Pi delegation entirely) and would still leave the two systems' failure models coupled
for no benefit this feature's own scope needs — `--caused-by-spawn` is deferred (see
"Contexto"), so nothing today reads a spawn's corresponding run, if one even exists.

### D2 — The renamed deferral: this feature is ADR-0013 D3's "P3.1"

ADR-0013 D3 named the future work "P3.1" without naming what it would be called. This ADR
records, for anyone tracing that reference forward, that the answer is `010-spawn-provenance`
— opened as its own feature rather than a package of `006-execution-graph`, because
`006`'s `data["acceptance_criteria"]` froze at `AC-20..AC-29` from its own `init` (the only
command that writes that list) and refuses to re-open without a destructive `--force` that
would erase already-accepted package history (see `docs/specs/010-spawn-provenance/spec.md`,
"Origen"). `docs/specs/006-execution-graph/spec.md` itself is not edited by this ADR or by
010's package — its "no spawn nodes in P3" text was exact for what P3 built and does not
need to be rewritten for a different feature's later addition over the same shared code.

### D3 — `--caused-by-spawn` and its edge remain deferred, unchanged from ADR-0013

This feature adds the `spawn` node type (AC-02) with **zero edges** — inventory visible
next to a package's findings/reviews/repairs, not a navigable provenance chain. The
doctrine-change prerequisite ADR-0013 D3 named is still not met: no caller in any of the
three runtimes passes a `run_id`- or otherwise-derived event id capable of joining a spawn
to the finding it produced. That decision is explicitly out of this feature's scope too
(see `docs/specs/010-spawn-provenance/spec.md`, "Alcance explícitamente excluido") and
remains open for whichever future package finally has a real doctrine change to make it
worth building.

## Consecuencias

- `ai/scripts/feature-state.py`'s `graph` subcommand, `set_agents_app.py --graph`, and
  `render_notes`'s `grafo.md` (the same three surfaces ADR-0013 already unified on one
  `build_execution_graph`/`render_mermaid` pair) now also show a package's spawn spend —
  free, by the same derive-in-read design ADR-0013 D1 established, since `_add_package_spawns`
  reads `package["spawns"]` the same way every other join reads its own source list.
- `routing_core/store.py` gains no new column, no new table, and no new caller from this
  feature. `spawn_id` and `run_id` remain two independent identifiers for two independent
  systems; nothing here creates a join between them, and nothing here promises one will
  exist later.
- A reader tracing a finding still cannot answer "which spawn raised the review that
  produced this" — only that some spawn happened, visible as an unconnected node in the
  same package's subgraph. This is D3's named limit, not a defect: recorded here and in
  `docs/specs/010-spawn-provenance/spec.md`'s "Alcance explícitamente excluido" so the next
  reader does not have to rediscover why the edge is missing.
- `docs/adr/0013-execution-graph-view.md` keeps its `Accepted` status and every one of its
  own decisions (D1, D2, D4, D5) unchanged; only its status line and its row in
  `docs/adr/README.md` gain a `Superseded in part by ADR-0014` note, per this index's own
  rule that a decision is never rewritten retroactively, only annotated and superseded
  forward.
