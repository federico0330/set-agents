# Feature 006 — execution-graph, contract 1.2.0

Status: P1 and P2 delivered and accepted (both entregados fuera de la máquina de estados — ver
`docs/notas/decisiones/2026-07-28 feature-006-delivered-outside-state-machine.md` — y cubiertos por el waiver
`006-execution-graph` en `ai/scripts/check-feature-state.py`, que P3 retira). P3 ya no está bloqueado:
`005-P2-vault-mandatory` está `accepted` (ADR-0012, 2026-07-29). Contract bumped 1.1.0 → 1.2.0 to add P3's
own ACs (AC-20..AC-29, P2 stopped at AC-19). **`SPEC_CHALLENGE` corrió cuatro veces sobre esta enmienda**:
`revision_required` en las primeras tres pasadas (11+5+5 hallazgos bloqueantes en total, 4 preguntas al
usuario solo en la primera), todos aplicados abajo en los tres "Amendment log" sucesivos.

## Amendment log — what contract 1.0.0/1.1.0 got wrong

- P3's scope existed only as prose, with no numbered, verifiable ACs — unjudgeable as a package contract.
  AC-20..AC-29 make each element of that prose (typed edges, mermaid emission, finding navigability, vault
  degradation) independently testable.
- The header claimed P3 was blocked on `005-P2-vault-mandatory`; that package has been `accepted` since
  2026-07-29 and the header was never updated. Corrected here, not silently — the stale claim is exactly the
  kind of defect this feature's own P2 (finding-verification) exists to catch when it appears in a review
  finding instead of a spec header.
- The P2 heading below (`## P2 — finding-verification`) still said *"delivered, pending review"* after P2 was
  already `accepted` — the exact same class of stale-header defect as the previous bullet, caught by the same
  `SPEC_CHALLENGE` pass that found it. Corrected to `delivered, accepted`.

## Amendment log — segunda pasada de `SPEC_CHALLENGE` (contract 1.2.0, sin bump de versión — corrige la
misma enmienda antes de `init`)

Decidido con el usuario, por cada hallazgo bloqueante que requería una decisión de producto:

- **`--caused-by-spawn` sale de P3.** El challenger midió que ninguna de las 8 features del repo pasa hoy un
  `--event-id` a `record-spawn` — la doctrina del orquestador nunca lo hace en los 3 runtimes. El flag nacería
  sin un solo caller real, ejercitado solo en fixtures sintéticos. Queda registrado como candidato a un
  **P3.1 futuro**, condicionado a que primero se decida — en un paquete aparte, porque es cambio de doctrina —
  quién acuña el id de spawn y cómo llega a los prompts canónicos de los 3 runtimes. `--commit` sí se queda:
  tiene caller real desde el día uno (`repair-agent` conoce su propio commit).
- **`init 006-execution-graph` declara solo AC-20..AC-29** (las ACs de P3), nunca AC-01..AC-19. La feature
  **se queda en `PACKAGE_ACCEPTED` tras aceptar P3, nunca transiciona a `DONE`** — es una restricción de
  *proceso*, no un gate de código nuevo: `done_ready()` técnicamente lo permitiría (P3 sería el único paquete
  registrado y estaría `accepted`), pero el orquestador no invoca `transition DONE` para esta feature mientras
  AC-01..AC-19 sigan fuera de la máquina de estados, porque hacerlo afirmaría que el contrato completo de 27
  ACs se entregó bajo tracking cuando solo 9 lo estuvieron. Registrado también en `log-decision`.
- **ADR-0013** (próximo número libre en `docs/adr/README.md`) documenta el diseño: grafo derivado en lectura
  de `ai/state/features/*.json` sin store nuevo, emisión mermaid stdlib-only, vocabulario cerrado de cinco
  tipos de arista, y el veredicto de arriba sobre `--commit`/`--caused-by-spawn`.
- **El edge `bloqueó` entra a P3** (AC-26 nuevo, abajo) — cierra la promesa original de cinco tipos de arista
  en vez de dejarla en cuatro sin decirlo.

