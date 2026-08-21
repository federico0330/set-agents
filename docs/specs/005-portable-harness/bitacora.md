# Bitácora — 005-portable-harness

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-21T13:49:43+00:00

[2026-07-27T14:51:01+00:00] spec-challenger · started
Cliente: Antes de pedirte que lo apruebes, una instancia independiente busca agujeros en el contrato: cosas que suenan bien pero no se pueden comprobar, riesgos con tus datos reales, y contradicciones internas.
Ingeniería: SPEC_CHALLENGE opened. spec-challenger (read-only) probing: guest-test verifiability (AC-07), SEC-A02 re-anchoring to PROJECT_ROOT (AC-02), regex escaping of the baked absolute root (AC-01), SCHEMA 4->5 migration semantics (AC-03), real-data note migration (AC-13), and whether the sign-flipped opt-in test (AC-10) weakens a regression.

[2026-07-27T14:51:01+00:00] product-analyst · done
Cliente: Escribimos el contrato de la mejora: qué tiene que lograr, cómo se comprueba que está bien hecho y en qué orden se construye. Quedaron 27 criterios de aceptación repartidos en tres bloques: que el sistema funcione en cualquier proyecto, que Obsidian sea obligatorio y automático, y que el menú de la terminal se maneje con flechitas.
Ingeniería: SPEC_DRAFT closed. product-analyst wrote docs/specs/005-portable-harness/{spec,acceptance,plan}.md and indexed 005 (Draft) plus the missing 004 row in docs/specs/README.md. 27 ACs (AC-00..AC-26) across P1-portable-core, P2-vault-mandatory, P3-tui. Verified every cited path/line against the repo: no material errors in the approved plan.

[2026-07-27T14:52:35+00:00] orchestrator · done
Cliente: Medí el riesgo más alto del plan antes de tocar nada: tus notas de los 4 proyectos. Son 29 archivos y NO hay ningún choque de nombres, así que se pueden recuperar sin perder nada. El único caso delicado es iey-ai, que ya tiene 2 archivos tuyos en el repo: esos quedan intactos y las 13 notas se suman al lado.
Ingeniería: Pre-planning evidence gathered read-only: docs/specs/005-portable-harness/evidence/vault-migration-inventory.md. All four <vault>/Proyectos/<name> entries are real dirs (legacy --private topology); all four target repos exist. 29 files total. iey-ai is the only merge case (repo docs/notas holds 2 non-harness files); comm -12 on the two file lists is empty => zero name collisions. Closes the spec … _(truncado al render)_

