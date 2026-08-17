# D4 repair cycle 3 — exact AC-11 grammar

- Package: `D4-harness-por-CLI`
- Base: `bfe7b2d`
- Scope: D4-F01 and D4-DR02 only. No installer, uninstall, state, global-home, or reinstall path changed.

## Finding → change → verification

| Finding | Minimal change | Verification |
|---|---|---|
| D4-F01 | `_dispatch_virgin_session()` now accepts the two required tokens (`claude --`), leaving `argv[2:]` empty for the child. | `test_virgin_session_uses_an_isolated_home_without_reading_or_mutating_installed_lane` calls `--virgin claude --` through the allowlisted shim and observes exit 0. |
| D4-DR02 | ADR-0055 says AC-11 is implemented in D4 and records the actual isolation basis. | The ADR no longer assigns an eventual implementer or relies on an unverified individual OpenCode lookup rule. |

## Gates

```text
ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.HarnessTests.test_virgin_session_uses_an_isolated_home_without_reading_or_mutating_installed_lane -v
Ran 1 test in 14.974s
OK

ai/scripts/heartbeat-run.py --interval 20 -- ./ai/scripts/verify.sh
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS

git diff --check
exit 0
```

Remaining findings: none from this repair set. Blockers: none.
