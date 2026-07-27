# Estado del desarrollo

_Generado por `feature-state.py` en cada mutación de estado. No editar a mano._

Actualizado: 2026-07-27T17:58:36+00:00

## Features

| Feature | Modo | Fase | Paquete | Aceptados | Spawns | Reviews | Findings abiertos | Blocker | Próximo paso | Último evento |
|---|---|---|---|---|---|---|---|---|---|---|
| 002-adaptive-pi-orchestration | feature | BLOCKED | P1-routing-core (repair_required) | 0/1 | 12/12 | 2/2 | 5 | HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhausted 12 spawns plus 2 deep-review cycles. Requires redesign of trusted catalog/observations and crash-safe telemetry before further implementation. | - | 2026-07-24T16:16:04+00:00 block |
| 003-trusted-routing-pi-runtime | feature | PACKAGE_ACCEPTED | P1R-trusted-routing (accepted) | 1/1 | 16/16 | 3/3 | 0 | - | INTEGRATION | 2026-07-25T03:01:53+00:00 accept-package |
| 004-adaptive-dispatch | feature | DONE | P3-pi-lane (accepted) | 3/3 | 20/12 | 1/2 | 0 | - | - | 2026-07-27T14:04:38+00:00 transition |
| 005-portable-harness | feature | PACKAGE_ACCEPTED | P1-portable-core (accepted) | 1/1 | 12/12 | 2/2 | 0 | - | INTEGRATION | 2026-07-27T17:58:36+00:00 accept-package |

## Quick-fixes recientes

- _sin quick-fixes registrados_

## Bitácora (últimos 15)

[2026-07-27T17:57:30+00:00] P1-portable-core · delta-reviewer · done
Cliente: La última revisión confirmó que el arreglo no recorta la prueba: el proyecto invitado sigue instalándose, ruteándose y verificando su identidad guardada; sólo se evitó repetir toda la suite desde adentro.
Ingeniería: Independent focused delta review PASS: direct guest AC-09 in 22.189s, explicit cwd lifecycle including failure close, absolute APP_CLI/read-only Pi guards, full verify behavior, and delta-scoped ownership all confirmed. No new findings.

[2026-07-27T17:55:36+00:00] P1-portable-core · debugger · done
Cliente: Se encontró y corrigió la causa: la prueba invitada estaba haciendo otra prueba completa adentro y por eso superaba el límite. Ahora valida lo necesario para una instalación invitada y termina rápido, sin perder ninguna comprobación de identidad ni portabilidad.
Ingeniería: Expanded diagnosis proved a nested full 181-test suite, not a deadlock. Minimal repair: verify.sh detects SET_AGENTS_GUEST_VERIFY and runs only the portable smoke assertions already complemented by the outer scaffold/install/routing/SQLite proof; normal verify remains unchanged. Added a 90s guest subprocess timeout regression. Direct guest, guest verify, full verify, and diff check passed.

[2026-07-27T17:55:36+00:00] P1-portable-core · delta-reviewer · started
Cliente: Una revisión final independiente va a comprobar que el arreglo acelera sólo el control interno invitado y no deja ningún proyecto sin validar ni mezcla identidades.
Ingeniería: Reusing the prior independent gate instance without creating a new package spawn (the physical P1 spawn budget is exhausted). Read-only delta review: inspect only the guest verify-mode repair and DLT-001/002 behavior, reproduce guest/full gates, and audit cross-project isolation.

[2026-07-27T17:48:35+00:00] P1-portable-core · debugger · started
Cliente: Con tu autorización, se amplía el diagnóstico para mirar el proceso invitado por dentro y encontrar exactamente qué espera antes de corregirlo.
Ingeniería: Expanded debugging scope after explicit user authorization. This is the 12th and final P1 instantiation budget: debugger may instrument subprocess execution with bounded diagnostics, identify the exact waiter, and make the minimal repair; subsequent independent delta/gate work will reuse existing agents without creating another state instantiation.

[2026-07-27T17:43:19+00:00] P1-portable-core · debugger · blocked
Cliente: La prueba invitada sigue quedando esperando y el diagnóstico no pudo ver con certeza qué paso interno se frena. Para no dar por terminado algo que no pasó su control final, el paquete queda detenido con el detalle registrado.
Ingeniería: debugging-loop hard stop: direct AC-09 guest test reproduced timeout 124 twice; verify.sh likewise did not terminate in the nested guest test. No root cause was proven, so no code/test change was made. Per project policy, ambiguous repeated deterministic gate failure requires human decision rather than speculative repair.

[2026-07-27T17:37:37+00:00] P1-portable-core · debugger · started
Cliente: La prueba invitada tarda más de lo permitido. Un diagnóstico acotado va a identificar qué paso se queda esperando y corregir únicamente esa causa, sin aflojar la prueba.
Ingeniería: debugging-loop: timeout 90 on the guest test is reproducible. Debugger owns only the affected implementation/test/docs paths and must prove root cause before editing; no test weakening, no unrelated refactor. One spawn remains for independent delta/security review.

