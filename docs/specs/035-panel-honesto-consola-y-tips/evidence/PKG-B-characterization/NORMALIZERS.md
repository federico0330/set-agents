# PKG-B characterization normalizers

**Sealed:** 2026-08-20 (F004 repair — resealed before recapture)

Closed list — each named function in `characterize.py` maps 1:1 to exactly one row below.
The runner refuses to compare if the bijection breaks.

| Function | What it normalizes | Allowed because |
|---|---|---|
| `normalize_timestamps` | ISO-8601 datetimes and date-only tokens in output | Run-to-run clock |
| `normalize_absolute_tmp_paths` | Absolute paths under `/tmp`, `/var/tmp`, `TMPDIR`, and disposable `$HOME` (compiled from the child `HOME` sidecar, never `Path.home()` at import) | Isolation uses temp dirs |
| `normalize_durations_ms` | Latencies and durations expressed as `<n>ms` | Probe/network timing |
| `normalize_pids` | Process IDs (`pid=`, `PID `, standalone 4–7 digit tokens after `pid`) | Subprocess churn |
| `normalize_versions` | Git short SHA in `APP_STATUS sha=` and semver-like version tokens | Same tree, but runner normalizes residual noise |

**Universe closed.** Nothing else is permitted. A normalizer added after seeing `RESULT.md` is a finding, not an adjustment. Order regressions must DIFF — no global block sort.
