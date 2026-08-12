# F-02 (refresh de models.toml [catalog]) vuelve a P1: un hallazgo se repara en el paquete que lo levanto

<!-- notas:auto -->
- fecha: 2026-08-10 · actor: orchestrator
- alcance: [[features/019-harness-evolution|019-harness-evolution]] · [[features/019-harness-evolution/P1-provider-auto-adoption|P1-provider-auto-adoption]]

## Contexto

Habia reasignado F-02 a P2 por ownership (models.toml era read_only_path de P1). El propio harness rechazo la aceptacion de P1 con 'medium findings need closure or explicit acceptance': un hallazgo medio abierto bloquea el paquete que lo registro, y no existe comando para marcarlo 'accepted' sin repararlo. La reasignacion cruzada era la forma equivocada del movimiento -- lo correcto es ampliar el ownership del paquete que tiene el hallazgo, no mudar el hallazgo a otro paquete.

## Decisión

Se aprueba una excepcion de ownership sobre models.toml para P1 y F-02 se repara ahi: refresh de [catalog].opencode_zen y opencode_go con la medicion en vivo del 2026-08-10. La excepcion registrada en P2 queda superseded por esta y no debe usarse.

## Consecuencias

P1 toca models.toml, que no estaba en sus owned_paths originales. La direccion del cambio es fail-closed: la interseccion de _configured_models sigue siendo el techo auditado, solo se pone al dia con lo medido. P2 ya no hereda esta tarea.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
