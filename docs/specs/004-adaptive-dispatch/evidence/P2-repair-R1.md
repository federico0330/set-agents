# P2-opencode-lane — repair evidence (R1)

Consolidated repair of 3 findings from the package-reviewer + security-auditor panel over
P2-opencode-lane (feature 004-adaptive-dispatch), before acceptance. Baseline for this repair:
the uncommitted P2 implementation described in `docs/specs/004-adaptive-dispatch/evidence/P2-implementation.md`
(T-201..T-204, 150/150 tests). No opportunistic refactors; routing core
(`routing_core/**`, `set_agents_app.py`, `routes.v1.toml`, `tests/test_routing.py`) and `roles.tsv`
untouched.

## SEC-A01 (medium) — degraded-mode doctrine must branch on the reason taxonomy

**File**: `Global/_canonical/agents/orchestrator.md`, "Tiered dispatch — decide→spawn protocol"
(now lines 140-207; the branching rewrite is steps 2-3, lines ~149-196).

**Root cause confirmed in source** (read-only, `ai/scripts/set_agents_app.py` lines 106-120,
230-298 and `ai/scripts/routing_core/service.py` lines 93-192): `--route-decide`'s exit code is
NOT a fine-grained signal — several structurally different outcomes share exit 1 (`ok=false`).
The only reliable branch key is the envelope's `reason_codes` list. The confirmed reason
taxonomy:
- `ok=true`, `execution_enabled=true`, empty `reason_codes`: a normal authorized decision
  (writer or non-writer/non-review). `data.provider` can legitimately be `openai-codex` OR
  `anthropic` (a route can win with any provider; OpenCode can only ever dispatch
  `openai-codex`, since `anthropic` runs through the claude-code runtime — confirmed against the
  context pack's "proyección lane↔catálogo" section and `_opencode_projected_route` in
  `generate.py`).
- `ok=true`, `reason_codes == ("REVIEW_IDENTITY_UNVERIFIED",)`: the one benign non-executable
  shape (`_DECIDE_OK_NON_EXECUTABLE_REASONS` in `set_agents_app.py` L113) — no `review_of_run_id`
  was offered yet.
- `reason_codes == ("ROUTING_UNAVAILABLE",)`: router/probe/CLI-level unavailability (catch at
  `set_agents_app.py` L298, an `except (routing.RoutingError, OSError, TypeError, ValueError,
  OverflowError)` around the whole decide path) — no run was ever authorized.
- Every other `ok=false` reason is the routing brain's `service.route()` actively refusing the
  request: `REVIEW_IDENTITY_INVALID` (service.py L108/114 — a `review_of_run_id` WAS offered and
  rejected: wrong role, not a real terminal writer, or a lookup error), `REVIEWER_INDEPENDENCE_
  UNAVAILABLE`/`NO_ELIGIBLE_ROUTE` (L150 — no eligible route survived the hard exclusions),
  `PROVIDER_UNAUTHENTICATED` (L133/172/181/183 — inventory/re-probe rejected the model),
  `CATALOG_INVALID` (L168 — a fresh snapshot recheck failed), `AUTHORIZATION_INVALID` (L170 — the
  re-validated identity no longer matches), `AUTHORIZATION_REPLAY`/`STATE_CONFLICT` (`store.py`
  L236/258/288/301/332/340/347 — durable-store level replay/conflict detection), plus the
  CLI's own parse-level `FACTS_INCOMPLETE`/`CONTEXT_UNRESOLVED`/`ROUTING_INPUT_INVALID`.

**Problem repaired**: the OLD doctrine's step 3 ("Model-mismatch") + step 4 ("Router
unavailable") only distinguished two shapes and implicitly treated everything else that wasn't
an explicit `openai-codex`+`luna/sol/terra` match as either a model-mismatch or a router failure
— there was no explicit branch for `AUTHORIZATION_REPLAY`, `REVIEWER_INDEPENDENCE_UNAVAILABLE`,
or `REVIEW_IDENTITY_INVALID`, so an orchestrator following the doctrine literally had nowhere to
route a hard denial except into one of the two "spawn BASE agent" paths — silently discarding the
routing brain's enforcement/audit signal.

