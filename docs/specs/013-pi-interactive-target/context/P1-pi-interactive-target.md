# P1-pi-interactive-target — context pack

Contract: `docs/specs/013-pi-interactive-target/spec.md` v1.3.0 (hash in
`ai/state/features/013-pi-interactive-target.json`). Covers AC-01..AC-14.

## Objective (2-3 lines)

Give `pi` interactive its own fourth generated harness surface (`Global/pi/**` →
`~/.pi/agent/`) so opening `pi` loads THIS repo's roles/skills/prompts/doctrine, the same
way OpenCode/Claude Code/Codex already do — plus the two narrowly-scoped items outside
`Global/pi/**` (dispatch-lane closure, ADR skeleton) the contract requires alongside it.

## Files/paths (why)

- `ai/scripts/generate.py` — fourth converter branch inside the existing per-role loop
  (base-agent loop is now at **lines 347-397**, not the spec's stale `:335-384` — see
  Drift below); `validate()`'s two harness-tuple loops (now **:539**, **:547**);
  `validate_pi_target()` (now **:509-522**, KEPT per round-2 C-01, docstring-only fix);
  `write_indexes()` (**:299-303**); mkdir loop (**:343-344**); skills/commands copy
  tuples (**:423-426**); doctrine-file `copy2` calls (**:428-431**).
- `ai/scripts/install.py` — `--target` choices (`:23`), `all_targets` (`:29-33`),
  `SPECIAL` (`:36-40`, gains no entry for pi), collision guard lives here (new logic,
  AC-09), exit code `2` for the guard (see `INSTALL_ABORTED_UNSAFE_ROOT`, `:63-75`).
- `ai/scripts/verify.sh` — freshness loop (`:25-27`, add a 4th `diff -ruN "Global/pi"`
  line); portability heredoc (`:32-50`) needs **no** change, already generic.
- `build.sh` — `usage()` (`:12`), install-mode target loop (already generic via
  `all_targets`), `diff`/`generate` mode loops (`:75-77`/`:80-83`, mechanically add `pi`).
- `Global/_shared/AGENTS.pi.md` (new) — fourth doctrine file, twelve generic sections +
  orchestrator operating content (spawn economy, question policy, narration registers)
  folded in per user decision 1. Source the orchestrator content from
  `Global/_canonical/agents/orchestrator.md`, current sections: Delegation flow `:123`,
  Tiered dispatch `:160`, Consult mode `:355`, Spawn economy `:367`, Package audit policy
  `:400` (new since spec was drafted — not cited by spec, informational only, not
  required content), Question policy `:415`, Turn continuity `:441`, Hard boundary
  `:497`, Narración `:506` — **all of these line numbers are stale in the spec itself**
  (see Drift below); use the file as read today.
- `ai/scripts/set_agents_spawn.py` (**exception-only**, AC-12) — argv at `:244-248`
  (flags `:245-246`), comment `:241-243`. NOT in `owned_paths`; touch only via the
  `--exception` granted on this package (see Out-of-scope).
- `tests/test_harness.py:3046-3054` — extend with pi-target coverage; the ONLY allowed
  edit to the existing `test_pi_target_validate_requires_canonical_prompt_per_role` is
  its stale comment (R3-01) — assertions/behavior stay byte-identical.
- `docs/adr/0017-pi-interactive-target.md` (new, skeleton) + in-file amendment inside
  `docs/adr/0007-pi-lane.md` near its `## Decisión 4` (`:93-112`, current lines
  confirmed unchanged) + `docs/adr/README.md` row updates for `0007` and `0017`
  (current `0007` row is line 14, `0016` is the last row at line 23 — `0017` is next).
- `ai/state/decisions-log.jsonl` — `log-decision` superseding
  `ac09-ac10-pi-minimal-target-accepted` (line 14 of that file).

## Constraints (ADRs/invariants)

- ADR-0007 (Accepted) — this package amends Decision 4 (title/premise/install-clause/
  validate_pi_target consequence) and narrows Decision 2's residual-risk framing; does
  not reopen anything else.
- ADR-0008 (Accepted) — D2/D10 pruning fence: never touch third-party content not in
  `MANIFEST`; `--doctor --harness pi` envelope stays BYTE-IDENTICAL (no branches added).
- Repo doctrine: regression tests are never weakened/skipped/deleted — `validate_pi_target`
  and `test_pi_target_validate_requires_canonical_prompt_per_role` keep their exact
  current assertions/behavior; only stale docstring/comment text may change.
- No opportunistic refactor of the three existing `AGENTS.*.md` files into one shared
  source — the 4th file is a fourth near-duplicate, same precedent as the other three.

## Local validations (exact commands)

- `python3 -m unittest discover -s tests -v`
- `./ai/scripts/verify.sh` → expect `VERIFY_PASS`
- `./build.sh --check` → expect `SELF_SCAFFOLD_SYNC_OK files=2`
- `./build.sh --diff` → expect a clean 4th `pi` diff once generated+committed
- `./build.sh --install --target pi --output <staging>` (or direct
  `python3 ai/scripts/install.py --staging <staging> --home <scratch> --target pi --preview`)
  against a scratch `$HOME` for AC-08/AC-09 checks
- AC-13's credential-gated E2E: `pnpm dlx --package @earendil-works/pi-coding-agent which pi`
  then `cd <scratch-empty-dir> && HOME=<scratch> timeout 20 script -qc "<resolved-pi-path>
  --verbose --offline --no-session --no-approve" <logfile>` — degrades to
  `BLOCKED`/`HUMAN_DECISION_REQUIRED` if the real `pi` binary/`pi-subagents` are absent,
  never a silent skip.

## Out-of-scope (do NOT touch even if tempted)

- The 7 already-installed pi extensions / `~/.pi/agent/settings.json` / `~/.pi/agent/npm/`.
- Any `set_agents_spawn.py` change beyond AC-12's exact two flags + its one stale comment
  — and only under the granted ownership exception, never as an implicit side effect.
- `Global/pi/themes/**` (no themes target).
- Manual cleanup of the gentle-extension leftovers (`~/.pi/agent/agents/sdd-*.md`,
  `~/.pi/agent/chains/*`, `~/.pi/agent/gentle-ai/support/`) — user-authorized, one-time,
  outside this package, not this package's logic.
- `--doctor --harness pi` envelope (`set_agents_app.py:602`) — contractually
  byte-identical, zero branches added.
- Merging the three existing `AGENTS.*.md`/`CLAUDE.md` files into one shared source.

## Known spec drift (read before citing any line number)

Every `generate.py` line citation in the approved spec is stale (the tree gained the
tier-variant loop from feature 004/T-202 and other work after the spec was drafted).
`orchestrator.md`'s own section line numbers cited by AC-07 are also stale (it grew a
new `## Package audit policy` section and general content since). Content/behavior the
spec describes is otherwise intact — use the line numbers in this context pack (read
live at package-planning time) instead of the spec's.
