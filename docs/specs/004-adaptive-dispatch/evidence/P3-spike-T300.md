# T-300 spike — Pi lane feasibility (evidence-first, read-only)

Date: 2026-07-27. Scope: bounded feasibility probe for P3-pi-lane. No installs, no mutation, no Pi login.
Verdict per AC-09g: **FEASIBLE — all four questions YES**, with two non-blocking caveats (version drift,
Pi currently unauthenticated). No `HUMAN_DECISION_REQUIRED` on feasibility grounds.

## Environment probed
- Pi launcher: `~/.local/bin/pi` (lazy wrapper → `@earendil-works/pi-coding-agent` via pnpm, soft version
  pin `PNPM_CONFIG_MINIMUM_RELEASE_AGE=7200`).
- Installed Pi version: **0.81.1** (plan assumed 0.82.x — minor drift, see caveat 1).
- Config root: `~/.pi/agent/` → `auth.json` (0600, currently `{}` empty), `settings.json` (9 extension
  packages incl. `pi-subagents`, `gentle-pi`), `npm/package.json` (pinned extension deps), `extensions/`,
  `skills/`.
- SDK package inspected at the pnpm store: `dist/` (`index.js` main, exports `.` + `./rpc-entry`),
  `examples/sdk/` (13 examples), `docs/{providers,models}.md`, `dist/core/sdk.d.ts` typings.

## Q1 — Pinned Pi install probeable → YES (caveat 1)
- Reproducible install via the wrapper (pnpm + release-age soft-pin) and pinned extension `package.json`.
  Built-in model catalogs ship with Pi and cache offline in `~/.pi/agent/models-store.json`.
- **Caveat 1**: installed 0.81.1 ≠ plan's 0.82.x. P3-T301 ("managed pinned Pi install") must pin an EXACT
  version (the wrapper's release-age is a soft pin, not a lock). Not a blocker.

## Q2 — Auth-status probeable without side effects → YES
- `~/.pi/agent/auth.json` (0600) holds one key per authenticated provider (`openai`, `anthropic`, `google`,
  … per `docs/providers.md`). Reading its key-set is non-mutating — the SAME probe pattern the routing core
  already uses for opencode/claude/codex pairs (catalog.py `_PAIR_COMMANDS`).
- `pi --list-models --offline` reports availability without network; currently returns "No models available.
  Use /login…" (fail-closed correct: empty auth ⇒ no models). Exit 0.
- Programmatic: `ModelRuntime.getAvailable()` returns only models "that have valid API keys" (SDK example
  `02-custom-model.ts`) — a clean programmatic auth-status.

## Q3 — SDK per-session effort + model → YES (definitive)
- `dist/core/sdk.d.ts`: `createAgentSession({ model?: Model, thinkingLevel?: ThinkingLevel, modelRuntime? })`
  → **per-session model AND thinking level**, typed. `thinkingLevel` ∈ off|minimal|low|medium|high|xhigh|max
  (CLI `--thinking`), "clamped to model capabilities", default from settings else 'medium'.
- Example `examples/sdk/02-custom-model.ts`: `getModel("anthropic","claude-opus-4-5")` →
  `createAgentSession({ model, thinkingLevel: "medium", modelRuntime })`. Returns `{ session,
  modelFallbackMessage }` (fallback observability if a saved session's model differs).
- Three independent per-spawn model mechanisms, any usable by `set_agents_spawn` (P3-T303):
  1. **SDK**: `createAgentSession({model, thinkingLevel})` (in-process JS).
  2. **RPC**: `--mode rpc` + `./rpc-entry` export (programmatic protocol).
  3. **CLI subprocess**: `pi --model provider/id[:thinking] --print --mode json <task>` (mirrors how the
     harness already spawns opencode/codex; simplest, no JS host needed).

## Q4 — Model-ID mapping → YES (mapping layer is P3-T305, well-defined)
- Pi uses canonical `provider/id`. Providers reachable by OAuth subscription (`docs/providers.md`
  §Subscriptions): **ChatGPT Plus/Pro (Codex)** → key `openai`, and **Claude Pro/Max** → key `anthropic`.
  These map 1:1 to the catalog's enabled providers `openai-codex` and `anthropic` (routes.v1.toml).
- Model NAMES differ: catalog uses `opus`/`sonnet`/`haiku`/`gpt-5.6-luna|sol|terra`; Pi uses canonical ids
  like `claude-opus-4-5`. The catalog→Pi-id mapping is exactly P3-T305's "model-ID mapping" task — feasible,
  bounded, and offline-verifiable once Pi is authenticated (its catalog populates `models-store.json`).
- API-key providers (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, …) are an alternative auth path (env or
  auth.json), relevant if subscription OAuth is not used.

## Blocking prerequisite for P3 (NOT a feasibility NO) — user action
Pi's `auth.json` is empty: **Pi is not logged into any provider.** To (a) verify live Pi model ids against
the catalog and (b) actually route a spawn through Pi, the user must `pi` → `/login` into ChatGPT Plus
(Codex) and/or Claude Pro/Max (subscriptions already held per project memory). Until then, P3 can be built
and tested ONLY hermetically with `PI_SIMULATION_ONLY` kept true; the flip (T-305) and live QA need auth.

## Recommendation
Proceed to P3-pi-lane. Decompose against reality:
- T-301 pin an EXACT Pi version (not release-age soft-pin); managed install + status/rollback + `--doctor
  --harness pi`.
- T-302 `pi` target in generate/install (fresh-context children, no delegation, depth 0).
- T-303 `set_agents_spawn` over the **CLI subprocess** path first (`pi --model … --print --mode json`) —
  lowest-risk, no in-process JS host; SDK/RPC as an optimization later.
- T-304 extension/spawn guards (002 AC-04 at the new enforcement point); read-only children until green.
- T-305 `(pi, <provider>)` probe pairs + parsers (auth.json key-set + `--list-models`); catalog→Pi model-id
  map; gated `PI_SIMULATION_ONLY` flip; rollout/rollback docs + ADR/architecture updates.
All hermetic/simulated until the user authenticates Pi, then live QA + the flip.
