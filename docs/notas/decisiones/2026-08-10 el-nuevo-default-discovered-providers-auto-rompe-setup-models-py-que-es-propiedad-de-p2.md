# El nuevo default discovered_providers='auto' rompe setup_models.py, que es propiedad de P2

<!-- notas:auto -->
- fecha: 2026-08-10 · actor: orchestrator
- alcance: [[features/019-harness-evolution|019-harness-evolution]] · [[features/019-harness-evolution/P1-provider-auto-adoption|P1-provider-auto-adoption]]

## Contexto

P1 cambia el default de [routing].discovered_providers de [] a 'auto'. setup_models.py:156 y :364 hacen list(routing.get('discovered_providers', [])), que sobre el string 'auto' produce ['a','u','t','o']. Reproducido en vivo: el panel imprime 'proveedores descubiertos rutables: a, u, t, o'. El implementer de P1 detecto el defecto y revirtio su fix porque setup_models.py es owned_path de P2, no suyo.

## Decisión

No se parchea desde P1 (respeto de ownership). Queda como primer item obligatorio de P2, cuyo AC-16 reescribe esa misma linea del panel y el wizard. La verificacion en vivo del panel entra como gate de P2.

## Consecuencias

Entre la aceptacion de P1 y la de P2 el wizard de modelos muestra una lista de caracteres en vez de proveedores. Ventana corta, mismo turno, sin efecto sobre el ruteo ni sobre models.toml.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
