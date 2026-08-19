# ADR-0061 — Techo frontier aparte de `attempts.spawns`

- Estado: **Accepted** (2026-08-19). Feature `034-cuota-organica-y-writer-barato`, PKG-C.
  Aprobado con el Feature Contract (hash `539a4ff6b58b9ca67df9342dddcc79783660dcac73ce987a5da58ce136bd9721`).
- No supersede `MODE_BUDGETS`. Enmienda ADR-0039 **en parte**: el vocabulario
  cerrado de `block_with_reason.counter.scope` gana un tercer valor `frontier`.
- Precedencia DEC-PRECEDENCE-CEILING: el techo gana a salvage (ADR-0062) y a
  auto-promotion.

## Contexto

`MODE_BUDGETS.scoped.max_spawns_per_package == 8` (`feature_state_lib/model.py:123-128`)
cuenta **despachos**, no peso del modelo. 033 AC-6.4 hizo visible `usados/techo` de
ese 8. Un paquete puede quemar 8 spawns baratos o 8 frontier y el contador no
distingue. `record-spawn` incrementa `attempts.spawns` y bloquea contra
`max_spawns_per_package` (`feature-state.py:420-425`). `compact_package`
(`model.py:277-347`) no tiene campo de peso.

DEC-FRONTIER-CAP: 4 despachos pesados por paquete, 16 por feature. Chocar =
`HUMAN_DECISION_REQUIRED`. No se sube `max_spawns`. Auto-promotion o salvage que
exigirían un frontier con el cupo lleno: gana el techo.

`cost-report.py` Sección 2 (`:14-24`, `:417-448`) cuenta sesiones de `spawns[]` /
history `record-spawn`; no hay rollup por tier ni `% green-on-first-attempt`.

## Decisión

1. **Constantes fuera de `MODE_BUDGETS`:** `FRONTIER_CAP_PER_PACKAGE = 4`,
   `FRONTIER_CAP_PER_FEATURE = 16`. El dict por modo (`feature`/`scoped`/
   `quick-fix`/`incident`) queda byte-igual. Caps no se duplican en el JSON
   (evitar drift); status renderiza `used/cap` leyendo la constante.

2. **Campos aditivos (UNVERIFIED-en-árbol — no existen hoy; `.get()` default 0
   / `None`, precedente `spawns` en `model.py:303-306`):**
   - feature: `frontier_used: int`, `writer_promotion: {cheap_consecutive_failures, next_rung}`
     (`next_rung` default `"base"`, **nunca** `"fast"` — ADR-0060)
   - package: `frontier_used: int`, `salvage` (shape en ADR-0062), `writer_rung`,
     `cheap_strike_recorded` (latch del +1)
   - `risk_signal` vive en el feature (ADR-0064), no aquí.

3. **Clasificación en `record-spawn`, no un flag seteable.** Cuenta frontier
   cuando `--model` está presente, el modelo **no** es el default barato/free
   de ADR-0060, y el rol no es `local-gate-runner` / P001. Jueces pesados sí.
   Salvage sí. `--model` ausente: no incrementa (aditivo para callers viejos;
   doctrina ADR-0031: el orquestador pasa `--model`). No existe `--frontier`
   que el caller pueda mentir.

4. **Mutación solo por verbos existentes.** `record-spawn` incrementa y rechaza
   el 5º/17º con error nombrado `FRONTIER_CAP_EXHAUSTED` + `block_with_reason`.
   `record-gate` actualiza `cheap_consecutive_failures` **como máximo +1 por
   paquete** si el barato no fue green-on-first-attempt: latch
   `package.cheap_strike_recorded`. Si `package.salvage` **ya existe**, **no**
   incrementar de nuevo (el rojo del salvage no es un segundo fallo del barato;
   un solo paquete no puede producir 2 consecutivos). Reset del contador de
   feature solo en green-on-first-attempt (gate verde **y** `salvage is None`).
   Verde-después-del-salvage no resetea. `create-package` copia `next_rung`
   (`"base"` si ausente) a `package.writer_rung`. 2 consecutivos → próximo
   paquete `"balanced"` luego `"frontier"`. OpenCode: `@tier`
   (`generate.py:581-585`). Cursor: override de invocación, no `@tier`.
   `% green-on-first-attempt` se **deriva** en `cost-report.py`
   Sección 2 — no se persiste un porcentaje. Universo AC-C.6: salvage-verde no
   entra al numerador. Sección 1 y 2 no se suman.

5. **Precedencia:** el chequeo de techo corre **antes** de aceptar un salvage
   (ADR-0062) o un spawn del paquete promovido a no-barato. Cupo lleno → humano.

6. **`reopen` (ADR-0039):** tercer shape cerrado de `counter`:
   `{"scope": "frontier", "key": "used", "grain": "package"|"feature"}`.
   `frontier_used` **no** vive bajo `attempts` — esa fusión anularía el punto
   de este ADR. `_reset_blocker_counter` (`cli_lifecycle.py:473-487`) amplía el
   `scope not in {attempts, finding}` para admitir `frontier`. Un blocker sin
   `counter` sigue sin resetear nada.

## Opciones rechazadas

- **Subir `MODE_BUDGETS.scoped.max_spawns_per_package` de 8 a 12 (o “más
  despachos para que entren los jueces”).** Es exactamente el disfraz que 034
  prohíbe. El 8 cuenta volumen; el 4 cuenta peso.
- **Reusar `attempts.spawns` con un divisor o un peso.** Mezclaría dos
  presupuestos en un entero. `reopen` no sabría qué resetear.
- **Persistir el `% green-on-first-attempt` en el JSON.** Se stalea el momento
  que llega otro gate; el fixture salvage-verde lo corrompería en silencio.
  Se deriva al reportar.
- **Flag `--frontier` en `record-spawn`.** El caller puede mentir. La
  clasificación es del CLI contra el default barato medido.
- **Contar P001 / `local-gate-runner` como frontier.** 033 AC-6.2: no son
  modelo pesado.
- **Incrementar `cheap_consecutive_failures` en cada `record-gate` rojo,
  incluido el rojo del salvage.** Un paquete (barato rojo + salvage rojo)
  sumaría 2 y promovería el siguiente sin un segundo paquete. DEC-PROMOTE
  cuenta fallos **del barato**, máximo +1 por paquete; `salvage` ya existente
  no suma otra vez.
- **Default `next_rung` / `writer_tier` = `"fast"`.** `"fast"` es
  `MODEL_TIERS[0]` (`models_config.py:45`) y un agente OpenCode-only
  (`generate.py:581-585`). Feature nueva = `"base"`.
- **Eximir a los jueces del techo** (“el ahorro es el implementer”). 4/paquete
  deja reviewer + security + judge + salvage; el 5º para. Eximirlos vacía el
  cupo.

## Consecuencias

- Status / bitácora muestran `frontier_used/cap` al lado de `spawns used/techo`,
  dos columnas, dos presupuestos.
- Auto-promotion que convertiría al escritor en frontier con cupo lleno no
  arranca: humano. Feature nueva = rung `"base"`; no hereda `writer_promotion`.
- Schema JSON: campos nuevos ausentes en features viejas leen 0 / `None`.
  `validate_state` acepta ausencia; no backfill.

## Evidencia

`docs/specs/034-cuota-organica-y-writer-barato/design.md` §3.
`feature-state.py:420-425`, `model.py:123-128` y `:277-347`,
`cli_lifecycle.py:444-460`, `cost-report.py:14-24`.
