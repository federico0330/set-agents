# Feature 006 — execution-graph, contract 1.0.0

Status: P1 delivered (commit `90e9948`), P2 delivered pending independent review. P3 blocked on
`005-P2-vault-mandatory`.

Depends on: feature 004 (adaptive-dispatch) DONE — the deterministic router (`ai/catalogs/routes.v1.toml`)
is the tier mechanism this feature composes with instead of duplicating. Does not change what gets routed
or why.

## Contexto

The delivery lifecycle is a graph: nodes are bounded assignments, edges are the data that crosses between
them. The harness already implements most of the good half of that model without naming it — typed contracts
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

## P2 — finding-verification (delivered, pending review)

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

## P3 — graph-view (blocked)

Blocked on `005-P2-vault-mandatory`: the trace viewer lives in the vault, and the vault is today neither
guaranteed nor read. Scope: every spawn becomes a note node with typed edges (`produjo`, `verificó`,
`refutó`, `reparó`, `bloqueó`), `set-agents --graph` emits the execution DAG as mermaid, and a finding is
navigable to the node that produced it, the node that verified it, and the commit that repaired it —
without the chat session.

## Verificación

`./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → `SELF_SCAFFOLD_SYNC_OK files=2` ·
`python3 -m unittest discover -s tests -v` · `git diff --check` · ownership vs baseline. Test count rises,
never falls, and no test is skipped.
