# PKG-3 repair (PKG3-F01, PKG3-F02)

## Bite (`cp`, never git restore/checkout/stash)

Broken: `/tmp/pkg3-repair/setup_models.py.broken`. Green: `/tmp/pkg3-repair/setup_models.py.green`.

`_models_in_use` / `_current_cell_value` broken: both new tests RED

```
AssertionError: {'openai/gpt-5.5': ['coord', 'coord', 'debugger'], 'openai/gpt-5.6-luna': None}
  != {'openai/gpt-5.5': ['coord', 'debugger'], 'openai/gpt-5.6-luna': ['implementer']}
AssertionError: ... 'audit': {'opencode': {}} ...
```

`cp .../setup_models.py.green ai/scripts/setup_models.py` → GREEN (`Ran 3 tests in 0.039s OK`)

## Change

- F01 `setup_models.py:446` `_models_in_use`: unique first-seen names; walks `roles.*.tiers.*.opencode`. Test calls `_models_in_use`.
- F02 `setup_models.py:608` read via `_current_cell_value` `.get()` (`:76`). `parse_address` stays on apply (`:626`).

## Gates

`python3 -m unittest` TuiTests + test_menu_ui + test_models_wizard_ui: `Ran 119 tests in 4.677s OK`
`./build.sh --check`: `BUILD_CHECK_PASS`
`git diff --check`: exit 0
`verify.sh` not run.
