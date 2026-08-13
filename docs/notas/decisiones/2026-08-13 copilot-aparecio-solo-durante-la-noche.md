# Copilot paso de no listable a 26 modelos durante la noche, y el harness lo adopto solo

<!-- notas:auto -->
- fecha: 2026-08-13 · actor: orchestrator
- alcance: [[features/022-disponibilidad-real|022-disponibilidad-real]] · [[features/022-disponibilidad-real/P5-altas-y-bajas-automaticas|P5-altas-y-bajas-automaticas]]

## Contexto

ADR-0034 midio el 2026-08-10 que 'opencode models github-copilot --pure' devolvia 'Provider not found' incluso con --refresh, y la spec de 022 lo declaro como limite aguas arriba que la feature no podia desbloquear. El orquestador lo remidio anoche a las 00:30 y seguia igual: detected_unlistable=true, models_listable=0, verified_cli_id=None.

## Decisión

Se registra el cambio de estado, medido dos veces. A las ~09:40, 'opencode models github-copilot --pure' devuelve 26 modelos (github-copilot/claude-fable-5, claude-haiku-4.5, claude-opus-4.7, ...), y --route-doctor reporta github copilot listed_by_provider=26 verified_cli_id=github-copilot. La verificacion empirica de AC-16 propuso el candidato por el nombre de la credencial, el CLI contesto un listado bien formado, y el id se acepto SIN QUE NADIE TOCARA CODIGO. Es exactamente el comportamiento que AC-16 diseño, ocurriendo por primera vez con un proveedor real.

## Consecuencias

usable_after_ceiling sigue en 0 y detected_unlistable en true, y esta BIEN: github-copilot no es un par auditado en _PAIR_COMMANDS, asi que se descubre pero todavia no se rutea. Es el fail-closed del diseño. Volverlo ruteable es un acto curado y, gracias a P1, hoy es UNA fila en provider_registry.PROVIDERS en vez de seis entradas en lockstep manual -que es literalmente la afirmacion de ADR-0034:124-126 que P1 corrigio por inexacta y que ahora si es cierta. Queda como decision del usuario: si quiere Copilot ruteable, es esa fila mas un par en _PAIR_COMMANDS, con su review.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
