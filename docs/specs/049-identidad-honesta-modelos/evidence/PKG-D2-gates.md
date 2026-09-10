# PKG-D2 — gate summary (sanitized)

- **C2_REF:** `ff91f5538c3ee588b29a6b7267ad82439191b5c1`
- **Worktree:** `/tmp/set-agents-049-d2.OwbVs7`

## Scoped unittest (AC-09)

```text
python3 -m unittest -v tests.test_model_identity_integration_049 tests.test_model_identity_tty_049
rc=0  tests=19  failures=0  errors=0  elapsed≈4.0s
```

## Global gates

| Gate | rc | note |
| --- | ---: | --- |
| `./build.sh --check` | 0 | `BUILD_CHECK_PASS` |
| `./ai/scripts/verify.sh` | 1 | pre-C2 failures in harness/routing/spawn (see owner-return) |
| `git diff --check` | 0 | clean |
| contract-hash (worktree paths) | 1 | quartet absent at C2_REF — see owner-return |

## Contract hash (root reference only)

Computed from `/home/federico/SET-AGENTES` where the quartet exists:

`sha256:47923adc4a83d40a78edd210aedf91959397e97d319d9d64f406258a07813278`

Worktree command fails with `FileNotFoundError` for `docs/specs/049-identidad-honesta-modelos/spec.md`.

## verify.sh pre-existing failures (not PKG-D2)

Modules with FAIL/ERROR unrelated to `test_model_identity_*`:

- `tests.test_decide_always`
- `tests.test_harness` (menu/proponer/MCP/setup_models)
- `tests.test_routing` (ADR-0043 AC-10)
- `tests.test_spawn_materialization` (wizard panel)

No `model_identity` failures observed in verify run.
