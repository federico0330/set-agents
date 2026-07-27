# P2-opencode-lane — implementation evidence

Baseline: `71abca1e87d057f33ef9278d954e01ae46d6a94d` (P1-dispatch-core accepted). Contract 1.1.0, tasks
T-201..T-204.

## T-201 — per-role tier tables (`models.toml` + `models_config.py`)

`models.toml`: for the five declared roles (`security-auditor`, `package-reviewer`, `delta-reviewer`,
`implementer`, `debugger`) added `[roles.<role>.tiers.<tier>]` for `tier ∈ {fast, balanced, frontier}`, each
declaring exactly one field — a lane-aware `opencode = { "go-zen"=…, "zen"=…, "local"=… }` map. All three
lanes carry the same model per tier ON PURPOSE: `fast → openai/gpt-5.6-luna`, `balanced →
openai/gpt-5.6-sol`, `frontier → openai/gpt-5.6-terra` — the only namespace that ever projects from
OpenCode to the catalog is `openai/<M>` against the `openai-codex` provider (see T-202), so any lane
variance would only ever produce a coherence-gate failure, never a real choice. `debugger` already had a
flat `[roles.debugger]` override (`codex_effort`, `opencode`); the tier table is additive on top of it, and
the other four roles get a `[roles.<role>]` table containing only `tiers` (no other override — base
resolution still falls through to their area). Base agents unaffected: `resolve_role`'s field-by-field merge
still only reads `AREA_FIELDS`.

`ai/scripts/models_config.py`:
- `TIER_FIELD = "tiers"` (L28-31, next to `AREA_FIELDS`): the one role-override key that is not an area
  field.
- `resolve_role` (L224-...): the unknown-field check over `[roles.<role>]` now explicitly skips
  `TIER_FIELD` (only for the override table, never for `[areas.*]` — areas can never declare tiers), so a
  tiered role's base resolution is untouched by the presence of a `tiers` sub-table.
- `load_role_tiers(config, profile) -> {role: {tier: opencode_model}}` (new function, after `load_roles`):
  roles without a `[roles.<role>.tiers]` table are absent from the result (base-only, one emitted agent — no
  code change needed for this half of AC-06, it falls out of the data). A role WITH the table must cover the
  full closed vocabulary (fast/balanced/frontier, no partial fan-out — missing or unknown tier ⇒
  `ModelsError`). Each `[roles.<role>.tiers.<tier>]` must declare exactly `opencode` (extra/renamed keys
  rejected); its lane map may cover any subset of `LANES` plus an optional `"default"` fallback — coverage
  is enforced per the ACTIVE profile at resolution time (missing lane + no default ⇒ `ModelsError`), not by
  requiring all three lanes literally present in the file (used the `"default"` escape hatch design named in
  the context pack, though in practice every table here lists all three lanes explicitly). Every resolved
  model is validated EXACTLY like any other role's `opencode_model`: `OPENCODE_MODEL_RE` + `subscription_of`
  against `[subscriptions]` — never a codex/claude catalog-list membership check (tiers have no claude/codex
  twin).
- `emit()`: extended to round-trip the `tiers` sub-table (`load(emit(x)) == x` invariant, T-201's own test
  `test_models_config_emit_roundtrip` and a manual round-trip check on the real `models.toml` both pass) —
  not asked for explicitly in the context pack, but without it `./setup-models.sh`'s wizard would silently
  DROP every tier table on its next deterministic rewrite, which is a real footgun for a "single source of
  truth" file. Noted here as a deliberate scope addition, not a deviation from any acceptance criterion.

## T-202 — variant emission + coherence gate + validate/prune (`generate.py`, `install.py`)

`ai/scripts/generate.py`:
- `generate()` (L298-...): now also loads `config`/`role_tiers` via `models_config.load_config` +
  `load_role_tiers`, and derives `variant_names` (sorted `"<role>@<tier>"` strings). After the base
  per-role loop (base agent bodies cached in a `bodies` dict so the variant loop reuses them without
  re-reading disk), a new loop emits `out/opencode/agents/<role>@<tier>.md` for every `(role, tier)` in
  `role_tiers` — same `desc`/`mode`/`temperature`/`oc_steps`/`oc_hidden`/`oc_permissions`/body as the base
  agent, the ONLY differing line is `model:`. Claude Code and Codex loops are untouched — no variant is ever
  written there. `out.rmtree`+recreate still happens once, before either loop.
