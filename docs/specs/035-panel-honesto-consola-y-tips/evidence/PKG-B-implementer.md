# PKG-B implementer evidence

Feature `035-panel-honesto-consola-y-tips` · tasks T-101, T-103, T-104, T-105 · 2026-08-20.

## T-101 — characterization (AC-B.1, AC-B.2)

**Store:** `docs/specs/035-panel-honesto-consola-y-tips/evidence/PKG-B-characterization/`

| Step | Command | Outcome |
|---|---|---|
| Normalizers sealed | wrote `NORMALIZERS.md` (6 functions, dated 2026-08-20) before any capture | bijection enforced in runner |
| Manifest sealed | `python3 …/characterize.py manifest` | `MANIFEST.md` HEAD `788eb6207e5ccaca7c7a73642eb7f17f58e275bd` |
| Baseline | `python3 …/characterize.py baseline` | 44 cases → `baseline/*.stdout\|.stderr\|.exit` |
| After (same binary) | `python3 …/characterize.py after` | 44 cases → `after/` |
| Compare | `python3 …/characterize.py compare` | `RESULT.md`: **38 identical**, **6 declared-uncharacterizable**, **0 diff cases** |

**CLI entry (MANIFEST):** `python3 ai/scripts/set_agents_app.py`

**Declared-uncharacterizable (6):** `--route-decide`, `--route-dispatched`, `--route-terminal`, `--route-quota-exhausted`, `--fresh-probes` (host policy: Cursor never `--route-decide`); `--quota-failover-e2e` (blocks on live subscription).

**Isolation:** disposable `HOME` + `SET_AGENTS_STATE=$HOME/.local/state/set-agentes` + temp git project; no live credentials injected.

## T-103 — move valve (§11.2)

**Result:** nothing moved (path **(b)** per T-102 / ADR-0066).

All 16 residual commands fail at least one valve condition (globals `PROJECT_KEY`/`PROJECT_ROOT`/`ROOT`/`ROUTING_WARNINGS`/`STATE_DIR`/`APP_CONFIG`, lazy back-import, or `patch.object(app,…)` in read-only tests). Zero new files under `ai/scripts/`.

**Docstring correction (F-B-ARCH-01):** one sentence added in `routing_cli.py` and `vault_ops.py` pointing at `PKG-B-residue-matrix.md` and correcting the stale `_import()` mechanism (`tests/test_harness.py:788-796`).

## T-104 — residue matrix

**Path:** `docs/specs/035-panel-honesto-consola-y-tips/evidence/PKG-B-residue-matrix.md`

**Rows:** 16/16 with third column filled (`file:line` reads + greps). All **anclado**.

## T-105 — line count

| When | Command | Lines |
|---|---|---|
| before | `wc -l ai/scripts/set_agents_app.py` (2026-08-20 baseline) | **4399** |
| after | `wc -l ai/scripts/set_agents_app.py` (this spawn) | **4399** |

No code moved; count unchanged as expected.

## Local validations

```
python3 -m py_compile ai/scripts/routing_cli.py ai/scripts/vault_ops.py docs/specs/035-panel-honesto-consola-y-tips/evidence/PKG-B-characterization/characterize.py
python3 docs/specs/035-panel-honesto-consola-y-tips/evidence/PKG-B-characterization/characterize.py compare
wc -l ai/scripts/set_agents_app.py
```

Production callables in owned modules were not changed beyond module docstrings; `./ai/scripts/verify.sh` and full unittest suites deferred to gate-runner per spawn contract.

## Findings

| id | severity | evidence | required outcome |
|---|---|---|---|
| F-B-ARCH-01 | low (documentation) | Stale `_import()` mechanism in pre-existing docstrings; corrected one sentence each in owned files; `project_identity.py` untouched (not owned) | package-reviewer confirms matrix cites `:788-796`, not old story |

## Destilado (dominio: architecture)

- Path **(b)** closes PKG-B: 44-case three-channel characterization precedes any move; same-binary baseline/after shows only normalizable noise (38/38 captured cases identical).
- Extraction ceiling is test identity + mutable globals, not import syntax: `_import()` restores `sys.modules` after exec (`tests/test_harness.py:788-796`); sixteen routing/vault commands stay in `set_agents_app.py` with a filled residue matrix.
- `set_agents_app.py` remains **4399** lines — evidence, not a goal; the deliverable is enumeration plus honest characterization, not line deletion.
