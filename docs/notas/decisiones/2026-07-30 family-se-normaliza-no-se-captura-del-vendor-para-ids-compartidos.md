# Para modelos compartidos entre lanes de OpenCode, family se normaliza (colisiona), no se copia del vendor

<!-- notas:auto -->
- fecha: 2026-07-30 · actor: orchestrator
- alcance: [[features/008-dynamic-selection|008-dynamic-selection]]

## Contexto

Ronda 2 del spec-challenger sobre P2-discovered-inventory encontro N-01 (blocker) y N-02 (high): la AC-17 nueva pedia que family fuera 'el valor vendor-reportado' capturado por el probe. Medido en vivo: 9 de 11 modelos compartidos entre opencode-zen/opencode-go tienen la misma family vendor-reportada, pero 2 (minimax-m2.7, minimax-m3) tienen family DISTINTA por lane (zen='minimax', go='minimax-m2.7'/'minimax-m3'). Con el mandato literal de la AC, esos 2 modelos -- que son el MISMO modelo bajo dos providers -- pasarian REVIEW_FAMILY_CONFLICT (service.py:149) y REVIEW_PROVIDER_CONFLICT (service.py:155) como independientes entre si, fabricando una independencia de revisor falsa. Ademas, capturar family via probe exige un segundo comando con --verbose, que rompe el parser existente (RoutingError PROVIDER_UNAUTHENTICATED en output verbose) y contradice AC-20/AC-21 ('no probe mechanism change').

## Decisión

family sigue siendo un campo curado a mano (igual que roles/tools/tier), nunca sondeado por el probe -- no hace falta --verbose ni tocar el parser. Pero para todo model id que aparezca bajo mas de un provider (detectable por el propio roster comparado en AC-11/AC-18, sin sondear nada nuevo), el curador tiene que setear la MISMA family en las dos filas -- normalizada para que colisione, no copiada literal del vendor. Esto preserva la garantia real de REVIEW_FAMILY_CONFLICT (mismo modelo nunca se revisa a si mismo) en vez de documentar fielmente una taxonomia de vendor que la rompe. Se verifica con un test que, para cada id compartido entre providers en el catalogo, exige family identica en ambas filas curadas -- no con nada que dependa del probe.

## Consecuencias

product-analyst reescribe AC-17 con este mecanismo (curado + regla de colision para ids compartidos, sin --verbose). El campo subscription/metered de AC-18 tambien se resuelve como mapa curado a nivel de provider (mismo patron que el mapa credencial->id-CLI de AC-12/13), no como columna nueva en las filas de routes.v1.toml -- evita reabrir el esquema cerrado de fila (catalog.py:359-360,366) que hoy rechaza cualquier clave extra, y es coherente con el non-goal de P2 de no agregar filas curadas nuevas para los modelos de Zen/Go.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
