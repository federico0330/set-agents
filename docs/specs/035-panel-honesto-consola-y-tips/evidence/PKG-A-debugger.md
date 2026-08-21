# PKG-A debugger evidence — `_init_ready_package` panel path

## Root cause

`tests/test_module_docs.py:_init_ready_package` (lines 62–97) called `record-review` after
`transition PACKAGE_REVIEW` on a `--complexity medium` package. PKG-A guards require a full
review panel for medium complexity (`REVIEW_PANEL_REQUIRED`, exit 2). Six tests ERROR because
`_run(..., check=True)` raised `CalledProcessError`.

## Minimal fix

Replaced the single `record-review` call at line 91 with the legal panel sequence
(`start-review-panel` → `record-subreview` ×2 → `finalize-review-panel`), matching
`tests/test_harness.py:492-508 full_panel_pass`.

### Rewritten helper (file:line)

- `tests/test_module_docs.py:62-104` — `_init_ready_package` helper
- `tests/test_module_docs.py:73` — `--complexity medium` unchanged on `create-package`
- `tests/test_module_docs.py:91-98` — panel path replaces `record-review`
- `tests/test_module_docs.py:374` — untouched (`--complexity medium`, no `record-review`)

### Production code

No edits to `ai/scripts`, `PROYECTO`, or `Global`.

## Verification

```text
$ python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_module_docs
.........................
----------------------------------------------------------------------
Ran 25 tests in 17.222s

OK
exit: 0
```

## Regression test added

No — existing six tests cover the helper; fix restores prior assertions.
