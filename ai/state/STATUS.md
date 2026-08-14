# Estado del desarrollo

_Generado por `feature-state.py` en cada mutación de estado. No editar a mano._

Actualizado: 2026-08-14T05:09:03+00:00

## Features

| Feature | Modo | Fase | Paquete | Aceptados | Spawns | Reviews | Findings abiertos | Blocker | Próximo paso | Último evento |
|---|---|---|---|---|---|---|---|---|---|---|
| 002-adaptive-pi-orchestration | feature | BLOCKED | P1-routing-core (repair_required) | 0/1 | 12/12 | 2/2 | 5 | HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhausted 12 spawns plus 2 deep-review cycles… | - | 2026-07-24T16:16:04+00:00 block |
| 003-trusted-routing-pi-runtime | feature | DONE | P1R-trusted-routing (accepted) | 1/1 | 16/16 | 3/3 | 0 | - | - | 2026-07-29T17:13:45+00:00 transition |
| 004-adaptive-dispatch | feature | DONE | P3-pi-lane (accepted) | 3/3 | 20/12 | 1/2 | 0 | - | - | 2026-07-27T14:04:38+00:00 transition |
| 005-portable-harness | feature | DONE | P3-tui (accepted) | 3/3 | 20/12 | 1/2 | 0 | - | - | 2026-07-30T16:16:18+00:00 transition |
| 006-execution-graph | feature | PACKAGE_ACCEPTED | P3-graph-view (accepted) | 1/1 | 9/12 | 1/2 | 0 | - | PACKAGE_ACCEPTED | 2026-08-02T14:44:35+00:00 record-spawn |
| 007-quota-visibility | feature | DONE | P3-correct-record (accepted) | 3/3 | 13/12 | 1/2 | 0 | - | - | 2026-07-29T17:10:45+00:00 transition |
| 008-dynamic-selection | feature | DONE | P1-uninterrupted-delegation (accepted) | 1/1 | 6/12 | 1/2 | 0 | - | - | 2026-08-02T14:53:39+00:00 transition |
| 009-self-application | feature | DONE | P3-panel-integrity (accepted) | 3/3 | 13/12 | 1/2 | 0 | - | - | 2026-07-29T17:10:45+00:00 transition |
| 010-spawn-provenance | feature | PACKAGE_ACCEPTED | P1-spawn-provenance (accepted) | 1/1 | 11/12 | 1/2 | 0 | - | PACKAGE_ACCEPTED | 2026-08-02T14:44:35+00:00 record-spawn |
| 011-quota-failover | feature | BLOCKED | P1-quota-failover (package_gates) | 0/1 | 3/12 | 0/2 | 0 | HUMAN_DECISION_REQUIRED: AC-06 exige una suscripción Anthropic controlada y genuinamente agotada junto a un proveedor alterno usable; la precondición no está v… | - | 2026-07-30T17:04:39+00:00 block |
| 012-discovered-inventory | feature | DONE | P1-discovered-inventory (accepted) | 1/1 | 8/12 | 1/2 | 0 | - | - | 2026-08-02T15:00:53+00:00 transition |
| 013-pi-interactive-target | feature | DONE | P1-pi-interactive-target (accepted) | 1/1 | 9/12 | 1/2 | 0 | - | - | 2026-08-02T22:40:39+00:00 transition |
| 014-model-preference-policy | feature | DONE | P1-model-preference-policy (accepted) | 1/1 | 7/12 | 1/2 | 0 | - | - | 2026-08-03T00:38:12+00:00 transition |
| 015-anthropic-dispatch-parity | feature | DONE | P1-anthropic-dispatch-parity (accepted) | 1/1 | 0/12 | 1/2 | 0 | - | - | 2026-08-01T22:46:55+00:00 transition |
| 016-audit-debt-repayment | feature | DONE | P1-harness-debt (accepted) | 2/2 | 10/12 | 1/2 | 1 | - | - | 2026-08-03T00:02:59+00:00 transition |
| 019-harness-evolution | feature | DONE | P5-tools-discovery (accepted) | 5/5 | 14/12 | 1/2 | 0 | - | - | 2026-08-12T02:43:19+00:00 transition |
| 020-honest-dashboard | feature | DONE | P2-anclas-verificables (accepted) | 2/2 | 4/12 | 1/2 | 1 | - | - | 2026-08-12T11:19:21+00:00 transition |
| 021-gates-que-no-mienten-ni-callan | feature | DONE | P2-gates-que-no-callan (accepted) | 2/2 | 6/12 | 2/2 | 0 | - | - | 2026-08-12T21:09:05+00:00 transition |
| 022-disponibilidad-real | feature | DONE | P5-altas-y-bajas-automaticas (accepted) | 5/5 | 16/12 | 1/2 | 0 | - | - | 2026-08-13T13:40:43+00:00 transition |
| 023-senales-de-consumo | scoped | INTEGRATION | B4-estimado-nunca-dato-del-proveedor (accepted) | 4/4 | 8/8 | 1/2 | 0 | - | DONE | 2026-08-14T05:09:03+00:00 transition |
| 024-listo-para-terceros | scoped | PACKAGE_PLANNING | C4-higiene-de-repo-publico (planned) | 0/4 | 0/8 | 0/2 | 0 | - | PACKAGE_IMPLEMENTATION | 2026-08-13T15:19:15+00:00 create-package |
| 025-consola-minima-y-flexible | scoped | PACKAGE_PLANNING | D5-vault-en-todo-spawn (planned) | 0/5 | 0/8 | 0/2 | 0 | - | PACKAGE_IMPLEMENTATION | 2026-08-13T15:20:00+00:00 create-package |
| 026-orquestador-elige-modelo | scoped | DONE | P2-modelo-por-instancia (accepted) | 2/2 | 2/8 | 1/2 | 0 | - | - | 2026-08-13T15:35:37+00:00 transition |

