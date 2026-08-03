# ADR-0023 — Bounded repair: a line-count ceiling frozen once per cycle, tied to the existing retry budget

- Estado: Accepted (2026-08-03). Continuación del estudio de RDD de `gentle-ai` (ver ADR-0020 para el
  contexto compartido); esta pieza específica corresponde a la decisión de producto "Techo de reparación"
  confirmada por el usuario.

## Contexto

gentle-ai limita cada corrección a `min(200, ceil(original_changed_lines/2))` y permite exactamente un intento
antes de escalar a un estado terminal `escalated` (recuperación manual explícita, nunca un segundo intento
silencioso). SET-AGENTES ya tiene "máximo dos ciclos de deep review por paquete" pero ningún techo de líneas
dentro de un ciclo — un repair podría, en teoría, reescribir mucho más de lo que el finding pedía sin que nada
lo marque. El usuario confirmó sumar un techo de líneas, atado al presupuesto de ciclos ya existente (no un
mecanismo nuevo y paralelo).

`ai/scripts/feature_state_lib/candidate_identity.py` (ADR-0020) y `classify-risk.py` (ADR-0021) ya existen,
así que este techo reusa el mismo dato — `candidate_identity.changed_lines` — como línea base de "qué tan
grande era lo que había que reparar", sin volver a congelar nada por separado.

## Decisión

1. **Fórmula**: `cap = {"small": 40, "medium": 100, "high": 200}[package.complexity]` (con `100` como default
   defensivo si `complexity` no está seteado — no debería pasar, pero no es motivo para fallar duro en una
   ceremonia adicional); `budget_lines = min(cap, ceil(original_changed_lines / 2))`. `original_changed_lines`
   viene de `candidate_identity.changed_lines`, congelado en `PACKAGE_GATES` antes del panel (ADR-0020/0021),
   nunca vuelto a medir por cada intento de repair.
2. **Dónde se congela**: la primera vez que `record-repair` corre en un ciclo dado
   (`package.get("repair_ceiling") is None`), dentro de `cmd_record_repair`
   (`ai/scripts/feature_state_lib/cli_repair.py`) — no en cada uno de los 5-6 puntos de entrada a
   `PACKAGE_REPAIR` (review, delta review, testing, runtime QA, transición manual) que ADR-0009's D8 ya
   enumera. Es una simplificación deliberada respecto al diseño original: el techo solo importa cuando
   `repair-agent` efectivamente produce un diff, así que un único punto de congelado —dentro del comando que
   ya recibe la evidencia del repair— es más simple y menos invasivo que instrumentar cada entry point, sin
   perder la propiedad de "se congela una sola vez por ciclo". Si `candidate_identity` no existe todavía
   (`freeze-candidate` nunca corrió para este paquete), NO se congela ningún techo — el mecanismo es aditivo,
   nunca retroactivo.
3. **Enforcement**: nuevo `ai/scripts/check-repair-ceiling.py` (twin en `PROYECTO/`, hermano estructural de
   `check-owned-paths.py`: mismo shape de argumentos, misma convención `git diff --numstat <baseline>` contra
   el working tree, mismo patrón `*_PASS`/`*_FAIL` + exit 0/2). `gate-runner` lo corre después del pase de
   `repair-agent` y antes de `delta-reviewer`, registrado vía el verbo `record-gate --name repair-ceiling
   --status pass|fail` ya existente — sin verbo CLI nuevo.
4. **Interacción con el presupuesto de 2 ciclos**: `cmd_record_gate` especial-casea `--name repair-ceiling
   --status fail` para llamar `block_with_reason` INMEDIATAMENTE, sin pasar por el acumulador genérico de
   3-strikes de `gate_failures` (ese acumulador es para fallas de gate reintentables; una violación del techo
   en el único repair permitido no lo es, por diseño — mismo principio que gentle-ai llama "ordinary lineage
   admits exactly one correction"). `BLOCKED` ya es la fase que se reporta como `HUMAN_DECISION_REQUIRED` — no
   hace falta vocabulario de bloqueo nuevo.
5. `record-repair` gana un `--changed-lines <N>` opcional (bookkeeping, nunca obligatorio — no puede romper
   los 600+ tests existentes que llaman `record-repair` sin él) que guarda `repairs[i].changed_lines` — el
   campo que la ADR-0020/PKG-01's chequeo estático de `validate_state` ya esperaba. `check-repair-ceiling.py`
   NUNCA confía en este valor autoreportado por defecto: remide desde git independientemente, salvo que se le
   pase `--changed-lines` explícitamente (solo para tests).
6. `repair-agent.md` gana una quinta condición de stop: el diff de repair excede
   `repair_ceiling.budget_lines` → `BLOCKED`, nunca un segundo intento silencioso.

## Rejected alternatives

- **Congelar el techo en cada uno de los 5-6 entry points a `PACKAGE_REPAIR`.** Más fiel a "en el momento en
  que se entra a reparar", pero significativamente más invasivo (toca `cli_review.py`, `cli_repair.py` dos
  veces más, y la transición manual en `cli_lifecycle.py`) para el mismo resultado observable, dado que nada
  puede violar el techo hasta que `record-repair` corre de todos modos.
- **Que `check-repair-ceiling.py` pueda fallar el gate de forma reintentable (como `gate_failures`).** Rechazado:
  el techo modela exactamente el "un solo intento" que gentle-ai ya probó — permitir reintentos lo convertiría
  en un límite blando, no un techo.
- **Requerir `--changed-lines` en `record-repair`.** Rechazado: hubiera roto la compatibilidad con las
  llamadas existentes de `record-repair` en la suite de 600+ tests inmutable.

## Consecuencias

- El techo reusa `candidate_identity.changed_lines` (ADR-0020) como única fuente de "tamaño original" — cero
  medición nueva, cero freeze paralelo.
- La aplicación real (el gate que puede bloquear el paquete) vive en un script determinístico, nunca en
  juicio de agente — mismo principio que `check-owned-paths.py` ya establece para ownership.
- Un paquete que nunca declaró `candidate_identity` (porque el freeze aún no corrió, p.ej. durante la
  transición mientras esta feature se adopta gradualmente) no se ve afectado — el mecanismo es aditivo.
