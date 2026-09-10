# Waiver del techo de reparación PKG-C2 a 315

<!-- notas:auto -->
- fecha: 2026-09-10 · actor: orchestrator
- alcance: [[features/049-identidad-honesta-modelos|049-identidad-honesta-modelos]] · [[features/049-identidad-honesta-modelos/PKG-C2|PKG-C2]]

## Contexto

Tras el único reintento de repair-agent, REPAIRED_C2_REF=726017d7 midió 315 líneas contra NEW_FOUNDATION_REF=3878fb0d; el techo congelado era 100 y el gate repair-ceiling bloqueó conforme a ADR-0023/gentle-ai (un intento, luego escalación humana).

## Decisión

El usuario autorizó explícitamente el waiver del techo a 315 para este ciclo. No se abre un segundo repair. Se reabre el bloqueo, se registra repair-ceiling pass con evidencia del waiver, y se continúa delta review → testing → runtime QA → accept PKG-C2 → PKG-D2 sobre el delta ya producido.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
