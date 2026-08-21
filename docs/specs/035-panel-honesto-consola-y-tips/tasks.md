# 035 — Tareas

> Orden de ejecución. Cada tarea nombra su AC, su paquete candidato, su validación local
> y el checkpoint de riesgo cuando lo tiene. Los IDs de paquete son **candidatos**: el
> `package-planner` los confirma o reagrupa después de `USER_APPROVAL`.

**Paquetes candidatos:** PKG-A (panel honesto, CLI de estado) · PKG-B (extraer
routing/vault de la consola) · PKG-C (TIPS-USO + puntero desde COMO-FUNCIONA).

**Rutas por paquete (hint de `owned_paths`, disjuntas a propósito):**

> **Revisión post-challenge (2026-08-20).** Incorpora los siete hallazgos
> `F-035-001..007`. DEC-DOOR y el recorte de `record-repair --skip-delta` no se relitigan.
> **La primera tarea sigue siendo T-001** — con su alcance corregido: audita y **reporta**
> todas las puertas, pero este slice solo **cierra** `record-review`.

| paquete | escribe | espeja / regenera |
|---|---|---|
| PKG-A | `ai/scripts/feature_state_lib/**`, `ai/scripts/feature-state.py`, `tests/test_harness.py`, **`Global/_canonical/agents/orchestrator.md`**, **`docs/adr/<nuevo>.md`** (F-035-001) | `PROYECTO/ai/scripts/**` (`build.sh:69-79`), `Global/*/hooks/feature_state_lib` **y** `Global/*/agents/orchestrator.md` (`generate.py:667`) — `generate.py` **no** se modifica |
| PKG-B | `ai/scripts/set_agents_app.py`, `ai/scripts/routing_cli.py`, `ai/scripts/vault_ops.py`, módulos nuevos en `ai/scripts/`, `tests/test_routing.py` | nada (`set_agents_app.py` **no** vive en `PROYECTO/`, verificado con `rg`) |
| PKG-C | `TIPS-USO.md`, `docs/COMO-FUNCIONA.md`, `README.md` (una línea condicional) | nada |

---

## PKG-A — Panel honesto

### T-001 · Auditar todas las puertas hacia `PACKAGE_TESTING` (y reportar, no cerrarlas todas)
- **AC:** AC-A.5 (y habilita AC-A.4).
- **Qué:** enumerar cada verbo/transición que puede dejar un paquete en `PACKAGE_TESTING`
  y decir, por cada uno, si chequea `has_open_findings`. Ya medido en el contrato:
  `finalize-review-panel` **sí** (`cli_review.py:158-160`); `record-delta-review` **sí**
  (lo afirma el comentario de `transitions.py:103`); `record-review` **no**
  (`cli_review.py:54-56`) — es la que se cierra acá; **`record-repair --skip-delta` no**
  (`cli_repair.py:246-253` mira solo los findings **reparados**, `:280-282` pone la fase)
  — queda **fuera** (no-goal 12). **Sin verificar:** si existe una `transition` directa.
- **Alcance corregido (F-035-002 / F-035-003):** el entregable es la **tabla**, no el
  cierre de todas las puertas. Esa tabla es lo que le da al comentario de T-007 una puerta
  real que nombrar en vez de una inventada.
- **Validación local:** lectura + `rg`; el resultado es una tabla en la evidencia del
  paquete, no código.
- **Dueño sugerido:** `architect` (es una decisión de dónde vive el invariante).
- **Checkpoint de riesgo:** si la auditoría encuentra una puerta **no prevista** (algo
  distinto de `skip-delta`, p. ej. una `transition` directa), **para y lo dice** antes de
  escribir el guarda. Un guarda instalado solo en la puerta que motivó el AC es el defecto
  que `require_verified` (`cli_review.py:278-284`) documenta en su docstring — y la
  mitigación acá no es cerrarlas todas de prepo, es que el comentario de `transitions.py`
  **no mienta** sobre cuáles quedan.

### T-002 · Predicado de panel requerido, tolerante a las tres formas de ausencia
- **AC:** AC-A.3 (habilita A.1). Cierra **F-035-005**.
- **Qué:** la resolución del panel de un paquete no lee `required_reviewers` a secas: lo
  re-deriva de `complexity` + riesgo resuelto (`resolve_package_risk`,
  `model.py:555-562`; `required_reviewers_for`, `model.py:565-575`), con fail-safe a FULL.
  Forma exacta (función nueva vs llamada en sitio): **UNVERIFIED**, decide architecture.