[2026-07-27T17:33:32+00:00] P1-portable-core · gate-runner · blocked
Cliente: La validación independiente confirmó las pruebas principales, pero la verificación completa quedó cortada mientras repetía la prueba invitada. Se repetirá hasta tener un resultado definitivo.
Ingeniería: Independent gate: unittest discover (181 tests), py_compile, build --check and diff --check passed. verify.sh was interrupted without terminal result during the nested AC-09 guest test. A baseline ownership check also mixed prior worktree artifacts; the authorized delta paths must be checked explicitly.

[2026-07-27T17:26:15+00:00] P1-portable-core · implementer · done
Cliente: El ruteo Pi ya usa el proyecto correcto en sus tres pasos y la prueba ahora revisa la identidad que quedó guardada. Se confirmó el ciclo de ruteo; falta repetir en forma independiente la prueba invitada completa.
Ingeniería: Implementer completed the approved DLT-001/002 delta: optional app-CLI cwd defaults to ROOT, a single routing_cwd is threaded through all lifecycle calls (including failure close), APP_CLI remains absolute and Pi keeps spawn_cwd. Added real hermetic SQLite lifecycle evidence plus guest dispatches.project_key assertion; py_compile, five focused lifecycle tests, and diff check passed. Guest focal wrapper ended without a terminal result, so independent gate owns its rerun.

[2026-07-27T17:26:15+00:00] P1-portable-core · gate-runner · started
Cliente: Una validación independiente repetirá el recorrido completo como proyecto invitado y verificará que no se mezclen identidades entre proyectos.
Ingeniería: PACKAGE_GATES: gate-runner is read-only and independent of the implementer. It must rerun the non-conclusive guest focal plus full unittest discovery, py_compile, build --check, verify.sh, diff --check, and check-owned-paths; explicitly prove cross-project isolation in the new Pi cwd lifecycle.

[2026-07-27T17:18:39+00:00] P1-portable-core · implementer · started
Cliente: Vamos a cerrar el último desvío del ruteo Pi: al trabajar dentro de tu proyecto, sus tres pasos usarán siempre ese proyecto y la prueba invitada comprobará la identidad guardada realmente en la base.
Ingeniería: P1 was reopened from HUMAN_DECISION_REQUIRED under explicit user authorization. The approved exception is exactly ai/scripts/set_agents_spawn.py: add optional cwd to the lifecycle CLI helper and thread one routing_cwd through decide/dispatched/terminal including exception close. Update D5/spec/plan and test the persisted dispatches.project_key without altering store, allowlist, metric_rollups, or Pi read-only guards.

[2026-07-27T17:12:50+00:00] P1-portable-core · delta-reviewer · blocked
Cliente: La revisión de delta confirmó que todo lo demás quedó cerrado, pero queda un problema que no puedo decidir por mi cuenta: para que la lane Pi use el proyecto correcto hay que modificar el spawner, un archivo que el alcance aprobado excluyó expresamente. Además falta que la prueba invitada observe la identidad efectivamente escrita por el ruteo.
Ingeniería: Delta review repair_required: P1-DLT-001 proves a subprocess environment export cannot propagate to parent set_agents_spawn; fixing Pi project scope requires expanding P1 ownership to that excluded file. P1-DLT-002 requires guest DB-level identity evidence. Stop for human scope decision.

[2026-07-27T17:04:51+00:00] P1-portable-core · delta-reviewer · started
Cliente: Un revisor independiente comprueba punto por punto que los ocho problemas detectados quedaron cerrados, sin introducir otros nuevos.
Ingeniería: Focused DELTA_REVIEW after one consolidated repair. Reproduce all original attacks/failures, inspect only repair delta and verify no new scope/security regression.

[2026-07-27T17:04:38+00:00] P1-portable-core · repair-agent · done
Cliente: La reparación del primer ciclo está terminada: se cerraron las acciones cruzadas entre proyectos, el manejo de archivos externos inseguros, los conflictos de scaffold y la prueba invitada real. Un revisor de delta verificará estos ocho puntos uno por uno.
Ingeniería: Consolidated repair covers P1-REV-001..008 plus FIFO finding, limited to routing store/app/tests. Focal routing, scaffold, guest, py_compile and diff checks pass. Delta-review is mandatory; one deep-review cycle remains.

[2026-07-27T16:53:34+00:00] P1-portable-core · repair-agent · started
Cliente: Un agente corrige en un solo paquete los problemas de aislamiento entre proyectos, validación de archivos externos, scaffold y prueba invitada. Después una revisión de delta comprobará cada corrección.
Ingeniería: PACKAGE_REPAIR cycle 1. Ownership limited to P1 paths. Fix all eight findings with regressions; no scope expansion. Must preserve AC contracts, use project_key in every lifecycle mutation, and make untrusted project data fail closed/degrade.

[2026-07-27T16:52:48+00:00] P1-portable-core · security-auditor · done
Cliente: La auditoría confirmó que los datos de un proyecto externo necesitan validación estricta y que ninguna acción de un proyecto puede afectar a otro.
Ingeniería: SEC-A02 audit: confirmed cross-project mutable lifecycle, malformed structure crash, FIFO blocking, and fallback semantics risks; repair must prove negative cases.

