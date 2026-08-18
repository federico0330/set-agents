# Bitácora — 022-disponibilidad-real

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-18T14:19:56+00:00

[2026-08-13T00:13:18+00:00] P1-registro-de-proveedores · implementer · started · modelo anthropic/opus · effort medium
Cliente: Unificar la lista de proveedores de IA que hoy esta repetida en siete lugares del codigo, para que sumar uno nuevo sea una linea y no siete.
Ingeniería: P1 de 022 (AC-01..03). Deriva _OPENCODE_PROVIDER_KEYS, _OPENCODE_CLI_IDS, _PAIR_COMMANDS, PROVIDER_BILLING_KIND, el key map de _configured_models, DISCOVERABLE_PROVIDERS y _MODEL_PREFERENCE_PROVIDERS de un PROVIDERS unico. Refactor puro: AC-02 exige caracterizacion byte-identica. Trampas medidas: el lockstep real existe en test_routing.py:3191-3200 y hay que preservarlo; _MODEL_PREFERENCE_PROVIDE… _(truncado al render)_

[2026-08-13T01:03:16+00:00] P1-registro-de-proveedores · package-reviewer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Una segunda opinion, hecha por otro proveedor de IA distinto del que escribio el codigo, que revisa que el cambio no haya roto nada ni prometido de mas.
Ingeniería: Writer fue claude-code/anthropic/opus (run1_370bfc8a). Independencia por PROVEEDOR distinto (service.py:353 la exige dura): reviewer en opencode/openai-codex/gpt-5.6-terra, decision dec1_4ac1490e, independence_verified=true. Asignacion acotada a 3 puntos + 1 mordida por la leccion de los ocho stalls.

[2026-08-13T01:27:32+00:00] P1-registro-de-proveedores · repair-agent · started · modelo anthropic/opus · effort medium
Cliente: Arreglar dos controles automaticos que decian estar cuidando el codigo y en realidad no cuidaban nada.
Ingeniería: P1-F01 (critical): la guarda AC-01b compara valores rederivados de la misma fuente. P1-F02 (high): el refactor volvio tautologica la guarda preexistente de ADR-0034 AC-10, que antes cruzaba dos tablas independientes. Ambas verificadas upheld por el orquestador con una mutacion unica del registro. Writer original y repair son ambos opus/anthropic; la independencia aplica al reviewer, no al reparad… _(truncado al render)_

[2026-08-13T01:56:40+00:00] P1-registro-de-proveedores · delta-reviewer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Un tercer revisor confirma que el arreglo de los dos controles realmente funciona y no rompio nada.
Ingeniería: Delta acotado a tests/test_routing.py (unico archivo tocado por el repair). Reparador fue claude-code/anthropic/opus; delta reviewer en codex/openai-codex/gpt-5.6-terra, dec1_c4cd7f80, independence_verified=true.