- **Medición que la tarea tiene que respetar** (re-medida 2026-08-20 sobre **76 paquetes**
  en 31 archivos de `ai/state/features/`): `required_reviewers` **ausente en 71**, poblado
  en 5, **`null` explícito en 0**; `complexity` ausente en 4. La forma real es la **clave
  ausente**, así que un predicado escrito contra `pkg["required_reviewers"] is None` no
  toca ni un paquete real.
- **Validación local:** **tres** tests unitarios contra state files escritos a mano — no
  generados por `create-package`, que sí persiste el campo (`cli_lifecycle.py:334`):
  (1) clave `required_reviewers` **ausente**; (2) `required_reviewers: null` explícito;
  (3) `complexity` ausente → **fail-safe FULL**, que se conserva.
- **Checkpoint:** acá es donde un fixture engaña, y el que engaña no es el que falta sino
  el que sobra: un test que cubra **solo** `null` pasa en verde sin tocar ninguno de los 76
  paquetes reales. Sin los tres casos, la tarea no está hecha.

### T-003 · `record-review` rechaza cuando el panel requerido es FULL
- **AC:** AC-A.1, AC-A.2.
- **Qué:** error nombrado `REVIEW_PANEL_REQUIRED`, con roles faltantes y el verbo
  correcto (`start-review-panel`). El rechazo **no** cobra un ciclo de deep review
  (hoy `cli_review.py:46` incrementa en cada llamada). Por DEC-DOOR el rechazo es del
  **verbo**: alcanza a los tres verdicts, no solo a `pass`.
- **Validación local:** test del rechazo en `medium` con `pass` **y** con
  `repair_required` (F-035-004: el segundo caso es el que tres sitios del golden suite
  ejercitan) + test de que `small`+`low` sigue pasando + test de que
  `deep_review_cycles` no se movió.

### T-004 · `record-review pass` rechaza con finding bloqueante abierto
- **AC:** AC-A.4. Cierra **F-035-002** y la parte de **F-035-004** que toca los verdicts.
- **Qué:** `BLOCKING_FINDING_OPEN`, mismo predicado y mismas severidades que
  `finalize-review-panel` (`cli_review.py:159`). En panel **SINGLE**,
  `repair_required`/`blocked` intactos; en panel **FULL** no aplica porque T-003 ya rechazó
  el verbo (precedencia escrita en AC-A.1). **El alcance es el verbo `record-review`**:
  `record-repair --skip-delta` no se toca (no-goal 12).
- **Validación local:** test del rechazo + test de que `repair_required` con findings
  abiertos en un paquete `small`+`low` sigue funcionando.

### T-005 · Reescribir las mordidas medidas del golden suite
- **AC:** AC-A.1, AC-A.4, AC-A.5, invariante 6 del spec. Cierra **F-035-003** y
  **F-035-004**.
- **Qué:** los **7** sitios enumerados en `acceptance.md` § Mordida de PKG-A. Los cinco de
  membresía (`:8580`, `:10170`, `:12399`, `:12451`, `:13006` — todos `--complexity medium`)
  pasan al camino del panel: `start-review-panel` + `record-subreview` ×2 +
  `finalize-review-panel`, conservando la aserción que cada test protege.
  Los dos de finding abierto:
  - `test_next_does_not_blame_a_late_review_that_never_happened`
    (`tests/test_harness.py:9024-9039`) **se parte en dos** tests coherentes, porque una
    sola reescritura no puede alcanzar el estado por `record-late-review` y a la vez seguir
    afirmando que ninguna late review ocurrió (F-035-003): (1) el rechazo por
    `record-review pass` con finding `high`, que **no menciona** late review en ninguna
    parte; (2) el advisor sobre un estado alcanzado por una puerta que **existe de verdad**
    (`record-repair --skip-delta`, o un `record-late-review` realmente corrido),
    conservando `assertIn("blocking finding", ...)` y `assertNotIn("late review", ...)`.
  - `test_accept_package_rejects_open_findings_and_bad_actors`
    (`tests/test_harness.py:11044-11054`): el `record-review pass --finding <high>` de
    `:11048` es **setup**, no la aserción. Se arma el mismo estado por una vía legal y se
    conservan las **dos** aserciones (`repair-agent cannot accept packages` y
    `critical/high findings`).
  - Todos los comentarios citan este spec.
- **Validación local:** cada test **rojo** antes del guarda y **verde** después, con la
  salida de las dos corridas en la evidencia. Un test que nunca se vio rojo no cuenta
  (patrón 034 AC-B.2).
- **Checkpoint:** ningún fixture baja su `complexity` de `medium` a `small` para esquivar
  el guarda. Eso convierte un test del camino FULL en uno del camino SINGLE: es pérdida de
  cobertura, no reescritura (no-goal 10).

