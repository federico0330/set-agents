# El approve del catalogo de herramientas no entra al canal del agente

<!-- notas:auto -->
- fecha: 2026-08-11 · actor: orchestrator
- alcance: [[features/019-harness-evolution|019-harness-evolution]] · [[features/019-harness-evolution/P5-tools-discovery|P5-tools-discovery]]

## Contexto

AC-33 pide extender coord_policy._tools_channel_allowed a las dos flags nuevas (--tools-propose y --tools-approve). La decision de producto ya tomada por Federico en el pedido original (seccion 0.4) es: el catalogo se abre bajo demanda con propose -> aprobacion humana -> approve -> install, siempre preguntando antes de instalar, con sudo siempre manual. ADR-0037 (resolve antes de preguntar, fuente 1: el pedido original) aplica: esto no se re-pregunta.

## Decisión

--tools-propose SI entra al canal permitido del agente; --tools-approve NO. El approve ES la aprobacion humana: si el agente puede correrlo por su cuenta, el flujo propose -> humano -> approve es teatro y AC-30/AC-31 pierden su razon de ser. El approve lo corre el humano, o el orquestador despues de una respuesta explicita del humano, por su propio canal. El implementer puede argumentar lo contrario en ADR-0038 solo con un mecanismo que preserve la aprobacion humana real; no por conveniencia.

## Consecuencias

Queda escrito en el context pack de P5 y tiene que quedar argumentado y testeado en ADR-0038. El test adversario correspondiente: allowed() rechaza un argv con --tools-approve.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
