# P1R context pack — trusted routing-v2

## Objective and acceptance

Replace the experimental router with the one cohesive trusted routing-v2 slice: harness-observed facts, an internally
built immutable catalog, content-bound routes, persisted review identity, private SQLite lifecycle, and simulated-only
operator visibility. It must preserve the 28-role roster, schema-1 compatibility, OpenCode/Claude Code/Codex behavior,
Sol/medium parent invariant, and Pi opt-in; Pi has no P1R execution adapter.

Covered acceptance: **AC-01, AC-01a, AC-02, AC-02a, AC-03, AC-03a, AC-04, AC-05, AC-06, AC-07, AC-07a, AC-08, AC-09**
in `../acceptance.md`. P2/P3 remain paused until independent P1R acceptance.

## Approved work items and order

1. **T-001 — trusted request/fact/catalog boundary:** mandatory fresh `ObservedTaskFacts`; internally build immutable
   `CatalogSnapshot` from catalog/roster/resolved models/fresh probes/metrics; prove fact downgrade matrix and four
   runtime inventories.
2. **T-002 — static route and independent review identity:** SHA-256 `rt1_<16hex>` binding, collision invalidation,
   CSPRNG `run1_` IDs, separate authorization, and `ImplementationIdentity` from a terminal persisted writer only.
3. **T-003 — private SQLite lifecycle:** fixed POSIX-local root, `BEGIN IMMEDIATE`, one writer/fallback, closure before
   dispatch, partial/terminal crash safety, permissions, symlink/corruption/platform fail-closed behavior.
4. **T-004 — non-mutating operations and retention:** simulated-only explain, schema-2 CLI envelopes/exits, no-follow
   legacy warnings, privacy allowlists, 90-day/10,000 retention, exact retained p50/p90 and lifetime rollups.
5. **T-005 — evidence and handoff:** consolidate all above tests and gates; repair the two named hermetic harness tests
   without weakening them; prepare the independent review handoff.

## Owned implementation surface

- `ai/catalogs/routes.v1.toml` — new audited static route source; no caller catalog is authoritative.
- `ai/scripts/routing_core/**` — domain/service/catalog/store/gates adapters, inward dependencies only.
- `ai/scripts/routing.py` — thin compatibility facade/composition and stable `RoutingService.route(request, facts, review_of_run_id=None)`.
- `ai/scripts/models_config.py`, `ai/scripts/setup_models.py`, `models.toml` — only compatibility-preserving schema,
  resolved-model, enabled-provider, and Pi Sol/medium changes required by P1R.
- `tests/test_routing.py` — focused production-shaped routing-v2, concurrency, crash, privacy, and CLI coverage.
- `tests/test_harness.py` — only `HarnessTests.test_install_sh_dry_run_plans_missing_tools` (PATH-isolated from host
  aliases) and `HarnessTests.test_models_config_emit_roundtrip` (schema-1 in-memory compatibility plus deterministic
  schema-2 emission; never schema-1 byte-equality).
- `docs/specs/003-trusted-routing-pi-runtime/context/P1R-trusted-routing.md` and
  `docs/specs/003-trusted-routing-pi-runtime/evidence/P1R-*` — current package instructions and gate evidence only.

## Shared and read-only context

- **Shared:** `ai/scripts/set_agents_app.py` — add only thin routing CLI integration; preserve all unrelated commands.
- **Shared dirty-baseline entries:** `docs/adr/README.md`, `docs/specs/README.md` — existing user changes are tolerated
  by ownership gating but are not P1R implementation work; do not edit or revert them.
- **Read-only:** `roles.tsv` (canonical duty/capability); `tests/fixtures/models.toml`; `ai/scripts/verify.sh`;
  `PROYECTO/ai/scripts/{feature-state.py,check-owned-paths.py}`; `../{spec,acceptance,design,plan,tasks}.md`;
  `../../../adr/0005-trusted-routing-sqlite-lifecycle.md`; 002 context/findings under
  `../../002-adaptive-pi-orchestration/{context/P1-routing-core.md,findings/P1-R1.md}`.
- The repository is deliberately dirty before P1R (`ai/scripts/{models_config.py,set_agents_app.py,setup_models.py,routing.py}`,
  `models.toml`, `tests/test_routing.py`, state/spec/ADR/notes and the two README files). Preserve every unrelated or
  pre-existing user change; never use reset/checkout/revert to obtain a clean tree.