### T-006 · Confirmar la enumeración contra la suite completa
- **AC:** AC-A.1, AC-A.4.
- **Qué (acotado por F-035-004):** ya **no** es "descubrir cuántos caen" — están contados.
  Re-medido el 2026-08-20: 31 apariciones del string, **25** como argumento citado, de las
  que 5 son entradas de `history`/`event` en fixtures (`:9514`, `:9530`, `:9636`,
  `:12234`, `:12739`) → **20 invocaciones reales del CLI**, de las cuales **7 caen** y
  **13 no** (clasificación completa en `acceptance.md`). Esta tarea corre la suite entera
  para confirmar esa tabla y detectar un caso que la clasificación **estática** no pudo
  ver: un fixture que mute `complexity` con `update-package` después de crear el paquete.
- **Validación local:** `tests/test_harness.py` verde entero, y la tabla de mordida
  confirmada o corregida en la evidencia.
- **Checkpoint:** si aparece un sitio afectado que no está en los 7 enumerados, se
  **registra** (la enumeración del contrato estaba incompleta) antes de reescribirlo. Si el
  total se vuelve un paquete propio, **para y lo dice** en vez de arrastrar un diff de test
  de 500 líneas dentro de PKG-A.

### T-007 · Retirar el comentario-deuda de `transitions.py`
- **AC:** AC-A.5. Cierra **F-035-003**.
- **Qué:** la frase "record-review is outside this package's criteria and every package
  in flight uses it" (`transitions.py:106-107`) no sobrevive. La rama `:96-109` **no** se
  borra **y no se declara inalcanzable**: su comentario nombra la puerta que de verdad
  queda —`record-repair --skip-delta`, `cli_repair.py:246-253` + `:280-282`— y cita la
  decisión que la difiere
  (`docs/notas/decisiones/2026-08-20 035-skip-delta-fuera-del-slice.md`).
- **Validación local:** `rg` de la frase retirada devuelve vacío, y el comentario nuevo
  nombra un `file:line` que existe.
- **Checkpoint:** declarar la rama inalcanzable cuando `skip-delta` la alcanza es peor que
  el comentario viejo. Si T-001 encontró además una `transition` directa, el comentario la
  nombra también.

### T-008 · Paridad de copias y regeneración
- **AC:** AC-A.7.
- **Qué:** `ai/scripts` ↔ `PROYECTO/ai/scripts` sin drift; `Global/*/hooks/feature_state_lib`
  regenerado.
- **Validación local:** `./build.sh --check` (`SELF_SCAFFOLD_DRIFT`, `build.sh:69-79`) +
  `ai/scripts/verify.sh`.
- **Checkpoint:** el golden suite corre el CLI **del template**
  (`tests/test_harness.py:32`). Un cambio solo en `ai/scripts/` no lo ve ningún test —
  esta tarea no es cosmética.

### T-009 · Verificar el histórico
- **AC:** AC-A.6.
- **Qué:** confirmar que las 27 features `DONE` y todo paquete `accepted`/`superseded`
  siguen validando, y dejar registrado el estado de los tres paquetes vivos afectados
  (032 `C1`, 011 `P1-quota-failover`, 002 `P1-routing-core`).
- **Validación local:** `verify.sh` + una lectura de los 31 archivos (76 paquetes).
- **Checkpoint de riesgo:** si el guarda quedó en un camino de validación que se
  re-ejecuta al leer un archivo histórico, **eso es un defecto**, no un efecto
  secundario aceptable.

### T-010 · ADR de contrato + doctrina de `orchestrator.md`
- **AC:** AC-A.9. Cierra **F-035-001**.
- **Qué:** tres piezas en el **mismo** paquete que el guarda:
  1. **ADR `Accepted`** que enmienda el contrato público de `record-review`: la firma no
     cambia; lo que se agrega son `REVIEW_PANEL_REQUIRED` (membresía, alcanza a los tres
     verdicts) y `BLOCKING_FINDING_OPEN` (`pass` con finding abierto), con `small`+`low`
     conservado como la puerta legítima. **Lo redacta `architect`** — producto declaró que
     entra en alcance y qué tiene que resolver, no su texto.
  2. **`Global/_canonical/agents/orchestrator.md` enmendado.** Hoy `:103` lista
     `record-review` entre los verbos del ciclo normal y `:105-108` presenta el panel como
     lo que se usa "when multiple specialist reviewers **are useful**" — opcional. Después:
     panel **obligatorio** con panel resuelto FULL, `record-review` descrito como la puerta
     de `small`+`low`.
  3. **Regeneración** de los cuatro árboles con el `copytree` que ya existe
     (`generate.py:667`). Las copias **no** se editan a mano y **`generate.py` no se
     modifica** (no-goal 13).