**Fix**: rewrote doctrine step 3 into an explicit three-way branch, allowlisting only the two
honest-degrade shapes and the one benign shape, with everything else (named exhaustively AND as a
fail-closed default) going to `HUMAN_DECISION_REQUIRED`. New text (quoted from
`Global/_canonical/agents/orchestrator.md` lines 149-196, propagated verbatim to
`Global/opencode/agents/orchestrator.md`, `Global/claude-code/agents/orchestrator.md`, and
`Global/codex/agents/orchestrator.toml`):

```
3. **Branch on the decision outcome.** Exactly two shapes are a legitimate, honest degrade to the BASE
   agent; the benign reviewer shape spawns the base reviewer by design; every other non-ok decision HALTS.
   Never collapse this into a catch-all "anything else / non-zero exit → degraded mode" — that would
   silently rewrite a HARD ROUTING DENIAL (a spoofed/replayed `review_of_run_id`, an unverifiable
   authorization) into an unconditional base-agent spawn, discarding the routing brain's
   enforcement/audit signal and breaking the independence/replay guarantees `--route-decide` exists to
   provide.
   a. **Legitimate degrade — the lane cannot honor an otherwise-honest decision:**
      - **Off-lane model.** `ok=true`, `data.execution_enabled=true`, but `data.provider != "openai-codex"`
        (e.g. an anthropic fallback like `haiku`/`sonnet`/`opus` — a model this lane genuinely cannot
        spawn). The routing brain DID authorize a run; it is simply not one OpenCode can dispatch. Close it
        as abandoned (`python3 ai/scripts/set_agents_app.py --route-terminal <run_id> failure`), then spawn
        the BASE static agent `<role>`.
      - **Router/probe unavailable.** `reason_codes == ["ROUTING_UNAVAILABLE"]` (or the CLI call itself
        failed to produce a usable decision: crash, timeout, malformed output). No run was ever authorized
        here, so there is nothing to close: spawn the BASE agent `<role>` directly. Do not retry the decide
        call in a loop — one attempt, then degrade.
      Narrate both as an explicit, honest degrade naming the concrete reason (`off-lane: <data.model>` or
      `ROUTING_UNAVAILABLE`) — never a bare "degraded mode" with no reason attached.
   b. **Benign non-executable review** — `reason_codes == ["REVIEW_IDENTITY_UNVERIFIED"]` (see step 4 below):
      not a degrade, the designed shape for "no verified writer run offered yet" — spawn the BASE reviewer.
   c. **HARD DENIAL — HALT, never a silent base spawn.** Every other non-ok decision, including but not
      limited to `AUTHORIZATION_REPLAY`, `REVIEWER_INDEPENDENCE_UNAVAILABLE`, `REVIEW_IDENTITY_INVALID`,
      `AUTHORIZATION_INVALID`, `NO_ELIGIBLE_ROUTE`, `PROVIDER_UNAUTHENTICATED`, `CATALOG_INVALID`,
      `STATE_CONFLICT`, `FACTS_INCOMPLETE`, or `CONTEXT_UNRESOLVED` — and, as a fail-closed default, any
      decision that is not literally one of the (a)/(b) shapes above, even a reason not named here. These
      are the routing brain actively REFUSING the request, not a lane limitation: do not spawn anything for
      this role/task on this decision. Stop and raise `HUMAN_DECISION_REQUIRED`, quoting the exact
      `reason_codes` — never a generic "degraded" — so the blocker is legible and actionable.
      **`REVIEW_IDENTITY_INVALID` vs `REVIEW_IDENTITY_UNVERIFIED`**: UNVERIFIED (3b) means no
      `review_of_run_id` was offered — benign, spawn the base reviewer. INVALID means one WAS offered and
      the routing brain rejected it (wrong role, not a real terminal writer, forged/stale/replayed id) — a
      hard denial (3c): halt, never degrade.
```

