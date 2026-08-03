# ADR-0017 — Pi interactive target: fourth generated harness tree, install target, collision guard, dispatch-lane closure

Status: Accepted
Date: 2026-08-02
Feature: `013-pi-interactive-target`

## Contexto

Extends ADR-0007 (Pi lane: CLI-subprocess dispatch spawner) and ADR-0008 (two-roots portability). ADR-0007's
own dispatch lane (`ai/scripts/set_agents_spawn.py:244-250`'s fixed argv) and interactive `pi` (this ADR) are,
and remain, two different sessions with two different flag sets — confirmed live: the dispatch lane passes
`--no-session --no-extensions --no-context-files --no-skills --no-prompt-templates`, so none of
`Global/pi/AGENTS.md`, `Global/pi/agents/**`, `Global/pi/skills/**`, or `Global/pi/prompts/**` ever reach a
dispatch-lane child. Interactive `pi`, opened by a human directly (not through this harness's dispatch lane),
had no equivalent of OpenCode/Claude Code/Codex's own generated role/skill/prompt/doctrine tree — this ADR
closes that gap.

## Decisión 1 — amends ADR-0007 Decisión 4 (three pieces, not one)

See the in-file amendment inside `docs/adr/0007-pi-lane.md`, placed directly above its own Decisión 5. The
three amended pieces: (a) the Decision's own title/premise ("target `pi` MÍNIMO ... sin árbol generado") is
false the moment this feature's `generate.py` fourth branch ships a real `Global/pi/agents/<role>.md` per
active-roster role; (b) the "`install.py` no gana un target `pi`" clause is amended — `install.py` gains a
fourth target, `pi` → `~/.pi/agent`, using the exact existing per-target mechanism (`all_targets`,
`managed_files()`, `previous_targets()`'s generic pruning fence — no per-harness branch needed in any of the
three); (c) `validate_pi_target()`'s consequence text becomes incomplete, not false — the function is KEPT
(round 2 finding C-01 of the approved contract: removing a function a live regression test,
`tests/test_harness.py::test_pi_target_validate_requires_canonical_prompt_per_role`, calls directly would
violate this repo's own "regression tests are never weakened/skipped/deleted" doctrine), only its docstring
is corrected, and `validate()` gains two ADDITIONAL checks over the generated output that this 2026-07-27 text
predates.

## Decisión 2 — narrows ADR-0007 Decisión 2's residual-risk framing (dispatch-lane closure, AC-12)

Once `Global/pi/skills/**`/`Global/pi/prompts/**` are installed under `~/.pi/agent/`, every dispatch-lane `pi`
child would otherwise auto-discover and load this harness's own skill catalog and prompt library too — added
context weight the dispatch lane's original minimal-and-auditable design never accounted for, though not a
guard-table violation (skills/prompt-templates grant no new tool/argv/cwd/env access). Closed directly, not
left as an accepted residual risk: `set_agents_spawn.py`'s fixed argv gains `--no-skills` and
`--no-prompt-templates`, unconditional alongside the three pre-existing T-304 guards, under an
`update-package --exception` ownership grant on that file for this package (precedent:
`ai/state/features/005-portable-harness.json`'s own P1 exception on the same file).

## Decisión 3 — skills copy compatibility (AC-05), resolved without a live spike

`docs/skills.md`'s own Validation section documents `compatibility` as an optional, informational frontmatter
field pi's lenient loader never enforces as a discovery filter ("unknown frontmatter fields are ignored").
`Global/_canonical/skills/**` copies to `Global/pi/skills/**` byte-identical, unconditionally, the same
`copy_tree` call already used for the other three harnesses with one added tuple member.

## Decisión 4 — prompts converter translation questions (AC-06), both resolved

1. `agent: <role>` has no pi prompt-template frontmatter equivalent (`docs/prompt-templates.md`'s Format
   section recognizes only `description`/`argument-hint`). It is stripped from the emitted frontmatter and
   folded into the prompt body as an explicit `subagent({ agent: "<role>", task: ... })` instruction instead
   — never silently dropped, preserving the separation-of-duties role binding a converted prompt still needs.
2. `$ARGUMENTS` needs no translation: `docs/prompt-templates.md`'s own Arguments section documents it as a
   NATIVE alias for `$@` in pi's template engine. It copies through verbatim.

## Decisión 5 — tool-ceiling divergence accepted (AC-03)

For `coord-ro`-class roles (today exactly `orchestrator`), pi's own delegation concept — the `subagent` tool,
an open token with no observed per-name allowlist syntax — is genuinely wider in shape than Claude Code's
closed `Agent(<27 roles>)` allowlist. Accepted as a documented, deliberate divergence, not a gap: pi-subagents'
own SKILL.md enforces a hard structural boundary at the engine level regardless of the parent's frontmatter
token — "Ordinary children also do not receive the `subagent` extension tool" and "Default subagent nesting
depth is 2" — so an ordinary child spawned under `coord-ro`'s delegation has no further delegation tool at
all, and any fanout agent is still depth-capped. The converter pins `maxSubagentDepth: 2` explicitly for the
`coord-ro` class rather than relying silently on that documented default.

## Decisión 6 — the `settings.json`-pointer alternative was considered and rejected (AC-14 item 8)

`pi` documents an alternative: a `settings.json` pointer directly at another harness's skill directory (e.g.
`~/.claude/skills`), requiring zero generated tree. Rejected — it would break this repo's established
one-copy-per-harness-tree symmetry with the other three targets and would entangle a managed file
(`Global/pi/skills/**`) with the user's own free-form `settings.json`, which `install.py` manages for no
harness today.

## Decisión 7 — collision guard for `~/.pi/agent/agents/` (AC-09)

The one write target among the four generated harness trees with real, pre-existing third-party content risk
(the gentle-ai extension leftovers, `sdd-*.md`). `install.py` fails closed (exit code `2`, matching its own
existing `INSTALL_ABORTED_UNSAFE_ROOT` precedent and `check-drift.sh`'s internal-error convention — not `1`,
which would be indistinguishable from ordinary `DRIFT_DETECTED`) whenever a file it is about to write to
`~/.pi/agent/agents/` already exists on disk and was NOT recorded in its own `MANIFEST` from a prior run.
Fires identically in `--preview` and write mode. No override flag — the operator resolves the collision by
hand, outside the installer, per ADR-0008 D2's "never touch third-party content" doctrine.

## Decisión 8 — end-to-end load proof (AC-13)

Static file/frontmatter checks alone would go green even if the real `pi` binary silently ignored one of the
generated trees. `pi --verbose`, invoked against a scratch `$HOME` under a pty with an explicit timeout,
renders a real startup header (`[Context]`/`[Skills]`/`[Prompts]`, no `[Agents]` section — pi core has no
"agents" resource family; `Global/pi/agents/**`'s discoverability is instead proven via `pi-subagents`' own
`subagent({ action: "list" })`/`/subagents-doctor`). Credential/environment-gated: a CI environment without a
real, locally-installed `pi` binary plus `pi-subagents` degrades this specific check to
`BLOCKED`/`HUMAN_DECISION_REQUIRED`, never a silent skip and never a false pass on the static-check layer
alone.

## Superseded decision

`ai/state/decisions-log.jsonl`'s `ac09-ac10-pi-minimal-target-accepted` entry (2026-07-27,
`004-adaptive-dispatch`/`P3-pi-lane`) asserted "install.py stays untouched; P3 adds no generated pi agent
tree" — true for the dispatch-lane-only surface that package shipped, false for the separate interactive
surface this feature adds. Explicitly superseded by a new `log-decision` entry naming this slug (see
`ai/state/decisions-log.jsonl`), following the same in-prose supersession precedent already used by this
repo's own `buenos-dias-anthropic-surcharge-claim-was-wrong-supersedes-first-pass` entry.

## Rollback

`install.py`'s existing generic, backed-up rollback mechanism (`backups_root`/`rollback()`) covers the new
`pi` target the moment it is registered in `all_targets` — no pi-specific rollback code, same as the other
three harness targets. Reverting the two dispatch-lane flags (AC-12) is a one-line revert of the fixed argv.
Reverting the generator/install/verify/build changes (AC-02..AC-11) is an ordinary code revert; no data
migration, no mutable state beyond the managed files themselves.

## Status

`set_agents_app.py --doctor --harness pi` stays byte-identical per ADR-0008's Implementer Contract item 3 —
this feature adds zero branches to `cmd_doctor`.
