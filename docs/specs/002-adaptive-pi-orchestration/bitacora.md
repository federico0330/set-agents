# Bitácora — 002-adaptive-pi-orchestration

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-18T15:14:04+00:00

[2026-07-24T14:51:58+00:00] done
Cliente: La instancia no arrancó por una restricción técnica; se reintenta sin ampliar alcance.
Ingeniería: Spawn rechazado pre-instanciación por agent_type con fork completo; retry con contexto explícito y fork_turns=none.

[2026-07-24T14:56:52+00:00] P1-routing-core · spec-challenger · blocked
Cliente: El challenge read-only excedió su tiempo y fue interrumpido sin cambios; se reintenta de forma acotada.
Ingeniería: Retry de SPEC_CHALLENGE: mismo agente, sólo blocker/high y veredicto proceed/no-proceed.

[2026-07-24T14:59:11+00:00] P1-routing-core · spec-challenger · done
Cliente: El challenge detectó ocho huecos de precisión; se corrigen usando decisiones ya presentes en el plan aprobado.
Ingeniería: Retorno SPEC_CHALLENGE: SC-01..SC-08. No cambia intención; exige contrato lane/tier, dispatch fail-closed, schema2, privacidad, rollout y rollback explícitos.

[2026-07-24T15:04:41+00:00] P1-routing-core · package-planner · done
Cliente: La planificación confirmó P1 y corrigió ownership, context pack y superficie observable.
Ingeniería: PACKAGE_PLANNING PROCEED; P1 high, runtime_surface=true, setup_models owned, P2 boundary explícito.

[2026-07-24T15:04:58+00:00] P1-routing-core · implementer · started
Cliente: Un único implementador construye configuración, router, telemetría y CLI con pruebas focalizadas.
Ingeniería: PACKAGE_IMPLEMENTATION P1; ownership exclusivo de seis paths, modelo frontier/high, sin autoaprobación.

[2026-07-24T15:11:32+00:00] P1-routing-core · implementer · done
Cliente: P1 quedó implementado con pruebas focalizadas verdes; el gate global expuso dos expectativas antiguas.
Ingeniería: PACKAGE_IMPLEMENTATION return: P1-T1..T5 completos; verify falla sólo en schema1 fixture y bootstrap env-sensitive, ambos fuera de tests P1.

[2026-07-24T15:12:39+00:00] P1-routing-core · package-reviewer · started
Cliente: Una revisión independiente contrasta P1 completo contra el contrato aprobado y sus gates.
Ingeniería: PACKAGE_REVIEW panel P1-R1; correctness/integration/test gaps, read-only, familia independiente.

[2026-07-24T15:12:39+00:00] P1-routing-core · security-auditor · started
Cliente: Una segunda revisión busca bypasses, filtraciones y fallas de permisos en router, gates y telemetría.
Ingeniería: PACKAGE_REVIEW panel P1-R1 security lane; allowlists, HMAC, filesystem permissions, input validation, read-only.

[2026-07-24T15:19:43+00:00] P1-routing-core · package-reviewer · done
Cliente: La revisión funcional encontró brechas concretas en catálogo, clasificación, gates, fallback, reportes y cobertura.
Ingeniería: P1-R1 package-reviewer repair_required: 12 hallazgos, 9 high y 3 medium, AC-05..AC-13.

[2026-07-24T15:19:43+00:00] P1-routing-core · security-auditor · done
Cliente: La revisión de seguridad confirmó spoofing de catálogo, downgrade, symlinks, replay y filtración por valores.
Ingeniería: P1-R1 security-auditor repair_required: SEC-001..SEC-007, catálogo confiable, GateSpec, fallback durable y telemetry nofollow/lock.

[2026-07-24T15:20:23+00:00] P1-routing-core · repair-agent · started
Cliente: Una única reparación agrupada endurece catálogo, gates, fallback y telemetría sin ampliar el alcance.
Ingeniería: PACKAGE_REPAIR batch 1; P1-R1.md es source of findings, mismos owned paths, finding-specific tests, delta review obligatorio.

[2026-07-24T15:29:16+00:00] P1-routing-core · repair-agent · done
Cliente: La reparación cerró los huecos de seguridad y trazabilidad del router sin ampliar el alcance.
Ingeniería: P1-R1 consolidado: catálogo sellado, envelope estricto, GateSpec inmutable, fallback durable, telemetría nofollow y tests focalizados 8/8; listo para DELTA_REVIEW.

[2026-07-24T15:29:34+00:00] P1-routing-core · delta-reviewer · started
Cliente: Una mirada nueva comprueba que las correcciones cerraron los problemas sin agregar regresiones.
Ingeniería: DELTA_REVIEW de P1-R1; contraste finding→change→verification, read-only, sin reabrir fuera del delta salvo regresión directa.

[2026-07-24T15:36:00+00:00] P1-routing-core · delta-reviewer · done
Cliente: La revisión focalizada detectó bypasses reproducibles; P1 vuelve a reparación y no se acepta todavía.
Ingeniería: DELTA_REVIEW repair_required: sólo P1-R1-004 cerrado; nueve grupos de hallazgos reabiertos como P1-DR1-001..009, sin full re-review.