- **Dueño sugerido:** `architect` para el ADR y la redacción de la doctrina; el implementer
  corre la regeneración.
- **Validación local:** `rg` sobre `Global/*/agents/orchestrator.md` no encuentra la
  recomendación vieja; el ADR existe con estado `Accepted`; `./build.sh --check` verde.
- **Checkpoint:** un CLI que rechaza lo que su propia doctrina aconseja es peor que el gap
  original. Si esta tarea no cierra, PKG-A **no** cierra — no es documentación opcional.

---

## PKG-B — La consola partida

### T-101 · Caracterización previa del CLI, en tres canales
- **AC:** AC-B.1, AC-B.2. Cierra **F-035-007**.
- **Qué:** para el **set representativo** de combinaciones de `set_agents_app.py:4008-4154`
  —por grupo de la tabla de "Contratos públicos": una invocación válida, una con argumento
  faltante, una con valor inválido, más `--help` y la invocación sin argumentos— capturar
  `stdout` completo, `stderr` completo y **código de salida**, **antes** de mover una línea.
  Los tokens medidos (`APP_STATUS`, `VAULT_INIT_OK`/`VAULT_INIT_SKIP`, `VAULT_LINK_SKIP`,
  `VAULT_LINK_CONFLICT`, `TOOL`, `MCP`) quedan dentro de lo capturado; no son el criterio.
- **Dos entregables más, del mismo commit:**
  - **La lista de normalizadores, escrita antes de la primera comparación**: timestamps,
    rutas absolutas de `tmp`/`$HOME`, duraciones/latencias en ms, PIDs, versiones, orden no
    determinístico donde el comando no lo garantiza. Nada más.
  - **El plan de aislamiento** de flags mutantes (`--vault-init`, `--vault-link`,
    `--scaffold`, `--update`, `--tools-install`, `--mcp-add`/`--mcp-remove`,
    `--provider-add`/`--provider-remove`, `--plugin-on`/`--plugin-off`,
    `--model-pin-set`/`--model-pin-clear`, `--routing-migrate`, `--prune-dead`) y de las
    que tocan credenciales o red (`--provider-verify`, `--check-update`,
    `--quota-failover-e2e`, `--fresh-probes`): `HOME`/proyecto temporal desechable,
    `--dry-run` donde exista. **Ningún valor de secreto se registra** — solo presencia o
    ausencia. Una flag que no se pueda caracterizar sin efecto lateral **se declara así**.
- **Validación local:** el archivo de caracterización existe, tiene los tres canales, y
  está fechado antes del primer commit de movimiento.
- **Checkpoint:** una caracterización posterior al diff no es caracterización, y un
  normalizador agregado **después** de ver un diff es el diff escondiéndose: se registra
  como finding. Esta tarea **bloquea** T-103.

### T-102 · Decidir el techo real de la extracción
- **AC:** AC-B.4, AC-B.6, assumption 7 del spec.
- **Qué:** determinar si el `_import()` de `tests/test_harness.py:663-684` puede
  arreglarse estructuralmente (lo que desbloquearía mover casi todo) o si tocarlo es un
  cambio al contrato golden que necesita ACs propios. Ese resultado elige cuál de los
  dos cierres legales aplica.
- **Dueño sugerido:** `architect`.
- **Checkpoint de riesgo:** si la respuesta es "hay que tocar el helper de tests", eso
  **no** entra en este slice: se registra y PKG-B cierra por el camino (b) —residuo
  enumerado con razón.

### T-103 · Mover el residuo que se pueda mover
- **AC:** AC-B.3, AC-B.5, AC-B.7.
- **Qué:** mover, sin cambiar comportamiento, lo que T-102 habilite. Routing residual:
  `:550`, `:575`, `:586`, `:671`, `:794`, `:800`, `:833`, `:866`, `:874`, `:882`,
  `:3619`. Vault residual: `:2869`, `:2900`, `:2989`, `:3146`+, `vault_menu`.
- **Validación local:** `tests/test_routing.py` + `tests/test_harness.py` +
  `./build.sh --check`, **sin** cambios de color; y la comparación de los **tres** canales
  (`stdout`+`stderr`+exit) contra la caracterización de T-101, con los normalizadores que
  T-101 declaró y **ninguno** nuevo.
- **Checkpoint:** un bug encontrado al mover se registra como finding y se repara
  aparte (AC-B.3). Un normalizador nuevo también.