## Quick-fixes recientes

- [2026-08-12T15:24:52+00:00] render_notes emitia trailing whitespace en la linea de un finding sin category ni summary, rompiendo git diff --check y por lo tanto verify.sh. Defecto PREEXISTENTE (ya estaba en notas commiteadas de 007, 009, 012 y 013); recien entro al diff porque se regenero una nota nueva. 83 de 324 findings del repo caen en ese caso. Arreglo: el separador em-dash solo se emite si hay label, con _short aplicado antes del chequeo para cubrir labels de solo whitespace. Test de regresion en test_harness.py:2340-2356 con mordida confirmada. sync-notes regenero 14 notas. Los 5 espejos con md5 identico. — archivos: ai/scripts/feature_state_lib/render_notes.py, tests/test_harness.py — gate: verify.sh -> VERIFY_PASS con 973 OK / 3 skips y EXIT=0; build.sh --check -> GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; git diff --check limpio — resultado: done
- [2026-08-06T13:33:48+00:00] Preserve explicit --project context in set_agents_app.py script mode by aliasing __main__ for lazy routing_cli imports — archivos: ai/scripts/set_agents_app.py, tests/test_routing.py — gate: python3 -m unittest focused router context tests: 2 PASS; py_compile PASS; git diff --check PASS; live route-decide context_ok=true — resultado: done
- [2026-08-03T02:36:03+00:00] P1F-01: cmd_transition's repair_entry pop for PACKAGE_REPAIR was nested under 'if args.package_id:'; since --package-id is optional on transition, a manual transition without it skipped the pop and let a stale repair_entry from a prior cycle auto-escape review inference. Hoisted the pop to always run on to_phase==PACKAGE_REPAIR, resolving the package via package_by_id (falls back to current_package_id) inside try/except StateError. — archivos: ai/scripts/feature-state.py, PROYECTO/ai/scripts/feature-state.py, tests/test_harness.py — gate: git diff --check: clean — resultado: done
- [2026-07-30T01:22:42+00:00] P2-vault-mandatory (accepted): exclude_notes_from_git/_notes_currently_excluded chequeaban (project/'.git').is_dir(), falso para un git worktree enlazado (.git es archivo ahi) -- docs/notas quedaba trackeado por git en vez de excluido, contradiciendo DEC-5. Fix: resolver via 'git rev-parse --show-toplevel/--git-common-dir' anclado a que el proyecto SEA el top-level (no solo estar dentro de un repo), con env purgado de GIT_DIR/GIT_WORK_TREE/GIT_COMMON_DIR/GIT_INDEX_FILE, timeout y manejo de git ausente. Bono: vault_doctor_report ahora distingue dangling de un symlink cuyo target fue borrado (antes reportaba healthy). Encontrado migrando ~/iey de verdad; revisado por un segundo agente (package-reviewer) que encontro 7 hallazgos adicionales sobre el primer fix, todos reparados y re-verificados con pass. — archivos: ai/scripts/set_agents_app.py, tests/test_harness.py — gate: 331 tests verdes, verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, git diff --check limpio, package-reviewer pass (2da pasada) — resultado: done
- [2026-07-30T01:22:33+00:00] P2-vault-mandatory (accepted): write_vault_registry_entry resolvía el vault_path a través del symlink recién creado, guardando el directorio real del repo en vez del symlink del lado del vault. vault_doctor_report reportaba health=drift para siempre en todo proyecto hybrid recién linkeado. Fix: normalizar resolviendo solo el padre (parent.resolve()/name), nunca el componente final. Encontrado migrando ~/iey de verdad. — archivos: ai/scripts/set_agents_app.py, tests/test_harness.py — gate: 331 tests verdes, verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, git diff --check limpio, package-reviewer pass — resultado: done