Hallazgos no-bloqueantes también aplicados sin volver a preguntar (correcciones mecánicas, no decisiones de
producto): el join estructural de AC-20 ahora incluye `reviews[]` y `late_reviews[]` (findings de
`record-review`/`record-late-review` no tenían edge `produjo`); `--commit` valida el sha contra el repo
(nunca fabrica un nodo-commit de un sha inexistente); AC-22 (antes AC-23) define asserts estructurales
concretos como oráculo de "mermaid válido" en vez de la frase no-verificable "valid Mermaid", y un
desambiguador intra-paquete explícito en vez de apoyarse solo en `slugify()`; el subcomando `graph` gana
`--root` para ser testeable contra un directorio de fixture; `render_notes()` describe su contrato real
(best-effort, se salta con `--no-render`, nunca levanta) en vez de la promesa falsa "on every successful
mutate()"; la nota del grafo lleva backlink desde la nota de feature y un guard de nombre reservado; AC-25
(antes AC-26) corrige la cita de precedente (no es `build.sh`/`cmd_scaffold`, es `verify.sh` subprocesando
`check-feature-state.py`); se agrega un AC de navegabilidad explícito (los labels de nodo llevan lo mínimo
para seguir un finding sin abrir el JSON); y el retiro del waiver de `check-feature-state.py` gana su propio
AC con la atomicidad exacta respecto al `init`.

## Amendment log — tercera pasada de `SPEC_CHALLENGE` (contract 1.2.0, sin bump de versión)

La segunda pasada verificó las correcciones anteriores contra el código real y encontró 5 problemas nuevos
introducidos por esas mismas correcciones (`revision_required` de nuevo) — ninguno de producto, los cinco de
precisión técnica: un esquema de ids que su propio charset no puede producir; un AC apoyado en
`package["blockers"]`, que no existe (los blockers son de **feature**, no de paquete); una dicotomía
resuelto/no-resuelto para el edge `bloqueó` que exigía un join por timestamp — justo lo que otro AC del mismo
contrato prohíbe — contra datos donde además `cmd_reopen` marca `resolved_at` sobre *todas* las entradas sin
discriminar y `cmd_fail_task` emite blockers bajo un evento distinto (`fail-task`, no `block`); la promesa de
"degradación sin vault" del primer amendment log que se había perdido en la renumeración de la segunda pasada;
y la validación de `--commit` sin definir su postura ante un git que no puede responder (ausente, no-repo,
clone shallow) — con el propio repo ya documentando la postura correcta para ese caso en
`check-feature-state.py`. Las cinco se resolvieron con el precedente ya existente en el código (nunca
inventando un mecanismo nuevo) y quedan aplicadas en AC-20..AC-29 arriba, sin volver a preguntar: son
correcciones mecánicas sobre ACs cuyo alcance el usuario ya aprobó, no nuevas decisiones de producto.

## Amendment log — cuarta pasada de `SPEC_CHALLENGE` (contract 1.2.0, sin bump de versión)

La tercera pasada confirmó C1/C3/C4/C5 cerrados y encontró 5 bloqueantes más, todos mecánicos y sin
`open_questions` (el propio challenger lo señaló: dos decisiones chicas de diseño quedan para ADR-0013, no
para el usuario). Aplicados sin volver a preguntar: AC-22 gana los tipos de nodo `feature` y `package` que
faltaban (el edge `produjo` necesitaba un nodo `review` como origen y no estaba enumerado; el edge `bloqueó`
necesitaba un nodo contenedor y "package node" no era ningún tipo declarado); AC-26 se reancla al nodo
`feature` cuando `data["blockers"]`'s entry trae `package_id: None` (caso real y alcanzable — `record-gate`
lo admite opcional); AC-21 acota el sha a 7–40 hex antes de cualquier lookup de git, y nombra explícitamente
la tensión que el fail-open acepta (un hex bien formado sin git disponible se vuelve nodo-commit sin
verificar) en vez de dejarla implícita; AC-28 se reescribe entero con la estructura real de la única prueba
existente (`tests/test_harness.py:3106`, cuatro grupos de aserciones, no "dos tests") y nombra el destino de
cada grupo, incluyendo una prueba nueva in-process que preserva el guard del bug de shallow-clone
independiente de qué feature esté waived en cada momento; y la cabecera del contrato ahora cuenta las cuatro
pasadas reales en vez de fosilizarse en "dos" — el mismo defecto de header rancio que este mismo amendment
log ya cazó dos veces antes. **Cuarta pasada, `ready_for_user_approval` con tres inserciones mecánicas**
(namespace disjunto `subgraph`/nodo en AC-22, fuente de `role` para `reviews[]` en AC-27, y el tercer caso de
`package_id` no-matcheado en AC-26) aplicadas arriba sin abrir una quinta ronda — el challenger confirmó
explícitamente que el contrato queda listo para implementar.

