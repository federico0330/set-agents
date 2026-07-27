# AC-09/AC-10 literal deviations accepted: minimal pi target + pnpm-store pin

<!-- notas:auto -->
- fecha: 2026-07-27 · actor: orchestrator
- alcance: [[features/004-adaptive-dispatch|004-adaptive-dispatch]] · [[features/004-adaptive-dispatch/P3-pi-lane|P3-pi-lane]]

## Contexto

P3-R1 PKG-N03/N04 (info): install.py unchanged (no generated pi tree; validate_pi_target + --no-extensions instead) and the 'managed dir' is realized as pnpm's content-addressed store via pnpm dlx --package @pkg@0.81.1.

## Decisión

Accepted per the context-pack recommended architecture + ADR-0007 Decisions 3/4: the CLI-subprocess spawner passes the canonical role prompt via --append-system-prompt (per-role artifact IS the canonical prompt, identity), no delegation tool (proven live), exact version pinned via pnpm --package, one-line rollback. The AC intent (per-role artifact equivalence, verify surface, no delegation, pinned+rollbackable install) is met; the literal wording is superseded by the pre-approved architecture.

## Consecuencias

install.py stays untouched; P3 adds no generated pi agent tree. If a managed pi dir is ever needed, it is additive later.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