- `oc_permissions(capability, roles, role=None, yolo=False, variant_names=())`: new `variant_names` param.
  In the `coord-ro` branch (the orchestrator's own frontmatter), each variant name gets an explicit
  `"<role>@<tier>": allow` line in the `task:` allowlist — variants are neither a roster row (the existing
  `roles`-filtered loop) nor a canonical `opencode-agents` file (the existing glob loop), so without this
  third source `"*": deny` would block every tiered spawn. Also added, in the same branch, the routing CLI
  as a second sanctioned mutation channel for `bash:` (see T-203) — two new `allow` lines for
  `set_agents_app.py --route*` / `--routing*`, next to the pre-existing `feature-state.py *` exception.
- `check_variant_catalog_coherence(role_tiers, routes_path)` (new, pure/offline): `_opencode_projected_route`
  projects `openai/<M>` → `("openai-codex", M)` and anything else (the `opencode/*` zen aggregator
  included) → no projection. For every declared `(role, tier, model)` it filters `routes.v1.toml`'s
  `[[routes]]` rows to `provider == projected[0] and model == projected[1] and tier == tier and role in
  row.roles`, and requires EXACTLY one match — zero or ambiguous both `die()` (→ `RuntimeError` surfaced by
  `generate.main()` as `CHECK_FAILED`, exit 2). No subprocess, no probe — a static lookup over the full
  parsed TOML.
- `validate(out, roles=None, role_tiers=None, routes_path=None, models_path=None)`: extended. The
  opencode/claude-code/codex role-set-equality check now adds `variant_expected` to the OPENCODE side only
  (claude-code/codex keep their original `expected` set — I initially wrote a bug here, `expected |
  opencode_only` applied to ALL three harnesses instead of opencode-only, caught immediately by
  `CHECK_FAILED: claude-code: generated role set mismatch` on the first local run and fixed before any other
  gate). The orchestrator-task-allow loop gained a second loop asserting every `variant_expected` name has
  an `allow` line. `check_variant_catalog_coherence` runs at the end of `validate()`, so it fires on every
  `generate()` call and every `build.sh --check`.
- `main()`: added `--routes` (optional, defaults to `ai/catalogs/routes.v1.toml`) purely as a test seam,
  mirroring the existing `--roles`/`--models` seams — never used by `build.sh`, only by the negative
  coherence test (which instead overrides `--models`, since that's the surface that actually varies; the
  seam is there for completeness and any future test that needs a synthetic catalog).

`ai/scripts/install.py`: **not modified**, verified instead. `write_indexes()` globs `out/<harness>`
recursively AFTER the variant files are written, so `managed-files.txt` picks up the 15 new
`<role>@<tier>.md` paths automatically; `install.py`'s `managed_files()` reads that same manifest, and its
generic prune-by-manifest-diff (`previous_targets()` minus `new_targets`) already covers any managed file
regardless of naming pattern. Proven by `test_install_prunes_tier_variant_removed_from_models_toml` (new,
T-204): dropping `[roles.debugger.tiers]` between two installs prunes exactly `debugger@{fast,balanced,
frontier}.md` and leaves the base `debugger.md` and the other four roles' variants untouched.

## T-203 — orchestrator doctrine + permission surface

`Global/_canonical/agents/orchestrator.md`: inserted a "Tiered dispatch — decide→spawn protocol" subsection
right after step 6 of the Delegation flow (which now also names the five tiered roles and points here).
Covers, in order: (1) run `--route-decide` before delegating a tiered role; (2) match by the DECIDED MODEL,
never the tier label alone — spawn `<role>@<tier>` only when `data.provider == "openai-codex"` AND
`data.model` is exactly `gpt-5.6-luna|sol|terra`; (3) model-mismatch (e.g. an anthropic fallback like
`haiku`) ⇒ `--route-terminal <run_id> failure` (abandoned) + degraded mode with the BASE agent; (4) router
unavailable ⇒ degraded mode with the BASE agent, no retry loop; (5) reviewers route to a variant only with a
verified `review_of_run_id` (from state or `--routing-recent-writers`) — otherwise spawn the base reviewer;
(6) worker death closes the run the same way as model-mismatch; (7) the opening narration's `Ingeniería:`
line must name the decision's `route_id`/`run_id`; (8) the routing CLI is documented as an explicitly
MUTATING-capable coord exception (decide authorizes, dispatched/terminal close runs the coord owns), narrated
like any spawn.

Permission surface (two symmetric edits):
- `ai/scripts/coord_policy.py::SAFE`: added
  `r"python3 ai/scripts/set_agents_app\.py --rout(e|ing)-\S+"` — matches `--route-decide`,
  `--route-dispatched`, `--route-terminal`, `--route-explain`, `--routing-report`, `--routing-open-runs`,
  `--routing-recent-writers`; `FORBIDDEN_SYNTAX`/`FORBIDDEN_OPTIONS` still block shell composition and
  dangerous flags around it exactly like the `feature-state.py` exception.
- `ai/scripts/generate.py::oc_permissions` coord-ro branch: two new `bash:` allow lines,
  `"python3 ai/scripts/set_agents_app.py --route*": allow` and `"...--routing*": allow` (OpenCode's glob
  matcher needs both prefixes since `--routing-report` does not literally start with `--route`).

**Deviation from the context pack's literal wording, recorded here for the review panel**: the pack's T-202
bullet says to add each `<role>@<tier>` name "to the `task:` allowlist OpenCode … y a la lista `Agent(...)`
de claude-code". I added the OpenCode `task:` lines but deliberately did NOT add variant names to
`claude_tools`'s `Agent(...)` list for the claude-code orchestrator. Rationale: `claude_tools` builds
`Agent(...)` by filtering the real resolved `roles` rows (from `roles.tsv`) against `ORCHESTRATOR_TASK_ALLOW`
— there is no `roles.tsv` entry named e.g. `implementer@fast`, so nothing in that call site could ever
reference a variant without emitting a Claude Code agent file for it, which would directly contradict the
context pack's own "Invariantes que NO se tocan" section ("Claude/Codex sin variantes") and AC-06's own text
("Given the five roles, When generated for Claude Code/Codex … the base agents are still emitted
unchanged"). I read the two statements in the same document as being in tension and resolved it in favor of
the explicit invariant + the acceptance criterion (the authoritative text), not the summary bullet. Verified:
`test_tier_variants_emitted_identical_to_base_and_orchestrator_can_delegate_them` asserts no claude-code or
codex artifact name ever contains `@`.

## T-204 — tests (`tests/test_harness.py`)

Five new tests, all in `HarnessTests` (kept in `test_harness.py`, not `test_routing.py`, which is P1's
read-only domain suite):

1. `test_tier_variants_emitted_identical_to_base_and_orchestrator_can_delegate_them` — for the 5×3 variants:
   body/permissions/steps identical to base after stripping the `model:` line; the three tier models per
   role are pairwise distinct; orchestrator's `task:` allowlist contains every `"<role>@<tier>": allow`;
   Claude Code/Codex never emit an `@`-named artifact; a role with no tier table (`orchestrator`) has zero
   `orchestrator@*.md` files.
2. `test_install_prunes_tier_variant_removed_from_models_toml` — mirrors
   `test_install_prunes_orphaned_managed_files_but_keeps_user_files`: real install with the repo's tier
   surface, then a second install from a models.toml copy with `[roles.debugger.tiers]` deleted; asserts
   `PRUNED_ORPHANS=` fires, the three `debugger@*` files are gone, the base `debugger.md` and the other four
   roles' variants survive.
3. `test_route_lane_lifecycle_hermetic_and_worker_death_closure` — AC-08: a local
   `_routing_probe_stubs` fixture (mirrors `test_routing.py`'s `_probe_stubs`, kept local since it's a
   different test module) plus `SET_AGENTS_ROUTING_TEST_ROOT` drives
   decide(writer)→dispatched→terminal(success) through the real `set_agents_app.py` CLI subprocess, all
   exit 0; `--routing-report --json` shows `retained_events >= 1`; a second decide is closed straight from
   `authorized` via `--route-terminal … failure` (the worker-death doctrine) and lands in state
   `abandoned`; `--routing-open-runs` confirms nothing is left open.
4. `test_variant_coherence_gate_fails_build_on_unprojectable_tier_model` — two sub-cases via
   `_repo_models_variant` (existing helper, deterministic-emitter copy of the real `models.toml`): (a) a
   tier model reusing the go-zen area's own `openai/gpt-5.6-fast` alias (which does not exist in the
   catalog) → `CHECK_FAILED`, exit 2, stderr names `variant coherence` and `debugger@fast`; (b) a tier model
   in the `opencode/*` zen-aggregator namespace (structurally valid, never catalog-reachable from OpenCode)
   → same failure shape, stderr names `implementer@balanced`.
5. Extended (not new) `test_coordinator_policy`: five new ALLOWED cases (`--route-decide`,
   `--route-dispatched`, `--route-terminal`, `--routing-report`, `--routing-recent-writers`) and four new
   DENIED cases (shell composition around `--route-decide`, a spoofed `other/set_agents_app.py` path, and
   an unrelated `set_agents_app.py --mcp-add` subcommand that must stay outside the allowlist). No existing
   case removed or weakened.

## Local validations (this machine, real run)

| Check | Result |
|---|---|
| `python3 -m unittest discover -s tests -v` | **150/150 OK** (test_harness.py + test_routing.py; P1's 29 unaffected, +5 new + 2 extended in `test_coordinator_policy`) |
| `./build.sh --check` | `CHECK_PASS: generated and validated profile go-zen` |
| `./build.sh` | regenerated `Global/`; 15 new tracked files under `Global/opencode/agents/*@{fast,balanced,frontier}.md` (5 roles), `Global/opencode/managed-files.txt` updated, `orchestrator.md`/`.toml` updated in all three harnesses, `Global/claude-code/hooks/coord_policy.py` synced |
| `python3 -m py_compile ai/scripts/*.py ai/scripts/routing_core/*.py tests/*.py` | clean, no output |
| `./ai/scripts/verify.sh` | **VERIFY_PASS** (150 tests, drift clean — `Global/` == fresh generate) |
| `git diff --check` (incl. untracked, via `git add -N`) | clean, no whitespace errors |
| Coherence gate fails on a bad tier model (temporary, via `--models` override — real `models.toml` never touched) | confirmed twice: `openai/gpt-5.6-fast` (0 catalog matches) and `opencode/kimi-k2.7-code` (wrong namespace, 0 matches); both `CHECK_FAILED`, exit 2 |
| Live `--route-decide` for `implementer` (real `models.toml`/`routes.v1.toml`, hermetic probe stubs, test routing root) | `provider=openai-codex`, `model=gpt-5.6-luna`, `tier=fast`, `execution_enabled=true` → orchestrator doctrine maps this to `implementer@fast`, matching the emitted variant's `model: openai/gpt-5.6-luna` exactly |

## Notes for the review panel

- The `oc_permissions` bug I introduced and self-caught (see T-202: `expected | opencode_only` leaking into
  claude-code/codex's expected set) is worth a deliberate look — I fixed it before any gate ran, but the
  panel should confirm the harness-set-equality invariant per harness is exactly right, since a silent
  widening there would mask a real generation defect in either direction.
- The claude-code `Agent(...)` deviation (T-203 section above) is a judgment call resolving a tension
  inside the context pack itself; the panel should confirm the resolution (favor the explicit invariant +
  AC-06's literal text over the T-202 summary bullet) is the correct read.
- `models_config.emit()`'s new tier-table serialization was not explicitly requested; it closes a real gap
  (the wizard would otherwise silently destroy the tier tables on its next `--set`/`--add-model` write) but
  is additional surface the panel may want to scrutinize for the round-trip invariant specifically.
- The lane-uniform tier tables (same model for go-zen/zen/local) are a data choice, not a code constraint —
  `load_role_tiers` supports per-lane variance and a `"default"` fallback; I chose uniformity because any
  lane-specific choice within these five roles' tiers would currently be `opencode/*`-namespaced (this
  repo's zen/local lanes lean on the zen aggregator) and would therefore always fail the coherence gate. If
  a future catalog exposes non-openai-codex, opencode-reachable tiered rows, the lane maps can diverge
  without any code change.
