# Los cinco hallazgos del architect sobre P0 no pudieron entrar al expediente del paquete

<!-- notas:auto -->
- fecha: 2026-07-28 · actor: orchestrator
- alcance: [[features/007-quota-visibility|007-quota-visibility]] · [[features/007-quota-visibility/P0-role-affinity|P0-role-affinity]]

## Contexto

Consecuencia directa del defecto start-review-panel-silent-noop. Finalizar el panel movio el paquete a PACKAGE_REPAIR, y desde ahi record-review tambien esta prohibido. No existe ningun comando sancionado que acepte los hallazgos de un segundo revisor independiente que llego despues de finalizar el panel. Se registran aca porque son reales y verificados en vivo; NO se edita el archivo de estado a mano.

## Decisión

F-07 (high): nada exige que los dos grupos de roles sean disjuntos. catalog.py:387 solo verifica la union, asi que un rol duplicado en ambos grupos empata curated_priority=10 contra si mismo y el desempate lo decide un hash de route_id. Probado en vivo: implementer duplicado selecciona openai-codex en vez de anthropic, sin error. F-08 (medium): la particion construida es exactamente una particion por duty, el eje que models.toml [areas.<duty>] ya posee segun ADR-0003, asi que P0 crea una segunda fuente de verdad hecha a mano sin ADR que lo justifique. F-09 (medium): brainstormer es generativo y no evaluativo pero cayo en el grupo audit por ser read-only; read-only no equivale a evaluativo. F-10 (medium): la inversion de prioridad del grupo audit es inerte para los 6 roles de review verificada, porque REVIEW_PROVIDER_CONFLICT decide el proveedor antes de que curated_priority se lea. F-11 (low): sin failover post-dispatch, agotar cuota de Anthropic a mitad de spawn es fallo terminal, y ahora la clase de trabajo expuesta es la cara.

## Consecuencias

El architect tambien refuto de forma independiente la sospecha de contaminacion de telemetria (exclusion_count solo lo incrementa _event(rejected); medido 8 exclusiones con exclusion_count=0), coincidiendo con el package-reviewer. Deuda preexistente detectada al pasar: docs/specs/003-trusted-routing-pi-runtime/design.md:455 afirma lo contrario sobre exclusiones desde la reparacion FD-008, y docs/adr/0009-finding-verification.md existe en disco pero falta en docs/adr/README.md. Tercer defecto del arnes de la misma familia: el ciclo de review no admite un hallazgo tardio por ningun canal.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
