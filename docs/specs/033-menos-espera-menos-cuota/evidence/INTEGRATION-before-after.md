# 033 integration — before / after (2026-08-18 → 2026-08-19)

Feature `033-menos-espera-menos-cuota`. Six packages accepted. Phase INTEGRATION.
Without this comparison the feature has not proved it saved wait or quota.

Commands were run on `/home/federico/SET-AGENTES`, branch `main`, HEAD `de8a476`.
No push. AC-4.5 remains residual.

## Table

| Signal | 2026-08-18 baseline | After (six packages accepted) | Source |
|---|---|---|---|
| Menú Modelos, freeze before first frame | ≈16 s (13.12 s probe + 2.9 s catalog) | First `run_picker` **0.031 s** wall for the two first-paint tests; bite on the frozen 5 s probe was **RED ~5.03 s / GREEN ~0.030 s** | Baseline: operator request 2026-08-18. After: `python3 -m unittest tests.test_models_wizard_first_paint tests.test_models_wizard_ui.WizardBehaviorTests.test_first_paint_does_not_call_detect_subscriptions` → `Ran 2 tests in 0.031s OK`. Bite: `docs/specs/033-menos-espera-menos-cuota/evidence/PKG-2-implementer.md`. Live 16 s TTY session: **sin verificar** (no interactive wizard timed here). |
| Lista de modelos | 125 flat items, 5 providers | Grouped by provider, `n de total` / `n de coincidencias`, current marked `●`, headers not selectable | Baseline: operator request. After: PKG-3 `ai/scripts/tui.py` `_position_caption` / `PickerState.headers`; evidence `PKG-3-implementer.md`. Live recount of 125: **sin verificar** (would re-run `opencode models`). |
| Gate completo | 1237 s, 1286 tests | **788 s (13m08s), 1336 tests**, fail=0 error=0 skip=4, `VERIFY_PASS` | Baseline: operator request. After: `bash ai/scripts/verify.sh` via `heartbeat-run.py` 2026-08-19 post `de8a476`. Reporter: `ran 1336 tests in 13m08s`. |
| Consumo (CLI-native, Section 1) | 246 sessions / 8 days, 6.4G tokens, 92% cache_read | Same window `--since 2026-08-10`: **246 sessions, 6.4G total, 6.0G cache_read** | `python3 ai/scripts/cost-report.py --project /home/federico/SET-AGENTES --since 2026-08-10` line `TOTAL (Section 1 …) 246 … 6.4G`. This host’s Claude/Codex stores did not shrink; Cursor work does not land there. |
| Consumo (harness registry, Section 2) | **0** (routing.db only; Cursor subagents never hit `*_spawn.py`) | **144 sessions, tokens 0** (feature-state `spawns[]` / history `record-spawn`) | Same command, `TOTAL (Section 2 …) 144`. AC-6.5. Tokens stay 0 because feature-state does not store them. Two extra Cursor roles (repair + delta) after the scoped ceiling were **not** `record-spawn`’d (decision `033-pkg6-dos-despachos-extra-autorizados`). |
| CI | verify-linux green; verify-macos 1 wall-clock fail; windows-bootstrap failures=7 errors=1 skipped=654 | **AC-4.5 residual.** Local commits are **11 ahead** of `origin/main`; not pushed. No SHA of three green jobs in the same run. | `git status -sb` → `main...origin/main [adelante 11]`. `git log origin/main..HEAD --oneline` (11 commits, 1f5a24f…de8a476). User rule: no push unless asked. Workflow skip ceiling is in `.github/workflows/ci.yml` (PKG-4) but unproven on GitHub. |

## Cross-package still holds

- PKG-1 lane collapse left PKG-2 disk-first paint and PKG-3 grouping in place (`setup_models.py` / `tui.py` still own those behaviors; PKG-1 did not revert them).
- PKG-5 reporter still presents `verify.sh` (1336 tests, live ETA line).
- PKG-6: `PACKAGE_IMPLEMENTATION` still requires `docs/specs/<feature>/context/<PKG>.md`; status spawn cell is the **current package** (`render_status.py:235` `spawn_budget_counts(data, current)`).

## Residuals

1. **AC-4.5** — SHA of linux + macos + windows-bootstrap green in the **same** GitHub Actions run. Needs `git push` of `main` (11 local commits) and a green CI cycle. Not done here.
2. **Live TTY freeze** of the Modelos menu — not re-timed on a real terminal; the 0.031 s figure is the unittest wall, the 0.030 s figure is the AC-2.5 bite.
3. **Live catalog length** after grouping — not re-counted against OpenCode tonight.
4. **Section 1 token burn** — unchanged on this window; the Cursor-host saving (one session instead of twelve dispatches) is doctrinal (feature 032) and not visible in Section 1.

## Packages

| ID | Status | What landed |
|---|---|---|
| PKG-4 | accepted | Windows/macOS CI honesty, skip ceiling 660 |
| PKG-5 | accepted | verify reporter, ETA, fail-as-you-go |
| PKG-2 | accepted | first paint from disk &lt; 300 ms, auto-probe after |
| PKG-3 | accepted | grouped picker, counter, current marker |
| PKG-1 | accepted | one OpenCode string, fail-loud on quota |
| PKG-6 | accepted | context pack, P001 local-gate-runner, panel by risk, 80% WARN on current package, Section 2 ≠ 0 |
