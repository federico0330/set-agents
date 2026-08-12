# Estado del desarrollo

_Generado por `feature-state.py` en cada mutación de estado. No editar a mano._

Actualizado: 2026-08-12T14:28:51+00:00

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
| 021-gates-que-no-mienten-ni-callan | feature | PACKAGE_REVIEW | P1-check-que-verifica (package_review) | 0/2 | 2/12 | 0/2 | 0 | - | - | 2026-08-12T14:28:51+00:00 record-spawn |

## Quick-fixes recientes

- [2026-08-06T13:33:48+00:00] Preserve explicit --project context in set_agents_app.py script mode by aliasing __main__ for lazy routing_cli imports — archivos: ai/scripts/set_agents_app.py, tests/test_routing.py — gate: python3 -m unittest focused router context tests: 2 PASS; py_compile PASS; git diff --check PASS; live route-decide context_ok=true — resultado: done
- [2026-08-03T02:36:03+00:00] P1F-01: cmd_transition's repair_entry pop for PACKAGE_REPAIR was nested under 'if args.package_id:'; since --package-id is optional on transition, a manual transition without it skipped the pop and let a stale repair_entry from a prior cycle auto-escape review inference. Hoisted the pop to always run on to_phase==PACKAGE_REPAIR, resolving the package via package_by_id (falls back to current_package_id) inside try/except StateError. — archivos: ai/scripts/feature-state.py, PROYECTO/ai/scripts/feature-state.py, tests/test_harness.py — gate: git diff --check: clean — resultado: done
- [2026-07-30T01:22:42+00:00] P2-vault-mandatory (accepted): exclude_notes_from_git/_notes_currently_excluded chequeaban (project/'.git').is_dir(), falso para un git worktree enlazado (.git es archivo ahi) -- docs/notas quedaba trackeado por git en vez de excluido, contradiciendo DEC-5. Fix: resolver via 'git rev-parse --show-toplevel/--git-common-dir' anclado a que el proyecto SEA el top-level (no solo estar dentro de un repo), con env purgado de GIT_DIR/GIT_WORK_TREE/GIT_COMMON_DIR/GIT_INDEX_FILE, timeout y manejo de git ausente. Bono: vault_doctor_report ahora distingue dangling de un symlink cuyo target fue borrado (antes reportaba healthy). Encontrado migrando ~/iey de verdad; revisado por un segundo agente (package-reviewer) que encontro 7 hallazgos adicionales sobre el primer fix, todos reparados y re-verificados con pass. — archivos: ai/scripts/set_agents_app.py, tests/test_harness.py — gate: 331 tests verdes, verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, git diff --check limpio, package-reviewer pass (2da pasada) — resultado: done
- [2026-07-30T01:22:33+00:00] P2-vault-mandatory (accepted): write_vault_registry_entry resolvía el vault_path a través del symlink recién creado, guardando el directorio real del repo en vez del symlink del lado del vault. vault_doctor_report reportaba health=drift para siempre en todo proyecto hybrid recién linkeado. Fix: normalizar resolviendo solo el padre (parent.resolve()/name), nunca el componente final. Encontrado migrando ~/iey de verdad. — archivos: ai/scripts/set_agents_app.py, tests/test_harness.py — gate: 331 tests verdes, verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, git diff --check limpio, package-reviewer pass — resultado: done

## Bitácora (últimos 15)

[2026-08-12T14:28:51+00:00] P1-check-que-verifica · package-reviewer · started · modelo anthropic/sonnet · effort medium
Cliente: Un revisor independiente comprueba que el control arreglado detecta de verdad, y que no rompio el instalador ni el cambio de modelos.
Ingeniería: package-reviewer sobre 021/P1: anthropic/sonnet, independence_verified=true frente al writer openai-codex/gpt-5.6-sol. Eje critico: el implementer TOCO setup_models.py, que el context pack no listaba en owned_paths, porque encontro que la nota del orquestador ('sigue funcionando sin tocarlo') era falsa. Hay que validar el hallazgo, el arreglo y la ampliacion de alcance.

[2026-08-12T13:35:29+00:00] P1-check-que-verifica · implementer · started · modelo openai-codex/gpt-5.6-sol · effort medium
Cliente: Arreglar el control que decia verificar que los archivos generados estaban al dia y en realidad no verificaba nada.
Ingeniería: P1 de 021 (AC-01..05): --check compara el STAGING contra los 4 arboles con --profile go-zen FIJO (decision de Federico: con perfil local rompe install.sh:370 y setup_models.py). Reusa el diff de verify.sh:26-28, no el de --diff que lleva || true. AC-04 se resuelve por ORDENAMIENTO, sin tocar los 17 call sites.

