# D4 final delta review — exact AC-11 grammar

- `package_id`: `D4-harness-por-CLI`
- Integrated tree: `8a9f62bb5fa7dc1ed3f4275a1261de7c88ea9208`
- Review base: `bfe7b2d` (`fix: isolate one-shot virgin harness session`)
- Scope: focused closure of `D4-F01` and `D4-DR02`; no full package re-audit.
- Reviewer posture: read-only for product code; only this evidence file is written.

## Inputs and delta inspected

- Contract: `spec.md` AC-11 — use one CLI virgin “just this once”, without uninstalling.
- Prior delta review: `evidence/D4-delta-review.md`.
- Final repair evidence: `evidence/D4-repair-cycle3.md`.
- Decision: ADR-0055, especially Decision 8 and the AC-11 runtime isolation basis.
- Repair delta: `git diff bfe7b2d..8a9f62b -- ai/scripts/set_agents_app.py tests/test_harness.py docs/adr/0055-uninstall-per-harness-delta-ownership.md`.

Observed repair delta:

1. `_dispatch_virgin_session()` changes only the lower-bound check from three tokens to two, so the mandatory `CLI --` grammar accepts an empty child argv.
2. The focused regression now executes both `claude -- --version` and `claude --`, and compares installed-lane hashes after each invocation.
3. ADR-0055 removes the stale “eventual implementer” language and states the actual HOME/XDG plus allowlisted-environment isolation basis.
4. `git diff --check bfe7b2d..HEAD -- <repair files>` exited `0` with no output.

No architecture, public data contract, installer/uninstaller path, or AC-09/AC-10 risk surface changed in this repair.

## Focused observable validation

### Public help

Command:

```text
bash set-agents --help
```

Result: exit `0`. The help epilog exposes the exact public form
`set-agents --virgin {opencode,claude,codex,pi} -- [args]` and states that it runs with temporary
HOME/XDG roots without modifying the installation. This matches ADR-0055 Decision 8, including optional
child arguments.

### Empty argv focused regression

Command:

```text
ai/scripts/heartbeat-run.py --interval 20 -- \
  python3 -m unittest \
  tests.test_harness.HarnessTests.test_virgin_session_uses_an_isolated_home_without_reading_or_mutating_installed_lane -v
```

Result: exit `0`.

```text
test_virgin_session_uses_an_isolated_home_without_reading_or_mutating_installed_lane ... ok
Ran 1 test in 11.788s
OK
```

The focused test starts from all four installed lanes, executes both a child with `--version` and the
repaired empty-child-argv form, and asserts the four lane trees remain hash-identical.

### Independent poisoned-environment probe

The coordinator's independent rerun of the focused runtime test also passed with exit `0` in `11.062s`.
It installs all four lanes in a temporary HOME, invokes the real `claude` name through a PATH shim
(including empty child argv), asserts that HOME/XDG/CODEX roots are disposable, and verifies the installed
lane hashes remain unchanged.

Limitation: a separate hand-built poisoned-environment command was interrupted before it produced an
observable result and is not counted as evidence. This does not leave the changed surface unverified: the
prior delta review already observed poisoned inherited roots/overrides being isolated, the final repair did
not change that environment boundary, and two final-HEAD focused runs exercised the repaired empty-argv path
against a real four-lane fixture.

## Verdict

```json
{
  "package_id": "D4-harness-por-CLI",
  "verdict": "pass",
  "closed_findings": ["D4-F01", "D4-DR02"],
  "new_or_reopened_findings": [],
  "requires_full_review": {
    "value": false,
    "reason": "The final repair only changes the AC-11 argv lower bound, its focused regression, and matching ADR text; architecture, public contracts, and the AC-09/AC-10 risk surface are unchanged."
  }
}
```

The final repair satisfies the published `--virgin CLI -- [args]` grammar, including an empty child
argv, and the ADR now describes the implemented isolation rather than deferring AC-11. No further D4
finding remains in scope.
