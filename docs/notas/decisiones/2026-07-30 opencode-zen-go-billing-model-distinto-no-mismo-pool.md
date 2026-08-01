# OpenCode Go es suscripción mensual, OpenCode Zen es pago por uso (API key) — no comparten pool y no son el mismo tipo de proveedor

<!-- notas:auto -->
- fecha: 2026-07-30 · actor: orchestrator
- alcance: [[features/008-dynamic-selection|008-dynamic-selection]]

## Contexto

El spec-challenger de P2-discovered-inventory encontró que opencode-zen y opencode-go exponen 11 modelos byte-idénticos (misma family, distinta api.url) y que el repo tiene señales contradictorias sobre su cuota: COMO-CAMBIAR-MODELO.md sugiere ventanas de 5hs independientes por lane, pero models_config.py:48 mapea ambos a la misma clave de suscripción 'zen'. Se preguntó al usuario, dueño real de las dos suscripciones.

## Decisión

El usuario aclaró: OpenCode Go es una suscripción mensual (costo fijo ya pagado, cupo propio) y OpenCode Zen es pago por uso vía API key (costo marginal por token, sin cupo fijo que se agote de la misma forma). No comparten pool. Además esto no es solo una cuestión de independencia de cupo: son dos categorías de proveedor distintas -- exactamente el eje 'suscripción con cupo vs. medido por uso' que ya se diseñó para el modelo de dos capas de 008-P3 (capa 1: cualquier suscripción con cupo disponible gana sin comparar; capa 2: fallback medido solo si ninguna suscripción tiene cupo, techo diario en USD). OpenCode Go entra como candidato a capa 1; OpenCode Zen entra como candidato a capa 2, y debe ponderarse menos (usarse como último recurso) precisamente porque tiene costo marginal real, a diferencia de Go.

## Consecuencias

P2-discovered-inventory necesita un campo curado nuevo (no sondeado, igual que family/roles/tools/tier -- ver hallazgo F-05 del challenger) que distinga suscripción-con-cupo vs. medido-por-uso, para que P3 pueda leerlo sin re-derivar la distinción. El tracking de agotamiento per-provider de 011 sigue siendo correcto para Go (tiene cupo real que agotar); para Zen 'agotamiento' no aplica en el mismo sentido -- lo que aplica es el techo diario en USD de la capa 2 de P3. Esto se pasa como contexto al product-analyst para la revisión de P2 pendiente por los 19 hallazgos del challenger.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
