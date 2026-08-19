# PKG-D repair — SEC-001

Package: PKG-D. Feature: `034-cuota-organica-y-writer-barato`.
Finding-verifier `734a5ccf` upheld SEC-001. One consolidated pass. No `--route-decide`.
No Engram. No Cursor in `RUNTIMES`. No heavy `repair-agent` pin. Shipped pins
unchanged. `inherit` stays in `[catalog].cursor` (`models.toml:26`). Do not call
`accept-package` / `record-repair`.

## SEC-001 — mixed inherit on review-ro / audit / judge must die at generate

**Defect.** `family()` (`ai/scripts/models_config.py:568-577`) returns the raw slug
`inherit`, so `inherit` looks distinct from `composer-2.5`. Universal-inherit died
only when **all** pins were `inherit` (`generate.py` post-loop). Setting
`[areas.audit].cursor = "inherit"` (implementer stays `composer-2.5`) passed
`load_roles`, `validate_cursor_target`, and `CursorRuntimeTargetTests`. At runtime
Cursor `inherit` is the parent model
(https://cursor.com/docs/subagents) — the reviewer shares the writer.

**Change.** Dual fail-closed on `review-ro` + `duty in {audit, judge}` +
`cursor_model == "inherit"`:

1. `load_roles` (`models_config.py:644-652`) — die before a lying tree is emitted.
2. `validate_cursor_target` (`generate.py:768-778`) — preferred generate-time
   guard (034 SEC-001). Universal inherit (`:801-802`) still dies separately.

`family()` keeps returning the raw slug (coord may pin `inherit`; this helper has
no writer pin to collapse against). Comment at `:572-576` points at the guards.

`[catalog].cursor` still lists `inherit`. `RUNTIMES` (`models_config.py:44`)
unchanged. `repair-agent` stays on `composer-2.5`. No `--route-decide`.

**Test.** `test_mixed_inherit_on_audit_reviewer_is_forbidden_at_generate`
(`tests/test_harness.py:14878`): copy ROOT `models.toml`, set only
`[areas.audit].cursor = "inherit"` (header anchored at `\n[areas.audit]\n` so
comments mentioning the table do not match), `generate.py --models` that file
`--output` a temp dir (never `Global/`). Expect non-zero and `inherit` /
`reviewer` / `forbidden`. Contrasting: shipped ROOT `models.toml` generate rc=0.
`test_no_cursor_agent_pins_a_model` (`:14840`) stays, not deleted.

### Guard (file:line)

```
ai/scripts/generate.py:768-778  validate_cursor_target
ai/scripts/models_config.py:644-652  load_roles
```

Live generate of the bite (temp copy, never `Global/`):

```
rc 2
CHECK_FAILED: cursor: inherit on reviewer spec-challenger is forbidden (Cursor inherit is the parent model; mixed inherit shares the writer)
```

First audit-duty roster role is `spec-challenger`. Shipped tree: zero
`model: inherit` on review-ro/audit/judge.

### Test (file:line)

`tests/test_harness.py:14878` `test_mixed_inherit_on_audit_reviewer_is_forbidden_at_generate`

## Gates

```
python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest -v tests.test_harness.CursorRuntimeTargetTests
test_bootstrap_projects_the_cursor_surface_into_a_project ... ok
test_build_check_fails_when_the_tracked_cursor_tree_drifts ... ok
test_every_roster_role_reaches_the_cursor_target ... ok
test_mixed_inherit_on_audit_reviewer_is_forbidden_at_generate ... ok
test_no_cursor_agent_pins_a_model ... ok
test_readonly_reuses_the_codex_sandbox_predicate_rather_than_a_second_one ... ok
test_scaffold_leaves_the_doctrine_rule_in_an_existing_project ... ok
test_the_canonical_skills_reach_cursor_verbatim ... ok
test_the_cursor_coordinator_is_told_not_to_dispatch_through_another_lane ... ok
test_the_doctrine_rule_is_always_applied_and_is_the_shipped_doctrine ... ok
test_the_installer_knows_where_cursor_config_lives ... ok
Ran 11 tests in 20.381s
OK
```

```
python3 ai/scripts/heartbeat-run.py --interval 20 -- ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=23
GLOBAL_TREE_SYNC_OK harnesses=5
BUILD_CHECK_PASS
```

```
git diff --check
(exit 0, no whitespace errors)
```

Not touched: `docs/specs/032-*`, 033, Engram, `RUNTIMES`, `--route-decide`,
`MODE_BUDGETS`, heavy `repair-agent` pin, `[catalog].cursor` membership,
`docs/notas` by hand.
