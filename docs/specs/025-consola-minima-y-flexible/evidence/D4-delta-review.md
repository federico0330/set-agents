# D4 delta review — one-shot virgin CLI

```json
{
  "package_id": "D4-harness-por-CLI",
  "verdict": "repair_required",
  "closed_findings": [],
  "new_or_reopened_findings": ["D4-F01", "D4-DR02"],
  "requires_full_review": {
    "value": false,
    "reason": "The repair is confined to the AC-11 command boundary, its regression test, and matching ADR/evidence; it does not change architecture or the AC-09/AC-10 install/uninstall risk surface."
  }
}
```

## Closure check

`D4-F01` is **reopened**. The repair replaces the old false scenario with a real one-shot command over an
already-installed four-lane fixture, and the environment boundary itself is sound: a separate sandbox run
made the installed lane and installer state unreadable, poisoned inherited `CODEX_HOME`, every XDG root,
`OPENCODE_CONFIG`, and `CLAUDE_CONFIG_DIR`, then observed the child receive only a temporary `HOME`,
`CODEX_HOME`, `TMPDIR`, and temporary XDG roots. The child exited `0`; hashes of all four lane markers plus
`install-targets.json` were identical before/after; and the reported scratch directory was removed.

The focused committed regression also passes:

```text
ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.HarnessTests.test_virgin_session_uses_an_isolated_home_without_reading_or_mutating_installed_lane -v
Ran 1 test in 15.608s
OK
```

However, the documented grammar is not implemented exactly, so AC-11 is not fully usable as the normal
interactive CLI session it promises.

## New or reopened findings

### D4-F01 — reopened

- `severity`: `high`
- `category`: `correctness`
- `acceptance_criterion`: `AC-11`
- `file`: `ai/scripts/set_agents_app.py`
- `line`: `3685`
- `evidence`: `_dispatch_virgin_session()` rejects `len(argv) < 3`, while the public grammar at lines
  3684/3686 and ADR-0055 line 93 declares `[CLI args...]` optional. Executing
  `python3 ai/scripts/set_agents_app.py --virgin claude --` against an isolated fake home and an allowlisted
  shim returns `2` and prints usage instead of launching the child with an empty argv.
- `reproduction`: create a temporary `HOME` and a `claude` shim in a temporary `PATH`, then run
  `HOME=<tmp-home> PATH=<shim-bin>:/usr/bin:/bin python3 ai/scripts/set_agents_app.py --virgin claude --`;
  observed `rc=2` before the shim executed.
- `required_outcome`: accept the mandatory separator with zero or more child arguments (the lower bound is
  two tokens after `--virgin`), and add a regression that proves an empty child argv launches the selected
  CLI. Keep malformed/mixed modes rejected.
- `suggested_scope`: `ai/scripts/set_agents_app.py`, `tests/test_harness.py`.

### D4-DR02 — new

- `severity`: `low`
- `category`: `correctness`
- `acceptance_criterion`: `AC-11`
- `file`: `docs/adr/0055-uninstall-per-harness-delta-ownership.md`
- `line`: `102`
- `evidence`: the amended ADR records the implemented command at lines 93-98, but lines 102-103 still say
  implementation is deferred to a later package, and lines 129-133 still assign verification to an
  "eventual implementer." This is now false durable state created by the same repair.
- `reproduction`: compare ADR-0055 lines 93-98 with 102-103 and 129-133.
- `required_outcome`: describe AC-11 as implemented now and either record the actual runtime basis for the
  XDG choice or explain that overriding all roots plus clearing inherited per-CLI overrides avoids relying
  on one unverified OpenCode lookup rule.
- `suggested_scope`: `docs/adr/0055-uninstall-per-harness-delta-ownership.md`.

## Delta regression and scope assessment

- The early `--virgin` intercept is standalone and cannot be combined with ordinary `set-agents` modes.
- The child argv is a list, never a shell string; the CLI selector is closed to the four supported lanes.
- The child environment is rebuilt from a narrow allowlist and does not inherit installed-home config
  overrides; temporary roots are mode `0700` and cleaned after exit.
- The new scenario C is materially stronger than the discarded gate: it starts with all lanes installed and
  compares them after the one-shot run. Its remaining blind spot is the empty-child-argv parser case above.
- No unrelated product-code scope creep was found. The diff's D3 evidence edit is metadata alignment only.

