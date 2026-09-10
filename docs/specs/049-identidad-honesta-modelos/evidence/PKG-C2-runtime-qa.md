# PKG-C2 — Runtime QA (hermetic)

**Date:** 2026-09-10  
**Candidate:** `/tmp/set-agents-049-c2.YfrczU` @ `ff91f5538c3ee588b29a6b7267ad82439191b5c1`  
**Scope:** cache-first home, apply/lock/restore behaviors (no live OpenCode TTY, no `Global/**`)

## Global boundary

```bash
git -C /tmp/set-agents-049-c2.YfrczU diff --name-only 3878fb0d..ff91f55 | grep -c Global || true
```

| Exit | Output |
|------|--------|
| 0 | `0` |

No `Global/**` paths in the C2 repair delta.

## Check 1 — First frame / menu: zero measurement subprocesses (cache-seeded path)

**Test:** `HomeFirstPaintTests.test_first_frame_is_cache_only_and_has_human_actions`  
**Also:** `ModelsPresentationTests.test_first_frame_seeds_host_counts_from_disk`

```bash
cd /home/federico/SET-AGENTES
PYTHONPATH=ai/scripts python3 ai/scripts/heartbeat-run.py --interval 30 -- \
  python3 -m unittest -v \
  tests.test_console_model_state_049.HomeFirstPaintTests.test_first_frame_is_cache_only_and_has_human_actions \
  tests.test_console_model_state_049.ModelsPresentationTests.test_first_frame_seeds_host_counts_from_disk
```

| Exit | Outcome |
|------|---------|
| 0 | Both OK. `menu()` does not call `launch_update_check`, `measure_hosts`, `drift_state`, or `first_run`. Home labels include Estado, Configurar, Modelos, Forma de trabajo, Actualizar estado, Modo experto, Salir. Disk host-count cache seeds RAM via `_seed_host_counts_cache` without subprocess. |

Worktree re-run (subset): same test OK @ worktree HEAD.

## Check 2 — Pin set/clear lock contention fails closed

**Tests:** `PinWriterLockTests`, `ConcurrencyAndSubprocessTests.test_concurrent_host_pin_writer_blocks`

```bash
cd /home/federico/SET-AGENTES
PYTHONPATH=ai/scripts python3 -m unittest -v \
  tests.test_model_apply_049.PinWriterLockTests \
  tests.test_model_apply_049.ConcurrencyAndSubprocessTests.test_concurrent_host_pin_writer_blocks
```

| Exit | Outcome |
|------|---------|
| 0 | All OK. With `models-apply.lock` held (`fcntl.LOCK_EX`): `cmd_model_pin_set`, `cmd_model_pin_clear`, and `write_host_pin_locked` raise `ModelsError` before any `atomic_write`; no overlay mutation. |

Worktree re-run: `PinWriterLockTests` + `ModelStateCliTests` OK.

## Check 3 — `--model-state` CLI remains read-only

**Tests:** `ModelStateCliTests`

```bash
cd /home/federico/SET-AGENTES
PYTHONPATH=ai/scripts python3 -m unittest -v tests.test_model_state_049.ModelStateCliTests
```

| Exit | Outcome |
|------|---------|
| 0 | OK. Valid query → rc 0, single schema v1 JSON, no `session_id`. Mutating/invalid argv (`--update`, bad `--project`) → rc 2, empty stdout, stderr mentions `model-state`. |

**Hermetic side-effect probe:**

```bash
TMP=$(mktemp -d)
export SET_AGENTS_STATE="$TMP/state"
mkdir -p "$SET_AGENTS_STATE"
# query OK
python3 ai/scripts/set_agents_app.py --model-state --json --project "$PWD"  # rc 0
# mutate combo rejected
python3 ai/scripts/set_agents_app.py --model-state --json --update          # rc 2, stdout empty
find "$TMP" -type f | wc -l  # 0 before and after
```

| rc (query) | rc (--update) | stdout (--update) | state files touched |
|------------|---------------|-------------------|---------------------|
| 0 | 2 | 0 bytes | 0 |

## Summary

| Check | Result |
|-------|--------|
| Cache-first first frame (no measurement subprocesses) | PASS |
| Host-count disk cache seed | PASS |
| Pin set lock contention fail-closed | PASS |
| Pin clear lock contention fail-closed | PASS |
| Host pin writer lock contention fail-closed | PASS |
| `--model-state` read-only CLI | PASS |
| No `Global/**` in C2 delta | PASS |

**Overall:** PASS — hermetic unittest + CLI probes match PKG-C2 acceptance for cache-first home and lock fail-closed behavior.
