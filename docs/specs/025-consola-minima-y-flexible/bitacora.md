# Bitácora — 025-consola-minima-y-flexible

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-15T12:56:16+00:00

[2026-08-14T11:11:13+00:00] D1-superficie-humana · implementer · started · modelo anthropic/sonnet · effort medium
Cliente: Que la aplicacion de terminal muestre solo lo que te sirve, sin caracteres raros ni comandos que no vas a usar.
Ingeniería: AC-01..03. Medido: MENU_ITEMS son 10 items con emoji (set_agents_app.py:3523-3534), y dos de ellos ya llevan DOS espacios en vez de uno porque sus glifos miden distinto -la prueba del problema-. El CLI expone 68 flags. Ocultar es help=argparse.SUPPRESS, nunca borrar: coord_policy las tiene en su allowlist y los spawns las invocan. Y --json debe preservar el formato actual byte por byte porque el …
