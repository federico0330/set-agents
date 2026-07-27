# T-300 spike: P3-pi-lane is FEASIBLE (all four YES)

<!-- notas:auto -->
- fecha: 2026-07-27 · actor: orchestrator
- alcance: [[features/004-adaptive-dispatch|004-adaptive-dispatch]]

## Contexto

P3-pi-lane gated by spike T-300 (AC-09g): probeable pinned install, auth-status without side effects, SDK per-session effort/model, catalog<->Pi model-ID mapping. Evidence: docs/specs/004-adaptive-dispatch/evidence/P3-spike-T300.md. Probed installed Pi 0.81.1 read-only (CLI --help/--list-models --offline, SDK typings dist/core/sdk.d.ts, examples/sdk, docs/providers.md, ~/.pi/agent config).

## Decisión

FEASIBLE, no HUMAN_DECISION_REQUIRED on feasibility. createAgentSession({model,thinkingLevel}) is typed + exampled (per-session model AND effort); CLI --model provider/id[:thinking] --print --mode json is a subprocess per-spawn path mirroring opencode/codex spawning; Pi OAuth subscriptions ChatGPT-Plus(Codex)->openai and Claude-Pro/Max->anthropic map 1:1 to catalog providers openai-codex/anthropic; auth.json key-set + --list-models are non-mutating auth probes. Recommend building set_agents_spawn over the CLI-subprocess path first.

## Consecuencias

P3 can proceed. Two caveats: (1) installed 0.81.1 != plan's 0.82.x -> T-301 must pin an EXACT version, not the wrapper's release-age soft-pin. (2) Pi auth.json is EMPTY -> P3 builds/tests hermetically with PI_SIMULATION_ONLY true; the flip (T-305) + live QA + live model-id verification require the USER to pi /login into ChatGPT Plus and/or Claude Pro/Max (subscriptions already held).
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
