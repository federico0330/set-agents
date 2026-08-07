# Bloque de fin de turno pasa a formato informativo (ADR-0033)

<!-- notas:auto -->
- fecha: 2026-08-07 · actor: claude-code

## Contexto

El usuario reporto que el bloque Estado/Hice/Sigue/Necesito-de-vos no se entendia: no re-explicaba de que trata el feature/paquete y comprimia todo en etiquetas telegraficas.

## Decisión

Nueva plantilla 'Etiquetas con contexto' (En que estamos / Paquete / Hice / Conviene ahora / Necesito de vos), tono informativo/divulgativo nivel estudiante de ingenieria informatica, max ~8 lineas. ADR-0033; ADR-0011 conserva intacto el sentinel 'Necesito de vos' y la regla de fin de turno. tests/test_harness.py ahora aserta las etiquetas nuevas y cubre tambien el lane pi (brecha cerrada).

## Consecuencias

Global/_canonical/agents/orchestrator.md y Global/_shared/AGENTS.pi.md editados; ./build.sh --install --yes aplicado a los 4 runtimes.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
