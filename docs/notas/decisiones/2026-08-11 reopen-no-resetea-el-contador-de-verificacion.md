# HUMAN_DECISION_REQUIRED: reopen limpia el blocker pero no el contador, y deja al paquete permanentemente inaceptable

<!-- notas:auto -->
- fecha: 2026-08-11 · actor: orchestrator
- alcance: [[features/019-harness-evolution|019-harness-evolution]] · [[features/019-harness-evolution/P5-tools-discovery|P5-tools-discovery]]

## Contexto

Defecto del harness encontrado dogfooding, con P5 como victima. Secuencia: (1) el orquestador registro una llamada a record-verification por finding, 15 findings, y la septima agoto max_verifications_per_package=6; (2) _apply_verdicts (feature-state.py:699) bloquea ANTES de registrar, asi que F-07 nunca quedo con veredicto; (3) reopen limpio el blocker pero NO toco package['attempts']['verifications'], que sigue en 6; (4) F-07..F-11 (todos medium) estan REPARADOS en el arbol y verificados a mano por el orquestador, pero no se pueden registrar: require_verified (cli_review.py:277) guarda las dos puertas, record-repair y record-delta-review --closed-finding; (5) has_open_findings(medium) en package_accept_ready (model.py:441) impide aceptar el paquete. --skip-reason no sirve: exige que todos los findings abiertos sean low. El resultado es un paquete estructuralmente inaceptable, con el trabajo hecho y los gates en verde: VERIFY_PASS, CHECK_PASS + SELF_SCAFFOLD_SYNC_OK files=2, git diff --check limpio, sin artefactos parasitos. La ironia es que el docstring del propio budget (model.py:94-100) dice que es 'un backstop contra runaway, NO el control anti-reintentos', y que debe estar dimensionado contra los flujos que los otros budgets ya permiten.

## Decisión

PENDIENTE DE FEDERICO. El orquestador NO se autoriza a resolverlo solo, por una razon de integridad: es el mismo actor que agoto el presupuesto, y reescribir la guarda que lo atrapo seria exactamente el bypass que la separacion de funciones existe para impedir. Opciones planteadas: (A) arreglar el harness -- que reopen resetee attempts['verifications'] del paquete que reabre, porque si no, reopen no puede recuperar esta clase de blocker; toca feature_state_lib (modulo estado, ownership de P3 ya aceptado) con copias byte-identicas en 5 arboles y tests-contrato. (B) resetear el contador a mano en ai/state/features/019-harness-evolution.json y seguir, registrando el bypass. (C) supersede-package de P5 para obtener presupuesto fresco (queda 1 subdivision), a costa de perder el hilo review/repair. Recomendacion del orquestador: (A), porque el defecto es real y va a volver a morder a cualquier paquete con muchos findings; (B) solo si se quiere cerrar 019 primero y arreglar el harness despues, y en ese caso el bypass tiene que quedar registrado y con su propio ticket.

## Consecuencias

P5 queda en DELTA_REVIEW con 10 de 15 findings registrados como reparados y 5 (F-07..F-11) reparados en el arbol pero abiertos en el estado. La feature no puede llegar a INTEGRATION hasta resolverlo.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
