# 007-quota-visibility · P3-correct-record

<!-- notas:auto -->
## Motivo

- objetivo: Retractar la afirmacion registrada de que el carril anthropic de Pi cobra por token como extra-usage, y retirar la remediacion rm que ya no aplica
- complejidad: small
- riesgo: Ninguno tecnico. El riesgo es dejar una afirmacion equivocada en un documento que el usuario lee como autoritativo.
- paths: `docs/notas/BUENOS-DIAS.md`, `ai/state/features/007-quota-visibility.json`, `ai/state/STATUS.md`, `ai/state/decisions-log.jsonl`, `ai/state/narrative-log.jsonl`, `docs/notas/**`
- depende de: P2-spawn-accounting

## Tareas

- [x] Reescribir la seccion de costo con lo verificado y registrarlo con log-decision (completed) · docs/notas/BUENOS-DIAS.md seccion 3: el bloque 'Lo que falta, y es el bloqueante real' (routing.db schema-4 + rm) reemplazado por una nota de retractacion fechada, sin ofrecer remediacion porque no hay nada que remediar (routing.db no existe, 007-P1 cerro la clase de bug). La advertencia sobre sobrecargo de anthropic reemplazada con la medicion real (mismo bucket OAuth, costo real = piso de entrada por spawn, 3221/6 tokens)., El bloque 'Lo que si esta' (100-112) no se toco: AC-19 solo alcanza a las dos afirmaciones falsas, no al inventario que sigue siendo cierto., log-decision buenos-dias-anthropic-surcharge-claim-was-wrong registrado, enlazado a routing-db-schema4-unmigratable, feature 007 / package P3-correct-record., Cero cambios de codigo: grep confirma que solo docs/notas/BUENOS-DIAS.md cambio de contenido de producto; el resto son los archivos de estado que log-decision/complete-task escriben (owned_paths declarados).

## Hallazgos

- F-01 [high] closed — correctness
- F-02 [high] closed — correctness
- F-03 [medium] closed — correctness
- F-04 [medium] closed — integration
- F-05 [medium] closed — correctness
- F-06 [medium] closed — correctness
- F-07 [low] closed — correctness
- F-08 [low] closed — correctness
- N-01 [medium] closed — integration
- N-02 [low] closed — correctness
- N-03 [low] closed — correctness

## Recorrido

- review: repair_required (8 hallazgos)
- verificación: 0 refutados, 6 sostenidos
- verificación: 0 refutados, 3 sostenidos
- repair: F-01, F-02, F-03, F-04, F-05, F-06, F-07, F-08 → 8 archivos
- repair: N-01, N-02, N-03 → 7 archivos
- delta review: repair_required
- delta review: pass
- testing: pass
- runtime QA: pass (waived)
- gate `package verify`: pass
- gate `self-scaffold-sync`: pass
- gate `whitespace`: pass
- gate `ownership`: pass

↩ [[features/007-quota-visibility|007-quota-visibility]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._

**Corrección 2026-07-29 (hallazgo N-01 de DELTA_REVIEW, texto revisado tras una segunda verificación que
refutó la primera redacción de esta misma nota):** la primera línea de "Tareas" arriba (bloque auto-generado
desde `local_validations`) repite dos afirmaciones que **ya eran falsas cuando se escribieron**, no que se
volvieron falsas después: `complete-task` de este paquete se registró a las 2026-07-29T15:25:48+00:00, y el
dispatch real que recreó `routing.db` en schema 6 quedó grabado a las 2026-07-29T13:10:29Z (10:10 -03) —
**2h15m antes**. "routing.db no existe" y "3221/6 tokens como única muestra" ya eran incorrectas en el
momento de escribirlas; nadie las verificó contra el disco antes de darlas por completadas. El texto correcto:
`routing.db` **existe** en schema 6 con un dispatch real; hay **dos** muestras en vivo (3221/6 de la feature
004 y 3321/5 de ese mismo dispatch). `feature-state.py` no ofrece un comando para enmendar `local_validations`
fuera de `PACKAGE_IMPLEMENTATION`, así que esta nota es la corrección — ver `docs/notas/BUENOS-DIAS.md`
(fuente de verdad actual) y la decisión `buenos-dias-anthropic-surcharge-claim-was-wrong-supersedes-first-pass`.
