# INTEGRATION — Feature 035 · panel honesto, consola partida, TIPS al día

**Feature:** `035-panel-honesto-consola-y-tips`  
**Phase:** INTEGRATION (integrator spawn, 2026-08-21)  
**Spec hash:** `296e051fccfd0cea2f222cc7061987f6b66507d9ed2b10539d7e58ea3169331c`  
**Integrated packages:** PKG-A (estado), PKG-B (consola), PKG-C (docs, module waiver)

---

## Cross-package composition

Three accepted packages compose without contract drift:

| Surface | Evidence | Contradiction? |
|---|---|---|
| Panel CLI vs doctrine | `cli_review.py:31-47` (`REVIEW_PANEL_REQUIRED`), `:58-67` (`BLOCKING_FINDING_OPEN`); `Global/_canonical/agents/orchestrator.md:105-118` (panel mandatory for FULL; `record-review` is small+low door) | **None** — ADR-0065 + orchestrator prose match CLI guards |
| Consola CLI vs characterization | `PKG-B-characterization/RESULT.md`: 45 cases — `identical=43`, `declared-uncharacterizable=2`, `diff_cases=0`; `set_agents_app.py` **4340** lines (`wc -l` 2026-08-21); `mutant-provider-remove` added (JUDGE-035-002) | **None** — path (b) extraction ceiling documented in `PKG-B-residue-matrix.md` (16/16 rows) |
| TIPS vs COMO-FUNCIONA | `TIPS-USO.md:7-18` (three can orchestrate; ADR-0064 panel caveat); `docs/COMO-FUNCIONA.md:227-229` (TIPS aligned); `:436-451` (§11: three PKG-A/B/C delivered, not deferred) | **None** — stale “OpenCode sole control plane” / “TIPS atrasado” / “record-review skips security-auditor” absent |
| TIPS vs cost-report | `TIPS-USO.md:136-144` (two vantage points; Cursor in spawns[], empty routing.db) matches `cost-report.py` contract cited in AC-C.3 | **None** |
| Module impacts | `module-impact-detect` 2026-08-21: PKG-A → `estado` (`already_covered`); PKG-B → `consola` (`already_covered`); PKG-C → no candidates (`module_impact_waived` in state) | **None** — no new `record-module-impact` required |

**Declared-uncharacterizable (host policy, not regressions):** `--route-decide` and `--fresh-probes` family — Cursor never `--route-decide` (`PKG-B-characterization/RESULT.md:38-52`).

---

## AC coverage table

