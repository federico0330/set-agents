# Juez bloquea: §11 miente y falta --provider-remove

<!-- notas:auto -->
- fecha: 2026-08-21 · actor: orchestrator
- alcance: [[features/035-panel-honesto-consola-y-tips|035-panel-honesto-consola-y-tips]] · [[features/035-panel-honesto-consola-y-tips/PKG-C|PKG-C]]

## Contexto

adversarial-judge 37b21687 JUDGE_FAIL. JUDGE-035-001 COMO-FUNCIONA.md:438-447 sigue listando A/B como pendientes y afirma que record-review saltea security-auditor (falso post PKG-A, AC-C.4). JUDGE-035-002 AC-B.2.4 lista --provider-remove y MANIFEST no lo tiene. late-review rechaza paquetes accepted. INTEGRATION no va a PACKAGE_REPAIR. El CLI pide raise against integration or block.

## Decisión

No BLOCKED todavia. Integrator reabre la composicion: reescribe §11 para apuntar a 035 A/B/C como entregados, y agrega caso aislado --provider-remove. Sin CLI reopen. Sin bump JSON. PKG-B queda en 10/10; el follow-up se registra en PKG-C.

## Consecuencias

Segundo spawn integrator + recapture del caso nuevo. Re-juez. Si el juez vuelve a FAIL, ahi si BLOCKED.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
