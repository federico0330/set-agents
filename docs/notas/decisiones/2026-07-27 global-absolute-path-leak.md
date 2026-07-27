# Pre-existing absolute-path leak in tracked Global/ templates (out of P1 scope, tracked)

<!-- notas:auto -->
- fecha: 2026-07-27 · actor: orchestrator
- alcance: [[features/005-portable-harness|005-portable-harness]]

## Contexto

AC-01 assumed 'zero absolute paths in Global/**'. The architect verified this is false today: Global/_canonical/opencode-agents/package-gate-runner.md and its compiled copy Global/opencode/agents/package-gate-runner.md hardcode /home/federico/iey/iey-ai/... permission entries, including client-project module names. Both files are git-tracked and pushed to origin (github.com/federico0330/SET-AGENTS, visibility PRIVATE).

## Decisión

Do NOT fix inside P1: package-gate-runner.md is outside P1's owned_paths and fixing it would be an opportunistic refactor. AC-01's assertion is implemented as the architect's R1/R2/R3 ratchet instead of the literal (currently false) 'zero absolute paths' claim: R1 placeholder present wherever set_agents_app.py is referenced, R2 zero occurrences of the building machine's HARNESS_HOME, R3 a non-increasing ratchet over pre-existing absolute paths.

## Consecuencias

The leak stays until a dedicated package addresses it; the ratchet guarantees it cannot grow. Repo is private so this is not a public disclosure, but the template ships client-project paths to every machine that installs the harness, and those permission entries are dead (they reference a project that is not the installing user's). Flagged to the user.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
