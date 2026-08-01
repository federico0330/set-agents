# Context pack — P1-anthropic-dispatch-parity

Spec: `docs/specs/015-anthropic-dispatch-parity/spec.md` (contract 3.1.0, hash in state file). Read AC-01..AC-08
and `## Contexto` §A-H yourself for full reasoning — this pack curates, it does not replace, that text.

## Objective (AC-01..AC-08)
Redirect any routed decision that resolves to provider `anthropic` onto a real, non-interactive Claude Code CLI
subprocess spawn (the user's real OAuth subscription), instead of the dead OpenCode-lane path. This closes the
review-independence gap for the ~12-day window while two providers remain authenticated, with a CLI-level tool
ceiling as a DECIDED security control, doctrine updated across harnesses, two static-config collisions fixed,
and the design recorded in a new ADR. **Highest-priority feature, real ~12-day deadline.**

## Files (why each matters)
- `ai/scripts/routing_core/service.py:104-224` — `RoutingService.route()`'s exclusion loop. AC-01 edits ONLY
  the `facts.selected_runtime`-keyed sites: `:137,144,145,195,200,201,206,208` (8 sites, `:144` is a pi-guard,
  behavior unchanged but must stay counted). `:128` and `:171` (sort key) are explicitly NOT touched.
- NEW file (name your own choice, sibling to `ai/scripts/set_agents_spawn.py`, e.g.
  `ai/scripts/claude_code_spawn.py`) — AC-02's spawn module. Do NOT call
  `set_agents_spawn.route_and_spawn`; reuse its LIFECYCLE SHAPE only (decide→dispatch→spawn→terminal for
  writers; no bookkeeping at all for review-class, matching `set_agents_spawn.py:374-377`'s own refusal path).
- `Global/_canonical/agents/orchestrator.md:160-227` — "Tiered dispatch" doctrine. AC-03/AC-04 rewrite step 2
  and the branch-on-outcome section. Edit ONLY the canonical copy; regenerate the rest with `./build.sh`.
- `Global/opencode/agents/orchestrator.md`, `Global/claude-code/agents/orchestrator.md`,
  `Global/codex/agents/orchestrator.toml` — generated copies, never hand-edit; refresh via `./build.sh`.
  `Global/pi/` does not exist yet (013 still in `PACKAGE_PLANNING`) — only 3 copies exist today.
- `models.toml:93,96,99,188` — AC-06 values-only fixes: `[areas.audit].opencode."go-zen"` vs
  `[roles.implementer.tiers.balanced].opencode."go-zen"` collision (a); `[areas.audit].claude`/
  `[areas.judge].claude` `"opus"`→`"fable"` (b, NOT `"sonnet"` — that would collide with
  `[areas.implement].claude`, also `"sonnet"`, `models.toml:81`).
- `docs/adr/0019-anthropic-dispatch-parity.md` (NEW) + `docs/adr/README.md` row.
- `tests/test_routing.py`, `tests/test_harness.py` — extend, never weaken/skip existing assertions.

## Read-only (reference, do NOT edit)
`ai/scripts/routing_core/catalog.py` (AC-07: zero diff — the snapshot layer already admits
`(route_id,"claude-code","anthropic",...)`, `catalog.py:565-567`), `ai/scripts/routing_core/domain.py`,
`ai/scripts/set_agents_spawn.py` (structural precedent ONLY, never called), `ai/scripts/set_agents_app.py`,
`ai/scripts/models_config.py`, `ai/catalogs/routes.v1.toml`, `docs/adr/0007-pi-lane.md`,
`docs/adr/0011-uninterrupted-delegation.md` (D4 halt rule — preserved, not relaxed).

## Constraints (ADRs/invariants)
- ADR-0011 D4: `REVIEWER_INDEPENDENCE_UNAVAILABLE` halts, unchanged, in every runtime. AC-04's regression test
  must prove the day-13 fixture (only `anthropic` authenticated) still hard-halts.
- SEC-A02 precedent (`set_agents_spawn.py:70,332-335`): the routed entry point never gets a `guard_tools`
  override. AC-02 mirrors this: **Bash categorically excluded from every argv, both role classes, no
  parameter widens it.**
- **Mandatory on every AC-02 spawn, no exception**: `--setting-sources user` (blocks project-scope
  `.claude/settings.json` hooks / agent-file shadowing — the R3-01 gap `--tools ""` alone does NOT close);
  cwd = repo root; `--add-dir` NEVER passed. Do not reach for `--bare` (breaks OAuth) or `--safe-mode`
  (breaks `--agent`) as substitutes.
- Task delivered via **stdin**, never a trailing positional (R2-07: swallowed by a variadic `--tools`).
- Review-class: `--tools "Read,Grep,Glob"`, no `--permission-mode`. Writer-class (cross-lane redirect only):
  `--tools "Read,Grep,Glob,Edit,Write" --permission-mode acceptEdits`, Bash excluded — narrower than normal
  `code-rw` (`Edit,Write,Bash`); no Bash-based local validation inside this spawn.
- Review-class spawns are Bash-less: the **caller** (orchestrator/AC-04 doctrine) must supply the diff, as a
  readable file inside cwd or embedded in the stdin task text.
- AC-01 redirect is conditional-only: it fires ONLY when the requested `(facts.selected_runtime, provider)`
  pair itself is unauthenticated. Never touch `("pi","anthropic")`'s already-working path.

## Local validation
`./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → scaffold sync clean (after regenerating the
3 harness copies) · `python3 -m unittest discover -s tests -v` (count must rise, never fall, zero skips) ·
`git diff --check` · ownership check vs baseline (`ai/scripts/check-owned-paths.py`).

## ADR number — live-verified this session
`docs/adr/` lists through `0016` on disk (`0016-discovered-inventory.md`, Accepted). `0017` is
claimed-not-materialized by `013-pi-interactive-target`; `0018` by `014-model-preference-policy`'s own AC-09.
Neither file exists on disk. **Use `0019`** — re-`ls docs/adr/` immediately before creating the file to catch
a last-minute race (013/014 are not being implemented concurrently, but re-check anyway).

## Early checkpoint (mandatory, before proceeding past AC-02's skeleton)
This package touches auth/authorization (review-independence) and untrusted-code-execution containment
(headless Bash spawn vector). Once AC-02's spawn module has a composed argv (both role classes) but BEFORE
wiring AC-03/AC-04 doctrine on top of it, stop and get a `security-auditor` look at the literal argv: is
`--setting-sources user` present, is `--add-dir` absent, is `Bash` absent from `--tools` in both role classes,
does `--permission-mode acceptEdits` appear ONLY for the writer class. Do not proceed to doctrine wiring on an
unreviewed argv.

## Cross-feature sequencing note
`013-pi-interactive-target` (still `PACKAGE_PLANNING`, no packages yet) also plans to touch
`Global/_canonical/agents/orchestrator.md` (converting it into `Global/pi/AGENTS.md`). No live ownership
collision today (013 has claimed no owned_paths yet), but 013's own package-planning should read
`orchestrator.md` in its POST-015 state once this package lands — logged via `log-decision`, not resolved
here.

## Out of scope — do NOT touch
- `catalog.py`, `routes.v1.toml`, `set_agents_spawn.py`, `models_config.py` schema (AC-07/Non-goals).
- Promoting `claude-code` to `[runtime].primary`/`.fallbacks` (Non-goals).
- `011-quota-failover`'s scope (no quota-failover signal recording for the new lane — Non-goals).
- Any `[areas.*]`/`[roles.*]` value in `models.toml` other than the two named AC-06 cells.
- Fixing the day-13 permanent review halt once the second provider is truly gone — accepted, documented,
  time-boxed limitation, NOT a defect this package fixes. Do not add a done-condition for it.
- `014-model-preference-policy`'s files — read-only reference only, no edits.