Depends on: feature 004 (adaptive-dispatch) DONE — the deterministic router (`ai/catalogs/routes.v1.toml`)
is the tier mechanism this feature composes with instead of duplicating. Does not change what gets routed
or why.

## Contexto

The delivery lifecycle is a graph: nodes are bounded assignments, edges are the data that crosses between
them. (P3, below, renders findings/reviews/verifications/repairs/blockers as nodes — the "bounded assignment"
metaphor that motivates the feature; spawn nodes are explicitly out of P3's scope, deferred with
`--caused-by-spawn`.) The harness already implements most of the good half of that model without naming it — typed contracts
persisted on disk (context packs, ACs, `ai/state/features/*.json`), a router where the model classifies and
code decides, one writer per file (`owned_paths`), separation of duties, model tiering per node, and
consolidation done in code rather than by paying an agent for a flatMap.

Two things were missing, both verified against the tree before this contract:

1. **Independent work was serialized by omission.** `parallel`/`in parallel` appeared in exactly three
   places across all of `Global/_canonical/`, all of them in consult mode. The review panel — whose members
   read the same integrated diff and none of whose outputs feed another's input — had no concurrency
   instruction at all.
2. **Nothing verified a finding before acting on it.** `orchestrator.md` sent findings straight from the
   panel to `repair-agent`, and `feature-state.py` had no terminal finding status other than "repaired"
   (`closed`) or "won't fix" (`accepted`). A reviewer who was wrong forced a code change.

## Alcance explícitamente excluido

- **Claude Code `Workflow` / dynamic workflows.** Runtime-exclusive. SET-AGENTES targets OpenCode +
  Claude Code + Codex; adopting it would contradict the portability thesis of feature 005. The graph is
  expressed in harness data (state files + catalog), never in a vendor's tooling.
- **"Coordination costs zero tokens."** Half false, and the false half is the one that matters: the script
  pays no inference, but every subagent reloads its own context. Fan-out buys wall-clock, not quota. This is
  written verbatim into `orchestrator.md` so it cannot be re-derived wrongly later.
- **N independent skeptics per finding.** 3–9× cost, and it breaks the `~12 spawns per package` soft cap.
  Adopted batched instead (P2 / ADR-0009 D1).
- **Loop-until-dry without a hard convergence signal.** The two-cycle cap already converges; an open-ended
  loop is how quota gets burned. The cap stays a cap.

## P1 — false-edges (delivered)

- **AC-01** — `orchestrator.md` instructs the review panel to be spawned concurrently in a single batch, and
  states explicitly that concurrency does not change the review-cycle count.
- **AC-02** — `orchestrator.md` states as a hard rule that consolidating, flattening, deduplicating, sorting
  or counting outputs never justifies a spawn: it is `feature-state.py`'s deterministic work.
- **AC-03** — the general rule is stated with its economics: fan out when no output feeds another's input;
  this buys latency, NOT quota, and never licenses a wider fan-out than the spawn cap allows.
- **Dropped after measurement, not omitted:** "run the gates concurrently". `unittest` is 208 s of
  `verify.sh`'s ~220 s; parallelizing `py_compile` and `git diff --check` saves ~2 seconds. A real false
  edge that carries no value.

## P2 — finding-verification (delivered, accepted)

Design and rejected alternatives: **ADR-0009**.