[2026-07-24T15:36:23+00:00] P1-routing-core · repair-agent · started
Cliente: Un último lote corrige únicamente los nueve bypasses que la revisión pudo reproducir.
Ingeniería: PACKAGE_REPAIR batch 2; P1-DR1-001..009, pruebas negativas obligatorias, mismos owned paths, sin autoaprobación.

[2026-07-24T15:40:12+00:00] P1-routing-core · repair-agent · started
Cliente: La validación local encontró tres fallas concretas; el mismo lote vuelve a corregirlas antes de registrarse.
Ingeniería: PACKAGE_REPAIR batch 2 retry; catálogo app/validator mismatch, Sol alias y bool-as-int reproducidos; nuevos tests deben fallar antes y pasar después.

[2026-07-24T15:42:35+00:00] P1-routing-core · repair-agent · started
Cliente: Una reparación mínima cierra las dos obligaciones de telemetría que el retry dejó explícitamente pendientes.
Ingeniería: PACKAGE_REPAIR batch 2 final retry; append O(1) amortizado y fallback realmente consumido, con migración/rotación y tests.

[2026-07-24T15:47:30+00:00] P1-routing-core · repair-agent · blocked
Cliente: El primer retorno del segundo lote corrigió varias fallas, pero la validación local reprodujo tres defectos y lo devolvió.
Ingeniería: Batch 2 no registrado: app/validator mismatch, alias Sol literal y bool-as-int; retry requerido.

[2026-07-24T15:47:30+00:00] P1-routing-core · repair-agent · blocked
Cliente: El retry cerró esos tres defectos, pero declaró dos obligaciones de telemetría aún pendientes.
Ingeniería: Batch 2 todavía no registrable: append O(n) y fallback ofrecido contado como consumido; reparación acotada adicional.

[2026-07-24T15:47:30+00:00] P1-routing-core · repair-agent · done
Cliente: La reparación final cerró las dos obligaciones de telemetría y dejó 15 pruebas focalizadas verdes.
Ingeniería: Append amortizado con metadata privada, rotación agregada, fallback_used explícito, outcomes/exclusiones y fail-closed de sidecar.

[2026-07-24T15:47:40+00:00] P1-routing-core · delta-reviewer · started
Cliente: Un revisor nuevo intenta romper otra vez el router, los gates, el fallback y la telemetría.
Ingeniería: DELTA_REVIEW 2; P1-DR1-001..009, read-only, probes adversariales y presupuesto final de reparación ya consumido.

[2026-07-24T15:56:24+00:00] P1-routing-core · delta-reviewer · blocked
Cliente: La revisión final reprodujo fallas altas; el paquete no puede aceptarse dentro del presupuesto aprobado.
Ingeniería: DELTA_REVIEW 2 repair_required: P1-DR2-001..008; repair_batches=2, hard stop HUMAN_DECISION_REQUIRED.

[2026-07-24T16:00:41+00:00] P1-routing-core · repair-agent · started
Cliente: Un único especialista corrige los ocho defectos reproducidos sin tocar Pi ni ampliar el alcance.
Ingeniería: PACKAGE_IMPLEMENTATION exception cycle 3; P1-DR2-001..008, owned P1 paths, hosted model, finding-specific regressions, no self-approval.

[2026-07-24T16:06:48+00:00] P1-routing-core · repair-agent · done
Cliente: El tercer ciclo autorizado corrigió los ocho defectos y dejó 20 regresiones focalizadas verdes.
Ingeniería: P1-DR2-001..008 implementados en routing.py/tests; gates locales PASS, verify global conserva dos fallas P3 conocidas.

[2026-07-24T16:07:21+00:00] P1-routing-core · package-reviewer · started
Cliente: Una revisión funcional independiente contrasta el P1 completo con el contrato y los ocho defectos reparados.
Ingeniería: PACKAGE_REVIEW P1-R2; correctness/integration/tests, read-only, closure evidence for P1-DR2.

[2026-07-24T16:07:21+00:00] P1-routing-core · security-auditor · started
Cliente: Una revisión de seguridad intenta reproducir escapes, carreras, filtraciones y downgrade.
Ingeniería: PACKAGE_REVIEW P1-R2 security lane; filesystem/no-follow/crash consistency/reviewer independence, read-only.

[2026-07-24T16:16:03+00:00] P1-routing-core · package-reviewer · blocked
Cliente: La revisión funcional cerró tres defectos, pero reprodujo cinco fallas altas y rechazó P1.
Ingeniería: P1-R2 package-reviewer repair_required: DR2-004/005/006 closed; DR2-001/002/003/007/008 open con probes.

[2026-07-24T16:16:03+00:00] P1-routing-core · security-auditor · blocked
Cliente: La revisión de seguridad no pudo completar porque el proveedor bloqueó el contenido de la auditoría.
Ingeniería: P1-R2 security subreview errored por policy del proveedor; sin hallazgos inventados, evidencia registrada como blocked.
