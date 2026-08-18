# Independencia de review en Cursor: mismo modelo, contexto limpio, degradacion registrada

<!-- notas:auto -->
- fecha: 2026-08-18 · actor: orchestrator
- alcance: [[features/033-menos-espera-menos-cuota|033-menos-espera-menos-cuota]]

## Contexto

En Cursor todos los roles heredan el modelo del selector (docs/notas/decisiones/2026-08-18 cursor-entra-como-runtime-anfitrion-nunca-como-lane-de-ruteo.md). El pedido de arranque prohibe --route-decide y *_spawn.py --dispatch-* porque rutearian a otra suscripcion. La independencia del revisor queda apoyada solo en el contexto limpio del subagente.

## Decisión

Delegar solo con subagentes nativos de Cursor (implementer, package-reviewer, finding-verifier, etc.). Registrar la degradacion same-model/clean-context en record-subreview --evidence y finalize-review-panel --evidence de cada paquete. Nunca --route-decide ni dispatch.

## Consecuencias

Correlated blind spots entre escritor y revisor sobreviven. El costo queda legible en el record del paquete, no escondido.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
