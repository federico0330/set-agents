# Redirect de _effective_runtime es silencioso, sin reason_code

<!-- notas:auto -->
- fecha: 2026-08-01 · actor: orchestrator
- alcance: [[features/015-anthropic-dispatch-parity|015-anthropic-dispatch-parity]]

## Contexto

Hallazgo del checkpoint temprano de security-auditor sobre P1-anthropic-dispatch-parity (AC-01/AC-02), antes de cablear AC-03/AC-04.

## Decisión

No es una vulnerabilidad, pero _effective_runtime (service.py) redirige de un lane a otro sin dejar reason_code ni exclusion. El ADR-0019 (AC-08) debe registrar que el rastro de auditoría debería mostrar que un redirect ocurrió, no solo el RouteDecision.runtime posterior.

## Consecuencias

Deuda registrada para AC-08 (ADR-0019); no bloquea el resto del paquete.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
