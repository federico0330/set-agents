# 020 — Tablero honesto: lo trabado no se esconde, las anclas no mienten

- **Estado**: aprobado por delegación explícita de Federico (2026-08-11, sesión nocturna).
  Sus palabras: *"si notas alguna otra mejora, la implementes (con su respectivo flujo de
  implementación) y la dejes documentada en un mensaje de buenos días"*. El orquestador
  acotó esa autorización a mejoras delimitadas y reversibles, con spec, gates y review
  independiente, sin cambios doctrinales de fondo.
- **Origen**: dos defectos encontrados con evidencia durante el cierre de 019, ninguno
  buscado a propósito.
- **ADR**: 0040 (tablero honesto y anclas verificables).

## El problema, en una frase

El harness produce dos artefactos que el humano lee para orientarse —el digest matinal y
`docs/modules/`— y **los dos pueden mentir sin que nada lo detecte**.

## Evidencia (medida, no supuesta)

### D-1 — El digest esconde exactamente lo que necesita al humano

`ai/scripts/feature_state_lib/cli_reporting.py:194`:

```python
active = [d for d in states if not d.get("final_state")]
```

`block_with_reason` (`cli_lifecycle.py:396-402`) setea `data["final_state"] = "BLOCKED"`. Por
lo tanto una feature bloqueada **no es `active`**, y como `_pending_bits` —que sí sabe
renderizar bloqueos (`render_notes.py:151-156`)— solo se llama sobre `active`, su línea
`⛔ bloqueo:` nunca se emite. Tampoco cuenta como cierre.

Verificado sobre `docs/notas/BUENOS-DIAS.md` generado el 2026-08-11:

| feature | estado | ¿aparece en el digest? |
|---|---|---|
| `002-adaptive-pi-orchestration` | `BLOCKED` desde **2026-07-24**, `HUMAN_DECISION_REQUIRED` | **no** |
| `011-quota-failover` | `BLOCKED` desde **2026-07-30**, `HUMAN_DECISION_REQUIRED` | **no** |
| `006-execution-graph` | `PACKAGE_ACCEPTED`, sin tocar desde **2026-08-02** | sí, como "se está haciendo" |
| `010-spawn-provenance` | `PACKAGE_ACCEPTED`, sin tocar desde **2026-08-02** | sí, como "se está haciendo" |

Dos features llevan tres semanas esperando una decisión del dueño y el informe que él lee
todas las mañanas no las nombra. Y las dos que sí aparecen figuran como trabajo en curso
sin ninguna señal de llevar nueve días sin moverse.

### D-2 — Las anclas `file:line` de `docs/modules/` derivan sin red

El integrator de 019, corriendo a mano el chequeo de staleness que `/explicar` promete,
encontró deriva real en las secciones sembradas:

- `docs/modules/consola.md` dice que `set_agents_app.py:2510` es `main()` → **corrida +742 líneas**.
- referencias a `generate.py` → corridas +9.
- `feature-state.py:788` → corrida +4.

Causa: P3 sembró esos puntos de entrada y P5 agregó ~880 líneas a los mismos archivos.
Ningún review de paquete podía verlo: cada uno miró su propio diff. Es exactamente el
riesgo que se aceptó al aprobar la desviación del schema de AC-17 (tres secciones
derivadas, cinco sembradas a mano), cuyo único mitigante registrado es que alguien corra
`/explicar`. Registrado en `ai/state/decisions-log.jsonl`, slug
`anclas-file-line-de-docs-modules-derivan-sin-red`.

## Objetivo

Que los dos artefactos **no puedan mentir en silencio**: lo trabado se grita, y un ancla
que ya no apunta a lo que dice es un fallo detectable por comando.

## Paquetes y criterios de aceptación

### PKG-1 — `P1-digest-no-esconde` (`estado` / `narracion-notas`)

- **AC-01**: el digest gana una sección **`## Necesita tu decisión`**, ANTES de "Qué quedó
  listo", que lista toda feature con un blocker sin resolver — **independientemente de su
  `final_state`** — con su `feature_id`, la razón acortada por `_short` y **hace cuántos
  días** está así. Los días se cuentan desde el `at` del **último blocker sin
  `resolved_at`**, nunca desde `updated_at` a ciegas (SC-07: `002` tiene dos entradas en
  `blockers[]`, una resuelta y una vigente). Si no hay ninguna, la sección dice que no hay
  nada pendiente; no se omite (una sección que aparece y desaparece se lee como ruido, una
  fija se lee como tablero).
