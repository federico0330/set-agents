# Extender fundación C2 a dependencias integradas

<!-- notas:auto -->
- fecha: 2026-09-10 · actor: orchestrator
- alcance: [[features/049-identidad-honesta-modelos|049-identidad-honesta-modelos]] · [[features/049-identidad-honesta-modelos/PKG-C2|PKG-C2]]

## Contexto

El panel verificó que el candidato llama contratos de routing_core/service.py y provider_registry.py ausentes de la fundación congelada.

## Decisión

La reparación aislada puede versionar en una nueva FOUNDATION_REF las versiones actuales de ai/scripts/routing_core/service.py y ai/scripts/provider_registry.py como preexistentes sin receipt; no se atribuyen a 049 ni se transportan como delta C2.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
