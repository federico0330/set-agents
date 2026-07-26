# Alcance 004: tier barato sin opencode/* y P3 condicionado a spike

<!-- notas:auto -->
- fecha: 2026-07-26 · actor: orchestrator
- alcance: [[features/004-adaptive-dispatch|004-adaptive-dispatch]]

## Contexto

Challenge B5: sin proveedores opencode/* el ahorro del tier barato es menor. Challenge B7: P3 (carril Pi) apoya en 3 incognitas no verificadas del SDK/auth de Pi.

## Decisión

Usuario (2026-07-26): (1) el tier fast de 004 usa solo proveedores auditados (gpt-5.4-mini/gpt-5.6-luna/haiku); agregar opencode/* (Zen/Go) con par auditado es feature futura. (2) P3 gated por spike T-300 con evidencia binaria (auth observable, effort por sesion, mapeo de modelos); cualquier NO => HUMAN_DECISION_REQUIRED.

## Consecuencias

Ruteo funcionando antes con menos scope; el ahorro maximo llega con la feature del tercer proveedor; P3 no puede consumir presupuesto sin viabilidad probada.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
