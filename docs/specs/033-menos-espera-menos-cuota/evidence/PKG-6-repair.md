# PKG-6 repair (PKG6-F01, PKG6-F02, PKG6-F03)

Ceiling vs `268fda6` (repair files only, no docs/notas): **194** lines (`git diff --numstat`, 150 code + 44 this file). Cap 200. `repair_ceiling` in state is `None` → `check-repair-ceiling.py` `REPAIR_CEILING_PASS` (`no repair_ceiling frozen`). `--baseline 268fda6` same early pass. Bite: `cp`, never git restore.

## PKG6-F01 high AC-6.4

`render_status.py:235` `spawn_budget_counts(data, current)`; `render_notes.py:196` same with `package`. Mirrors: `PROYECTO/` + `./build.sh` Global hooks.

Test `test_spawn_budget_warn_uses_current_package_not_feature_sum` (`test_harness.py:12679`). Two pkgs, ceiling 5, sum 7, current 4.

Bite `/tmp/pkg6-repair/render_status.py.green`. Revert to `spawn_budget_counts(data)`:

```
AssertionError: '4/5 WARN 80%' not found … | feat | scoped | … | 7/5 |
```

`cp` restore GREEN: `Ran 1 test in 2.138s OK`.

## PKG6-F02 medium AC-6.3

`feature-state.py:524` `if missing:` (no `len(required)>1`). Extra-roles `len(roles)>1` kept `:531`. PROYECTO twin.

Test `test_start_review_panel_rejects_wrong_single_role_on_small_low` (`:12641`). small+low `--role security-auditor` → rc 2 names `package-reviewer`.

Bite: restore `if len(required) > 1 and missing:` → `AssertionError: 0 != 2`. Restore GREEN: `Ran 1 test in 2.120s OK`.

## PKG6-F03 medium AC-6.5

`cost-report.py:728-742`: `collect_pi` and `collect_feature_spawns` into separate dicts; both non-empty → two Section 2 tables, each own TOTAL. Feature-state ingest kept. No `--route-decide`.

Test `test_cost_report_does_not_double_count_pi_and_feature_state` (`:12738`). RED before fix: `'2' unexpectedly found in ['2']`. GREEN after.

## Gates

```
python3 -m unittest … (6 named + never-summed): Ran 7 tests in 7.507s OK
python3 ai/scripts/heartbeat-run.py --interval 20 -- ./build.sh --check
  SELF_SCAFFOLD_SYNC_OK files=23
  GLOBAL_TREE_SYNC_OK harnesses=5
  BUILD_CHECK_PASS
git diff --check: 0
check-repair-ceiling.py PKG-6: REPAIR_CEILING_PASS (ceiling unset)
verify.sh not run.
```