[2026-08-13T02:14:54+00:00] P2-techo-catalogo-tri-estado · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que agregar un proveedor de IA nuevo deje de exigir editar un archivo de configuracion a mano.
Ingeniería: P2 de 022 (AC-04..06). _configured_models -> resolve_ceiling con tres estados, consumido por los TRES sitios que hoy divergen: _probe_pairs:487-489 (el 'if not allowed: continue' que es el defecto), _read_probe_cache:429 (re-intersecta al leer; en auto una interseccion ingenua deja el cache siempre vacio) y build_snapshot:652-653 (que ademas tiene la lista de proveedores hardcodeada, alcance cedi… _(truncado al render)_

[2026-08-13T03:35:39+00:00] P2-techo-catalogo-tri-estado · package-reviewer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Un revisor de otro proveedor de IA confirma que el cambio hace lo que dice y no abrio una puerta de mas.
Ingeniería: Writer claude-code/anthropic/opus (run1_d8520988). Reviewer codex/openai-codex/gpt-5.6-terra, dec1_0cbd3fc5, independence_verified=true. Asignacion acotada a 3 puntos + 1 mordida.

[2026-08-13T03:41:24+00:00] P3-liveness-real · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que dar de alta o de baja una suscripcion se note en la decision siguiente, no cinco minutos despues.
Ingeniería: P3 de 022 (AC-07..10), clase security: lee archivos de credencial. Firma por runtime, todo stat/lectura local -- hoy _live_opencode_auth_signature:378 cuesta un SUBPROCESO por composicion y no hay que multiplicarlo por cuatro. Trampa medida y ausente de la spec: ~/.claude/.credentials.json contiene TAMBIEN mcpOAuth (token de Vercel), asi que hashear el archivo o su mtime rota en cada refresh de M… _(truncado al render)_

[2026-08-13T04:43:38+00:00] P3-liveness-real · package-reviewer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Un revisor de otro proveedor audita que leer las credenciales para detectar altas y bajas no filtre nada.
Ingeniería: Writer claude-code/anthropic/opus (run1_b2ca9919). Reviewer codex/openai-codex/gpt-5.6-terra, dec1_1b7703d7, independence_verified=true. Se le pide ademas dictaminar si el diseno de la firma aguanta aunque el supuesto de no-rotacion resultara falso, porque la captura A/B esta pendiente de un refresh natural.

[2026-08-13T05:02:20+00:00] P3-liveness-real · repair-agent · started · modelo anthropic/opus · effort medium
Cliente: Cerrar dos agujeros: cuando el archivo de credencial esta roto o ausente, el harness lo daba por bueno en vez de volver a preguntar.
Ingeniería: P3-F01 critical: un JSON objeto con forma invalida ({} en codex, {claudeAiOauth:{}} en claude) produce firma NO vacia; y el test que dice cubrir 'foreign-shaped JSON' solo prueba listas. P3-F02 high: pi_auth_provider_keys no comprueba st_uid propio y _pi_auth_signature hashea el conjunto vacio con la version, asi que archivo ausente o symlink dan firma no vacia. Ambos reproducidos por el orquesta… _(truncado al render)_

[2026-08-13T05:37:36+00:00] P3-liveness-real · delta-reviewer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Un tercer revisor confirma que los dos agujeros de seguridad quedaron cerrados y no se abrio otro.
Ingeniería: Delta acotado a catalog.py (firmas) y tests/test_routing.py. Reparador claude-code/anthropic/opus; delta reviewer codex/openai-codex/gpt-5.6-terra, dec1_2eeb028a, independence_verified=true.

[2026-08-13T05:44:21+00:00] P3-liveness-real · repair-agent · started · modelo anthropic/opus · effort medium
Cliente: Cerrar el ultimo agujero del mismo tipo: un archivo de credenciales con forma rara que el harness daba por bueno.
Ingeniería: P3-F03 critical: pi_auth_provider_keys acepta {'openai-codex': []} y hasta {'proveedor-inventado': {...}}, devolviendo keyset y firma no vacios. Ultimo ciclo de review disponible (1 de 2 consumido). Se pide ademas barrida sistematica: toda funcion que lea credenciales valida forma, todo test que diga cubrir 'foreign shape' cubre objetos.

[2026-08-13T06:21:25+00:00] P3-liveness-real · delta-reviewer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Ultima verificacion independiente antes de dar por bueno el paquete.
Ingeniería: Reparador claude-code/anthropic/opus (run1_ccfef5c2). Delta reviewer codex/openai-codex/gpt-5.6-terra, dec1_686d1590, independence_verified=true. Es el segundo y ultimo ciclo de review del presupuesto.

[2026-08-13T07:11:14+00:00] P4-proveedores-del-usuario · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que puedas agregar y sobre todo QUITAR proveedores desde la aplicacion, sin que el proximo install te los reponga.
Ingeniería: P4 de 022 (AC-11..15). Medicion clave del pack: el bloque ollama del opencode.json del usuario es BYTE-IDENTICO al que envia Global/_shared/opencode.json:5-23, o sea no lo agrego el; y el endpoint esta muerto (curl 000). El caso real es quitar lo que el harness impuso, no lo que el usuario agrego. AC-13 renderiza el bloque desde el registro; AC-14 extiende la poda de archivos a subarboles JSON y … _(truncado al render)_

[2026-08-13T09:07:14+00:00] P4-proveedores-del-usuario · package-reviewer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Un revisor de otro proveedor confirma que quitar un proveedor funciona y que la limpieza no te borra nada tuyo.
Ingeniería: Writer claude-code/anthropic/opus (run1_f193bfbd). Reviewer codex/openai-codex/gpt-5.6-terra, independence_verified=true. Se le pide dictaminar tambien el desvio de alcance a provider_registry.py que el implementer flageo solo.

[2026-08-13T09:14:38+00:00] P5-altas-y-bajas-automaticas · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que activar una suscripcion alcance para poder usarla, y darla de baja se note, sin tocar nada.
Ingeniería: P5 de 022 (AC-16..19), ultimo paquete. Evidencia en vivo: github copilot figura authenticated=true detected_unlistable=true models_listable=0; openai-codex lista 6 modelos y su inferencia devolvio token vencido (listable != usable); ollama declarado con 3 modelos y endpoint muerto (curl 000). La heuristica espacio->guion es trampa: el CLI id de opencode-zen es 'opencode'. AC-19 toca las TRES supe… _(truncado al render)_

[2026-08-13T12:31:26+00:00] P5-altas-y-bajas-automaticas · package-reviewer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Un revisor de otro proveedor confirma que el harness no se inventa proveedores y que dice la verdad sobre lo que midio.
Ingeniería: Writer claude-code/anthropic/opus (run1_12758dae; murio por error de API tras escribir codigo y tests, los gates los corrio el orquestador: 1065 OK, VERIFY_PASS). Reviewer codex/openai-codex/gpt-5.6-terra, dec1_7513f638, independence_verified=true. Asignacion acotada a 3 puntos + mordida, con prohibicion explicita de leer spec/evidencias: el primer reviewer de P4 murio consumido leyendo.
