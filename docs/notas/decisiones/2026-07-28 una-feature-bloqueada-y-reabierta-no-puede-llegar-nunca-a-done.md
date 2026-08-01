# done_ready mira si la lista de blockers esta vacia, no si algun blocker sigue abierto

<!-- notas:auto -->
- fecha: 2026-07-28 · actor: orchestrator
- alcance: [[features/009-self-application|009-self-application]] · [[features/009-self-application/P3-panel-integrity|P3-panel-integrity]]

## Contexto

Lo encontro el finding-verifier refutando F-04, y el orquestador lo confirmo leyendo el codigo. done_ready se niega a DONE con 'open blocker exists' cuando data['blockers'] es no vacia -- verdad de la lista, no de su contenido. cmd_reopen le estampa a cada blocker resolved_at, resolved_reason y resolved_by, pero nunca los remueve, y done_ready no filtra por resolved_at como si hace summarize_feature. Preexiste a este paquete, verificado en el arbol previo.

## Decisión

Se registra y no se repara. Esta fuera de los criterios de 009-P3 (AC-08 a AC-11 son el ciclo de review y dos registros derivados) y tocar la condicion de terminacion de toda feature durante un paquete de integridad de panel es exactamente el refactor oportunista que las reglas prohiben.

## Consecuencias

Toda feature que alguna vez se bloqueo y se reabrio legitimamente queda sin poder llegar a DONE, en silencio, hasta que alguien edite el archivo de estado a mano -- o sea, la salida es precisamente la que el modelo file-first existe para impedir. El arreglo es una linea: que done_ready filtre por blockers sin resolved_at, igual que summarize_feature. Ninguna feature viva esta hoy en ese estado, asi que la deuda no bloquea nada todavia.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
