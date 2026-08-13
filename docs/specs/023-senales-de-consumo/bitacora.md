# Bitácora — 023-senales-de-consumo

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-13T17:12:55+00:00

[2026-08-13T15:39:35+00:00] B1-registro-que-no-miente · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que el harness registre de verdad cuanto gasta cada agente, que hoy no lo hace.
Ingeniería: AC-01..03. Medido antes de implementar: 80 dispatches, 1 con numeros, 54 absent, 25 NULL. El plan decia que opencode y claude-code MIENTEN con ok+NULL; es falso, ponen absent, que es honesto. El defecto real: --usage existe (set_agents_app.py:3641) y la doctrina canonica no lo menciona NUNCA (grep da cero). El propio orquestador cerro ~20 runs esta sesion sin pasarlo.