### T-104 · Matriz del residuo: comando → dependencia → experimento → resultado
- **AC:** AC-B.4, AC-B.6. Cierra **F-035-006**.
- **Qué:** una matriz nueva, **una fila por comando residual**, con cuatro columnas:
  `comando` → `dependencia concreta que lo ancla` (`PROJECT_KEY`, `PROJECT_ROOT`/`ROOT`,
  `ROUTING_WARNINGS`, `app_config`/`write_app_config`, o el `_import()` de
  `tests/test_harness.py:663-684`) → **`experimento o lectura hecha`** (el intento de mover
  y qué falló, o el `rg`/lectura que prueba el acoplamiento, con `file:line`) →
  `resultado` (movido / anclado).
- **Lo que NO cuenta:** citar lo que `routing_cli.py:1-31` y `vault_ops.py:1-23` ya dicen.
  Esos docstrings son el **formato** de la matriz, no su contenido; son documentación
  preexistente y no evidencia producida por este paquete. Sin la tercera columna, la fila no
  cierra.
- **Validación local:** lectura; cero comandos residuales huérfanos y cero filas con la
  tercera columna vacía.

### T-105 · Reportar el conteo
- **AC:** AC-B.6.
- **Qué:** `wc -l ai/scripts/set_agents_app.py` antes (4399, medido 2026-08-20) y
  después, como evidencia. **No** es una meta: nada de borrar comentarios o código
  muerto para bajar el número.

---

## PKG-C — TIPS al día

### T-201 · Corregir el control plane
- **AC:** AC-C.1.
- **Qué:** `TIPS-USO.md:5-14`. Se conserva la advertencia sobre Codex (`:12-14`).
- **Validación local:** lectura contra las mediciones citadas.

### T-202 · Corregir los inventarios
- **AC:** AC-C.2, AC-C.3.
- **Qué:** `:3`, `:45`, `:127-129` (agregar `cursor` y `pi`) y `:133-134` (cobertura de
  Cursor en `cost-report.py:20-23`, `:836-843`).
- **Validación local:** `ls Global/` y `rg -i cursor ai/scripts/cost-report.py` como
  contra-medición.

### T-203 · Cerrar el lazo con `COMO-FUNCIONA`
- **AC:** AC-C.4, AC-C.6.
- **Qué:** `docs/COMO-FUNCIONA.md:227-230` (deja de decir que TIPS está atrasado),
  `:439-448` (§11 apunta a este spec), `:221` (celda del control plane histórico) y
  `README.md:305` si quedó falsa.
- **Validación local:** `rg "control plane"` en los tres archivos: ninguna afirmación
  contradice a otra.
- **Checkpoint:** esta tarea y T-201 van en el **mismo** paquete. Separarlas produce la
  contradicción inversa.

### T-204 · Respetar el alcance cerrado
- **AC:** AC-C.5.
- **Qué:** no se toca "Required lifecycle" (`:117-121`), MCP (`:150-156`, incluida la
  mención de Engram) ni bootstrap (`:25-32`).
- **Validación local:** el diff de `TIPS-USO.md` no incluye esas líneas.

---

## Orden y dependencias

```
PKG-A:  T-001 ─▶ T-002 ─▶ T-003 ─┬─▶ T-005 ─▶ T-006 ─▶ T-007 ─▶ T-008 ─▶ T-009
                 T-004 ──────────┘                              │
                 T-010 (ADR + doctrina) ───────────────────────▶┘
                 (mismo paquete que el guarda; T-008 regenera los árboles)

PKG-B:  T-101 ─▶ T-102 ─▶ T-103 ─▶ T-104 ─▶ T-105
        (T-101 es un gate duro: bloquea T-103)

PKG-C:  T-201 ─┬─▶ T-203 ─▶ T-204
        T-202 ─┘
```

PKG-A no depende de B ni de C. PKG-B y PKG-C son independientes entre sí y de A: las
rutas son disjuntas (tabla de arriba). El planner puede paralelizarlos si el techo de
despachos lo permite (`MODE_BUDGETS`, `model.py:123-128` — no se sube).

**T-010 no es opcional ni posterior.** El ADR y la doctrina viajan en el mismo paquete que
el guarda (AC-A.9): entre T-003/T-004 y T-008, porque T-008 es el que regenera los árboles
donde vive la copia de `orchestrator.md`.

**Primera tarea a implementar: sigue siendo T-001.** No cambió con la revisión, cambió su
alcance: antes de escribir un guarda hay que saber cuántas puertas hay y, sobre todo, cuáles
este slice **no** cierra — porque de eso depende que el comentario de T-007 nombre una
puerta real (`record-repair --skip-delta`) en vez de declarar inalcanzable algo que no lo
es.
