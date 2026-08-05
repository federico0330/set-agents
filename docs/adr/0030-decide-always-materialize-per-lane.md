# ADR-0030 — Decide siempre: una decisión de routing por spawn, materializada según el lane

- **Status**: Accepted
- **Date**: 2026-08-04
- **Relates to**: ADR-0018 (model preference / bias_class), ADR-0019 (anthropic dispatch parity),
  ADR-0029 (probe-driven model selection), spec 017.

## Context

The owner's product requirement is that model selection is the orchestrator's live decision, never a
hardcoded table. After 017, the routing brain (`set-agents --route-decide`) already accepts every one
of the 28 roster roles (`set_agents_app.py::cmd_route_decide` filters nothing by role), and
`routes.v1.toml`'s six curated rows list the full roster in their `roles` field. Yet the shipped
doctrine only invoked the router for the six tiered roles, so 22 roles ran exclusively on the curated
`models.toml` area defaults baked into their frontmatter. ADR-0018 named this explicitly as an
**accepted residual risk** ("no reachable real-world effect today … for the same operational
(doctrine-invocation) reason").

Two immutable contracts bound the solution space:

- `tests/test_routing.py:3583` pins the tiered roster to EXACTLY six roles (and zero
  `decision`/`unscoped` tiered), so "add `[roles.<role>.tiers.*]` for everyone" is off the table.
- `tests/test_routing.py:3597` + `_MP_TIERED_SENTENCE_RE` pin the six-name doctrine sentence
  verbatim across the four orchestrator files; the sentence stays untouched.

## Decision

1. **Every spawn gets a decision.** The orchestrator runs `--route-decide` with real
   `role`/`task_class`/`risk` before delegating ANY role, not only the six tiered ones. For roles
   outside writer/verified-review the envelope is `simulate` — still a decision, still recorded.
2. **Materialization is a lane-capability question, not a doctrine table.**
   - `provider == "anthropic"` → Claude-Code lane serves ANY roster role at the decided model
     (`claude_code_spawn.py --model <model>` over the base `<role>.md`; the lane always passed
     `--model` verbatim — no variants involved).
   - `provider == "openai-codex"` + tiered role → the emitted `<role>@<tier>` variant, exactly as
     the existing decide→spawn protocol states (unchanged).
   - `provider == "openai-codex"` + non-tiered role → the BASE agent (curated default), recording
     `MODEL_STATIC_FALLBACK` and the decided provider/model in the spawn record — a visible,
     narrated degrade, never a silent one.
3. **No fabricated enforcement.** `simulate` decisions authorize nothing durable: no
   `--route-dispatched`/`--route-terminal`, never presented as an authorized run.
4. **The curated table is re-labeled as what it is**: the Modelos wizard header calls the per-area
   table "defaults curados (fallback)" and states that live routing covers 28/28 roles.

## Consequences

- ADR-0018's "accepted residual risk" paragraph is superseded IN EFFECT for the doctrine half: the
  seven `decision` roles and the fourteen non-tiered `grunt`/`build` roles now produce observable
  routing decisions on every spawn. ADR-0018's own taxonomy, resolver, config schema, and sort-key
  contract needed zero change — exactly as its closing note predicted.
- The tiered roster stays six; full coverage arrives through lanes that apply `--model` at spawn
  time (claude-code today; pi's spawn CLI shares the property). A future widening of the OpenCode
  variant roster remains possible but is NOT required for coverage.
- Decision `effort` still does not propagate to any child process (Claude Code has no such flag;
  codex effort remains the static `codex_effort` column). Explicitly deferred as a future extension.
- Cost: one extra `--route-decide` per non-tiered spawn (envelope, no durable run). Cached probe;
  no new subprocesses beyond the CLI call itself.

## Verification

`tests/test_decide_always.py`: doctrine markers (`MODEL_STATIC_FALLBACK`, "ADR-0030") present in the
canonical orchestrator and its three generated copies; a local copy of the tiered-sentence regex
still matches all four files; `--route-decide` with a non-tiered role returns a well-formed decision;
the wizard panel carries the fallback re-label. The immutable suites prove the frozen contracts moved
nowhere.
