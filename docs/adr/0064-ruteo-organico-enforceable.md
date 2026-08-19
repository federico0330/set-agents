# ADR-0064 — Ruteo orgánico enforceable: `init scoped|feature` exige `--risk-signal`

- Estado: **Accepted** (2026-08-19). Feature `034-cuota-organica-y-writer-barato`, PKG-A.
  Aprobado con el Feature Contract (hash `539a4ff6b58b9ca67df9342dddcc79783660dcac73ce987a5da58ce136bd9721`).
- Enmienda ADR-0020 **en parte**: el write-side que 0020 dejó en “mode
  selection” (decisión 3: no un umbral nuevo de archivos, sino el modo) pasa
  a ser un **guarda de CLI**. El número 3 como constante cruzada con
  `request-triage` no cambia. El read-side de 0020 (1–3 archivos el
  orquestador los lee; 4+ delega) no se toca.

## Contexto

ADR-0020 unificó el número 3 del lado de **lectura** (`orchestrator.md:24-41`)
y dijo explícitamente que el write-side ya estaba cubierto por mode
selection, no por un umbral nuevo. Esa mode selection **no se chequea**:

- Skill: quick-fix es el default de 1–3 archivos (`request-triage/SKILL.md:88-98`).
- La misma skill, tabla de presupuestos: `scoped (default)` (`:122`).
- CLI: `init --mode` default `"scoped"` con un comentario que asume que quien
  llega a `init` ya tiene señal de riesgo (`feature-state.py:875-878`).
- `cmd_init` (`cli_lifecycle.py:150-181`) no persiste ninguna señal.
- `log-quickfix` existe y es mandatorio en la skill (`feature-state.py:1194-1201`);
  no hay test que falle si un 1–3 se `init` como `scoped` sin señal.

Gentle `routing.go:46-58` (“File count … or perceived risk alone never
selects SDD”) se copia **como comportamiento** en una sola dirección: sin
señal nombrada, no hay ceremonia. SET **sí** deja que una señal de riesgo
nombrada seleccione `scoped`/`feature`. DEC-ORGANIC. 033 AC-6.1 (context pack)
no aplica a un quick-fix porque un quick-fix no crea paquete (AC-A.5).

Un LLM-judge sobre “¿esto se siente scoped?” no es observable ni mordible.

## Decisión

1. **El observable es el CLI, no un clasificador de intención.** Se confirma
   la propuesta del spec. Fixture de mordida: un trabajo de blast radius 1–3
   archivos (copy), sin señal de la lista cerrada, que corre `init --mode
   scoped` (o `feature`) **sin** `--risk-signal` → falla con
   `RISK_SIGNAL_REQUIRED` y no crea state válido. El test queda rojo si ese
   `init` es aceptado. No se parsea el diff con un modelo.

2. **`init` gana `--risk-signal TOKEN`, obligatorio cuando `--mode` ∈
   {`scoped`, `feature`}.** `incident` no (break-glass). `quick-fix` no. El
   default de `--mode` **sigue** `scoped` (`feature-state.py:878`): un `init`
   desnudo sin flag falla. No se cambia el default a `quick-fix` — eso
   crearía un state file y contradice AC-A.6 (el camino feliz de 1–3 sin
   señal es **no** inicializar; `log-quickfix` al cierre).

3. **Tokens cerrados** (lista de `request-triage/SKILL.md:73-75` + el token
   de producto):

   ```text
   RISK_SIGNAL_TOKENS = frozenset({
       "money-billing",
       "data-migration",
       "auth-pii",
       "public-contract",
       "multi-module",
       "user-asked-full-pipeline",
   })
   ```

   Desconocido → `RISK_SIGNAL_INVALID`. Persistido en el JSON de feature
   (`risk_signal`, UNVERIFIED-en-árbol) **solo** por este verbo. Un JSON
   editado a mano no es camino verde. 034 misma usa
   `user-asked-full-pipeline`.

4. **Doctrina unificada.** `request-triage` y `orchestrator.md` dicen una
   sola cosa: default operativo de 1–3 sin señal = quick-fix
   (`implement → gate → log-quickfix`). La tabla deja de llamar `scoped`
   “default” para ese caso. El 3 sigue cruzado con ADR-0020: cambiarlo en un
   lado obliga a revisitar el otro. `log-quickfix` conserva flags
   `:1194-1201`; no se vuelve opcional.

5. **Precedencia con 033 AC-6.1.** Quick-fix no crea paquete → context pack
   no aplica. Si el diff revela una señal, se escala con la señal nombrada
   (`init` con token) y a partir de ahí rige 033.

6. **Función pura mínima, no un segundo guarda.** `valid_risk_signal(token)
   -> bool` sobre el frozen-set. El test de mordida pega al CLI. No hay
   clasificador de blast-radius en `init` (el orquestador declara la señal;
   el file-count es doctrina, no argv). File count **nunca** fuerza `scoped`
   (Gentle: el conteo solo no selecciona SDD). Señal nombrada sí.

## Opciones rechazadas

- **LLM-judge / heurística de “se siente grande”.** No es testable; la skill
  ya lo prohibió. AC-A.2 exige un test que falle.
- **Clasificador que cuenta archivos del working tree y rechaza scoped si
  hay ≤3.** El universo es el blast radius **declarado** del trabajo, no
  “cualquier repo con tres archivos” (AC-A.6). Un `init` de 034 (muchos
  archivos, usuario pidió SDD) pasaría por señal, no por `wc -l`.
- **Cambiar el default de `--mode` a `quick-fix`.** Crearía feature state
  para el camino que debe no tenerlo.
- **Hacer `--mode` required (sin default).** Breaking change innecesario:
  default `scoped` + flag obligatorio ya corta el `init` accidental.
- **Exigir señal también en `incident`.** Break-glass; DEC-ORGANIC nombra
  `scoped`/`feature`.
- **Aflojar `log-quickfix` porque ahora hay guarda en `init`.** Son puertas
  distintas: uno evita ceremonia; el otro deja rastro cuando no hubo
  feature. AC-A.4.

## Consecuencias

- Un arreglo de copy de dos archivos no puede colarse a ceremonia sin
  nombrar una mentira (`--risk-signal` falso). La mentira queda persistida
  y es auditable — peor para el operador que para el guarda, que es el punto.
- ADR-0020 read-side intacto. Write-side por fin tiene el mismo número **y**
  un test.
- 033 no se reabre: el context pack sigue siendo de paquetes.

## Evidencia

`docs/specs/034-cuota-organica-y-writer-barato/design.md` §5.
`feature-state.py:875-878`, `:1194-1201`.
`cli_lifecycle.py:150-181`.
`Global/_canonical/skills/request-triage/SKILL.md:73-75, 88-98, 122`.
`Global/_canonical/agents/orchestrator.md:24-41`.
ADR-0020 decisión 3.