Also updated: step 1 (now reads both `ok` and `reason_codes`, `--json` explicit), step 4/reviewers
(cross-references 3b vs 3c explicitly instead of a single vague "non-executable" line), step 6
(narration must name the exact `reason_codes` for a hard denial, not "degraded"). Old steps 3+4
merged into new step 3; old steps 5-8 renumbered 4-7 (all content preserved, worker-death and
permission-surface text otherwise unchanged).

**Test**: no pre-existing test pinned the old doctrine text verbatim, so none needed weakening or
deletion. Added `tests/test_harness.py::test_orchestrator_doctrine_branches_on_route_decide_reason_taxonomy`
(after `test_tier_variants_emitted_identical_to_base_and_orchestrator_can_delegate_them`), which
regenerates via `./build.sh` and asserts, across all three generated harness artifacts
(`Global/opencode/agents/orchestrator.md`, `Global/claude-code/agents/orchestrator.md`,
`Global/codex/agents/orchestrator.toml`): presence of `HARD DENIAL`, `HUMAN_DECISION_REQUIRED`,
`AUTHORIZATION_REPLAY`, `REVIEWER_INDEPENDENCE_UNAVAILABLE`, `REVIEW_IDENTITY_INVALID`,
`REVIEW_IDENTITY_UNVERIFIED`, `PROVIDER_UNAUTHENTICATED`, `NO_ELIGIBLE_ROUTE`,
`ROUTING_UNAVAILABLE`, and the off-lane condition `data.provider != "openai-codex"`; and absence of
the old hardcoded prose mapping (`` `gpt-5.6-luna` (→ `@fast`) ``, `` `gpt-5.6-sol` (→ `@balanced`) ``,
`` `gpt-5.6-terra` (→ `@frontier`) ``) — doubling as the PKG-N01 regression guard.

## PKG-N01 (low) — single source of truth for decided-model→variant

**File**: `Global/_canonical/agents/orchestrator.md`, doctrine step 2 (line ~151-156).

**Problem**: the old step 2 spelled out a literal prose table (`gpt-5.6-luna` → `@fast`,
`gpt-5.6-sol` → `@balanced`, `gpt-5.6-terra` → `@frontier`) as a third, unguarded leg that could
silently drift from `models.toml`'s tier tables (the actual source of truth) on a future
re-tiering — nothing would fail the build if the doctrine's hardcoded names went stale.

**Fix**: reframed the rule so the emitted variant's own `model:` line is the single source of
truth for the match — no model names are hardcoded in the doctrine anymore. New text:

```
2. **Match by MODEL, never by tier alone.** `data.tier` is a hint, not the identity. The single source of
   truth for the match is the emitted variant file itself, never a hardcoded prose table in this doctrine:
   when `data.provider == "openai-codex"`, spawn the `<role>@<tier>` variant whose emitted `model:` line
   equals `openai/<data.model>` verbatim. The model→tier binding lives exactly once, in `models.toml`'s
   `[roles.<role>.tiers.<tier>]` tables, kept truthful by the build-time coherence gate
   (`generate.py::check_variant_catalog_coherence`) — re-tiering the catalog must never require editing
   this doctrine.
```

**Belt-and-suspenders build-time assertion — deliberately NOT added**: the context pack offered
this as optional ("If you want..."). Evaluated and skipped: `generate.py`'s variant-emission loop
(lines 361-382) already writes `model: {tiers[tier]}` directly from the SAME `role_tiers` dict
sourced from `models.toml` — the emitted line and the models.toml value are the same Python object
at the point of writing, not two independently-derived values that could drift apart by a logic
bug. A "does the emitted file equal the models.toml value" assertion would be definitionally true
by construction and would not exercise any real risk, unlike `check_variant_catalog_coherence`
(already present, unmodified) which DOES bind two independently-sourced values
(emitted model ↔ `routes.v1.toml`) and is where the real coherence risk lives. No code added for
this half of the finding, to avoid an opportunistic no-op refactor.

