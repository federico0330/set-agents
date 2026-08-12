# El refresh de models.toml [catalog] opencode_zen/opencode_go (F-02 de la review de P1) se asigna a P2

<!-- notas:auto -->
- fecha: 2026-08-10 · actor: orchestrator
- alcance: [[features/019-harness-evolution|019-harness-evolution]] · [[features/019-harness-evolution/P2-billing-aware-ordering|P2-billing-aware-ordering]]

## Contexto

F-02 (medio) de la review independiente de P1: las listas opencode_zen/opencode_go de models.toml fueron medidas el 2026-07-30 y _probe_pairs intersecta contra ese techo, asi que discovered_providers='auto' no puede routear modelos que hoy existen y no estan en la lista (ling-3.0-tiny-free, longcat-2.0-free y 2 ids de opencode-go). El implementer de P1 no pudo tocarlo: models.toml es read_only_path de P1 y el ownership del state file manda sobre el texto del context pack. El refresh quedo sin dueno.

## Decisión

El refresh se asigna a P2, que ya es el paquete de la superficie de inventario vivo (AC-15 --route-doctor reporta exactamente esos listados y AC-16 reescribe el panel). Se registra como excepcion de ownership sobre models.toml para P2. La medicion a usar es la del 2026-08-10 que ya esta en la spec, re-verificada en vivo por el implementer de P2 antes de escribir.

## Consecuencias

P2 pasa a tocar models.toml, que no estaba en sus owned_paths originales. La direccion del cambio es fail-closed: la interseccion sigue siendo el techo auditado, solo se pone al dia con lo medido.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