[2026-07-27T15:00:45+00:00] spec-challenger · done
Cliente: El contrato no pasó limpio: la revisión independiente encontró 29 problemas, 15 de ellos serios. Entre otros: la migración de tus notas las habría dejado invisibles para el control de versiones, y un comando obligatorio del plan estaba prohibido por las propias reglas de permisos. Todos se arreglan en el contrato, antes de escribir una línea de código. Quedan 6 decisiones que son tuyas.
Ingeniería: SPEC_CHALLENGE closed: verdict revision_required. 15 HIGH blockers, 14 MEDIUM. Sharpest: SC-01 build-time path baking would break verify.sh:14-16 byte-identity gate on every other machine (substitution must live in install.py write path only; tracked Global/** keeps the placeholder). SC-03 find_vault's .parents excludes the start dir, so the headline AC fails standing at the project root. SC-06 A… _(truncado al render)_

[2026-07-27T15:19:51+00:00] product-analyst · done
Cliente: Contrato corregido: se cerraron los 29 problemas y entraron tus 3 decisiones. Ahora hay una propuesta en lenguaje de negocio para que puedas aprobar sin leer lo tecnico. Falta solo tu aprobacion para empezar a construir.
Ingeniería: Contract amended to 1.1.0: 32 ACs (was 27). Splits: AC-01 -> AC-01+AC-02 (install-time baking vs allowlist matcher fix); AC-02 -> AC-03+AC-04 (walk-up vs SEC-A02 trust level); AC-04 scope cut to P1 (vault link moved to P2). AC-07 -> AC-09 rewritten as a hermetic scripted test with named observables. New: AC-12 (vault intent marker), AC-23 (key decoder), AC-27 (terminal restore on abnormal exit). … _(truncado al render)_

[2026-07-27T15:25:51+00:00] P1-portable-core · architect · started
Cliente: Antes de escribir codigo, un arquitecto deja por escrito COMO se resuelve cada pieza: donde vive cada ruta, como se identifica cada proyecto sin confundirlo con otro, y como se migra la base de datos sin perder nada. Eso queda documentado para que dentro de un ano se entienda por que se hizo asi.
Ingeniería: AC-00 is a blocking predecessor of all P1 code. architect writes docs/adr/0008-two-roots-portability.md: HARNESS_HOME/PROJECT_ROOT doctrine, install-time-only baking (SC-01), allowlist dual fix incl. post-shlex.split matching (SC-02), self-inclusive nearest-ancestor-wins walk-up (SC-03/SC-04), SEC-A02 trust-level reframing (SC-05), persisted project-id primary with path-hash fallback and fail-clo… _(truncado al render)_

[2026-07-27T15:54:01+00:00] P1-portable-core · implementer · started
Cliente: Construimos el núcleo portátil: instalación sin rutas pegadas, detección del proyecto real, identidad persistente y migración segura del ruteo. La prueba de invitado queda para una validación independiente.
Ingeniería: PACKAGE_IMPLEMENTATION for P1 after AC-00. Ownership is limited to the approved P1 paths; implementer cannot approve its own work. T-111 hermetic guest E2E is reserved for independent gate/review per separation of duties.

[2026-07-27T16:07:00+00:00] P1-portable-core · implementer · done
Cliente: El núcleo portátil ya está construido y pasó sus comprobaciones locales: ahora el sistema puede instalarse sin quedar atado a una carpeta, identificar un proyecto separado y mantenerlos aislados. Antes de avanzar, otra instancia va a probarlo desde afuera, incluyendo el caso de una instalación invitada.
Ingeniería: Implementer checkpoint: T-101..T-110 are in the worktree with local py_compile, build.sh --check, diff check, focused routing/generation tests, scaffold idempotence, and manual schema-4→5 migration exercise. T-111 remains unaccredited by design; independent gate must add/verify migration and cross-project coverage.

[2026-07-27T16:07:08+00:00] P1-portable-core · gate-runner · started
Cliente: Una validación independiente va a probar el sistema como si fuera otra persona y otra computadora: instalación en carpeta con espacios, proyecto nuevo sin Git y separación total entre proyectos.
Ingeniería: PACKAGE_GATES after implementer checkpoint. Gate-runner is independent and owns no product edits; executes T-111 plus full/focused suites, build/verify/diff/ownership checks and specifically tests the identified migration/cross-project coverage gap.

[2026-07-27T16:19:46+00:00] P1-portable-core · gate-runner · done
Cliente: La prueba independiente encontró fallas reales, no cosméticas: la copia invitada todavía no pasa su verificación final y el harness actual no puede iniciar la migración porque no tiene identidad propia. Se encontraron antes de aceptar el paquete y se van a corregir de forma acotada.
Ingeniería: Independent gates: unittest discover 172 OK, test_routing 67 OK, py_compile/build/diff OK; migration rollback/DDL/cross-project denial proved. Failures: AC-01/09 placeholder verifier expects literal __SET_AGENTS_ROOT__ in coord_policy; routing-migrate requires absent harness project.json; ownership declaration omits generated state/notas and compiled Global artifacts. One consolidated repair batc… _(truncado al render)_

[2026-07-27T16:19:57+00:00] P1-portable-core · repair-agent · started
Cliente: Un agente va a corregir los tres desajustes encontrados: la verificación del clon, la identidad del harness y la declaración de archivos generados. Después se repite la prueba independiente.
Ingeniería: Consolidated PACKAGE_REPAIR after deterministic gate failures. Scope: preserve placeholders while enabling installed baking; ensure the harness has a persistent project identity without unsafe implicit reidentification; bring generated artifacts under approved ownership or generation discipline. No unrelated changes.

[2026-07-27T16:40:45+00:00] P1-portable-core · repair-agent · done
Cliente: Los tres problemas encontrados ya están corregidos y la prueba invitada completa pasa: clon separado, carpeta con espacios, home vacío y proyecto nuevo sin Git. Ahora una revisión de delta confirmará que la reparación resolvió sólo esos puntos y no abrió nada nuevo.
Ingeniería: Consolidated repair: complete placeholder literal retained in source/generated Global, harness project identity persisted, ownership made explicit and narrow, plus guest/migration regression coverage. Guest internal verify passed; focused checks/build/ownership/diff passed. Delta review is required and read-only.

[2026-07-27T16:43:19+00:00] P1-portable-core · package-reviewer · started
Cliente: Una revisión independiente revisa que el paquete completo cumpla exactamente lo acordado, incluyendo el clon invitado y la migración.
Ingeniería: PACKAGE_REVIEW independent functional/data review. Read-only; assess the complete P1 diff, tests, schema migration, portability and ownership against contract.

[2026-07-27T16:43:21+00:00] P1-portable-core · security-auditor · started
Cliente: Una auditoría de seguridad revisa que abrir un proyecto ajeno no permita leer archivos indebidos ni mezclar información de proyectos.
Ingeniería: Mandatory security review for external-project content trust boundary: O_NOFOLLOW, caps/validation, traversal, project-key scoping and command allowlist.

[2026-07-27T16:52:44+00:00] P1-portable-core · package-reviewer · done
Cliente: La revisión completa rechazó P1 por problemas reales de aislamiento, robustez y prueba: un proyecto no puede tocar ejecuciones de otro, archivos de estado malformados no pueden tirar el comando, el scaffold debe detectar conflictos y la prueba de invitado debe demostrar la instalación y el uso real. Se repararán todos juntos antes de revalidar.
Ingeniería: Package review cycle 1/2: eight actionable findings require consolidated repair across project-key lifecycle scoping, untrusted JSON/FIFO handling, identity fallback/degrade, scaffold conflicts, Pi project propagation, guest evidence, schema warning.

[2026-07-27T16:52:48+00:00] P1-portable-core · security-auditor · done
Cliente: La auditoría confirmó que los datos de un proyecto externo necesitan validación estricta y que ninguna acción de un proyecto puede afectar a otro.
Ingeniería: SEC-A02 audit: confirmed cross-project mutable lifecycle, malformed structure crash, FIFO blocking, and fallback semantics risks; repair must prove negative cases.

[2026-07-27T16:53:34+00:00] P1-portable-core · repair-agent · started
Cliente: Un agente corrige en un solo paquete los problemas de aislamiento entre proyectos, validación de archivos externos, scaffold y prueba invitada. Después una revisión de delta comprobará cada corrección.
Ingeniería: PACKAGE_REPAIR cycle 1. Ownership limited to P1 paths. Fix all eight findings with regressions; no scope expansion. Must preserve AC contracts, use project_key in every lifecycle mutation, and make untrusted project data fail closed/degrade.

[2026-07-27T17:04:38+00:00] P1-portable-core · repair-agent · done
Cliente: La reparación del primer ciclo está terminada: se cerraron las acciones cruzadas entre proyectos, el manejo de archivos externos inseguros, los conflictos de scaffold y la prueba invitada real. Un revisor de delta verificará estos ocho puntos uno por uno.
Ingeniería: Consolidated repair covers P1-REV-001..008 plus FIFO finding, limited to routing store/app/tests. Focal routing, scaffold, guest, py_compile and diff checks pass. Delta-review is mandatory; one deep-review cycle remains.

[2026-07-27T17:04:51+00:00] P1-portable-core · delta-reviewer · started
Cliente: Un revisor independiente comprueba punto por punto que los ocho problemas detectados quedaron cerrados, sin introducir otros nuevos.
Ingeniería: Focused DELTA_REVIEW after one consolidated repair. Reproduce all original attacks/failures, inspect only repair delta and verify no new scope/security regression.

[2026-07-27T17:12:50+00:00] P1-portable-core · delta-reviewer · blocked
Cliente: La revisión de delta confirmó que todo lo demás quedó cerrado, pero queda un problema que no puedo decidir por mi cuenta: para que la lane Pi use el proyecto correcto hay que modificar el spawner, un archivo que el alcance aprobado excluyó expresamente. Además falta que la prueba invitada observe la identidad efectivamente escrita por el ruteo.
Ingeniería: Delta review repair_required: P1-DLT-001 proves a subprocess environment export cannot propagate to parent set_agents_spawn; fixing Pi project scope requires expanding P1 ownership to that excluded file. P1-DLT-002 requires guest DB-level identity evidence. Stop for human scope decision.

[2026-07-27T17:18:39+00:00] P1-portable-core · implementer · started
Cliente: Vamos a cerrar el último desvío del ruteo Pi: al trabajar dentro de tu proyecto, sus tres pasos usarán siempre ese proyecto y la prueba invitada comprobará la identidad guardada realmente en la base.
Ingeniería: P1 was reopened from HUMAN_DECISION_REQUIRED under explicit user authorization. The approved exception is exactly ai/scripts/set_agents_spawn.py: add optional cwd to the lifecycle CLI helper and thread one routing_cwd through decide/dispatched/terminal including exception close. Update D5/spec/plan and test the persisted dispatches.project_key without altering store, allowlist, metric_rollups, or… _(truncado al render)_

[2026-07-27T17:26:15+00:00] P1-portable-core · gate-runner · started
Cliente: Una validación independiente repetirá el recorrido completo como proyecto invitado y verificará que no se mezclen identidades entre proyectos.
Ingeniería: PACKAGE_GATES: gate-runner is read-only and independent of the implementer. It must rerun the non-conclusive guest focal plus full unittest discovery, py_compile, build --check, verify.sh, diff --check, and check-owned-paths; explicitly prove cross-project isolation in the new Pi cwd lifecycle.

[2026-07-27T17:26:15+00:00] P1-portable-core · implementer · done
Cliente: El ruteo Pi ya usa el proyecto correcto en sus tres pasos y la prueba ahora revisa la identidad que quedó guardada. Se confirmó el ciclo de ruteo; falta repetir en forma independiente la prueba invitada completa.
Ingeniería: Implementer completed the approved DLT-001/002 delta: optional app-CLI cwd defaults to ROOT, a single routing_cwd is threaded through all lifecycle calls (including failure close), APP_CLI remains absolute and Pi keeps spawn_cwd. Added real hermetic SQLite lifecycle evidence plus guest dispatches.project_key assertion; py_compile, five focused lifecycle tests, and diff check passed. Guest focal w… _(truncado al render)_

[2026-07-27T17:33:32+00:00] P1-portable-core · gate-runner · blocked
Cliente: La validación independiente confirmó las pruebas principales, pero la verificación completa quedó cortada mientras repetía la prueba invitada. Se repetirá hasta tener un resultado definitivo.
Ingeniería: Independent gate: unittest discover (181 tests), py_compile, build --check and diff --check passed. verify.sh was interrupted without terminal result during the nested AC-09 guest test. A baseline ownership check also mixed prior worktree artifacts; the authorized delta paths must be checked explicitly.

[2026-07-27T17:37:37+00:00] P1-portable-core · debugger · started
Cliente: La prueba invitada tarda más de lo permitido. Un diagnóstico acotado va a identificar qué paso se queda esperando y corregir únicamente esa causa, sin aflojar la prueba.
Ingeniería: debugging-loop: timeout 90 on the guest test is reproducible. Debugger owns only the affected implementation/test/docs paths and must prove root cause before editing; no test weakening, no unrelated refactor. One spawn remains for independent delta/security review.

[2026-07-27T17:43:19+00:00] P1-portable-core · debugger · blocked
Cliente: La prueba invitada sigue quedando esperando y el diagnóstico no pudo ver con certeza qué paso interno se frena. Para no dar por terminado algo que no pasó su control final, el paquete queda detenido con el detalle registrado.
Ingeniería: debugging-loop hard stop: direct AC-09 guest test reproduced timeout 124 twice; verify.sh likewise did not terminate in the nested guest test. No root cause was proven, so no code/test change was made. Per project policy, ambiguous repeated deterministic gate failure requires human decision rather than speculative repair.

[2026-07-27T17:48:35+00:00] P1-portable-core · debugger · started
Cliente: Con tu autorización, se amplía el diagnóstico para mirar el proceso invitado por dentro y encontrar exactamente qué espera antes de corregirlo.
Ingeniería: Expanded debugging scope after explicit user authorization. This is the 12th and final P1 instantiation budget: debugger may instrument subprocess execution with bounded diagnostics, identify the exact waiter, and make the minimal repair; subsequent independent delta/gate work will reuse existing agents without creating another state instantiation.

[2026-07-27T17:55:36+00:00] P1-portable-core · delta-reviewer · started
Cliente: Una revisión final independiente va a comprobar que el arreglo acelera sólo el control interno invitado y no deja ningún proyecto sin validar ni mezcla identidades.
Ingeniería: Reusing the prior independent gate instance without creating a new package spawn (the physical P1 spawn budget is exhausted). Read-only delta review: inspect only the guest verify-mode repair and DLT-001/002 behavior, reproduce guest/full gates, and audit cross-project isolation.

[2026-07-27T17:55:36+00:00] P1-portable-core · debugger · done
Cliente: Se encontró y corrigió la causa: la prueba invitada estaba haciendo otra prueba completa adentro y por eso superaba el límite. Ahora valida lo necesario para una instalación invitada y termina rápido, sin perder ninguna comprobación de identidad ni portabilidad.
Ingeniería: Expanded diagnosis proved a nested full 181-test suite, not a deadlock. Minimal repair: verify.sh detects SET_AGENTS_GUEST_VERIFY and runs only the portable smoke assertions already complemented by the outer scaffold/install/routing/SQLite proof; normal verify remains unchanged. Added a 90s guest subprocess timeout regression. Direct guest, guest verify, full verify, and diff check passed.

[2026-07-27T17:57:30+00:00] P1-portable-core · delta-reviewer · done
Cliente: La última revisión confirmó que el arreglo no recorta la prueba: el proyecto invitado sigue instalándose, ruteándose y verificando su identidad guardada; sólo se evitó repetir toda la suite desde adentro.
Ingeniería: Independent focused delta review PASS: direct guest AC-09 in 22.189s, explicit cwd lifecycle including failure close, absolute APP_CLI/read-only Pi guards, full verify behavior, and delta-scoped ownership all confirmed. No new findings.

[2026-07-29T17:17:17+00:00] started
Cliente: Arranca el paquete mas grande y el unico con datos reales: mover las notas de Obsidian de vivir sueltas en cada repo a vivir en un vault central obligatorio, con instalacion multiplataforma, un backup real antes de tocar nada, y un modo de prueba (dry-run) que muestra que va a pasar sin tocar un solo archivo.
Ingeniería: Abre P2-vault-mandatory (contrato 1.1.0, AC-10..AC-21, 12 work items T-200..T-211 segun docs/specs/005-portable-harness/plan.md). Orden: primero lo que no toca datos reales; la migracion real (AC-16/T-206) se testea con fixtures sinteticos primero y solo corre contra ~/iey en --dry-run antes de la confirmacion separada.

[2026-07-29T18:04:37+00:00] P2-vault-mandatory · package-reviewer · started
Cliente: Antes de aceptar el paquete del vault, dos revisores independientes miran todo el codigo: uno busca errores concretos y mantenibilidad, el otro se enfoca en seguridad (dado que este paquete toca datos reales unica-copia y agrega comandos nuevos que leen archivos).
Ingeniería: Panel RP-01, package-reviewer + security-auditor declarados juntos en la apertura (12 work items, riesgo alto declarado en el plan.md original por real-data migration + superficie CLI nueva).

[2026-07-29T18:04:38+00:00] P2-vault-mandatory · security-auditor · started
Cliente: -
Ingeniería: Segundo miembro del mismo panel acotado RP-01: revisa vault_migration_plan/apply_vault_migration (borrado de datos reales), cmd_context (nunca debe leer superficies de credenciales), y la nueva entrada SAFE_ARGV en coord_policy.py.

[2026-07-29T20:59:20+00:00] P2-vault-mandatory · finding-verifier · started
Cliente: Antes de arreglar nada, alguien de afuera intenta tirar abajo cada uno de los 10 problemas de seguridad que se encontraron, para confirmar cuáles son reales.
Ingeniería: finding-verifier adversarial pass sobre P2-vault-mandatory; PACKAGE_REVIEW ya cerró con verdict repair_required y next_transition exige record-verification antes de entrar a PACKAGE_REPAIR.

[2026-07-30T01:53:46+00:00] started
Cliente: Arrancamos el selector de flechas de la terminal (menú con teclas en vez de números).
Ingeniería: Abriendo P3-tui: AC-22..AC-30 ya aprobados en el contrato 1.1.0, sin bloqueantes. Narrando apertura antes de crear el paquete (sin --package-id, sin record-spawn contra P2-vault-mandatory).

[2026-07-30T01:54:39+00:00] P3-tui · implementer · started
Cliente: Instanciamos al implementador que construye el nuevo menú con flechas.
Ingeniería: implementer, contra P3-tui, AC-22..AC-30, 8 tareas, adversarial-primero

[2026-07-30T03:04:50+00:00] P3-tui · package-reviewer · started
Cliente: Instanciamos al revisor independiente del nuevo menú.
Ingeniería: package-reviewer, contra P3-tui integrado, foco adversarial en AC-26/27 (handoff de terminal + señales)

[2026-07-30T03:21:05+00:00] P3-tui · repair-agent · started
Cliente: Instanciamos al reparador de los bugs que encontró el revisor.
Ingeniería: repair-agent, consolidado, F-01..F-10, tests de regresión rojo-primero por hallazgo

[2026-07-30T04:40:57+00:00] P3-tui · repair-agent · started
Cliente: Instanciamos al reparador de la segunda ronda de hallazgos del TUI.
Ingeniería: repair-agent, consolidado, 1 llamada record-repair al final

[2026-07-30T05:29:54+00:00] P3-tui · delta-reviewer · started
Cliente: Instanciamos al revisor final del TUI, segunda ronda.
Ingeniería: delta-reviewer, foco en si D-02/D-03/F-08 (mecanismos nuevos: render a stderr, clamp de header, filtro de search) quedaron genuinamente cerrados
