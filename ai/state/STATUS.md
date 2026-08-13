# Estado del desarrollo

_Generado por `feature-state.py` en cada mutación de estado. No editar a mano._

Actualizado: 2026-08-13T13:40:43+00:00

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
| 026-orquestador-elige-modelo | scoped | PACKAGE_PLANNING | P2-modelo-por-instancia (planned) | 0/2 | 0/8 | 0/2 | 0 | - | PACKAGE_IMPLEMENTATION | 2026-08-13T13:38:43+00:00 create-package |

## Quick-fixes recientes

- [2026-08-12T15:24:52+00:00] render_notes emitia trailing whitespace en la linea de un finding sin category ni summary, rompiendo git diff --check y por lo tanto verify.sh. Defecto PREEXISTENTE (ya estaba en notas commiteadas de 007, 009, 012 y 013); recien entro al diff porque se regenero una nota nueva. 83 de 324 findings del repo caen en ese caso. Arreglo: el separador em-dash solo se emite si hay label, con _short aplicado antes del chequeo para cubrir labels de solo whitespace. Test de regresion en test_harness.py:2340-2356 con mordida confirmada. sync-notes regenero 14 notas. Los 5 espejos con md5 identico. — archivos: ai/scripts/feature_state_lib/render_notes.py, tests/test_harness.py — gate: verify.sh -> VERIFY_PASS con 973 OK / 3 skips y EXIT=0; build.sh --check -> GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; git diff --check limpio — resultado: done
- [2026-08-06T13:33:48+00:00] Preserve explicit --project context in set_agents_app.py script mode by aliasing __main__ for lazy routing_cli imports — archivos: ai/scripts/set_agents_app.py, tests/test_routing.py — gate: python3 -m unittest focused router context tests: 2 PASS; py_compile PASS; git diff --check PASS; live route-decide context_ok=true — resultado: done
- [2026-08-03T02:36:03+00:00] P1F-01: cmd_transition's repair_entry pop for PACKAGE_REPAIR was nested under 'if args.package_id:'; since --package-id is optional on transition, a manual transition without it skipped the pop and let a stale repair_entry from a prior cycle auto-escape review inference. Hoisted the pop to always run on to_phase==PACKAGE_REPAIR, resolving the package via package_by_id (falls back to current_package_id) inside try/except StateError. — archivos: ai/scripts/feature-state.py, PROYECTO/ai/scripts/feature-state.py, tests/test_harness.py — gate: git diff --check: clean — resultado: done
- [2026-07-30T01:22:42+00:00] P2-vault-mandatory (accepted): exclude_notes_from_git/_notes_currently_excluded chequeaban (project/'.git').is_dir(), falso para un git worktree enlazado (.git es archivo ahi) -- docs/notas quedaba trackeado por git en vez de excluido, contradiciendo DEC-5. Fix: resolver via 'git rev-parse --show-toplevel/--git-common-dir' anclado a que el proyecto SEA el top-level (no solo estar dentro de un repo), con env purgado de GIT_DIR/GIT_WORK_TREE/GIT_COMMON_DIR/GIT_INDEX_FILE, timeout y manejo de git ausente. Bono: vault_doctor_report ahora distingue dangling de un symlink cuyo target fue borrado (antes reportaba healthy). Encontrado migrando ~/iey de verdad; revisado por un segundo agente (package-reviewer) que encontro 7 hallazgos adicionales sobre el primer fix, todos reparados y re-verificados con pass. — archivos: ai/scripts/set_agents_app.py, tests/test_harness.py — gate: 331 tests verdes, verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, git diff --check limpio, package-reviewer pass (2da pasada) — resultado: done
- [2026-07-30T01:22:33+00:00] P2-vault-mandatory (accepted): write_vault_registry_entry resolvía el vault_path a través del symlink recién creado, guardando el directorio real del repo en vez del symlink del lado del vault. vault_doctor_report reportaba health=drift para siempre en todo proyecto hybrid recién linkeado. Fix: normalizar resolviendo solo el padre (parent.resolve()/name), nunca el componente final. Encontrado migrando ~/iey de verdad. — archivos: ai/scripts/set_agents_app.py, tests/test_harness.py — gate: 331 tests verdes, verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, git diff --check limpio, package-reviewer pass — resultado: done

## Bitácora (últimos 15)

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

[2026-08-13T05:44:21+00:00] P3-liveness-real · repair-agent · started · modelo anthropic/opus · effort medium
Cliente: Cerrar el ultimo agujero del mismo tipo: un archivo de credenciales con forma rara que el harness daba por bueno.
Ingeniería: P3-F03 critical: pi_auth_provider_keys acepta {'openai-codex': []} y hasta {'proveedor-inventado': {...}}, devolviendo keyset y firma no vacios. Ultimo ciclo de review disponible (1 de 2 consumido). Se pide ademas barrida sistematica: toda funcion que lea credenciales valida forma, todo test que diga cubrir 'foreign shape' cubre objetos.

