# 033-pkg6-techo-scoped-deja-repair-fuera

<!-- notas:auto -->
- fecha: 2026-08-19 · actor: orchestrator
- alcance: [[features/033-menos-espera-menos-cuota|033-menos-espera-menos-cuota]] · [[features/033-menos-espera-menos-cuota/PKG-6|PKG-6]]

## Contexto

PKG-6 scoped techo 8, usados 8 (implementer x3 por un record-spawn duplicado del follow-up Global, local-gate-runner, gate-runner, package-reviewer, security-auditor, finding-verifier). Panel repair_required. Verifier upheld PKG6-F01 high y F02/F03 medium. Repair+delta piden 2 spawns mas. record-spawn del 9o bloquearia la feature.

## Decisión

No se despacha repair-agent. No se llama record-spawn contra el techo. El paquete queda en PACKAGE_REPAIR con findings upheld y verification grabada, a la espera de decision humana: dos despachos extra para cerrar el ciclo, o parar.

## Consecuencias

Sin esos dos despachos PKG-6 no llega a accepted y la feature 033 no cierra. Tocar MODE_BUDGETS scoped=8 contradice el spec. Saltar delta con F01 high es ilegal (--skip-delta).
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