- **AC-02**: **un solo predicado compartido** decide qué features siguen vivas, y los tres
  artefactos derivados lo consumen — nada de reimplementarlo por sitio. Hoy la misma lógica
  está escrita dos veces y las dos están mal: `cli_reporting.py:194`
  (`not d.get("final_state")`) y `feature-state.py` `_hub_body` (~`:199`,
  `if data.get("final_state"): continue`). El predicado excluye solo lo genuinamente
  terminado (`final_state == "DONE"`), de modo que `_pending_bits` —que ya sabe renderizar
  bloqueos— corra también sobre las bloqueadas. **Centralizarlo es el AC**, no un detalle
  de implementación: el defecto se duplicó justamente porque no había un solo lugar.
- **AC-03**: toda feature viva **no bloqueada** cuyo `updated_at` supere un umbral (**7
  días**, constante nombrada única, reutilizada por AC-01) se marca como estancada en "Qué
  se está haciendo", con los días. Las bloqueadas quedan **exentas** de esta marca: ya las
  cubre AC-01 con más detalle, y marcarlas además acá las nombraría cuatro veces en el
  mismo digest (SC-06), que es su propia forma de ruido. Tope de menciones por feature: dos
  — el titular de AC-01 y el bit accionable de "Qué falta".
- **AC-04**: `cmd_status` gana los campos calculados `blocked_days` y `stale_days`,
  derivados del **mismo** predicado y la **misma** constante que AC-01/AC-03 — no puede
  haber un comando que diga una verdad y otro que diga otra. (Reformulado por SC-04: la
  redacción anterior describía un agregado global que `cmd_status` no tiene, y no era
  verificable.)
- **AC-05**: test que **prueba el defecto**: un estado con una feature `BLOCKED` y otra
  `DONE`, y el digest tiene que nombrar la bloqueada. Debe fallar en rojo contra el
  `cli_reporting.py` de hoy.
- **AC-12**: el mismo test, contra `_hub_body`/`docs/notas/00 - Proyecto.md` (SC-05): hoy
  `002` y `011` figuran en "## Features" con etiqueta `BLOCKED` pero **están ausentes de
  "## Qué falta"**. Rojo contra el código de hoy.

### PKG-2 — `P2-anclas-verificables` (`narracion-notas`)

- **AC-06**: verificador de anclas — dado un `docs/modules/*.md`, extrae las referencias y
  reporta las que no existen o quedaron fuera de rango. **Dos formas, ambas cubiertas**
  (SC-02: en los docs de hoy hay ~20 de la primera y ~19 de la segunda, casi 1:1, así que
  cubrir solo la obvia daría `rc=0` verificando la mitad — una falsa seguridad, que es
  justo la clase de mentira que esta feature ataca):
  1. completa en un token — `render_notes.py:51`;
  2. abreviada — `` `:190` `` suelta, que se resuelve contra **el último archivo nombrado
     en el mismo ítem de lista o párrafo**. Una `` `:N` `` que no se pueda resolver así se
     reporta como **ancla no resoluble**, nunca se saltea en silencio.
  **Resolución del nombre de archivo** (SC-01, bloqueante): un ancla sin ruta completa se
  resuelve por basename **solo dentro de los `paths` del módulo que se está chequeando**
  (`modules.toml`, el mismo mecanismo de `render_modules.matching_modules`), **nunca** por
  búsqueda global — `feature_state_lib/*.py` está duplicado byte a byte en cinco árboles y
  una búsqueda global sería no determinística. Cero matches, o más de uno, dentro de esos
  `paths` es en sí mismo un ancla rota reportable.
  Un solo regex por forma, testeado contra los falsos positivos reales del repo:
  `localhost:8080`, `12:30`, `http://x:80`, un rango `10-20`.
- **AC-07**: comando `feature-state.py check-anchors [--module <slug>]`, read-only, que
  imprime cada ancla rota con su archivo, su línea y por qué. `rc=0` si están todas bien,
  `rc` distinto de cero si hay alguna rota — un chequeo que siempre devuelve cero no es un
  chequeo.
