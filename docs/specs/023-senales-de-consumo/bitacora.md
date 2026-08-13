# Bitácora — 023-senales-de-consumo

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-13T18:23:47+00:00

[2026-08-13T15:39:35+00:00] B1-registro-que-no-miente · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que el harness registre de verdad cuanto gasta cada agente, que hoy no lo hace.
Ingeniería: AC-01..03. Medido antes de implementar: 80 dispatches, 1 con numeros, 54 absent, 25 NULL. El plan decia que opencode y claude-code MIENTEN con ok+NULL; es falso, ponen absent, que es honesto. El defecto real: --usage existe (set_agents_app.py:3641) y la doctrina canonica no lo menciona NUNCA (grep da cero). El propio orquestador cerro ~20 runs esta sesion sin pasarlo.

[2026-08-13T17:18:29+00:00] B2-el-reporte-dice-de-donde-sale · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que el gasto que el harness ya captura llegue completo, y que el reporte no cuente la misma plata dos veces.
Ingeniería: AC-04a (nuevo, derivado de una medicion de B1), AC-04, AC-05. claude_code_spawn.py:602-605 y opencode_spawn.py:318-321 ya adjuntan --usage con formas que _usage_row descarta como invalid; hay que cablearlas a routing_core/usage.py. Y cost-report.py lee los stores propios de los CLIs, que son OTRA medicion del mismo gasto que dispatches: dos secciones que nunca se suman.