| AC | Package | Verification | Integration note |
|---|---|---|---|
| AC-A.1 | PKG-A | `tests/test_harness.py:8914+` (`REVIEW_PANEL_REQUIRED`); delta + package review | FULL panel rejects all verdicts via `require_review_panel` (`cli_review.py:31-47`) |
| AC-A.2 | PKG-A | `create_ready_package` path green; `tests/test_harness.py:431-468` | small+low `record-review pass` unchanged |
| AC-A.3 | PKG-A | Three fixtures: absent key / explicit null / absent complexity (`tests/test_harness.py:8931-9017`) | Fail-safe FULL preserved (`model.py:571`) |
| AC-A.4 | PKG-A | `BLOCKING_FINDING_OPEN` at `cli_review.py:58-67`; test `:9030` | Scope limited to `pass` on SINGLE panel |
| AC-A.5 | PKG-A | Split test scenarios; `transitions.py` comment cites skip-delta decision | Advisor path via `record-repair --skip-delta` preserved |
| AC-A.6 | PKG-A | Historical state files untouched; guard is on mutate verb only | Confirmed by full suite (no state mutation in read paths) |
| AC-A.7 | PKG-A | `./build.sh --check` in verify prelude | `SELF_SCAFFOLD_SYNC_OK files=23`, `GLOBAL_TREE_SYNC_OK harnesses=5` |
| AC-A.8 | PKG-A | Package review (MODE_BUDGETS unchanged) | Pre-existing spawn-budget BLOCKED path; constant not modified |
| AC-A.9 | PKG-A | ADR-0065 Accepted; orchestrator regenerated in four Global trees | `BUILD_CHECK_PASS` covers copytree parity |
| AC-B.1 | PKG-B | Pre-move characterization under `PKG-B-characterization/baseline/` | Dated before code movement |
| AC-B.2 | PKG-B | Post-move compare in `PKG-B-characterization/after/` + `RESULT.md` | 43/45 identical; 2 host-policy waivers; `mutant-provider-remove` (`--provider-remove nonexistent-id`, exit 2, disposable) |
| AC-B.3 | PKG-B | Package review + repair evidence | No behavior “improvements” in refactor diff |
| AC-B.4 | PKG-B | `PKG-B-residue-matrix.md` | Every residual command has anchor + experiment column |
| AC-B.5 | PKG-B | Matrix + module docstrings | No new undocumented duplication |
| AC-B.6 | PKG-B | 16/16 matrix rows with third column filled | Path (b): zero commands moved, all anclado |
| AC-B.7 | PKG-B | Package review | `routing_core/` contracts untouched |
| AC-B.8 | PKG-B | Global verify (this run) | No existing test changed color |
| AC-C.1 | PKG-C | `TIPS-USO.md:7-18` | Codex quota warning preserved (`:15-17`) |
| AC-C.2 | PKG-C | `TIPS-USO.md:3-4`, `:49`, `:133-134` | Five Global trees + Cursor + pi native paths |
| AC-C.3 | PKG-C | `TIPS-USO.md:136-144` | Two-section cost model; Cursor explicit |
| AC-C.4 | PKG-C | `docs/COMO-FUNCIONA.md:227-229`, `:436-451` (§11) | All three 035 items delivered; no false `record-review` skip claim |
| AC-C.5 | PKG-C | `PKG-C-implementer.md` diff scope | Lifecycle, MCP/Engram, bootstrap untouched |
| AC-C.6 | PKG-C | `README.md:305` reviewed | Index line still accurate as pointer |

**Note:** AC-B.2 acceptance criteria list in feature state ends at AC-B.8; AC-B.8 covers “no existing test changes color” — satisfied by integration verify.

---

## Global gate — `verify.sh`

**Command (exact):**

```bash
python3 ai/scripts/heartbeat-run.py --interval 30 -- ./ai/scripts/verify.sh
```

**Outcome:** **PASS** (`VERIFY_PASS`, exit 0)  
**Wall time:** 1488247 ms (~24m 48s)  
**Started:** 2026-08-21T12:31:04Z · **Ended:** 2026-08-21T12:55:52Z

### Prelude gates

| Token | Result |
|---|---|
| `SELF_SCAFFOLD_SYNC_OK` | files=23 |
| `GLOBAL_TREE_SYNC_OK` | harnesses=5 |
| `BUILD_CHECK_PASS` | ok |

### Test summary

```
ran 1372 tests in 23m42s  fail=0  error=0  skip=4
1372/1372 · ✗0
```

### Post-test gates

| Token | Result |
|---|---|
| `GLOBAL_PORTABILITY_OK` | ok |
| `CANONICAL_PATHS_OK` | ok |
| `FEATURE_STATE_OK` | ok |
| `VERIFY_PASS` | ok |

### Skips (environment / credentials — not integration defects)

1. `test_routing.RoutingTests.test_ac10_p2_local_live_parity_gate` — OpenCode Zen/Go credentials not verified  
2. `test_harness.HarnessTests.test_pi_verbose_startup_actually_loads_the_generated_tree_e2e` — `SET_AGENTS_PI_E2E=1` not set  
3. `test_harness.HarnessTests.test_pi_subagents_roster_discoverable_via_scripted_session_e2e` — `SET_AGENTS_PI_E2E=1` not set  
4. `test_spawn_materialization.SelectionPathTests.test_route_decide_envelope_reports_selection_path` — `NO_ELIGIBLE_ROUTE` / no live credentials

---

## Judge finding closures (follow-up, 2026-08-21)