[2026-08-12T11:19:21+00:00] done
Cliente: La feature 020 quedo cerrada. El informe de la manana ahora abre con lo que necesita tu decision, y la documentacion de modulos tiene un comando que contrasta sus referencias contra el codigo real.
Ingeniería: 020 DONE. 2 paquetes, ADR-0040, suite 943 -> 970. P1: predicado compartido de feature viva; el digest, el hub y cmd_status dejaron de esconder lo bloqueado. P2: check_anchors.py y el comando check-anchors, con cobertura declarada honestamente (12/38 con chequeo semantico, margen de falso negativo 10-25% por ancla). Deuda de 019 sobre las anclas derivadas: cerrada.

[2026-08-12T05:49:58+00:00] P2-anclas-verificables · implementer · started · modelo openai-codex/gpt-5.6-sol · effort medium
Cliente: El primer intento murio por infraestructura sin escribir nada. Se relanza una vez.
Ingeniería: Relanzamiento unico de P2. Mitigacion: escribir evidencia en el primer minuto y guardar a disco por tramo. Si vuelve a morir, se parte en dos encargos mas chicos en vez de un tercer intento completo.

[2026-08-12T05:36:28+00:00] P2-anclas-verificables · implementer · started · modelo openai-codex/gpt-5.6-sol · effort medium
Cliente: Ultimo tramo: que la documentacion de modulos no pueda decir que algo esta en una linea donde ya no esta.
Ingeniería: P2 de 020 (AC-06..11): gramatica de dos formas de ancla con resolucion por basename acotada a los paths del modulo, comando check-anchors read-only con rc distinto de cero, verificacion semantica acotada a simbolo en backticks adyacente, enganche never-raises en sync-notes, y correccion de las anclas rotas de hoy.

[2026-08-12T04:10:42+00:00] P1-digest-no-esconde · package-reviewer · started · modelo anthropic/sonnet · effort medium
Cliente: Un revisor independiente audita el arreglo del informe matinal antes de darlo por bueno.
Ingeniería: package-reviewer sobre 020/P1: anthropic/sonnet, independence_verified=true frente al writer openai-codex/gpt-5.6-sol. Eje especial: el implementer MODIFICO un fixture de test preexistente (final_state 'done' -> 'DONE'); hay que verificar que el invariante sigue probado y no que se ajusto el test para que pase.

[2026-08-12T03:00:02+00:00] P1-digest-no-esconde · implementer · started · modelo openai-codex/gpt-5.6-sol · effort medium
Cliente: Arranca el arreglo del informe matinal: que las cosas trabadas esperandote aparezcan primero en vez de desaparecer.
Ingeniería: P1 de 020 (AC-01..05, AC-12): un predicado compartido de feature viva reemplaza las dos copias mal escritas (cli_reporting.py:194 y _hub_body), seccion Necesita tu decision con dias desde el ultimo blocker sin resolver, marca de estancada con las bloqueadas exentas, blocked_days/stale_days en cmd_status, y tests que fallan en rojo contra el codigo de hoy.

[2026-08-12T02:43:33+00:00] done
Cliente: La feature 019 quedo cerrada: los cinco paquetes aceptados, integrados y con los gates globales en verde. El harness ahora adopta solo los proveedores que configuras, prefiere lo que ya pagas, te explica que cambio en tu forma de pensar el sistema, resuelve antes de preguntarte, y te pide permiso para sumar herramientas en vez de frenarse.
Ingeniería: 019 DONE. 5/5 paquetes accepted, 6 module_impacts, ADRs 0034-0038 mas 0039 (arreglo del motor de estado autorizado aparte). Suite 815 -> 917 (+102), VERIFY_PASS, CHECK_PASS + SELF_SCAFFOLD_SYNC_OK files=2, git diff --check limpio. Deuda explicita registrada: las anclas file:line sembradas en docs/modules/ derivaron dentro de la misma feature (set_agents_app.py:2510 corrida +742 lineas) -- la desv…

