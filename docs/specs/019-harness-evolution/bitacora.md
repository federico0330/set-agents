# Bitácora — 019-harness-evolution

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-17T02:15:23+00:00

[2026-08-10T14:15:12+00:00] P1-provider-auto-adoption · implementer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Arranca el primer bloque: hacer que el harness use de verdad todas las cuentas de IA que ya tenes conectadas, en vez de dos solas.
Ingeniería: PKG-1 (AC-01..AC-11): discovered_providers='auto' destraba build_effective_snapshot (service.py:142-151), fuente unica provider->prefijo CLI (opencode_spawn.py:117 vs catalog._OPENCODE_CLI_IDS), guardas de inferencia (cap balanced, reviewer stem fail-closed, is_inferred en el sort key) y probe-cache con key versionada. Medicion viva 2026-08-10: copilot autenticado pero sin modelos listables -> fa…

[2026-08-10T16:05:10+00:00] P1-provider-auto-adoption · package-reviewer · done
Cliente: El primer bloque quedo implementado y revisado por un segundo agente independiente: el harness ya puede usar de verdad las cuentas de IA conectadas, no solo dos. La revision encontro seis cosas para mejorar, ninguna grave; cuatro se arreglaron en el momento, una quedo asignada al bloque siguiente y otra era un falso positivo del control interno.
Ingeniería: P1 (AC-01..AC-11) implementado, revisado (PASS_CON_HALLAZGOS: 0 criticos, 0 altos, 2 medios, 4 bajos) y reparado en una pasada consolidada. Suite 815 -> 819 tests OK (skipped=3), verify.sh VERIFY_PASS, build.sh --check CHECK_PASS + SELF_SCAFFOLD_SYNC_OK, git diff --check limpio, OWNERSHIP_PASS. F-02 (models.toml [catalog] desactualizado, techo de _configured_models) reasignado a P2 con excepcion …

