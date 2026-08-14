# Bitácora — 023-senales-de-consumo

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-14T02:10:06+00:00

[2026-08-13T15:39:35+00:00] B1-registro-que-no-miente · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que el harness registre de verdad cuanto gasta cada agente, que hoy no lo hace.
Ingeniería: AC-01..03. Medido antes de implementar: 80 dispatches, 1 con numeros, 54 absent, 25 NULL. El plan decia que opencode y claude-code MIENTEN con ok+NULL; es falso, ponen absent, que es honesto. El defecto real: --usage existe (set_agents_app.py:3641) y la doctrina canonica no lo menciona NUNCA (grep da cero). El propio orquestador cerro ~20 runs esta sesion sin pasarlo.

[2026-08-13T17:18:29+00:00] B2-el-reporte-dice-de-donde-sale · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que el gasto que el harness ya captura llegue completo, y que el reporte no cuente la misma plata dos veces.
Ingeniería: AC-04a (nuevo, derivado de una medicion de B1), AC-04, AC-05. claude_code_spawn.py:602-605 y opencode_spawn.py:318-321 ya adjuntan --usage con formas que _usage_row descarta como invalid; hay que cablearlas a routing_core/usage.py. Y cost-report.py lee los stores propios de los CLIs, que son OTRA medicion del mismo gasto que dispatches: dos secciones que nunca se suman.

[2026-08-13T18:31:05+00:00] B3-ventana-y-rollup · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que el gasto se agregue por ventana y que la base no crezca sin limite, sin perder nada que alguien pueda necesitar.
Ingeniería: AC-06/07, clase migration. Medido: schema_version=7, dispatches 82 filas sin retencion, events 200 con retencion ya implementada (indices events_retention y events_route_retention, DELETE en store.py:946, compactacion que comparte la transaccion del escritor en :682). Hay 0 filas con replacement_of_run_id, asi que ese caso se valida con fixture y se declara asi.

[2026-08-13T19:15:46+00:00] B3-ventana-y-rollup · implementer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Retomar el trabajo que quedo cortado, en otro proveedor, sin perder nada.
Ingeniería: Relanzada de run1_0f2ddb58 que murio por session limit sin dejar codigo. Ahora codex/openai-codex/gpt-5.6-terra. OJO para el review posterior: el writer pasa a ser codex, asi que el reviewer NO puede ser codex.

[2026-08-13T19:47:55+00:00] B3-ventana-y-rollup · package-reviewer · started · modelo anthropic/opus · effort medium
Cliente: Un revisor de otro proveedor confirma que el cambio de base no perdio nada y que la limpieza no borra lo que hace falta.
Ingeniería: Writer fue codex/openai-codex/gpt-5.6-terra (run1_af1780fa, relanzado tras el limite de sesion de anthropic). Reviewer claude-code/anthropic/opus, dec1_97e06bb0, independence_verified=true: proveedor distinto, que es lo que exige la regla dura de service.py:353. El orquestador ya migro la base real del usuario (7->8, 84 filas, backup doble) y corrio el gate: 1098 OK, VERIFY_PASS.

[2026-08-13T20:47:18+00:00] B3-ventana-y-rollup · repair-agent · started · modelo anthropic/opus · effort medium
Cliente: Cerrar dos agujeros por los que el harness podia borrar registros que despues iba a necesitar.
Ingeniería: B3-F01 critical: close_exhausted no escribe rollup y la guarda EXISTS(rollup con esta clave) deja que un agregado ajeno 'pruebe' la fila, que se borra. B3-F02 critical: la guarda ordena run_id DESC y recent_writers ASC, asi que con terminal_at empatado borra la fila que el reviewer consulta primero. B3-F03 high: la QUINTA guarda hueca. F04/F05/F06 medium y low.

[2026-08-14T02:10:06+00:00] B3-ventana-y-rollup · delta-reviewer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Un tercer revisor confirma que los dos agujeros por los que se perdian registros quedaron cerrados.
Ingeniería: Reparador claude-code/anthropic/opus (run1_26d316ee). Delta reviewer en codex, proveedor distinto. El orquestador ya verifico los seis en el codigo y ademas encontro y cerro un hueco propio: B3-F02 estaba arreglado sin test que lo protegiera.