**Test**: covered by the same `test_orchestrator_doctrine_branches_on_route_decide_reason_taxonomy`
(assertNotIn on the three retired hardcoded strings, across all three harnesses) plus the
pre-existing, unmodified `test_tier_variants_emitted_identical_to_base_and_orchestrator_can_delegate_them`
and `test_variant_coherence_gate_fails_build_on_unprojectable_tier_model`, which already prove the
emitted-model↔catalog binding independently.

## PKG-N02 (low) — roster-intersect the variant expectation

**File**: `ai/scripts/generate.py`.

**Problem**: `variant_names` (in `generate()`) and `variant_expected` (in `validate()`) were built
directly from `models_config.load_role_tiers(config, profile)`'s raw result — every role name
with a `[roles.<role>.tiers]` table in `models.toml`, unfiltered — while variant EMISSION
(`generate()`'s per-role loop, `for row in roles: tiers = role_tiers.get(row["role"])`) is driven
by `roles`, the roster loaded from `roles.tsv`. In the current repo this drift is coincidentally
masked because `models_config.load_roles()` (called before `load_role_tiers()` in the same
`generate()`/`validate()` call) already validates that every `config["roles"]` key exists in
`roles.tsv` (`models_config.py` L264-266) — but that protection is incidental (it fires for ANY
role override, not specifically for a `tiers` table) and does not hold for a caller that supplies
`role_tiers`/`roles` independently (e.g. `validate()` called directly, as several existing tests
already do via explicit `roles`/`role_tiers` arguments). A future drift here would surface as the
opaque `"opencode: generated role set mismatch"` instead of naming the actual offending role.

**Fix**: added `generate.py::_roster_filtered_role_tiers(roles, role_tiers)` (new function,
`ai/scripts/generate.py:298-315`) — intersects `role_tiers`'s keys against the roster's role names
and fails closed with a targeted message naming the offending role(s) if any tier table belongs to
a role outside the roster; otherwise returns `role_tiers` unchanged. Wired into both call sites so
emission and expectation are provably built from the identical, already-validated set:
- `generate()`, `ai/scripts/generate.py:321`: `role_tiers =
  _roster_filtered_role_tiers(roles, models_config.load_role_tiers(config, profile))`
  (`variant_names` at L322 is now built from this filtered/asserted result).
- `validate()`, `ai/scripts/generate.py:497`: `role_tiers = _roster_filtered_role_tiers(roles,
  role_tiers)`, immediately after `role_tiers` is resolved (either the caller-supplied value or the
  freshly-loaded default) and before `variant_expected` is built (L505ish).

```python
def _roster_filtered_role_tiers(roles, role_tiers):
    """PKG-N02: variant EMISSION is always driven by `roles` (the active roster); the
    EXPECTATION (`variant_names`/`variant_expected`) must be built from that same
    roster-filtered set, never straight off `models_config.load_role_tiers`'s raw
    result — otherwise a tiered role absent from the active roster silently produces
    an expected-but-never-emitted variant, surfacing later as an opaque "generated
    role set mismatch" instead of a targeted diagnostic. Fails closed: a tiers table
    for a role outside the roster is a stale/mistaken models.toml entry, named
    explicitly, never silently dropped or silently honored."""
    roster_names = {row["role"] for row in roles}
    orphaned = sorted(set(role_tiers) - roster_names)
    if orphaned:
        die(
            f"models.toml declares [roles.<role>.tiers] for role(s) {orphaned} not present "
            f"in the active roster (roles.tsv) — remove the stale tier table or add the "
            f"role to roles.tsv"
        )
    return role_tiers
```

Chose "intersect + fail closed with a named diagnostic" (the stronger of the two options the
context pack offered) over silent-drop: a tiers table for a role outside the roster is always a
models.toml authoring mistake in this repo (there is no legitimate reason for it), so surfacing it
loudly is strictly safer than quietly excluding it from emission.

**Test**: `tests/test_harness.py::test_generate_dies_on_tier_table_for_role_outside_roster`
(new, after the new SEC-A01/PKG-N01 test) — unit-level, via `self._import("generate")`: (1) a
`role_tiers` dict containing a `"ghost-role"` key not present in a 2-entry synthetic `roles` list
raises `ValueError` naming `ghost-role`; (2) a `role_tiers` dict that IS a subset of the roster
passes through `_roster_filtered_role_tiers` unchanged (`assertEqual`).

## Local validations (this machine, real run, post-repair)

| Check | Result |
|---|---|
| `python3 -m unittest discover -s tests -v` | **152/152 OK** in 93.9s (P2-implementation's 150 + 2 new: `test_orchestrator_doctrine_branches_on_route_decide_reason_taxonomy`, `test_generate_dies_on_tier_table_for_role_outside_roster`; 0 failures, 0 errors, no test removed/weakened) |
| `./build.sh --check` | `CHECK_PASS: generated and validated profile go-zen` |
| `./build.sh` | `CHECK_PASS: generated and validated profile go-zen` / `Generated tracked artifacts for go-zen.` — doctrine propagated verbatim to `Global/opencode/agents/orchestrator.md`, `Global/claude-code/agents/orchestrator.md`, `Global/codex/agents/orchestrator.toml` (spot-checked: `### Tiered dispatch` present at L289/L153/L146 respectively; the 11-way reason-code grep and the off-lane-condition grep both hit once per file; the retired hardcoded model→tier strings hit zero times in all three) |
| `python3 -m py_compile ai/scripts/*.py ai/scripts/routing_core/*.py tests/*.py` | clean, no output (`PY_COMPILE_OK`) |
| `./ai/scripts/verify.sh` | **VERIFY_PASS** — 152/152 tests in 94.4s, drift clean (`Global/` tracked tree == fresh generate) |
| `git diff --check` (incl. untracked via `git add -N .`) | clean, no whitespace errors, exit 0 |

## Files changed in this repair pass (R1)

- `Global/_canonical/agents/orchestrator.md` — doctrine rewrite (SEC-A01 + PKG-N01), lines ~140-207.
- `ai/scripts/generate.py` — `_roster_filtered_role_tiers` (new, L298-315) + two call sites
  (L321, L497) (PKG-N02).
- `tests/test_harness.py` — 2 new tests, no existing test modified/weakened/deleted (no test in the
  suite pinned the old doctrine prose, so none needed updating for SEC-A01/PKG-N01; PKG-N02 had no
  prior direct coverage of `_roster_filtered_role_tiers` since the function is new).
- `Global/opencode/agents/orchestrator.md`, `Global/claude-code/agents/orchestrator.md`,
  `Global/codex/agents/orchestrator.toml`, `Global/claude-code/hooks/coord_policy.py`,
  `Global/opencode/managed-files.txt`, and the 15 `Global/opencode/agents/<role>@<tier>.md`
  variant files — regenerated by `./build.sh` (drift-check-tracked output, not hand-edited; content
  unchanged for the variant files themselves versus the pre-repair P2-implementation state, only
  `orchestrator.*` changed).

Not touched (read-only per repair scope): `ai/scripts/routing_core/**`, `ai/scripts/set_agents_app.py`,
`ai/catalogs/routes.v1.toml`, `roles.tsv`, `tests/test_routing.py`.

Not committed — this evidence file and the diff are handed to the independent delta-review; the
repair agent does not approve its own work.
