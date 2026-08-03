# Bitácora — 011-quota-failover

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-03T00:38:55+00:00

[2026-07-30T16:42:25+00:00] package-planner · started
Cliente: El contrato de cuotas quedó aceptado y se inició como trabajo nuevo, separado del historial de selección previa.
Ingeniería: Feature 011 registrada con hash aprobado y AC-01..AC-06; fase PACKAGE_PLANNING.

[2026-07-30T16:45:16+00:00] P1-quota-failover · implementer · started
Cliente: Se implementa el reemplazo único y seguro tras un agotamiento real de cuota.
Ingeniería: Implementación acotada de esquema, transacción BEGIN IMMEDIATE, integración Pi y pruebas deterministas para AC-01..AC-06.

[2026-07-30T16:52:23+00:00] P1-quota-failover · implementer · started
Cliente: Se retoma el núcleo ya guardado para cerrar pruebas y el runner real sin perder el avance.
Ingeniería: Nueva instancia implementa exclusivamente los pendientes documentados: tests deterministas AC-01..05 y runner/evidencia AC-06.

[2026-07-30T16:58:41+00:00] P1-quota-failover · implementer · started
Cliente: Se completa la comprobación real que debe bloquearse honestamente si falta la precondición controlada.
Ingeniería: Instancia focalizada para runner credencial-gated AC-06 y evidencia, sin expandir el núcleo de routing.

[2026-07-30T17:02:28+00:00] P1-quota-failover · implementer · done
Cliente: El reemplazo seguro y su comprobación real quedaron implementados; sin precondición controlada, el sistema informa un bloqueo seguro.
Ingeniería: Core schema-7, transición atómica, adaptador Pi, pruebas AC-01..05 y runner AC-06 documentados; cinco pruebas focalizadas PASS.

[2026-07-30T17:04:50+00:00] P1-quota-failover · runtime-verifier · blocked
Cliente: La prueba real no puede hacerse de forma segura sin una suscripción agotada controlada; el sistema quedó detenido sin gastar ni modificar nada.
Ingeniería: AC-06 requiere precondición externa verificable. Runner validado devuelve BLOCKED/HUMAN_DECISION_REQUIRED antes de abrir DB o invocar Pi; feature state quedó BLOCKED.

[2026-07-30T17:57:23+00:00] P1-quota-failover · started
Cliente: Antes de seguir, encontré que la suite completa tiene 2 pruebas rojas que la verificación acotada de la sesión anterior no corrió.
Ingeniería: verify.sh (suite completa, 473 tests) -> FAILED (failures=2): test_routing_migrate_uses_harness_identity_and_test_store espera 'to=6' y el schema real ya es 7; test_the_usage_columns_sit_exactly_where_alter_table_puts_them compara contra un DDL canónico que no incluye replacement_of_run_id. Ambos son literales desactualizados por el propio paquete P1-quota-failover (SCHEMA=7, columna agregada cor…