[2026-08-10T18:26:45+00:00] P2-billing-aware-ordering · implementer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Segundo bloque: que el harness prefiera lo que ya pagas por suscripcion (o lo gratis) antes que lo que se cobra por uso, y que la consola muestre de verdad que cuentas tenes y cuales sirven.
Ingeniería: P2 (AC-12..AC-16): billing_rank puro (0 = suscripcion o sufijo -free, 1 = metered/desconocido) insertado en el sort key tras TIER_ORDER y antes de _bias_rank, sin tocar exclusiones duras; reason code aditivo; set-agents --route-doctor con probes frescos; panel y wizard resolviendo 'auto' en vez de iterarlo. Primer item obligatorio: el defecto vivo setup_models.py:156,364 (list('auto') -> ['a','u'…

[2026-08-11T00:26:53+00:00] P2-billing-aware-ordering · delta-reviewer · done
Cliente: Segundo bloque cerrado. El harness ahora prefiere lo que ya pagas por suscripcion (o lo que es gratis) antes que lo que se cobra por uso, y solo recurre a lo pago cuando de verdad no hay alternativa. Ademas tenes un comando nuevo, --route-doctor, que te dice de un vistazo que cuentas estan conectadas, cuantos modelos ofrece cada una y cual no sirve: ahi se ve por que Copilot no se puede usar.
Ingeniería: P2 accepted (AC-12..AC-16, ADR-0035). billing_rank puro en el sort key en posicion 4 de 8, tras TIER_ORDER y antes de _bias_rank; el bucle de exclusiones no lo lee, asi que el costo nunca es criterio de elegibilidad. Reason code aditivo BILLING_RANK persistido en decisions-v1.jsonl. --route-doctor read-only (probado por hash del state dir) y expone detected_unlistable para M-1. Panel y wizard res…

[2026-08-11T00:29:31+00:00] P3-cognitive-module-docs · implementer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Tercer bloque, el mas grande: que el harness lleve un registro vivo de COMO quedo construido el software, no solo de en que paso del proceso esta. La idea es que abras un archivo por modulo y en 90 segundos sepas que hace, por donde pasa y que cambio ultimo.
Ingeniería: P3 (AC-17..AC-24): render_modules.py reutilizando merge_note/write_note/_short de render_notes (never-raises, atomico, render-failures.log), registro docs/modules/modules.toml con globs, comandos record-module-impact / module-impact-detect / --module-impact-waived, gate de entrada a INTEGRATION + done_ready (con la relacion a ADR-0024 explicitada), seccion nueva en el digest y seed real de este r…

[2026-08-11T03:35:24+00:00] P3-cognitive-module-docs · delta-reviewer · done
Cliente: Tercer bloque cerrado, el mas grande. Ahora el harness lleva un registro vivo de como quedo construido el software: abris docs/modules/ y en 90 segundos sabes que hace cada modulo, por donde fluye y que cambio ultimo. Ademas ya no se puede cerrar una entrega sin dejar registrado que cambio en el software (o decir explicitamente por que no hacia falta), y el resumen de la manana suma una seccion n…
Ingeniería: P3 accepted (AC-17..AC-24, ADR-0036). render_modules.py reutiliza merge_note/write_note/_short (never-raises probado en vivo, atomico, render-failures.log), modules.toml con globs, tres comandos nuevos, gate de entrada a INTEGRATION + done_ready con waiver como valvula, seccion nueva en el digest y seed real de 5 modulos con anclas file:line verificadas. 856 tests OK (desde 831). Cuatro ciclos de…

[2026-08-11T03:36:06+00:00] P4-doctrine-human-layer · implementer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Cuarto bloque: que cada cierre de entrega te diga en una linea que cambio en tu forma de entender el sistema, que los agentes resuelvan antes de preguntarte cosas que ya dijiste, y que exista un comando /explicar que te cuente como funciona cualquier parte del sistema siguiendo el codigo de verdad.
Ingeniería: P4 (AC-25..AC-29): sub-bloque Impacto humano en el cierre de paquete de orchestrator.md sin tocar ADR-0027/0033, pasos nuevos en integrator.md y architect.md, ADR-0037 con el protocolo 'Resolve antes de preguntar' insertado antes de la lista askable y espejado en las 4 gemelas de Global/_shared + request-triage, y el comando/skill /explicar propagado a los 4 arboles por generate.py. roles.tsv no …

[2026-08-11T16:04:17+00:00] done
Cliente: Retomamos el paquete 4 (la capa humana de la doctrina). El trabajo ya estaba hecho en disco por la instancia anterior, que murió antes de dejar su comprobante; una instancia fresca lo esta auditando contra los criterios y escribiendo la evidencia.
Ingeniería: P4: ADR-0037, /explicar (comando+skill, 4 arboles), sub-bloque Impacto humano en orchestrator.md, pasos nuevos en integrator.md/architect.md, espejos en las 4 fuentes de _shared + request-triage, y tests AC-25..AC-29 en test_harness.py:7716-7827. build.sh --check CHECK_PASS sin drift. Falta: evidencia P4-implementer.md, prueba de mordida por test, gates pegados. Context pack de P5 escrito y regis…

[2026-08-11T17:00:06+00:00] P4-doctrine-human-layer · package-reviewer · started · modelo anthropic/sonnet · effort medium
Cliente: Un revisor independiente, de otro proveedor que el que escribio el paquete, audita la capa humana de la doctrina antes de darla por buena.
Ingeniería: package-reviewer sobre P4: anthropic/sonnet en claude-code, tier balanced, effort medium, independence_verified=true frente al writer openai-codex/gpt-5.6-terra (decision dec1_7cc40574306ab8aedb624339e7d2ab07, BILLING_RANK provider=anthropic rank=0). Audita AC-25..AC-29 y una muestra aleatoria de las pruebas de mordida del implementer (contramedida registrada por las tres verificaciones fabricada…

[2026-08-11T17:36:08+00:00] done
Cliente: Paquete 4 cerrado y aceptado. El harness ahora te cuenta, al cerrar cada paquete, que cambio en tu modelo mental del sistema; resuelve solo lo que ya estaba decidido en vez de volver a preguntarlo; y tiene un comando nuevo, /explicar, que lee el codigo real y te lo traduce, avisandote si la documentacion quedo vieja. Arranca el paquete 5, el ultimo: abrir el catalogo de herramientas bajo demanda,…
Ingeniería: P4 accepted. Review independiente anthropic/sonnet (independence_verified=true vs writer openai-codex/gpt-5.6-terra): aprobado-con-findings, 2 findings low ambos de calidad de evidencia; reparados y cerrados por delta review. Sin cuarto test decorativo (se rompio la racha P1/P2/P3) y sin fabricacion de evidencia en esta ronda: 4 pruebas de mordida re-ejecutadas al azar por reviewer y delta-review…

[2026-08-11T17:37:55+00:00] P5-tools-discovery · implementer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Arranca el ultimo paquete: que el harness pueda pedirte permiso para sumar una herramienta que le falta, en vez de frenarse. Nada se instala sin que vos lo apruebes.
Ingeniería: P5 (AC-30..AC-35): openai-codex/gpt-5.6-terra, tier frontier, effort high. Ruteado con task_class=security y risk=high a proposito -- el paquete extiende coord_policy._tools_channel_allowed, que es el allowlist que decide que puede ejecutar un agente; balanced habria alcanzado para el resto del paquete pero no para esa pieza. Alcance: --tools-propose (valida y no instala, rechaza sudo y pipes ocu…

[2026-08-11T18:05:14+00:00] P5-tools-discovery · implementer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: El primer intento del ultimo paquete murio por un problema de infraestructura sin alcanzar a escribir nada. Se relanza una vez, con el mismo encargo.
Ingeniería: Relanzamiento unico de P5 tras 'Agent stalled: no progress for 600s'. Misma ruta (openai-codex/gpt-5.6-terra, frontier, high) porque la causa fue el watchdog de stream, no capacidad del modelo. Mitigacion agregada al encargo: trabajar en incrementos visibles y escribir ADR-0038 + esqueleto de evidencia ANTES de implementar, para que un segundo corte deje algo utilizable. Segunda muerte del mismo …

[2026-08-11T19:21:45+00:00] P5-tools-discovery · package-reviewer · started · modelo anthropic/opus · effort medium
Cliente: Un revisor independiente, de otro proveedor que el que escribio el paquete, audita el flujo de aprobacion de herramientas antes de darlo por bueno. Es la parte del sistema que decide que puede ejecutar un agente sin preguntarte.
Ingeniería: package-reviewer sobre P5: anthropic/opus en claude-code, tier frontier, effort medium, independence_verified=true frente al writer openai-codex/gpt-5.6-terra (decision dec1_7b5568f3b598b9b205b0606f1a07ae37). Ruteado con task_class=security y risk=high: el paquete extiende coord_policy._tools_channel_allowed y el mapa de permisos de OpenCode en generate.py. Ejes reforzados: casos adversarios prop…

[2026-08-11T22:20:43+00:00] P5-tools-discovery · delta-reviewer · started · modelo anthropic/opus · effort medium
Cliente: Un revisor independiente comprueba que los dos agujeros de seguridad quedaron realmente tapados, atacandolos el mismo en vez de leer el informe.
Ingeniería: delta-reviewer sobre P5: anthropic/opus frontier, independence_verified=true frente al writer openai-codex/gpt-5.6-terra. Alcance: las 15 reparaciones. Ejes: re-ejecutar los dos ataques criticos (F-01 y F-02) y confirmarlos FALLANDO; probar bypasses propios contra la allowlist de caracteres y el denylist de escaladores; confirmar que curl|bash del catalogo real sigue pasando; y auditar una muestr…

[2026-08-11T22:57:19+00:00] P5-tools-discovery · repair-agent · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Segunda vuelta de arreglos: el revisor encontro un camino que las dos revisiones anteriores no habian mirado, y una parte del arreglo anterior que quedo a medias.
Ingeniería: P5 repair ronda 2. NEW-01 (high): tools.local.toml untracked llega a bash -c por --tools-install --yes sin pasar por _validate_install_command, que en cmd_tools_install aparece solo en un comentario. F-06 reabierto: la reparacion anterior se hizo contra la lista de ejemplos del finding en vez de contra el defecto, y una tabla sin 'detect' sigue reventando la consola. Ultima reparacion disponible …

[2026-08-11T23:44:57+00:00] P5-tools-discovery · delta-reviewer · started · modelo anthropic/opus · effort medium
Cliente: El revisor vuelve a atacar, esta vez por la puerta que encontro la vez pasada, para confirmar que quedo cerrada sin romper lo que funcionaba.
Ingeniería: delta-reviewer ronda 2 sobre P5: anthropic/opus frontier, independence_verified=true frente al writer openai-codex/gpt-5.6-terra. Ejes: atacar el camino de lectura con su propio tools.local.toml adversario (no leer la evidencia); confirmar que las 20 entradas curadas siguen instalandose igual y que curl|bash de gcloud pasa; atacar la clase de F-06 con formas que la lista NO enumeraba; y auditar a…

[2026-08-12T00:37:40+00:00] P5-tools-discovery · delta-reviewer · started · modelo anthropic/opus · effort medium
Cliente: Ultima verificacion independiente del paquete antes de cerrarlo.
Ingeniería: delta-reviewer ronda 3 sobre P5: anthropic/opus frontier, independence_verified=true. Alcance: solo NEW-02 y las dos correcciones cosmeticas. El repair encontro un segundo call site (cmd_mcp_toggle :2191) que el reviewer anterior no habia nombrado.

[2026-08-12T01:32:09+00:00] P5-tools-discovery · delta-reviewer · started · modelo anthropic/opus · effort medium
Cliente: Verificacion final independiente del ultimo paquete.
Ingeniería: delta-reviewer ronda 4 sobre P5. Alcance: NEW-03 (forma nativa completa del spec mcp) y NEW-04 (transcripcion corregida). El orquestador ya re-verifico las 8 variantes en vivo. Contramedidas vigentes por decisions-log slug cuarta-verificacion-fabricada-y-patron-del-hermano: auditoria al azar en TODAS las rondas, y atacar la clase, no el ejemplo.

[2026-08-12T02:06:32+00:00] P5-tools-discovery · integrator · started · modelo openai-codex/gpt-5.6-sol · effort balanced
Cliente: Ultimo paso: comprobar que las cinco partes funcionan juntas y no solo por separado.
Ingeniería: integrator sobre 019: los 5 paquetes accepted, los 5 con module_impacts registrados (el gate de INTEGRATION que construyo P3 ya paso). Verifica los criterios de cierre (a)-(f) de la seccion 3 de la spec, corre los gates globales y consolida la evidencia de entrega.

[2026-08-12T02:43:33+00:00] done
Cliente: La feature 019 quedo cerrada: los cinco paquetes aceptados, integrados y con los gates globales en verde. El harness ahora adopta solo los proveedores que configuras, prefiere lo que ya pagas, te explica que cambio en tu forma de pensar el sistema, resuelve antes de preguntarte, y te pide permiso para sumar herramientas en vez de frenarse.
Ingeniería: 019 DONE. 5/5 paquetes accepted, 6 module_impacts, ADRs 0034-0038 mas 0039 (arreglo del motor de estado autorizado aparte). Suite 815 -> 917 (+102), VERIFY_PASS, CHECK_PASS + SELF_SCAFFOLD_SYNC_OK files=2, git diff --check limpio. Deuda explicita registrada: las anclas file:line sembradas en docs/modules/ derivaron dentro de la misma feature (set_agents_app.py:2510 corrida +742 lineas) -- la desv…
