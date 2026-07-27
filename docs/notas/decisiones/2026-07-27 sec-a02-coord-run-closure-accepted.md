# SEC-A02 accepted: coord may terminal/abandon any routing run

<!-- notas:auto -->
- fecha: 2026-07-27 · actor: orchestrator
- alcance: [[features/004-adaptive-dispatch|004-adaptive-dispatch]] · [[features/004-adaptive-dispatch/P2-opencode-lane|P2-opencode-lane]]

## Contexto

Security-auditor SEC-A02 (P2-R1): the coord's new mutating routing grant lets it close/abandon any open run; close_run has no caller-ownership check and multiple features can be mid-flight.

## Decisión

Ratified as intended blast radius, not repaired: same-UID/in-process adversary is OUT of scope per feature 003 R3 threat amendment; worker-death doctrine REQUIRES the coord to close runs it owns; every close is narrated (orchestrator doctrine step 8).

## Consecuencias

Coord routing mutation stays a trusted, narrated channel. If multi-writer isolation is ever needed, add caller-ownership to close_run (P3+ scope).
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