## Non-negotiable rules and checkpoints

- Task intent is untrusted: facts/catalog/auth/route ID/run ID/review identity/state root never come from a caller.
  Missing, stale, conflicting, ambiguous, or replayed required facts disable execution with `FACTS_INCOMPLETE`.
- Static ID tuple is exactly catalog version/provider/model/family/effort/sorted tiers/roles/tools/curated priority;
  runtime is excluded. Any truncation collision invalidates the entire snapshot.
- Review identity comes only from the actual selected/fallback immutable tuple of a terminal-success `code-rw` writer;
  exclude writer family before ranking and prefer another authenticated provider, otherwise fail closed.
- Production storage is only `~/.local/state/set-agentes/routing-v2`, not request/env selected. Require POSIX local
  support, no-follow ancestor/root/DB/WAL/SHM checks, UID/private `0700`/`0600`, SQLite WAL+FULL+FK+busy_timeout=0;
  unsupported/corrupt/unsafe state is `ROUTING_UNAVAILABLE` and is never repaired/retried automatically.
- `mark_dispatched` durably closes fallback before external invocation. Any post-dispatch, partial, consumed,
  terminal, or terminal-persistence-failure state blocks retry/fallback. This is a security checkpoint before T-003
  is considered complete.
- Explain is physically capability-less: no SQLite/file/authorization/dispatch/event/fallback/metric mutation.
  Legacy detection uses only no-follow `lstat` over the six exact names plus rotated regex; never open/read/import it.
- Do not add a gateway, remote DB/service, queue, cache, deployment, generic plugin system, raw telemetry/auth data,
  public routing contract, Pi execution, or changes to roles/existing runtime defaults.

## Exact local validations and package gates

Capture `P1R_BASELINE=$(git rev-parse HEAD)` immediately before implementation (current value at planning:
`66164c2a520aef4fc326b996e515a2240706d976`) and retain it in P1R evidence. The final ownership command is:

```bash
python3 PROYECTO/ai/scripts/check-owned-paths.py --state-file ai/state/features/003-trusted-routing-pi-runtime.json --package-id P1R-trusted-routing --baseline "$P1R_BASELINE"
```

Run and record each command/status (do not replace these with weaker checks):

```bash
python3 -m unittest discover -s tests -p 'test_routing.py' -v
python3 -m unittest -v tests.test_harness.HarnessTests.test_install_sh_dry_run_plans_missing_tools
python3 -m unittest -v tests.test_harness.HarnessTests.test_models_config_emit_roundtrip
python3 ai/scripts/setup_models.py --check
python3 -m py_compile ai/scripts/models_config.py ai/scripts/setup_models.py ai/scripts/routing.py ai/scripts/routing_core/*.py ai/scripts/set_agents_app.py tests/test_routing.py tests/test_harness.py
python3 -m unittest -v tests.test_routing.RoutingTests.test_gate_and_telemetry_negative_cases
./ai/scripts/verify.sh
git diff --check
```

The focused suite must execute every declared `GateSpec` using its immutable absolute `argv`, exact repository `cwd`,
and only allowlisted environment, including Python compile, unit tests, and harness verify; assert reject-by-ID/raw
shell/ambient PATH-cwd attempts. Runtime QA is CLI-only (no MCP/browser): invoke `set_agents_app.py --route-explain`
and `--routing-report` in JSON and human modes; prove one success exit `0`, unsafe/unavailable exit `1`, invalid or
conflicting input exit `2`, one schema-2 JSON document, redacted stderr, and byte-identical/no-created routing-v2
state before/after each simulation.

## Completion, review, and handoff

Done means all T-001–T-005 acceptance probes pass, no prohibited persistence/output exists, concurrent authorization
has at most one writer, every crash boundary blocks unsafe retry, legacy bytes remain untouched, and all commands
above plus ownership pass. Required reviewers are exactly `package-reviewer` and `security-auditor`; both are
read-only and implementation cannot approve itself. Complexity is **high**; use hosted `implementer` on
`openai/gpt-5.6-terra` at medium effort because this combines security-critical trust boundaries, SQLite atomicity,
crash/retry concurrency, and public CLI/persistence behavior. `runtime_surface=true`; focused tests are the
implementer deliverable (no separate `test-writer`).