| Finding | AC | Fix | Evidence |
|---|---|---|---|
| **JUDGE-035-001** | AC-C.4 | Rewrote `docs/COMO-FUNCIONA.md:436-451` (§11): PKG-A/B/C marked delivered; removed false claim that `record-review` can skip `security-auditor` | `COMO-FUNCIONA.md:443-446` cites ADR-0065 + `cli_review.py:31-67` |
| **JUDGE-035-002** | AC-B.2.4 | Added `mutant-provider-remove` to `characterize.py` CASES + `MANIFEST.md`; disposable `--provider-remove nonexistent-id` (exit 2, `PROVIDER_UNKNOWN`, no write); recaptured in `baseline/` and `after/` | `MANIFEST.md`: `` `--provider-remove nonexistent-id` ``; `RESULT.md`: `identical=43 declared-uncharacterizable=2 diff_cases=0` |
| **JUDGE-035-003** | AC-B.2 / path (b) | **Rejected** — no recapture against commit `788eb62` as a second CLI | See paragraph below + orchestrator decision `035-judge-003-path-b-same-binary` |
| **JUDGE-035-004** | Evidence bundle | **Closed** — independent reviews persisted mechanically from state | [`REVIEWS.md`](REVIEWS.md) |
| **JUDGE-035-005** | INTEGRATION blockers | **Closed** — removed stale `record-gate` row; `global_gates[0]` already `verify`/`pass` in state | This file §Remaining blockers |
| **JUDGE-035-006** | ADR-0066 | **Closed** — `wc -l` 4340 after F005 shadow delete; T-105 4399 was pre-movement report | `docs/adr/0066-el-cargador-de-tests-es-el-techo-de-extraccion.md:131-136` |

### JUDGE-035-003 — path (b), same tree, same binary

Approved design [`design.md:518-521`](../design.md) states that under path **(b)** — no production code moved — `baseline/` and `after/` run against **the same tree and the same binary**. The `mutant-provider-remove` case added in the JUDGE-035-002 follow-up was captured into both directories with the current `python3 ai/scripts/set_agents_app.py`; `--provider-remove` was **not** moved and no second CLI was invented. `MANIFEST.md` still records the seal-date git HEAD (`788eb62`) as metadata from the original characterization seal; it does **not** imply that post-integration cases must be replayed against that commit as a different executable. Orchestrator logged `035-judge-003-path-b-same-binary` accordingly.

**Compare command (JUDGE-035-002 follow-up):**

```bash
python3 ai/scripts/heartbeat-run.py --interval 15 -- \
  python3 docs/specs/035-panel-honesto-consola-y-tips/evidence/PKG-B-characterization/characterize.py compare
```

---

## Remaining blockers

Global gate already on record: `ai/state/features/035-panel-honesto-consola-y-tips.json` → `global_gates[0]` `name=verify`, `status=pass` (integrator `91fa466b`, 2026-08-21T12:57:04Z).

| Blocker | Owner | Notes |
|---|---|---|
| Fourth adversarial-judge re-run | orchestrator | PKG-C at spawn ceiling **10/10** — extra spawn authorization required. Prior judges: `37b21687`, `17a6cfd8`, `1329a320` (all `JUDGE_FAIL`; 001–006 addressed in integration follow-ups) |
| Feature transition `INTEGRATION → DONE` | orchestrator | Out of integrator scope |
| Environment skips (4) | n/a | Pre-existing credential/E2E gates; not introduced by 035 |

**No integration wiring bugs found.** No package re-open required.

---

## Evidence paths

- This file: `docs/specs/035-panel-honesto-consola-y-tips/evidence/INTEGRATION.md`
- **Independent reviews dump:** [`REVIEWS.md`](REVIEWS.md) (from `ai/state/features/035-panel-honesto-consola-y-tips.json`)
- PKG-A: `evidence/PKG-A-implementer.md`, `PKG-A-repair.md`, `PKG-A-doors.md`
- PKG-B: `evidence/PKG-B-characterization/`, `PKG-B-residue-matrix.md`, `PKG-B-repair.md`
- PKG-C: `evidence/PKG-C-implementer.md`
- ADR: `docs/adr/0065-record-review-membresia-y-finding-abierto.md`, `docs/adr/0066-el-cargador-de-tests-es-el-techo-de-extraccion.md`
- Verify transcript: integrator shell 2026-08-21 (`VERIFY_PASS` tail reproduced above)