## Bitácora (últimos 15)

[2026-08-14T04:11:49+00:00] B4-estimado-nunca-dato-del-proveedor · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que cuando el harness te diga cuanto gastaste, te diga tambien de donde saco el numero y cuanto de eso midio de verdad.
Ingeniería: AC-08/09/10, ultimo paquete de 023. usage_rollups (schema 9) ya trae suma Y conteo de reportados por metrica, que es la cobertura. Ningun proveedor expone cuota restante: sin presupuesto declarado se muestra 'consumido en la ventana', no 'restante'. Guard test al estilo del candado de DDL que nacio de la regresion de B3.

[2026-08-14T02:10:06+00:00] B3-ventana-y-rollup · delta-reviewer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Un tercer revisor confirma que los dos agujeros por los que se perdian registros quedaron cerrados.
Ingeniería: Reparador claude-code/anthropic/opus (run1_26d316ee). Delta reviewer en codex, proveedor distinto. El orquestador ya verifico los seis en el codigo y ademas encontro y cerro un hueco propio: B3-F02 estaba arreglado sin test que lo protegiera.

[2026-08-13T20:47:18+00:00] B3-ventana-y-rollup · repair-agent · started · modelo anthropic/opus · effort medium
Cliente: Cerrar dos agujeros por los que el harness podia borrar registros que despues iba a necesitar.
Ingeniería: B3-F01 critical: close_exhausted no escribe rollup y la guarda EXISTS(rollup con esta clave) deja que un agregado ajeno 'pruebe' la fila, que se borra. B3-F02 critical: la guarda ordena run_id DESC y recent_writers ASC, asi que con terminal_at empatado borra la fila que el reviewer consulta primero. B3-F03 high: la QUINTA guarda hueca. F04/F05/F06 medium y low.

[2026-08-13T19:47:55+00:00] B3-ventana-y-rollup · package-reviewer · started · modelo anthropic/opus · effort medium
Cliente: Un revisor de otro proveedor confirma que el cambio de base no perdio nada y que la limpieza no borra lo que hace falta.
Ingeniería: Writer fue codex/openai-codex/gpt-5.6-terra (run1_af1780fa, relanzado tras el limite de sesion de anthropic). Reviewer claude-code/anthropic/opus, dec1_97e06bb0, independence_verified=true: proveedor distinto, que es lo que exige la regla dura de service.py:353. El orquestador ya migro la base real del usuario (7->8, 84 filas, backup doble) y corrio el gate: 1098 OK, VERIFY_PASS.

[2026-08-13T19:15:46+00:00] B3-ventana-y-rollup · implementer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Retomar el trabajo que quedo cortado, en otro proveedor, sin perder nada.
Ingeniería: Relanzada de run1_0f2ddb58 que murio por session limit sin dejar codigo. Ahora codex/openai-codex/gpt-5.6-terra. OJO para el review posterior: el writer pasa a ser codex, asi que el reviewer NO puede ser codex.

[2026-08-13T18:31:05+00:00] B3-ventana-y-rollup · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que el gasto se agregue por ventana y que la base no crezca sin limite, sin perder nada que alguien pueda necesitar.
Ingeniería: AC-06/07, clase migration. Medido: schema_version=7, dispatches 82 filas sin retencion, events 200 con retencion ya implementada (indices events_retention y events_route_retention, DELETE en store.py:946, compactacion que comparte la transaccion del escritor en :682). Hay 0 filas con replacement_of_run_id, asi que ese caso se valida con fixture y se declara asi.

[2026-08-13T17:18:29+00:00] B2-el-reporte-dice-de-donde-sale · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que el gasto que el harness ya captura llegue completo, y que el reporte no cuente la misma plata dos veces.
Ingeniería: AC-04a (nuevo, derivado de una medicion de B1), AC-04, AC-05. claude_code_spawn.py:602-605 y opencode_spawn.py:318-321 ya adjuntan --usage con formas que _usage_row descarta como invalid; hay que cablearlas a routing_core/usage.py. Y cost-report.py lee los stores propios de los CLIs, que son OTRA medicion del mismo gasto que dispatches: dos secciones que nunca se suman.

