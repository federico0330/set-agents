# ADR-0062 — Salvage único por paquete; convive con el techo de líneas (0023)

- Estado: **Accepted** (2026-08-19). Feature `034-cuota-organica-y-writer-barato`, PKG-B.
  Aprobado con el Feature Contract (hash `539a4ff6b58b9ca67df9342dddcc79783660dcac73ce987a5da58ce136bd9721`).
- **No reemplaza** ADR-0023 (techo de líneas de repair, `check-repair-ceiling.py`).
  Conviven. Tampoco es ADR-0011 D2 (relaunch por plan/cuota exhausted).

## Contexto

Hoy la doctrina dice un `repair-agent` consolidado por fase
(`orchestrator.md:523-524`) y ADR-0023 limita **cuántas líneas** puede tocar ese
repair (`cap` por complejidad, freeze en `record-repair`, gate
`check-repair-ceiling.py`; un breach no es reintentable —
`cli_repair.py:36-41`). No hay política de “una escalada de **modelo** si el
escritor barato falló el gate”.

DEC-SALVAGE: una instancia de repair/modelo pesado **por paquete** si el
implementer-barato falla el gate. Segunda falla = `HUMAN_DECISION_REQUIRED`.
DEC-PRECEDENCE-CEILING: si ese salvage sería frontier y el cupo está lleno,
gana el techo (ADR-0061).

ADR-0011 D2 ya da un relaunch por agotamiento de cuota, otro modelo, una vez
por assignment. No es un gate rojo. Mezclarlos duplicaría “segundas chances”
sin nombrar cuál presupuesto se gasta.

## Decisión

1. **Un salvage por paquete, persistido.** Si el implementer-barato deja el
   gate de paquete rojo, hay exactamente un despacho en modelo pesado:
   `repair-agent` u otra mutante fresca. `record-spawn --salvage` escribe
   (UNVERIFIED-en-árbol):

   ```text
   package.salvage = {spawn_id, role, model, at}
   ```

   Un segundo `--salvage` en el mismo paquete → `SALVAGE_ALREADY_USED` y
   `block_with_reason` (`HUMAN_DECISION_REQUIRED`). Dos repairs en paralelo
   contra el mismo gate no son salvage legal.

2. **Ese salvage cuenta como frontier** (ADR-0061 AC-C.2). El techo se chequea
   **antes** de aceptarlo. Cupo lleno → no hay salvage automático.

3. **Convive con ADR-0023.** El techo de líneas sigue congelándose en
   `record-repair` y aplicándose con `check-repair-ceiling.py` sobre el diff
   del ciclo de `PACKAGE_REPAIR` post-panel. El salvage de 034 es una
   escalada de **modelo** ante gate rojo del escritor barato (típicamente en
   `PACKAGE_GATES` / re-implementación), no un permiso para reescribir más
   líneas. Un paquete puede tener **ambos**: salvage durante gates, y más
   tarde un repair acotado por líneas después del panel. Ni el uno libera al
   otro.

4. **No es D2.** Un relaunch por plan exhausted (ADR-0011 D2) no se contabiliza
   como salvage ni como segundo salvage: otro presupuesto, otra causa (no
   hubo gate rojo), tope propio de uno. El test de ciclo de paquete distingue
   los dos.

5. **Green-on-first-attempt** (ADR-0061): un gate que queda verde **después**
   del salvage entra al denominador y **no** al numerador. El flag
   `package.salvage` es la prueba; no hay un booleano `first_attempt` aparte
   que se pueda mentir.

6. **Modelo pesado — override, no pin.** En lanes con `--route-decide`:
   `model_request` efímero (ADR-0044 P2) al frontier de la escalera,
   **después** de las exclusiones duras. En Cursor: el frontmatter de
   `repair-agent` **es barato** (AC-D.1, todo `code-rw`). El pesado es
   override de invocación (V-D03). Si V-D03 no da override:
   `HUMAN_DECISION_REQUIRED`. **No** hay excepción que pinnee `repair-agent`
   pesado en `~/.cursor/agents/repair-agent.md`.

7. **El rojo del salvage no incrementa `cheap_consecutive_failures` otra vez**
   (ADR-0061): si `package.salvage` ya existe, `record-gate` no suma un segundo
   strike del barato. Máximo +1 por paquete.

## Opciones rechazadas

- **Reemplazar ADR-0023 con “un solo salvage de modelo”.** 0023 cubre el
  tamaño del diff; 034 cubre el peso del modelo. Un salvage pesado que
  reescribe 800 líneas seguiría violando 0023 — y debe seguir haciéndolo.
- **N salvages automáticos hasta que el gate cierre, con el techo de líneas
  como único freno.** Cascada de cuota, exactamente lo que DEC-SALVAGE corta.
- **Contar D2 como el salvage.** Un writer que se quedó sin plan y uno que
  entregó un gate rojo no son el mismo evento. Fusionarlos gasta el único
  salvage en un exhaustion y deja el gate rojo sin escalada legal.
- **Salvage que no cuenta frontier** (“es recuperación, no lujo”). El modelo
  es pesado; el cupo existe para eso. DEC-PRECEDENCE-CEILING.
- **Pinnear `repair-agent` pesado en el frontmatter Cursor “si no hay
  override”.** Viola AC-D.1 (todo `code-rw` pinnea barato). El fallback es
  `HUMAN_DECISION_REQUIRED` (V-D03), no un pin que haría pesado también un
  despacho que no es salvage.
- **Verbo CLI nuevo `record-salvage`.** Más superficie de mutación. Un flag
  en `record-spawn` (el spawn **es** el salvage) alcanza, igual que
  `--changed-lines` aditivo en `record-repair` (0023 decisión 5).

## Consecuencias

- El orquestador tiene una regla de parada observable: 1 pesado, 2º rojo =
  humano. No hay `_salvage2`.
- `package.salvage` ausente en features viejas = `None` = no hubo salvage.
- Repair-ceiling, spawn budget y frontier cap siguen siendo tres puertas
  distintas; un test por puerta.

## Evidencia

`docs/specs/034-cuota-organica-y-writer-barato/design.md` §2.
ADR-0023, ADR-0011 D2, `orchestrator.md:523-524`, `cli_repair.py:36-41`.