- **AC-04** — a read-only role `finding-verifier` exists in `roles.tsv` (`review-ro` / `audit`) and is
  routable: it appears in every row of `ai/catalogs/routes.v1.toml` and in `ORCHESTRATOR_TASK_ALLOW`, so all
  three runtimes can delegate to it.
- **AC-05** — its brief is inverted (refute, not confirm), its default under uncertainty is `upheld`, and it
  may not edit, patch, add findings, or refute on severity.
- **AC-06** — `record-verification` records `upheld|refuted` per finding. A `refuted` verdict without both
  `reason` and `evidence` is rejected by the CLI, not merely discouraged in prose.
- **AC-07** — `refuted` is a terminal finding status: it does not block `accept-package`, and the finding is
  never deleted — it keeps `verdict_reason`, `verdict_evidence`, `verified_by`, `verified_at` and is
  rendered with its grounds in the package note.
- **AC-08** — `record-repair` refuses a finding whose status is `refuted`.
- **AC-09** — `record-verification` never increments `deep_review_cycles`.
- **AC-10** — a finding refuted in cycle 1 is not relisted by the cycle-2 review panel.
- **AC-11** — when every finding is refuted the package moves straight to `PACKAGE_TESTING`: no repair, no
  delta review.
- **AC-12** — the cost gate is a physical waiver: `record-verification --skip-reason` is refused while any
  open finding is above `low`, and the skip is recorded in the state file.

Added after the review panel (ADR-0009 amendment log, contract 1.1.0):

- **AC-13** — only `finding-verifier` may refute, never a finding it raised itself, and `--actor` is required
  explicitly so `verified_by` always carries the real independence attribution.
- **AC-14** — `record-repair` refuses to run while the package has no verification record and any open finding
  is above `low`, and refuses any individual `medium+` finding that carries no verdict. The node is mandatory
  in code, waivable only on the record.
- **AC-15** — `reason` and `evidence` are non-empty strings after `strip()`, capped at 2000 chars; `evidence`
  has a minimum length and must cite a `file:line`, a `$` command with its output, or an `AC-\d+`. Both are
  rendered in the package note alongside the verifier's name.
- **AC-16** — `upheld` is terminal for verification, and `max_verifications_per_package` blocks the package
  when exhausted.
- **AC-17** — the skip-to-testing transition fires only when the package entered `PACKAGE_REPAIR` from review
  or delta review, never from a failed testing run or runtime QA.
- **AC-18** — a finding cannot be created with a terminal status; `_short` and `merge_note` neutralize the
  `notas:auto` markers so generated text can never move the machine/human boundary; replays of a
  `--event-id` are no-ops and duplicate verdicts in one batch are rejected.
- **AC-19** — `finding-verifier` has tier variants in `models.toml`, so the D5 escalation is applicable on
  every runtime, and `PROYECTO/prompt.md` + `PROYECTO/AGENTS.md` teach the node.

## P3 — graph-view

No longer blocked: `005-P2-vault-mandatory` is `accepted` (ADR-0012, 2026-07-29) — the trace viewer's home
exists and is read. Scope: every finding becomes a note node with typed edges (`produjo`, `verificó`,
`refutó`, `reparó`, `bloqueó`), `set-agents --graph` emits the execution DAG as mermaid, and a finding is
navigable to the node that produced it, the node that verified it, and the commit that repaired it (when
declared) — without the chat session. Design: **ADR-0013**.

This is also the **first package of feature 006 tracked through the state machine**. P1 and P2 were delivered
outside it (waiver `006-execution-graph`, not backfilled — AC-07 of `009-self-application` names this
explicitly: *"feature 006 is not backfilled"*). P3 does not reconstruct P1/P2 history; it starts tracking
clean from its own first event. `init 006-execution-graph` declares only **AC-20..AC-29** — never AC-01..
AC-19. Consequence, decided explicitly and not left implicit: **006 stays in `PACKAGE_ACCEPTED` after P3 is
accepted; `transition DONE` is never invoked for this feature.** `done_ready()` would technically allow it
(P3 would be the only registered package and it would be `accepted`), but doing so would assert that the
full 27-AC contract shipped under tracking when only P3's 9 ACs did. This is a process restriction, recorded
here and in `log-decision`, not a new code gate.

