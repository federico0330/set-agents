# PKG-B repair evidence (RP-01)

**package_id:** PKG-B  
**status:** repaired  
**date:** 2026-08-20

## Summary

| Field | Value |
|---|---|
| repaired_findings | PKG-B-F001, PKG-B-F002, PKG-B-F003, PKG-B-F004, PKG-B-F005, PKG-B-F006 |
| changed_files | `characterize.py`, `NORMALIZERS.md`, `MANIFEST.md`, `baseline/*`, `after/*`, `RESULT.md`, `PKG-B-residue-matrix.md`, `set_agents_app.py` |
| tests_run | `py_compile`, `python3 -m unittest tests.test_routing` → Ran 325 tests, OK (skipped=1) |
| remaining_findings | none |
| blockers | none |
| `wc -l set_agents_app.py` | **4340** (was 4399; −59 from deleting AST-identical `vault_link_private` shadow) |

---

## Root-cause groups

### Group A — runner integrity (F001, F002, F004, F006)

**Files:** `docs/specs/035-panel-honesto-consola-y-tips/evidence/PKG-B-characterization/characterize.py`, `NORMALIZERS.md`

| Finding | Change | Verification |
|---|---|---|
| **F001** | `ROOT = Path(__file__).resolve().parents[5]` (`characterize.py:17`); `_require_cli()` aborts if `CLI.is_file()` fails; `cmd_capture` refuses when every executable case hits `can't open file`; prior invalid `baseline/` and `after/` discarded | `baseline/global-help.stderr` empty (not launcher error); `rg "can't open file" baseline/` → no matches; baseline capture exit 0 |
| **F002** | `_build_child_env()` allowlist only (`PATH`, `HOME`, `TMPDIR`, `LANG`/`LC_ALL`, `TERM`, `GIT_TERMINAL_PROMPT`, `SET_AGENTS_STATE`, `SET_AGENTS_ROUTING_TEST_ROOT`); disposable routing sets `SET_AGENTS_ROUTING_TEST_ROOT` → `_routing_store()` test seam (`set_agents_app.py:68-73`) | `routing-valid` baseline exit captured; no pwd/home leakage in stderr |
| **F004** | Removed `normalize_nondeterministic_order` (global block sort); resealed `NORMALIZERS.md` to 5 functions, 1:1 bijection | `verify_normalizer_bijection()` passes at compare; `RESULT.md` → `diff_cases=0` |
| **F006** | No `os.environ` copy; HOME path regex compiled from child `.home` sidecar at compare time, not `Path.home()` at import | `_assert_env_safe()` validates allowlist keys only; disposable captures write `{case-id}.home` sidecar |

**Commands:**
```
python3 ai/scripts/heartbeat-run.py --interval 15 -- python3 docs/specs/035-panel-honesto-consola-y-tips/evidence/PKG-B-characterization/characterize.py baseline
# → 44 cases captured, exit 0

python3 ai/scripts/heartbeat-run.py --interval 15 -- python3 docs/specs/035-panel-honesto-consola-y-tips/evidence/PKG-B-characterization/characterize.py after
# → 44 cases captured, exit 0

python3 ai/scripts/heartbeat-run.py --interval 15 -- python3 docs/specs/035-panel-honesto-consola-y-tips/evidence/PKG-B-characterization/characterize.py compare
# → Wrote RESULT.md identical=42 declared=2 diff_cases=0
```

### Group B — host policy / case manifest (F003)

**Files:** `characterize.py` CASES, `MANIFEST.md`

| Finding | Change | Verification |
|---|---|---|
| **F003** | `--route-dispatched`, `--route-terminal`, `--route-quota-exhausted` → `disposable` + `needs_project=True` + routing test-root; `--quota-failover-e2e` → `disposable` (captured, exit 3); only `--route-decide` and `--fresh-probes` remain `declared-uncharacterizable` | `MANIFEST.md:18-21,52`; `mutant-quota-failover-e2e.exit` → `3`; `routing-route-dispatched.exit` → `1` (real CLI, not launcher error) |

### Group C — residue matrix / shadow deletion (F005)

**Files:** `set_agents_app.py`, `PKG-B-residue-matrix.md`

| Finding | Change | Verification |
|---|---|---|
| **F005** | AST-identical `vault_link_private` shadow deleted (former `:2989-3045`); import at `:2854` is canonical (`vault_ops.py:207`); matrix row `cmd_routing_decisions` third column fixed to `:900` (`entry.get("project_key") == PROJECT_KEY`); `vault_link_private` row rewritten with callee valve pass + caller anchor at `cmd_vault_link :3057` | Baseline captured with shadow; after captured without shadow; `compare` → all vault cases idéntico including `mutant-vault-link`; matrix `rg -c '^\| \`' → 16 rows |

**Recapture order (AC-B.1):** runner fixes → seal NORMALIZERS → baseline (unmoved tree) → delete shadow → after → compare.

**Commands:**
```
python3 -m py_compile ai/scripts/set_agents_app.py docs/specs/035-panel-honesto-consola-y-tips/evidence/PKG-B-characterization/characterize.py
# → exit 0

python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_routing
# → Ran 325 tests in 202.423s — OK (skipped=1)

wc -l ai/scripts/set_agents_app.py
# → 4340
```

---

## Per-finding closure

### PKG-B-F001 (high, testing)
- **Changed:** `characterize.py:17` (`parents[5]`), `_require_cli()`, launcher-error guard, discarded stale captures.
- **Verify:** baseline `global-help.exit` → `0`; no `can't open file` in any baseline stderr.

### PKG-B-F002 (high, data-integrity)
- **Changed:** `_build_child_env()` allowlist; `SET_AGENTS_ROUTING_TEST_ROOT` for routing disposable cases.
- **Verify:** characterization completes; routing cases use temp store not live `$HOME/.local/state`.

### PKG-B-F003 (medium, testing)
- **Changed:** CASES isolation for routing lifecycle flags; `MANIFEST.md` regenerated.
- **Verify:** `RESULT.md` identical for `routing-route-dispatched`, `routing-route-terminal`, `routing-route-quota-exhausted`, `mutant-quota-failover-e2e`.

### PKG-B-F004 (medium, testing)
- **Changed:** removed global sort normalizer; `NORMALIZERS.md` resealed (5 rows).
- **Verify:** bijection check passes; `diff_cases=0`.

### PKG-B-F005 (high, correctness)
- **Changed:** deleted shadow `vault_link_private`; matrix rows for `vault_link_private` and `cmd_routing_decisions` corrected.
- **Verify:** AST compare identical pre-delete; post-delete compare idéntico on all vault cases; `wc -l` 4340.

### PKG-B-F006 (high, security)
- **Changed:** no full environ copy; allowlist-only child env; HOME normalizer from sidecar.
- **Verify:** no secret values in captures; allowlist excludes `XAUTHORITY`/`ICEAUTHORITY`/token patterns.

---

## Destilado (dominio: architecture)

- La caracterización PKG-B ahora apunta al repo root real (`parents[5]`), usa env allowlist hermético con `SET_AGENTS_ROUTING_TEST_ROOT`, y compara 42 casos idénticos + 2 declarados (`--route-decide`, `--fresh-probes`).
- El shadow AST-idéntico de `vault_link_private` se eliminó (−59 líneas); la matriz de residuo sigue en 16 filas con experimentos `file:line` propios, no docstrings de módulo.
- Camino (b) ADR-0066 intacto: cero comandos movidos; la comparación baseline/after prueba que la extracción futura no rompe el CLI observable.