[2026-08-13T05:37:36+00:00] P3-liveness-real · delta-reviewer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Un tercer revisor confirma que los dos agujeros de seguridad quedaron cerrados y no se abrio otro.
Ingeniería: Delta acotado a catalog.py (firmas) y tests/test_routing.py. Reparador claude-code/anthropic/opus; delta reviewer codex/openai-codex/gpt-5.6-terra, dec1_2eeb028a, independence_verified=true.

[2026-08-13T05:02:20+00:00] P3-liveness-real · repair-agent · started · modelo anthropic/opus · effort medium
Cliente: Cerrar dos agujeros: cuando el archivo de credencial esta roto o ausente, el harness lo daba por bueno en vez de volver a preguntar.
Ingeniería: P3-F01 critical: un JSON objeto con forma invalida ({} en codex, {claudeAiOauth:{}} en claude) produce firma NO vacia; y el test que dice cubrir 'foreign-shaped JSON' solo prueba listas. P3-F02 high: pi_auth_provider_keys no comprueba st_uid propio y _pi_auth_signature hashea el conjunto vacio con la version, asi que archivo ausente o symlink dan firma no vacia. Ambos reproducidos por el orquesta…

[2026-08-13T04:43:38+00:00] P3-liveness-real · package-reviewer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Un revisor de otro proveedor audita que leer las credenciales para detectar altas y bajas no filtre nada.
Ingeniería: Writer claude-code/anthropic/opus (run1_b2ca9919). Reviewer codex/openai-codex/gpt-5.6-terra, dec1_1b7703d7, independence_verified=true. Se le pide ademas dictaminar si el diseno de la firma aguanta aunque el supuesto de no-rotacion resultara falso, porque la captura A/B esta pendiente de un refresh natural.

[2026-08-13T03:41:24+00:00] P3-liveness-real · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que dar de alta o de baja una suscripcion se note en la decision siguiente, no cinco minutos despues.
Ingeniería: P3 de 022 (AC-07..10), clase security: lee archivos de credencial. Firma por runtime, todo stat/lectura local -- hoy _live_opencode_auth_signature:378 cuesta un SUBPROCESO por composicion y no hay que multiplicarlo por cuatro. Trampa medida y ausente de la spec: ~/.claude/.credentials.json contiene TAMBIEN mcpOAuth (token de Vercel), asi que hashear el archivo o su mtime rota en cada refresh de M…

[2026-08-13T03:35:39+00:00] P2-techo-catalogo-tri-estado · package-reviewer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Un revisor de otro proveedor de IA confirma que el cambio hace lo que dice y no abrio una puerta de mas.
Ingeniería: Writer claude-code/anthropic/opus (run1_d8520988). Reviewer codex/openai-codex/gpt-5.6-terra, dec1_0cbd3fc5, independence_verified=true. Asignacion acotada a 3 puntos + 1 mordida.

[2026-08-13T02:14:54+00:00] P2-techo-catalogo-tri-estado · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que agregar un proveedor de IA nuevo deje de exigir editar un archivo de configuracion a mano.
Ingeniería: P2 de 022 (AC-04..06). _configured_models -> resolve_ceiling con tres estados, consumido por los TRES sitios que hoy divergen: _probe_pairs:487-489 (el 'if not allowed: continue' que es el defecto), _read_probe_cache:429 (re-intersecta al leer; en auto una interseccion ingenua deja el cache siempre vacio) y build_snapshot:652-653 (que ademas tiene la lista de proveedores hardcodeada, alcance cedi…

[2026-08-13T01:56:40+00:00] P1-registro-de-proveedores · delta-reviewer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Un tercer revisor confirma que el arreglo de los dos controles realmente funciona y no rompio nada.
Ingeniería: Delta acotado a tests/test_routing.py (unico archivo tocado por el repair). Reparador fue claude-code/anthropic/opus; delta reviewer en codex/openai-codex/gpt-5.6-terra, dec1_c4cd7f80, independence_verified=true.

[2026-08-13T01:27:32+00:00] P1-registro-de-proveedores · repair-agent · started · modelo anthropic/opus · effort medium
Cliente: Arreglar dos controles automaticos que decian estar cuidando el codigo y en realidad no cuidaban nada.
Ingeniería: P1-F01 (critical): la guarda AC-01b compara valores rederivados de la misma fuente. P1-F02 (high): el refactor volvio tautologica la guarda preexistente de ADR-0034 AC-10, que antes cruzaba dos tablas independientes. Ambas verificadas upheld por el orquestador con una mutacion unica del registro. Writer original y repair son ambos opus/anthropic; la independencia aplica al reviewer, no al reparad…

[2026-08-13T01:03:16+00:00] P1-registro-de-proveedores · package-reviewer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Una segunda opinion, hecha por otro proveedor de IA distinto del que escribio el codigo, que revisa que el cambio no haya roto nada ni prometido de mas.
Ingeniería: Writer fue claude-code/anthropic/opus (run1_370bfc8a). Independencia por PROVEEDOR distinto (service.py:353 la exige dura): reviewer en opencode/openai-codex/gpt-5.6-terra, decision dec1_4ac1490e, independence_verified=true. Asignacion acotada a 3 puntos + 1 mordida por la leccion de los ocho stalls.

