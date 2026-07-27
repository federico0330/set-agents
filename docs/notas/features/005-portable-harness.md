# 005-portable-harness

<!-- notas:auto -->
## Estado

- fase: `PACKAGE_ACCEPTED` · modo: feature · revisión 71
- spec: `docs/specs/005-portable-harness/spec.md` (hash `e821373ff2e8`)

## Paquetes

- [[features/005-portable-harness/P1-portable-core|P1-portable-core]] — accepted · Make the 004 adaptive router reachable and correctly scoped from any project on any machi…

## Approach y decisiones

- [2026-07-27] debugger: debugging-loop: timeout 90 on the guest test is reproducible. Debugger owns only the affected implementation/test/docs paths and must prove root cause before editing; no test weak…
- [2026-07-27] debugger: debugging-loop hard stop: direct AC-09 guest test reproduced timeout 124 twice; verify.sh likewise did not terminate in the nested guest test. No root cause was proven, so no code…
- [2026-07-27] debugger: Expanded debugging scope after explicit user authorization. This is the 12th and final P1 instantiation budget: debugger may instrument subprocess execution with bounded diagnosti…
- [2026-07-27] delta-reviewer: Reusing the prior independent gate instance without creating a new package spawn (the physical P1 spawn budget is exhausted). Read-only delta review: inspect only the guest verify…
- [2026-07-27] debugger: Expanded diagnosis proved a nested full 181-test suite, not a deadlock. Minimal repair: verify.sh detects SET_AGENTS_GUEST_VERIFY and runs only the portable smoke assertions alrea…
- [2026-07-27] delta-reviewer: Independent focused delta review PASS: direct guest AC-09 in 22.189s, explicit cwd lifecycle including failure close, absolute APP_CLI/read-only Pi guards, full verify behavior, a…
- decisión: [[decisiones/2026-07-27 global-absolute-path-leak|Pre-existing absolute-path leak in tracked Global/ templates (out of P1 scope, tracked)]]
- decisión: [[decisiones/2026-07-27 p1-pi-project-cwd-propagation|Pi lifecycle propagates project context by explicit cwd]]

## Qué falta

- → `INTEGRATION` — all packages accepted

## Presupuestos

- spawns: 12 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/005-portable-harness/bitacora.md`

_Actualizado: 2026-07-27T17:58:36+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
