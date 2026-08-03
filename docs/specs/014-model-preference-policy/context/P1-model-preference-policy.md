# Context pack — P1-model-preference-policy (feature 014, contract 3.2.0)

## Objective (AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-08, AC-09)
Add one configurable, credential-aware, role-class-scoped tie-break weight into
`RoutingService.route()`'s existing candidate sort key — never a second decision-maker, never a
hardcoded role→provider table (the reverted `007-P0` shape). Deliver: the closed 4-value taxonomy
(`decision`/`grunt`/`build`/`unscoped`) and its resolver; a sibling per-harness config file with a
dedicated atomic TOML writer and CLI; the sort-key insertion; `RouteDecision` observability fields;
and the design-decision ADR. On the primary `opencode` lane this now has REAL, live effect for six
roles (`delta-reviewer`, `finding-verifier`, `package-reviewer`, `security-auditor`, `implementer`,
`debugger`) via `015-anthropic-dispatch-parity`'s redirect — this must be proven, not just claimed.

## Files (why)
- `ai/scripts/routing_core/service.py` — the ONE integration point. `role_class = self._role_class(facts.role)`
  at line 170; `_role_class` at 299-304 (`"writer"`=code-rw, `"review"`=review-ro+{audit,judge}, else `"other"`);
  the sort call at line 246, currently `(indep_bool, TIER_ORDER[tier], curated_priority, route_id)` — insert the
  new element at position 3 (between tier and curated_priority): `(indep, tier, bias_rank, curated_priority, route_id)`.
  Never touch the exclusion loop (197-244) or `_effective_runtime` (133-158) — those are the redirect this
  contract only ever consumes.
- `ai/scripts/routing_core/domain.py` — `class RouteDecision` at 165, `to_dict()` at 177 (dataclasses.asdict,
  picks up new fields free). Add `bias_class: str | None = None` and `preference_configured: bool = False` at
  the end (all 14 `RouteDecision(` call sites in service.py are positional and already stop before/omit these).
- `ai/scripts/set_agents_app.py` — `_role_class_of` (230-233, pre-existing verbatim duplicate of
  `service.py::_role_class`, do not touch/dedupe, out of scope); `cmd_route_decide` (385+), the JSON envelope
  write at line 440 (`data["role_class"] = role_class`) — add `data["bias_class"]`/`data["preference_configured"]`
  alongside it, never colliding with the existing `role_class` key (disjoint vocab: `{decision,grunt,build,unscoped}`
  vs `{writer,review,other}`). `STATE_DIR` at line 39 (`~/.local/state/set-agentes`) — put the new sibling file
  here, e.g. `STATE_DIR / "model-preference.toml"`, with its OWN writer — never route through `write_app_config`
  (704-716, flat `key=value` serializer, silently corrupts nested tables) or `app_config()` (693-697, silently
  swallows parse failures as `{}` — the new loader must `die()` instead). New CLI flags follow existing idioms:
  `--route-terminal` (nargs=2, line 2529) for `--model-preference-role-override ROLE CLASS`; `--feature-id`
  (action="append", line 2566) for repeatable ordered `--provider NAME`.
- `roles.tsv` (read-only, 29 lines incl. header, 28 roles) — the `capability`/`duty` columns AC-01's predicates
  are keyed on. `models.toml` (read-only) — `[roles.<role>.tiers.*]` at lines 184-265, exactly six tiered roles:
  `debugger`, `delta-reviewer`, `finding-verifier`, `implementer`, `package-reviewer`, `security-auditor`.
  `[areas.implement]` at 80-84 — never touched (Non-goals), only cited by the doctrine-precedence test.
- `Global/_canonical/agents/orchestrator.md:157-158` + its 3 generated copies (`Global/claude-code/agents/
  orchestrator.md`, `Global/opencode/agents/orchestrator.md`, `Global/codex/agents/orchestrator.toml`) — read-only,
  the doctrine-consistency AC-01 test reads the "tiered roles" sentence from all four; never edit any of them.
- `docs/adr/` — new ADR required by AC-09. `0018` is the currently-unclaimed hole (`0017`, `0019` both Accepted
  and materialized) — RE-CHECK `docs/adr/README.md` live at ADR-write time, do not assume `0018` still open.
- `tests/test_routing.py` (4243 lines, `class RoutingTests`) — extend here, hermetic pattern already used:
  `RoutingService._for_tests` (service.py:106) / `routing._compose_for_tests` (routing.py:31) with injected
  inventory, never live-probed; new sibling-file tests must substitute a `tempfile.TemporaryDirectory()` for
  `STATE_DIR`, never touch the real machine's file.

## Invariants (must hold, tested)
- Sort key position: new element strictly between tier (pos 2) and curated_priority (today's pos 3) — AC-04 pt.5
  tripwire pins the exact 5-tuple shape so any future shape change (this contract's or `008-P3`'s) fails loudly.
- Absent config (no file, or role `unscoped`) → byte-identical `RouteDecision` output to today (AC-04c, AC-06).
- Never a new credential probe — reorders only what the existing exclusion loop already leaves standing (AC-03).
- Never edits `routes.v1.toml` `roles`/`tools`/`tier` membership, never a role-by-role provider table (AC-04.3, AC-05).
- Sibling config write is atomic (temp file + `os.replace`/`rename`), never `write_text` directly (round-1 F-02).
- Malformed provider/role/class token in the sibling file, or on the CLI, fails closed with a per-token `die()`
  message — never silently swallowed (round-1 F-07, round-3 R3-F-04).
- `bias_class` is `None` only for the two refusals strictly before `service.py:170` (lines 164, 169); populated
  for every refusal after it (176, 182, 191) — including both `FACTS_INCOMPLETE`-coded ones, which must differ.
- Live-effect tests for `grunt`'s 4 and `build`'s 2 tiered roles MUST evaluate `anthropic` against
  `('claude-code','anthropic')` (via `_effective_runtime`/`_PROVIDER_RUNTIME_REDIRECTS`), never
  `('opencode','anthropic')` directly and never an injected missing-pair fixture pretending the redirect is absent
  — see spec `## Verificación`, "fixture-that-would-fool-it", re-baselined round 4.

## Local validation
- `python3 -m unittest tests.test_routing -v`
- `./ai/scripts/verify.sh` (runs `build.sh --check`, full suite, `py_compile`, `git diff --check`)
- `python3 -m py_compile ai/scripts/routing_core/*.py ai/scripts/set_agents_app.py`
- Manual CLI smoke: `set-agents --model-preference-set build --provider anthropic --provider openai-codex`,
  `set-agents --model-preference-show`, then inspect `~/.local/state/set-agentes/model-preference.toml`.

## Out of scope — do NOT touch
- `docs/specs/008-dynamic-selection/spec.md`, its P1 doctrine/generated text, or P3's sketch.
- `models_config.py::resolve_role`/`[areas.<duty>]` resolution, `codex_orchestrator()`.
- `Global/_canonical/**` or any of its 3 generated copies (read-only, cited above).
- Any new `routes.v1.toml` row, any new `_PAIR_COMMANDS` pair (standalone Kimi Code onboarding — external dep).
- `011-quota-failover`'s `provider_exhausted`/`provider_exhaustions` (only the existing conditional read at
  `service.py:214` may exist; never call it unconditionally from new code).
- `_role_class_of` (`set_agents_app.py:230-233`) — pre-existing duplication, named not fixed, do not dedupe.