[2026-08-13T15:39:35+00:00] B1-registro-que-no-miente · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que el harness registre de verdad cuanto gasta cada agente, que hoy no lo hace.
Ingeniería: AC-01..03. Medido antes de implementar: 80 dispatches, 1 con numeros, 54 absent, 25 NULL. El plan decia que opencode y claude-code MIENTEN con ok+NULL; es falso, ponen absent, que es honesto. El defecto real: --usage existe (set_agents_app.py:3641) y la doctrina canonica no lo menciona NUNCA (grep da cero). El propio orquestador cerro ~20 runs esta sesion sin pasarlo.

[2026-08-13T14:27:39+00:00] P2-modelo-por-instancia · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que el orquestador pueda pedir que modelo usar para cada agente que lanza, sin quedar atado a uno solo.
Ingeniería: AC-04..07, clase public-contract: cambia el contrato del descriptor de --route-decide (set_agents_app.py:605, conjunto cerrado). El riesgo central es que se convierta en bypass: la preferencia entra DESPUES del bucle de exclusiones, como factor de sort, con el precedente de _bias_rank. Un test por barrera.

[2026-08-13T13:42:44+00:00] P1-latencia-por-modelo-no-por-sufijo · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que el modelo que coordina no sea forzosamente de OpenAI, como pediste.
Ingeniería: AC-01..03. El test test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart (test_harness.py:266) exige sufijo -fast para orchestrator/implementer/product-analyst, y -fast solo existe en el proveedor openai de opencode: la asercion dice latencia y significa OpenAI. Se conserva para los dos roles de volumen y se libera el coordinador. models.toml [areas.coord] a opencode-go/grok…

[2026-08-13T12:31:26+00:00] P5-altas-y-bajas-automaticas · package-reviewer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Un revisor de otro proveedor confirma que el harness no se inventa proveedores y que dice la verdad sobre lo que midio.
Ingeniería: Writer claude-code/anthropic/opus (run1_12758dae; murio por error de API tras escribir codigo y tests, los gates los corrio el orquestador: 1065 OK, VERIFY_PASS). Reviewer codex/openai-codex/gpt-5.6-terra, dec1_7513f638, independence_verified=true. Asignacion acotada a 3 puntos + mordida, con prohibicion explicita de leer spec/evidencias: el primer reviewer de P4 murio consumido leyendo.

[2026-08-13T09:14:38+00:00] P5-altas-y-bajas-automaticas · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que activar una suscripcion alcance para poder usarla, y darla de baja se note, sin tocar nada.
Ingeniería: P5 de 022 (AC-16..19), ultimo paquete. Evidencia en vivo: github copilot figura authenticated=true detected_unlistable=true models_listable=0; openai-codex lista 6 modelos y su inferencia devolvio token vencido (listable != usable); ollama declarado con 3 modelos y endpoint muerto (curl 000). La heuristica espacio->guion es trampa: el CLI id de opencode-zen es 'opencode'. AC-19 toca las TRES supe…

[2026-08-13T09:07:14+00:00] P4-proveedores-del-usuario · package-reviewer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Un revisor de otro proveedor confirma que quitar un proveedor funciona y que la limpieza no te borra nada tuyo.
Ingeniería: Writer claude-code/anthropic/opus (run1_f193bfbd). Reviewer codex/openai-codex/gpt-5.6-terra, independence_verified=true. Se le pide dictaminar tambien el desvio de alcance a provider_registry.py que el implementer flageo solo.

[2026-08-13T07:11:14+00:00] P4-proveedores-del-usuario · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que puedas agregar y sobre todo QUITAR proveedores desde la aplicacion, sin que el proximo install te los reponga.
Ingeniería: P4 de 022 (AC-11..15). Medicion clave del pack: el bloque ollama del opencode.json del usuario es BYTE-IDENTICO al que envia Global/_shared/opencode.json:5-23, o sea no lo agrego el; y el endpoint esta muerto (curl 000). El caso real es quitar lo que el harness impuso, no lo que el usuario agrego. AC-13 renderiza el bloque desde el registro; AC-14 extiende la poda de archivos a subarboles JSON y …

[2026-08-13T06:21:25+00:00] P3-liveness-real · delta-reviewer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Ultima verificacion independiente antes de dar por bueno el paquete.
Ingeniería: Reparador claude-code/anthropic/opus (run1_ccfef5c2). Delta reviewer codex/openai-codex/gpt-5.6-terra, dec1_686d1590, independence_verified=true. Es el segundo y ultimo ciclo de review del presupuesto.