- **AC-20** — every finding is representable as a graph node with exactly the edges its recorded data
  supports: `produjo` from whichever of `review_panels[].subreviews[]`, `reviews[]`, or `late_reviews[]`
  raised it, `verificó`/`refutó` from its verification, `reparó` from its repair when one exists. A `bloqueó`
  edge (see AC-26) is derived the same way, from `data["blockers"]` alone. All joins are structural — by
  membership/id, e.g. a finding id inside a subreview's finding list, a blocker entry's own `package_id` —
  never inferred from timestamp proximity, even when two entries share a timestamp by construction (e.g. a
  blocker and the `history` event recorded in the same call). Missing data means a missing edge, never a
  fabricated one.
- **AC-21** — `record-repair` accepts an optional `--commit <sha>`, constrained to 7–40 hex characters
  (`git`'s own abbreviation range) before any git lookup runs — `abcd` is well-formed hex but not a plausible
  sha, and is rejected on format alone. Beyond format, validation is **best-effort, fail-open**: the CLI
  attempts a read-only lookup (`git cat-file -e`-equivalent) against the repo at cwd; if git resolves the sha
  and it does not exist, the value is rejected and nothing is stored. If git itself cannot answer (absent, cwd
  is not a repository, shallow clone) the CLI does **not** fail closed — same posture `check-feature-state.py`
  already documents for its own git checks (announce, do not block a legitimate repair from being recorded)
  — it accepts the value and stores it, unverified. The graph never distinguishes verified/unverified commit
  nodes visually; it only distinguishes present/absent. **Named tension, decided, not accidental**: under
  fail-open with no git available, any 7–40 hex string becomes a commit node — a narrower case of AC-20's
  "never a fabricated one" than the ideal, accepted deliberately over blocking legitimate repairs; recorded
  in ADR-0013, not left implicit. When absent, `reparó` stops at the finding — the commit node is never
  guessed from `git log` against `changed_files`.
- **AC-22** — `feature-state.py graph [--feature-id ID]... [--root PATH] [--out PATH]` builds the graph. With
  no `--feature-id` given, it processes every `<root>/ai/state/features/*.json` present (this is how AC-25's
  `set-agents --graph` invokes it — a whole-repo view, not an error). Required node types: **feature** (one
  per feature, the container `bloqueó` anchors to for feature-scoped blockers — see AC-26), **package** (one
  per package inside its feature's subgraph — the container `bloqueó` anchors to for package-scoped
  blockers), finding, review (covers `review_panels[].subreviews[]`, `reviews[]`, and `late_reviews[]` alike
  — the source of every `produjo` edge, per AC-20), verification (including a waived verification — see
  AC-27), repair, commit (only when `--commit` was declared), and blocker (AC-26); no spawn nodes in P3
  (deferred with `--caused-by-spawn`, AC-29). "Valid" is defined by concrete structural assertions, not by the
  phrase alone: first non-empty line is exactly `flowchart TD`; every node id matches `[a-z0-9_]+` and is
  never a mermaid reserved word (`end`, `graph`, `subgraph`, `o`, `x`); every `subgraph` has a matching `end`
  (balanced count); labels are quoted and their internal `"`, `[`, `(`, and newlines are escaped. Node ids are
  built as `{type}_{norm(feature_id)}_{norm(package_id)}_{ordinal}` (the `package_id` component is omitted
  for feature-scoped nodes: `{type}_{norm(feature_id)}_{ordinal}`) — `norm()` lowercases and replaces every
  character outside `[a-z0-9]` with `_` (both `feature_id`/`package_id` contain `-` and, for `package_id`,
  uppercase — neither survives the AC-22 charset unnormalized) — plus an explicit ordinal index, never
  reliance on `slugify()` alone, which collides distinct raw ids (e.g. `F-001` vs `F.001`) inside the same
  package. One `subgraph` per feature and per package, with `subgraph` ids drawn from a **disjoint** prefix
  (`sg_{norm(feature_id)}[_{norm(package_id)}]`) so a `subgraph` id can never collide with a node id sharing
  the same feature/package — mermaid keys both in the same namespace, and `feature`/`package` now exist as
  both a `subgraph` *and* a node type; the structural-assertion list above includes "no `subgraph` id equals
  any node id" for exactly this reason. No node or edge references something absent from the source data.
  Output contract: without `--out`, the mermaid text goes to stdout (empty or populated, per
  AC-23); with `--out PATH`, it writes the raw mermaid text to `PATH` (overwriting), never a note-wrapped
  file. Partial multi-feature runs never abort: a `--feature-id` whose state file is missing contributes the
  AC-23 skeleton comment for that `<fid>` inside the same combined document instead of failing the whole
  invocation.
- **AC-23** — with no state file present at `<root>/ai/state/features/<fid>.json` (a freshly-scaffolded
  project, or a feature never initialized), `feature-state.py graph` never raises or prints a traceback: it
  emits the literal skeleton `flowchart TD\n%% no data for <fid>\n` and exits 0 — the same degradation
  posture as `cmd_context`'s `CONTEXT_VAULT_NOT_FOUND` — using the same stdout/`--out` contract AC-22 defines.
- **AC-24** — `render_notes()` writes `docs/notas/features/<fid>/grafo.md` inside the `notas:auto` markers,
  reusing the same graph-construction function AC-22's subcommand uses (no duplicated logic), on the same
  best-effort terms every other generated note already has: skipped when `RENDER_SKIP`/`--no-render` is set,
  reconciled later by `sync-notes`, and never raises — a broken graph render must not block state, exactly
  like the existing `render_notes` contract (it does *not* fire synchronously on literally every `mutate()`).
  When `notes_root()` returns `None` (no vault linked, no `ai/state` marker resolvable), `render_notes()`
  returns before writing any note for that feature at all — `grafo.md` included, on the same terms as every
  other generated note, same posture as `CONTEXT_VAULT_NOT_FOUND` — this is the "vault degradation" the
  amendment log above promises, made explicit here instead of only in AC-23's CLI path. The per-feature note (`docs/notas/features/<fid>.md`) gains a `[[grafo]]` backlink so the graph note
  is reachable by navigation, not only by direct path. A package literally named `grafo` (case-sensitive) is
  rejected by `create-package`: package notes are written at `docs/notas/features/<fid>/<pid>.md` with the
  **raw** `package_id`, never slugified, so `grafo` is the only string that can actually collide.
- **AC-25** — `set-agents --graph` invokes `feature-state.py graph` as a subprocess and re-prints its output
  without reimplementing graph construction — the same subprocess posture `verify.sh` already uses to run
  `check-feature-state.py` as a sibling tool; it degrades exactly like `feature-state.py graph` when there is
  no state.
- **AC-26** — a `bloqueó` edge exists from a container node to a synthetic blocker node for **every** entry
  in `data["blockers"]` (feature-level; `record-gate --package-id`/`--global-gate` and `block` both write
  into it, `cmd_fail_task` writes a compatible superset shape that additionally carries `task_id`) — resolved
  or not, regardless of whether it originated from `block_with_reason` (`history` event `block`) or from
  `cmd_fail_task` (`history` event `fail-task`), and the edge is derived from that list alone — never from
  `history`, and never conditioned on resolution state. The container is the **package** node (AC-22) when
  the entry's `package_id` is set and matches a known package; when `package_id` is `None`, unset, **or set
  but matching no known package** — all three real, reachable cases, since neither `cmd_block`'s
  `--package-id` (optional and unvalidated against `packages[]`) nor `record-gate`'s guarantees a match — the
  edge anchors to the **feature** node instead, never dropped silently. The blocker node's label shows
  `resolved` when `resolved_at` is present, `open` otherwise.
- **AC-27** — a finding node's label carries enough to be useful without opening the JSON: its `id`,
  `severity`, and (once verified) `verified_by`. A review node's label carries its `role` and `verdict` when
  the record has a `role` (subreview/late-review), or its `verdict` and the triggering `history` event's
  `actor` in place of `role` for plain `reviews[]`, which carries no `role` field at all. A verification
  node's label carries the verifying actor, sourced from the finding's `verified_by` for a
  normal verification, or from the triggering `history` event's `actor` for a waived verification
  (`record-verification --skip-reason`, which has no finding to read `verified_by` from —
  `verifications[]`/the skip record itself carries no actor field). A repair node's label carries the count of
  `changed_files`. A commit node's label carries the short sha. This is the minimum that makes
  "navigable... without the chat session" (this section's opening scope line) an observable, not just an
  aspiration.
- **AC-28** — retiring the `"006-execution-graph"` entry from `WAIVED` in `ai/scripts/check-feature-state.py`
  and creating `ai/state/features/006-execution-graph.json` via `init` land in the same commit (or the same
  uncommitted working-tree state at gate time) — never one without the other, because
  `stale_waivers()`/`violations()` fail in opposite directions otherwise (`WAIVER_UNNECESSARY` if the state
  file exists while still waived; `FEATURE_STATE_MISSING` if the waiver is gone before the state file exists).
  There is exactly **one** existing test that touches this,
  `test_feature_state_gate_fails_when_a_delivered_feature_has_no_state_file`
  (`tests/test_harness.py:3106`), with four independent assertion groups inside it — each is named here so
  none is silently weakened by the retirement:
  1. The synthetic-feature groups (`010-delivered`/`011-drafted`, `:3120-3173`) never mention `006` — untouched.
  2. The `006-execution-graph` `WAIVER_UNNECESSARY` group (`:3177-3187`) is repointed to assert the
     **post-retirement invariant**: the same synthetic fixture (a temp repo with a `006-execution-graph`
     state file and a matching delivery commit) now asserts plain `FEATURE_STATE_OK` — neither
     `WAIVER_UNNECESSARY` nor `FEATURE_STATE_MISSING` — because `006-execution-graph` is no longer in
     `WAIVED` at all, so there is nothing left to flag as unnecessary.
  3. The git-unusable group (`:3189-3196`) is untouched — unrelated to any waiver.
  4. The shallow-clone group (`:3198-3210`) clones the **real** `ROOT` repo, where `006-execution-graph`'s
     retirement means `assertNotIn("WAIVER_UNNECESSARY", ...)` would still pass, but trivially — nothing in
     `WAIVED` names `006-execution-graph` anymore for a shallow clone to misjudge, so the assertion stops
     proving what it used to. To keep that regression alive, a **new** in-process test is added (calling
     `stale_waivers()`/`delivery_commits()` as functions, not via subprocess) that `unittest.mock.patch`es
     `WAIVED` to a synthetic single-entry dict and mocks `delivery_commits()` to return `None` (the shallow-
     clone signal) — asserting the guard still reports `FEATURE_STATE_UNCHECKED` and never
     `WAIVER_UNNECESSARY` for that synthetic entry. This is the guard the shallow-clone bug (documented in
     `check-feature-state.py:79-90`) actually needs, independent of which real feature happens to be waived
     at any given time.
  The two source-text assertions (`:3214-3215`, citing `feature-006-delivered-outside-state-machine` and
  `docs/specs/009-self-application/spec.md:129-132`) go red once the `WAIVED` entry and its comment are
  removed — expected, and corrected in the same change: they become an `assertNotIn` confirming the retired
  entry's comment text is gone from the source, not a dangling `assertIn` on deleted prose.
- **AC-29** — features with history predating `--commit` (002 through 009, and 006's own unbackfilled P1/P2)
  still produce a structurally correct graph: spawn nodes are out of scope entirely (deferred with
  `--caused-by-spawn`, see the amendment log above), and the finding/review/verification/repair/blocker
  subgraphs connect using whatever data those files actually contain. Tests for this AC run against synthetic
  fixture state files created by the test itself, never against the live `ai/state/features/*.json` of other
  in-flight features — those change under the test's feet as other packages land.

## Verificación

`./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → `SELF_SCAFFOLD_SYNC_OK files=2` ·
`python3 -m unittest discover -s tests -v` · `git diff --check` · ownership vs baseline. Test count rises,
never falls, and no test is skipped.