[2026-08-12T02:06:32+00:00] P5-tools-discovery · integrator · started · modelo openai-codex/gpt-5.6-sol · effort balanced
Cliente: Ultimo paso: comprobar que las cinco partes funcionan juntas y no solo por separado.
Ingeniería: integrator sobre 019: los 5 paquetes accepted, los 5 con module_impacts registrados (el gate de INTEGRATION que construyo P3 ya paso). Verifica los criterios de cierre (a)-(f) de la seccion 3 de la spec, corre los gates globales y consolida la evidencia de entrega.

[2026-08-12T01:32:09+00:00] P5-tools-discovery · delta-reviewer · started · modelo anthropic/opus · effort medium
Cliente: Verificacion final independiente del ultimo paquete.
Ingeniería: delta-reviewer ronda 4 sobre P5. Alcance: NEW-03 (forma nativa completa del spec mcp) y NEW-04 (transcripcion corregida). El orquestador ya re-verifico las 8 variantes en vivo. Contramedidas vigentes por decisions-log slug cuarta-verificacion-fabricada-y-patron-del-hermano: auditoria al azar en TODAS las rondas, y atacar la clase, no el ejemplo.

[2026-08-12T00:37:40+00:00] P5-tools-discovery · delta-reviewer · started · modelo anthropic/opus · effort medium
Cliente: Ultima verificacion independiente del paquete antes de cerrarlo.
Ingeniería: delta-reviewer ronda 3 sobre P5: anthropic/opus frontier, independence_verified=true. Alcance: solo NEW-02 y las dos correcciones cosmeticas. El repair encontro un segundo call site (cmd_mcp_toggle :2191) que el reviewer anterior no habia nombrado.

[2026-08-11T23:44:57+00:00] P5-tools-discovery · delta-reviewer · started · modelo anthropic/opus · effort medium
Cliente: El revisor vuelve a atacar, esta vez por la puerta que encontro la vez pasada, para confirmar que quedo cerrada sin romper lo que funcionaba.
Ingeniería: delta-reviewer ronda 2 sobre P5: anthropic/opus frontier, independence_verified=true frente al writer openai-codex/gpt-5.6-terra. Ejes: atacar el camino de lectura con su propio tools.local.toml adversario (no leer la evidencia); confirmar que las 20 entradas curadas siguen instalandose igual y que curl|bash de gcloud pasa; atacar la clase de F-06 con formas que la lista NO enumeraba; y auditar a…

[2026-08-11T22:57:19+00:00] P5-tools-discovery · repair-agent · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Segunda vuelta de arreglos: el revisor encontro un camino que las dos revisiones anteriores no habian mirado, y una parte del arreglo anterior que quedo a medias.
Ingeniería: P5 repair ronda 2. NEW-01 (high): tools.local.toml untracked llega a bash -c por --tools-install --yes sin pasar por _validate_install_command, que en cmd_tools_install aparece solo en un comentario. F-06 reabierto: la reparacion anterior se hizo contra la lista de ejemplos del finding en vez de contra el defecto, y una tabla sin 'detect' sigue reventando la consola. Ultima reparacion disponible …

[2026-08-11T22:20:43+00:00] P5-tools-discovery · delta-reviewer · started · modelo anthropic/opus · effort medium
Cliente: Un revisor independiente comprueba que los dos agujeros de seguridad quedaron realmente tapados, atacandolos el mismo en vez de leer el informe.
Ingeniería: delta-reviewer sobre P5: anthropic/opus frontier, independence_verified=true frente al writer openai-codex/gpt-5.6-terra. Alcance: las 15 reparaciones. Ejes: re-ejecutar los dos ataques criticos (F-01 y F-02) y confirmarlos FALLANDO; probar bypasses propios contra la allowlist de caracteres y el denylist de escaladores; confirmar que curl|bash del catalogo real sigue pasando; y auditar una muestr…

[2026-08-11T19:21:45+00:00] P5-tools-discovery · package-reviewer · started · modelo anthropic/opus · effort medium
Cliente: Un revisor independiente, de otro proveedor que el que escribio el paquete, audita el flujo de aprobacion de herramientas antes de darlo por bueno. Es la parte del sistema que decide que puede ejecutar un agente sin preguntarte.
Ingeniería: package-reviewer sobre P5: anthropic/opus en claude-code, tier frontier, effort medium, independence_verified=true frente al writer openai-codex/gpt-5.6-terra (decision dec1_7b5568f3b598b9b205b0606f1a07ae37). Ruteado con task_class=security y risk=high: el paquete extiende coord_policy._tools_channel_allowed y el mapa de permisos de OpenCode en generate.py. Ejes reforzados: casos adversarios prop…

