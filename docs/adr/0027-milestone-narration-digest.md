# ADR-0027 — Narración por hito, digest matinal generado, notas como entrada

- Estado: Accepted (2026-08-04). Feature 017. Tercera de cinco (0025-0029).

## Contexto

La narración Cliente/Ingeniería era por-spawn (2 bloques por spawn + 1 por turno) en TODOS los modos,
sin ningún dial — hasta ~25 bloques por paquete en modo feature. El "café de la mañana"
(`docs/notas/BUENOS-DIAS.md`) existía pero era artesanal: ya se desactualizó dos veces y su corrección
costó dos ACs de dos features distintas, cuando todos los datos para generarlo viven en
`narrative-log.jsonl` / `decisions-log.jsonl` / `quickfix-log.jsonl` / `history[]` con timestamps ISO.
Y las notas Obsidian eran write-only: ningún agente las leía al arrancar (la única lectura, `set-agents
--context`, estaba gateada en tener un vault linkeado).

## Decisión

1. **Narración por hito**: bloques Cliente/Ingeniería solo en inicio de feature/paquete, resultado de
   review/delta, hallazgo inesperado o bloqueo, cierre de paquete/feature, y cierre de turno. Los spawns
   intermedios persisten igual (`record-spawn` al JSONL) pero sin bloque en chat. Quick-fix: un bloque al
   cierre. La transparencia no se pierde: se muda del chat al log, y el chat queda para lo que un cliente
   de verdad quiere leer.
2. **`feature-state.py digest [--since <ISO>|ayer]`**: regenera `docs/notas/BUENOS-DIAS.md` entre
   marcadores `notas:auto` (texto humano preservado vía `merge_note()`), con: qué quedó listo / qué se
   está haciendo / qué falta / decisiones nuevas / cola de trabajo. El digest deja de poder pudrirse:
   siempre es derivado de estado.
3. **Hub honesto**: `_pending_bits()` distingue "próximo paso automático" de "pendiente real" — una
   feature en fase terminal-por-diseño no lista pendientes fantasma.
4. **Notas como entrada**: `resume-feature` lee además la nota de feature (`## Approach y decisiones`) y
   la bitácora; el orquestador al abrir sesión lee `docs/notas/00 - Proyecto.md ## Qué falta` SIN exigir
   vault (el vault sigue sumando contexto de negocio cuando está).

## Rejected alternatives

- **Dial de verbosidad configurable (verbose/hitos/quiet)**: más superficie de config que mantener,
  contra la visión "cero configuración"; el nivel por-hito es el punto que el dueño pidió.
- **Digest como cron**: el comando idempotente alcanza; quien quiera cron lo agrega por fuera.

## Consecuencias

- El consumo de tokens de narración baja ~4x en modo feature sin perder trazabilidad (el JSONL es el
  registro completo; el chat, el resumen ejecutivo).
- `BUENOS-DIAS.md` pasa a régimen `notas:auto`: la sección generada es máquina-owned, las enmiendas
  humanas viven fuera de los marcadores.