- **AC-08**: verificación **semántica acotada** (recortado por SC-03, que lo señaló como el
  candidato a "proyecto disfrazado"). Se verifica el símbolo **solo** cuando viene en
  backticks **inmediatamente adyacentes al ancla, en la misma línea** — el caso de
  `docs/modules/consola.md:26`, que es el defecto insignia (`set_agents_app.py:2510`
  diciendo ser `main()`, corrido +742). La verificación es una comparación de texto: el
  identificador aparece o no en la línea destino, con una ventana chica. **Explícitamente
  fuera**: rangos, comodines (`cmd_route_*`), y símbolos separados del ancla por prosa —
  esos reciben chequeo de rango y nada más. **Nada de parsear Python**: si el criterio no
  se puede expresar como comparación de texto determinista, el AC se recorta a chequeo de
  rango y se deja constancia.
- **AC-09**: `sync-notes` corre el verificador y **avisa** por stderr sin fallar la
  mutación — mismo contrato never-raises que `render_notes` (`ai/scripts/feature_state_lib/render_notes.py:281-285`,
  `RENDER_FAILURE_LOG`). Documentar y probar que un verificador roto nunca rompe una
  mutación de estado.
- **AC-10**: las anclas rotas **de hoy** quedan corregidas, y el comando lo prueba: `rc=0`
  sobre los cinco módulos sembrados.
- **AC-11**: test que **prueba el defecto**: un doc de módulo con `archivo.py:9999` y con un
  símbolo movido; el verificador tiene que reportar los dos.

## No-goals

- No se toca el schema de `docs/modules/` ni la partición máquina/humano de ADR-0036: las
  cinco secciones sembradas siguen siendo humanas. Este verificador es la red que faltaba,
  no un reemplazo de la partición.
- No se convierte `check-anchors` en gate bloqueante de ninguna fase. Avisa; no traba.
  Convertirlo en gate es una decisión de Federico, no del harness.
- No se resuelven los blockers de 002 ni de 011: se los hace visibles, que es otra cosa.
- No se toca routing, tools discovery ni nada de 019.

## Riesgos

1. `tests/test_harness.py` es una suite-contrato con frases pineadas por grep; el digest
   tiene tests que assertean sus secciones. Toda sección nueva o movida puede romper uno:
   `grep -n` antes.
2. El regex de anclas es el corazón de PKG-2: laxo produce ruido que hace ignorar el
   comando, estricto no detecta nada. Testear en ambas direcciones, con los falsos
   positivos nombrados en AC-06.
3. `feature_state_lib/` tiene copias byte-idénticas en los 4 árboles y en `PROYECTO/`:
   `./build.sh` obligatorio, drift verificado con `./build.sh --check`.
4. El umbral de estancamiento es una constante de producto: si es muy chico, todo parece
   estancado y la señal se pierde.

## Gates

Por paquete: `python3 -m unittest discover -s tests` en verde (**`pytest` no está
instalado**; base **917 OK / 3 skips**, el conteo sube y nunca baja), `./build.sh --check`
sin drift, ACs con evidencia `file:line`. Review independiente, findings estructurados,
repair consolidado, delta review.

## Limitaciones conocidas (documentadas, no escondidas)

- **El umbral de 7 días es un supuesto, no una verdad medida** (SC-10). Se elige por
  reversibilidad: constante única, cambiarla es una línea. Si resulta ruidoso, se sube.
- **El schema no distingue una feature pausada a propósito de una estancada por accidente**
  (SC-11). `006` y `010` esperan un impacto de módulo y van a quedar marcadas igual. Para
  una feature sobre honestidad, sobre-marcar es el default más seguro; queda nombrado, no
  escondido.
- **ADR-0040 se redacta junto con la implementación** (SC-08), no antes: es el único punto
  donde esta feature se aparta del "ADR antes que código", y se aparta porque el ADR
  describe decisiones de diseño (gramática de anclas, predicado compartido) que la
  implementación tiene que fijar primero.

## Criterio de cierre

`docs/notas/BUENOS-DIAS.md` regenerado nombra a `002` y `011` con sus días de bloqueo;
`docs/notas/00 - Proyecto.md` los nombra en "Qué falta"; `cmd_status` devuelve
`blocked_days` coherente con ambos; `check-anchors` devuelve `rc=0` sobre los cinco
módulos; y los tests de AC-05 y AC-12 fallan contra el código de hoy y pasan contra el
nuevo.
