# Context pack — P1-digest-no-esconde (ADR-0040)

Spec: `docs/specs/020-honest-dashboard/spec.md`, **AC-01..AC-05 y AC-12**.

## El defecto, reproducible en un comando

```bash
python3 ai/scripts/feature-state.py digest
grep -n "002-adaptive\|011-quota" docs/notas/BUENOS-DIAS.md   # ← no aparecen
```

`002-adaptive-pi-orchestration` está bloqueada desde el **2026-07-24** y
`011-quota-failover` desde el **2026-07-30**, las dos con `HUMAN_DECISION_REQUIRED`. El
informe que Federico lee todas las mañanas **no las nombra**. Y `006-execution-graph` y
`010-spawn-provenance` figuran como trabajo en curso sin ninguna señal de llevar nueve días
sin moverse.

Causa, en dos lugares distintos que reimplementan la misma idea:

- `ai/scripts/feature_state_lib/cli_reporting.py:194` — `active = [d for d in states if not d.get("final_state")]`
- `ai/scripts/feature-state.py`, `_hub_body` (~`:199`) — `if data.get("final_state"): continue`

`block_with_reason` (`cli_lifecycle.py:396-402`) setea `final_state = "BLOCKED"`, así que una
feature bloqueada no es "activa" para ninguno de los dos. Y `_pending_bits`
(`render_notes.py:143-163`) **ya sabe** renderizar la línea `⛔ bloqueo:` — simplemente
nunca la llaman con esas features.

`TERMINAL = {"DONE", "BLOCKED"}` (`model.py:51`) es el único lugar donde se asigna
`final_state`: es un enum cerrado, no hay un tercer valor que temer.

## AC-02 es el corazón: un predicado, no tres copias

El defecto se duplicó **porque no había un solo lugar**. Escribí el predicado una vez
(feature viva = `final_state != "DONE"`) más la constante del umbral, y que lo consuman los
tres artefactos: `cmd_digest`, `_hub_body` y `cmd_status`. Si terminás con la condición
escrita dos veces, reprodujiste el bug que viniste a arreglar.

Elegí bien dónde vive: `feature_state_lib/` tiene un grafo de imports cuidado (mirá el
docstring de `cli_integration.py:1-13`, que documenta un ciclo que evitaron a propósito).

## Los AC, con sus trampas

- **AC-01** — sección `## Necesita tu decisión` **antes** de "Qué quedó listo". Los días se
  cuentan desde el `at` del **último blocker sin `resolved_at`**, no desde `updated_at`:
  `002` tiene dos entradas en `blockers[]`, una ya resuelta. Sección **fija**: si no hay
  nada, lo dice. Una sección que aparece y desaparece se lee como ruido.
- **AC-03** — las bloqueadas quedan **exentas** de la marca de estancadas. Con AC-02
  ampliando el conjunto, `002` y `011` aparecerían en "Necesita tu decisión", en "Qué se
  está haciendo" con la marca, y en "Qué falta" con el `⛔`: cuatro menciones de la misma
  cosa en un informe de ocho líneas. **Tope: dos** — el titular y el bit accionable.
- **AC-04** — `cmd_status` (`cli_lifecycle.py:188`) hoy es por-feature y vuelca el JSON
  crudo. Sumale `blocked_days` y `stale_days` calculados con **el mismo** predicado y la
  **misma** constante. No inventes un agregado global que no existe.
- **AC-12** — `_hub_body` / `docs/notas/00 - Proyecto.md`. Hoy `002` y `011` **sí** figuran
  en "## Features" con etiqueta `BLOCKED`, pero **no** en "## Qué falta". Ese es el bug.
- **AC-05 y AC-12** piden tests que **fallen en rojo contra el código de hoy**. Escribilos
  primero y verificá el rojo antes de tocar el render — si pasan contra el código actual,
  no están probando el defecto.

## Restricciones

- **ADR-0040 primero** (`ls docs/adr/` para confirmar que `0040` está libre, indexalo en
  `docs/adr/README.md`). Documentá el predicado compartido y por qué el umbral es una
  constante única. Es el único punto donde esta feature se aparta del "ADR antes que
  código" en un detalle: el ADR fija el diseño, la implementación lo concreta.
- **`./build.sh` obligatorio** tras tocar `feature_state_lib/`: hay copias byte-idénticas en
  los 4 árboles de `Global/` y en `PROYECTO/`, y un test pinea esa igualdad. Después
  `./build.sh --check`.
- `tests/test_harness.py` assertea secciones del digest **por grep**: `grep -n` antes de
  mover o renombrar una sección existente.
- El render **nunca** puede romper una mutación de estado: contrato never-raises de
  `render_notes.py:281-285` con `RENDER_FAILURE_LOG`.
- Sin refactors oportunistas.

## Limitaciones a respetar, no a resolver

El schema no distingue una feature pausada a propósito de una estancada por accidente:
`006` y `010` esperan un impacto de módulo y van a quedar marcadas igual. Para una feature
sobre honestidad, sobre-marcar es el default seguro. **No inventes un campo de "pausada"**:
está fuera de alcance.

## Validación local

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**; base **917 OK / 3
skips**, el conteo sube y nunca baja) · `./ai/scripts/verify.sh` → `VERIFY_PASS` ·
`./build.sh` y después `./build.sh --check` sin drift · `git diff --check` limpio.

Correr `tests.test_harness` **aislado** produce ~72 errores `KeyError: 'set_agents_app'`
preexistentes; usá `discover` o `verify.sh`.

Prueba viva que va como evidencia:

```bash
python3 ai/scripts/feature-state.py digest
grep -n "002-adaptive\|011-quota\|Necesita tu decisión" docs/notas/BUENOS-DIAS.md
grep -n "002-adaptive\|011-quota" "docs/notas/00 - Proyecto.md"
```

## Advertencia de proceso (leela, no es genérica)

La feature anterior acumuló **cuatro afirmaciones de verificación fabricadas**, y el último
review agregó un matiz: hubo transcripciones **anotadas** —con cabeceras que el comando
pegado nunca imprime, o salidas recortadas— que parecían literales sin serlo. Está en
`ai/state/decisions-log.jsonl`. **Cada bloque que pegues es literal, o está marcado como
recortado.** Si no lo corriste, escribí "sin verificar".

Y apareció **un test decorativo por paquete** en tres de los cinco paquetes de 019. Por cada
test nuevo: neutralizá el cambio, confirmá el rojo, revertí, y pegá esa prueba.

## Evidencia esperada

`docs/specs/020-honest-dashboard/evidence/P1-implementer.md`: tabla AC → cambio
(`archivo:línea`) → prueba; el digest **antes y después** con `002` y `011` apareciendo; el
hub antes y después; la prueba de mordida por test; y los gates pegados.

## Checkpoint

Murieron tres instancias por stall en la sesión anterior. Escribí la evidencia desde el
primer minuto y guardá a disco a medida que avanzás.

## Fuera de alcance

Resolver los blockers de `002` y `011` (hacerlos visibles es otra cosa) · el verificador de
anclas (P2) · el schema de `docs/modules/` y la partición de ADR-0036 · convertir nada en
gate bloqueante · routing, tools discovery y todo lo de 019.
