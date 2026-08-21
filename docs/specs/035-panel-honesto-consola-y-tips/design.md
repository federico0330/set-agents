# 035 — Diseño (PKG-A · panel honesto · PKG-B · consola partida)

> `architect`, 2026-08-20. Feature `035-panel-honesto-consola-y-tips`, spec hash
> `296e051fccfd0cea2f222cc7061987f6b66507d9ed2b10539d7e58ea3169331c`.
> **§ 1-10 son PKG-A** (assumptions 1-3 y 5, `spec.md:530-552`). Contrato: **ADR-0065**.
> Auditoría de puertas: `evidence/PKG-A-doors.md`.
> **§ 11 es PKG-B** (assumptions 6, 7 y 9), agregado en un segundo pase de diseño sin tocar
> nada de PKG-A. Contrato: **ADR-0066**. PKG-C no se diseña acá.

**Baseline (`solution-baselines`): ninguna aplica** — no es una webapp de gestión, ni
scraping/ML, ni una API B2B, ni e-commerce: es el CLI de estado de un harness ya establecido.
Manda la convención del repo. Ejes **store / API Gateway / deploy: n/a**, ya registrados como
tales en el `axes_log` de la feature (`spec.md:13-15`); ADR-0065 lo reafirma y no abre ninguno.

---

## 1. Dónde vive el chequeo (assumption 1 — RESUELTA)

**En el verbo que muta, vía un resolver puro compartido. No en `package_accept_ready`.**

| capa | qué hace | por qué ahí |
|---|---|---|
| `model.py` | **resuelve** el panel (lectura pura, sin escribir estado) | el dominio ya tiene `required_reviewers_for` + `resolve_package_risk`; no se duplica la regla |
| `cli_review.py` | **rechaza** en `cmd_record_review` | DEC-LEGACY: la negativa dispara en el verbo que muta, nunca al validar un registro histórico |
| `package_accept_ready` (`model.py:800-827`) | **no se toca** | corre sobre registros ya escritos; instalar el chequeo ahí re-juzgaría paquetes cuyo review se registró legalmente antes del cambio (AC-A.6) |
| `check_transition` (`transitions.py:33-38`) | **no se toca** | ya exige `reviews[]` con verdict `pass`/`repair_required` (`:35-36`), y `reviews[]` tiene exactamente dos escritores — `cli_review.py:45` y `:147` — así que su cierre de membresía es **derivado** del de `record-review`, no un segundo agujero |

El patrón "un invariante se enforcea en CADA transición" del docstring de `require_verified`
(`cli_review.py:278-284`) es correcto para **findings** (un hecho presente) y equivocado para
**membresía de panel** (un hecho histórico). Esa distinción es la decisión, y está en ADR-0065
§ Opciones rechazadas.

## 2. Funciones que agrega el implementer (nombradas acá ⇒ dejan de ser UNVERIFIED)

Estas firmas son **el contrato del implementer**. Todo lo que sigue va en las **dos** copias,
línea por línea (`ai/scripts/**` y `PROYECTO/ai/scripts/**`, hoy idénticas — AC-A.7).

### `ai/scripts/feature_state_lib/model.py`

```python
BLOCKING_SEVERITIES = frozenset({"critical", "high", "medium"})

def resolved_required_reviewers(package: dict[str, Any]) -> list[str]: ...
```

- `BLOCKING_SEVERITIES`: constante única para el conjunto que AC-A.4 obliga a compartir.
  Se usa en el guarda nuevo **y** se sustituye el literal de `cli_review.py:159`. Sustitución
  literal-por-nombre, cero cambio de comportamiento, dentro del archivo que PKG-A ya posee:
  es lo que vuelve "mismas severidades" verificable con `rg` en vez de una afirmación.
  **No** se tocan las otras tres copias del set (`cli_repair.py:335`, `transitions.py:37`,
  `model.py:810-813`): están fuera del AC y editarlas sería refactor oportunista.
- `resolved_required_reviewers(package)`: devuelve `package["required_reviewers"]` **solo** si
  es una lista no vacía de strings no vacíos (`strip()`), deduplicada preservando orden; en
  cualquier otro caso —clave **ausente** (71/76), `null` explícito (0/76 hoy), lista vacía,
  ítems no-string— re-deriva con
  `required_reviewers_for(package.get("complexity"), resolve_package_risk(package))`.
  Fail-safe FULL con `complexity` ausente/`None` (`model.py:571`) **se conserva**.
  **Nunca escribe.** No llama a `persist_review_requirements` (`model.py:578-583`), que sí
  escribe `risk` y `required_reviewers`: una lectura que muta backfillearía 71 paquetes
  legacy como efecto lateral del camino ACEPTADO (`small`+`low`). Esa es la trampa concreta
  de esta función.

### `ai/scripts/feature_state_lib/cli_review.py`

```python
def require_review_panel(package: dict[str, Any]) -> None: ...          # REVIEW_PANEL_REQUIRED
def require_no_blocking_findings(package: dict[str, Any]) -> None: ...  # BLOCKING_FINDING_OPEN
def _roles_without_subreview(package: dict[str, Any], roles: list[str]) -> list[str]: ...
```

- `require_review_panel`: levanta `StateError` **si y solo si**
  `len(model.resolved_required_reviewers(package)) > 1`. La condición es el tamaño del panel
  resuelto, **no** "faltan roles": si dependiera de los roles faltantes, un paquete FULL con
  las dos subreviews cargadas y el panel sin cerrar podría usar `record-review` y saltear el
  `has_open_findings` de `finalize-review-panel` — el agujero de vuelta por la ventana.
- `_roles_without_subreview`: privada, **solo para el mensaje**. Recorre
  `package.get("review_panels", [])` (todos los paneles, cualquier `status`) y devuelve los
  `roles` sin ninguna entrada en `subreviews[]`. No participa de la condición de rechazo.
- `require_no_blocking_findings`: levanta `StateError` si
  `has_open_findings(package, model.BLOCKING_SEVERITIES)`. Mismo predicado y mismo conjunto
  que `cli_review.py:159-160`.
- **Las dos levantan `StateError`; ninguna usa `block_with_reason`.** `mutate`
  (`feature-state.py:156-179`) solo escribe si el `updater` retorna truthy y no levanta, así
  que un rechazo descarta la mutación entera — incluido el `deep_review_cycles += 1` de
  `cli_review.py:46` (AC-A.1). `block_with_reason` **retorna** y persiste un `BLOCKED`:
  usarlo acá convertiría un verbo equivocado en una feature bloqueada.

### Puntos de inserción exactos en `cmd_record_review` (`cli_review.py:21-63`)

| dónde | qué | por qué exactamente ahí |
|---|---|---|
| después de `:28-30` (`package_review_ready`), **antes** de `:31-34` | `require_review_panel(package)` | antes del chequeo de presupuesto, que llama `block_with_reason` y **persiste** un `BLOCKED`: un `record-review` mal elegido no puede bloquear la feature |
| dentro de `elif args.verdict == "pass":` (`:54`), **antes** de `data["phase"] = "PACKAGE_TESTING"` (`:55`) | `require_no_blocking_findings(package)` | misma posición que `finalize-review-panel` usa en `:158-160`, y —crítico— **después** del merge de `--finding` de `:48-49`: los dos sitios medidos del golden suite son `record-review pass --finding <high>` en la **misma** llamada (`tests/test_harness.py:9032`, `:11048`); un chequeo previo al merge no los vería y AC-A.4 quedaría verde sin morder nada |

Nada más de `cmd_record_review` cambia: ni la firma, ni los tres verdicts, ni el envelope.

## 3. Tokens exactos (assumption 2 — RESUELTA)

Prefijo del mensaje, no campo nuevo del envelope. El envelope sigue siendo
`{"ok": false, "error": "<mensaje>"}` con exit 2 (`feature-state.py:1349-1353`) — la forma que
todo test parsea. Prefijo porque `assertIn("REVIEW_PANEL_REQUIRED", result.stdout)` y
`rg -n "REVIEW_PANEL_REQUIRED"` tienen que funcionar sin tocar el parser (precedente:
`RISK_SIGNAL_REQUIRED`/`RISK_SIGNAL_INVALID`, ADR-0064, `cli_lifecycle.py:157-161`).

```text
REVIEW_PANEL_REQUIRED: {package_id} requires the full review panel ({required}) for
complexity={complexity} risk={risk}; record-review is the small+low door and cannot record any
verdict here. Roles with no recorded subreview: {missing}. Use: start-review-panel --role
{role} [--role {role} ...], then record-subreview per role, then finalize-review-panel.
```

```text
BLOCKING_FINDING_OPEN: cannot pass review with blocking findings open: {id} ({severity}), ...
Record --verdict repair_required instead, or refute the finding with record-verification. Same
severities finalize-review-panel refuses: critical, high, medium.
```

- `{required}` / `{role}`: `resolved_required_reviewers(package)`, en orden, separados por `, `.
- `{complexity}`: `package.get("complexity") or "<unset>"`. `{risk}`:
  `resolve_package_risk(package)` (lectura pura).
- `{missing}`: `_roles_without_subreview(...)` unido por `, `; si queda vacío,
  `none (the open panel closes with finalize-review-panel)`.
- Se conserva la subcadena `blocking findings open`, que es lo que las aserciones del suite y
  el advisor de `transitions.py:109` ya usan como vocabulario.

## 4. Contrato del comentario de `transitions.py:96-109` (T-007)

**La rama no se borra y no se declara inalcanzable.** Se conservan `:97-101`; se reemplazan
**solo** `:102-107` (la frase "record-review is outside this package's criteria and every
package in flight uses it" no sobrevive). Texto para pegar:

```python
            # `record-review` no longer opens this door: since ADR-0065 it refuses `pass`
            # while a blocking finding is open (BLOCKING_FINDING_OPEN), the same set
            # finalize-review-panel and record-delta-review already refuse.
            # This branch stays because the state is still REACHABLE, through a door this
            # slice deliberately left open: `record-repair --skip-delta` sets PACKAGE_TESTING
            # at cli_repair.py:280-282 while its guard at :246-253 inspects only the findings
            # named by --finding-id on that call, so an unrepaired finding travels through.
            # Deferred on purpose, not forgotten:
            # docs/notas/decisiones/2026-08-20 035-skip-delta-fuera-del-slice.md
            # Full door audit: docs/specs/035-panel-honesto-consola-y-tips/evidence/PKG-A-doors.md
```

Verificación: `rg -n "record-review is outside this package"` vacío en `ai/scripts`,
`PROYECTO/ai/scripts` y `Global/`; y cada `file:line` citado existe.

## 5. Puertas hacia `PACKAGE_TESTING` (assumption 5 — RESUELTA, sin sorpresas)

Seis puertas reales (más una sintética de `--dry-run`), enumeración probada por
`rg '\["phase"\] *='` sobre los 25 sitios de escritura de fase. Detalle completo con
`file:line` en `evidence/PKG-A-doors.md`. Resumen: `finalize-review-panel` chequea,
`record-delta-review` chequea, `transition` chequea, `record-verification` (camino
todo-refutado, `feature-state.py:862-868`) chequea **más estricto** (`severities=None`),
`record-review` **no** (se cierra acá), `record-repair --skip-delta` **no** (no-goal 12).
**Ninguna puerta imprevista ⇒ ningún `HUMAN_DECISION_REQUIRED`, ningún guarda inventado
fuera de `record-review`.**

## 6. Doctrina: reemplazo para `Global/_canonical/agents/orchestrator.md:102-108` (T-010)

El `architect` **no** edita el canónico. El implementer reemplaza `:102-108` por este bloque
tal cual (`:109-111`, `extend-review-panel`, queda intacto justo debajo):

```markdown
- `record-gate`, including `check-owned-paths.py`, before package review.
- `record-verification`, `record-repair`, `record-delta-review`, and `accept-package` after the
  corresponding agent.
- **The review panel is the default door, not an upgrade.** `start-review-panel`,
  `record-subreview` (one per role), and `finalize-review-panel` are MANDATORY whenever the
  package's resolved panel is the full one — that is every package that is not `small`
  complexity AND `low` risk, including any package whose `complexity` is unset, which fail-safes
  to the full panel. `record-review` refuses every verdict there with `REVIEW_PANEL_REQUIRED`
  (ADR-0065); it is not a shortcut you may take when a second reviewer feels unnecessary.
  `--role` is required: name exactly the reviewers you are about to spawn, because
  `record-subreview` refuses a role the panel never declared and refuses it only once the spawn
  is already paid for. A panel consumes one deep review cycle no matter how many subreviewers
  contribute.
- `record-review` is the single-reviewer door, and only for a `small`+`low` package. It also
  refuses `--verdict pass` with `BLOCKING_FINDING_OPEN` while a `critical`/`high`/`medium`
  finding is open — the same set `finalize-review-panel` refuses; record `repair_required` or
  refute the finding instead. Neither refusal costs a deep review cycle.
```

Después: `./build.sh --check` regenera los cinco árboles con el `copytree`/render que ya
existe. `generate.py` **no** se modifica (no-goal 13) y las copias **no** se editan a mano.
Observable de AC-A.9: `rg -n "when multiple specialist reviewers are useful" Global/` vacío,
**incluido** `Global/codex/agents/orchestrator.toml` (el `rg` tiene que cubrir el `.toml`).

## 7. Fixtures que el guarda obliga (AC-A.3) y trampas nombradas

Cuatro casos, no uno. Los tres primeros los exige el spec; el cuarto lo agrega este diseño.

1. **Clave `required_reviewers` ausente** + `complexity: "medium"` → FULL, rechaza. Es la forma
   de 71 de 76 paquetes.
2. **`required_reviewers: null` explícito** → FULL, rechaza. 0 paquetes hoy; lo produce un
   editor a mano.
3. **`complexity` ausente/`None`** → fail-safe FULL, rechaza. 4 paquetes medidos.
4. **`required_reviewers: []` / lista con ítems vacíos** (presente-pero-inservible, DEC-ABSENCE)
   → re-deriva, no se lee como "sin requisito". Sin este caso, una lista vacía sería un bypass
   silencioso de `len(...) > 1`.

Los cuatro se escriben **a mano** como state files. Un fixture hecho con `create-package`
engaña: ese verbo **sí** persiste el campo (`cli_lifecycle.py:334`), y `update-package
--complexity` lo re-persiste (`:375-377`).

## 8. Integridad, concurrencia, fallas

- **Atomicidad:** un único `update()` bajo `mutate` (`feature-state.py:156-179`), que valida,
  bumpea `revision` y escribe atómico. Los dos guardas levantan **antes** de cualquier escritura
  efectiva; no hay estado intermedio observable ni ciclo cobrado.
- **Concurrencia:** sin estado nuevo. `record-subreview` sigue idempotente por rol
  (`cli_review.py:105-106`) y `replayed()` sigue cubriendo reintentos.
- **Modo de falla nuevo, dicho:** un paquete `medium`/`high` cuyo panel FULL choca
  `MODE_BUDGETS.scoped.max_spawns_per_package` (8, `model.py:125`) es
  `HUMAN_DECISION_REQUIRED` (AC-A.8), nunca un techo más grande ni un `--complexity` degradado.
- **Legacy:** 27 features `DONE` y todo paquete `accepted`/`superseded` siguen validando; el
  guarda no está en ningún camino de lectura/validación (`verify.sh:65` /
  `check-feature-state.py` no re-validan el lote — medido).

## 9. Gates que este cambio tiene que pasar

```
python3 -m unittest tests.test_harness
python3 -m unittest tests.test_honest_predicate tests.test_narracion_contrato
./build.sh --check && ./ai/scripts/verify.sh
rg -n "record-review is outside this package" ai/scripts PROYECTO/ai/scripts Global
rg -n "when multiple specialist reviewers are useful" Global/
```

strict-TDD (ADR-0022) está ON: cada guarda test-first, con las corridas **ROJA y VERDE** en
`docs/specs/035-panel-honesto-consola-y-tips/evidence/`. Restaurar con `cp` del módulo, nunca
`git checkout`/`restore`/`stash`.

## 10. Qué NO puede cambiar (contrato para el implementer)

- Firma de `record-review` y sus tres verdicts; envelope `{"ok": false, "error": ...}` + exit 2.
- Firmas de `start-review-panel`, `record-subreview`, `finalize-review-panel`,
  `extend-review-panel`, `record-late-review`.
- `record-repair --skip-delta`: **cero** cambios (no-goal 12).
- `MODE_BUDGETS`, `NON_ACCEPTING_ACTORS`, `REFUTING_ACTORS`, `RISK_SIGNAL_REQUIRED`,
  `required_reviewers_for`, `resolve_package_risk`, `persist_review_requirements`.
- `generate.py`; las copias generadas en `Global/*`; `set_agents_app.py`; `TIPS-USO.md`;
  `docs/COMO-FUNCIONA.md`.
- Ningún test se afloja, saltea ni borra, y ningún `--complexity medium` baja a `small`.

---

# 11. PKG-B — La consola partida

> `architect`, 2026-08-20, segundo pase. Resuelve las assumptions **6**, **7** y **9** del
> spec (`spec.md:553-569`). Nada de § 1-10 se reescribe. Contrato: **ADR-0066**.
>
> **Baseline (`solution-baselines`): ninguna aplica** — un refactor
> comportamiento-preservante del CLI de un harness ya establecido no es webapp de gestión,
> ni scraping/ML, ni API B2B, ni e-commerce. Manda la convención del repo.
> Ejes **store / API Gateway / deploy: n/a**, ya registrados como tales en el `axes_log` de
> la feature (`spec.md:13-15`); ADR-0066 no abre ninguno y no difiere ninguno con umbral,
> porque no existen en este paquete: cero persistencia nueva, cero superficie de red nueva,
> cero cambio de despliegue.
>
> **`docs/architecture/overview.md` NO se toca, y eso es la conclusión, no una omisión.**
> Ese archivo es el mapa del estado **actual**; PKG-B cierra por el camino (b) y el grafo de
> módulos de `ai/scripts/` queda **idéntico** (§ 11.3). Un mapa nuevo describiría un split
> que este paquete decide, con evidencia, no hacer. Por la misma razón no se agrega ninguna
> entrada a `docs/modules/modules.toml`: no hay módulo nuevo que documentar.

## 11.1 Veredicto de T-102 (assumption 7): **camino (b)**

**Tocar `HarnessTests._import` es un cambio al contrato del golden suite y necesita ACs
propios. No entra en este slice. PKG-B cierra por (b): residuo probado anclado y enumerado.**

Tres lecturas propias lo sostienen. Ninguna recicla `routing_cli.py:1-31` ni
`vault_ops.py:1-23` (AC-B.6 / F-035-006): las dos primeras **corrigen** lo que esos
docstrings dicen.

### F-B-ARCH-01 — el mecanismo que el spec y tres docstrings nombran está **desactualizado**

`acceptance.md:458-461` (AC-B.4), `vault_ops.py:13-17`, `project_identity.py:11-13` y
`routing_cli.py:14` afirman que `_import()` carga `set_agents_app.py` **sin registrarlo en
`sys.modules`**, de modo que un import inverso arranca un segundo exec top-level.

**Hoy eso es falso.** El helper vigente es `tests/test_harness.py:745-797` y hace lo
contrario: `previous = sys.modules.get(name, _SYS_MODULES_ABSENT)` (`:788`) y
`sys.modules[name] = module` (`:789`) **antes** de `spec.loader.exec_module(module)` (`:791`).
Durante el exec el nombre **sí** está registrado — es exactamente por eso que el
`sys.modules.setdefault("set_agents_app", sys.modules[__name__])` de `set_agents_app.py:33`
no explota, razón escrita en el propio comentario del helper (`:749-759`). Corolario medido:
`app_config` está definido en `:1075` y `vault_ops` se importa en `:2851`, así que un
`from set_agents_app import app_config` a nivel de módulo dentro de `vault_ops.py`
**resolvería** durante el exec; el fallo que el docstring describe no es el que ocurriría.

Esto **no cambia el veredicto**, cambia la razón — y la razón es lo que AC-B.6 exige en su
tercera columna. La matriz de T-104 cita el `finally` de `:792-796`, nunca la frase vieja.

*Tratamiento:* se registra como **finding de documentación** (no es un bug de código, así
que AC-B.3 no aplica). El implementer **puede** reemplazar la oración falsa por la correcta
en `routing_cli.py` y `vault_ops.py` (los dos en `owned_paths`), apuntando a la matriz —
**una oración por archivo, sin bloque nuevo de "documented deviation"**, y esa corrección
**no cuenta** como el cierre (AC-B.6 lo prohíbe explícitamente). `project_identity.py`
**no** está en `owned_paths` (`docs/notas/features/035-panel-honesto-consola-y-tips/PKG-B.md:10`):
queda intacto y el finding lo nombra.

### F-B-ARCH-02 — el ancla real es el `finally` que restaura, y está **pinneada por un test**

El helper restaura el estado previo al salir (`:792-796`): si el nombre estaba ausente lo
saca (`_SYS_MODULES_ABSENT`, `tests/test_harness.py:40`), si estaba presente lo repone. Es decir
que **después de que `_import` retorna, `sys.modules["set_agents_app"]` ya no es el objeto que
el test tiene en la mano como `app`**. Medido: **139** call sites de
`self._import("set_agents_app")` (`rg -c`), y **35** targets distintos de
`patch.object(app, "…")`.

Y ese comportamiento **es** el contrato: `test_import_helper_leaves_sys_modules_exactly_as_it_found_it`
(`tests/test_harness.py:12275-12335`) lo asegura en los **tres** estados previos posibles —
entrada preexistente sobrevive (`:12298-12299`), ausente sigue ausente (`:12309-12310`),
`None` explícito se repone como `None` presente (`:12327-12330`) — más un test de regresión
por subproceso (`:12266-12273`). El historial de por qué (`:12280-12289`) dice qué se rompió
cuando una primera versión del fix dejó el módulo registrado: los
`test_resolve_context_pack_*` de `tests/test_routing.py` empezaron a resolver contra el `ROOT`
real en vez del temp de cada test.

**Consecuencia arquitectónica, que es el techo:** una función que **se muda** fuera de
`set_agents_app.py` pierde la identidad de `__globals__` con el objeto que el test parchea.
No es un problema de resolución de nombres — `from routing_cli import (…)` (`:621`) y
`from vault_ops import (…)` (`:2851`) mantienen `app.<nombre>` perfectamente resoluble, así
que **"re-exportarlo" no arregla nada** y el implementer va a intentarlo si no se le dice.
Dos familias medidas:

| familia | sitios de parche | qué lee | qué pasa si se muda |
|---|---|---|---|
| `cmd_vault_doctor` (`:3192`) | `patch.object(app, "STATE_DIR", …)` en `tests/test_harness.py:4577`, `:4638`, `:4662`, `:4678`, `:4691`, `:4711`, `:5207` | `STATE_DIR` vía `_vault_doctor_marker_path` (`:3160-3162`), llamado en `:3222`; hoy su `__globals__` **es** el dict que `patch.object` muta | el marker se escribiría bajo el `STATE_DIR` real y no bajo el temp: el parche deja de aplicar |
| `vault_menu` (`:3339`) | `patch.object(app, "cmd_vault_init"/"cmd_vault_link")` en `:3702-3703`, `:3717-3718`, `:3733-3734`, `:3749-3750`, `:3768` | llama a los dos por nombre global | resolvería en `vault_ops.__dict__` → **corre el `cmd_vault_init` real**. `:3720`, `:3736`, `:3752` (`assert_called_once_with`) se ponen **rojos**; peor: `:3705-3706` (`assert_not_called`) queda **verde en falso** mientras el comando mutante de verdad se ejecuta |

Ese verde-en-falso sobre un comando mutante es peor resultado que el rojo, y es literalmente
lo que AC-B.8 llama el defecto.

**El residuo de routing está anclado por otra vía, y hay que decirlo distinto.**
`PROJECT_ROOT`, `PROJECT_KEY` y `ROUTING_WARNINGS` se reasignan en **un solo** sitio del
repo: el `global` de `main()` (`set_agents_app.py:4241`). `_routing_store()` (`:68-73`) lee
`PROJECT_KEY`, `_routing_output()` (`:524-527`) lee `ROUTING_WARNINGS`, y
`_project_root_or_harness()` (`:92-95`) lee `PROJECT_ROOT`/`ROOT`. Tres mediciones, con una
asimetría que importa:

1. `tests/test_routing.py` parchea **`ROOT`/`PROJECT_ROOT`** por asignación directa sobre el
   módulo canónico (`:3337-3338`, `:3344`, `:3688`, `:3701`, `:3715`, `:3743`, `:3750`,
   `:3756`) y `STATE_DIR`/`APP_CONFIG`/`MODEL_PREFERENCE_PATH` con `patch.object`
   (`:6314-6316`), llegando por un `import set_agents_app` plano (`:29`) que **sí** queda
   registrado — que es la razón por la que el patrón lazy de `routing_cli.py` funciona ahí.
2. `_routing_output` **sí** se ejercita bajo `_import`: `tests/test_harness.py:5480-5494` lo
   llama con `patch.object(app, "_term_width", …)` (`:5493`), y `_term_width` vive en `:3726`
   — mudarlo deja ese parche sin efecto.
3. **Tercer sitio de acoplamiento que el context pack no nombra** (`rg` propio):
   `tests/test_menu_ui.py` hace `import set_agents_app as app` (`:22`), parchea
   `app.ROUTING_WARNINGS` (`:241`) y llama **`app.cmd_route_doctor(human=human)` in-process**
   (`:246`). O sea que `cmd_route_doctor` (`:586`) tiene un sitio de parche vivo sobre un
   global mutable, y `tests/test_menu_ui.py` **tampoco** está en `owned_paths`
   (`PKG-B.md:10`): es read-only para este paquete igual que `tests/test_harness.py`.

**La asimetría:** `PROJECT_KEY` **no tiene ni un sitio de parche en todo `tests/`** (medido:
`rg -n 'PROJECT_KEY' tests/*.py` solo devuelve `PROJECT_KEY_COLUMN`/`_TEST_PROJECT_KEY` de
`routing_store`, que son otra cosa). Se setea **únicamente** en `main()` (`:4241`). Eso hace
que los nueve comandos que llegan a `_routing_store()` sean el caso **más** peligroso, no el
más libre: una mudanza que les rompa la resolución de `PROJECT_KEY` no tiene ningún test que
la ponga roja — se descubriría en producción, contra el store equivocado. Ese es el residuo
donde "no hay test que lo cubra" es un argumento para **no** moverlo, no para moverlo barato.

### F-B-ARCH-03 — arreglar el helper es, por construcción, fuera de alcance

Las tres formas de "arreglarlo estructuralmente" chocan con una regla del paquete:

1. **Dejar el módulo registrado** (el patrón de `TuiTests._import`, `:13918-13933`, que sí lo
   deja para `tui.py`) → pone en rojo las tres aserciones de `:12275-12335` y reintroduce la
   regresión de `tests/test_routing.py` documentada en `:12280-12289`. **AC-B.8: un test rojo
   es el defecto.**
2. **Reescribir los 12 sitios de parche** para que apunten al módulo dueño → cambia **qué
   afirma** el golden suite, en un archivo que **no** está en `owned_paths`
   (`PKG-B.md:10`); la excepción vigente es explícita: *"No autoriza al implementer de B a
   editar esas rutas"* (`docs/notas/decisiones/2026-08-20 035-pkg-b-owned-exceptions-uncommitted-a.md:13`).
3. **Inyectar una referencia al módulo en tiempo de exec** → seam de producción nuevo, o sea
   comportamiento observable nuevo. **AC-B.3 lo prohíbe.**

Los tres son la segunda mitad de la assumption 7 ("necesita ACs propios"), así que se
**registra** y el paquete cierra por (b), exactamente como `tasks.md:229-230` lo preautorizó.

**Umbral que desbloquearía el camino (a)** (YAGNI como decisión, no como silencio): un slice
propio con `tests/test_harness.py` en `owned_paths`, ACs que cubran (i) la semántica nueva de
`_import`, (ii) la reescritura de los 12 sitios de parche al módulo dueño y (iii) la
conservación de las tres aserciones de `:12275-12335` o su reemplazo argumentado. Ese slice
hereda gratis los dos activos que PKG-B produce (§ 11.4).

## 11.2 Qué se mueve y qué se queda (contrato de mudanza)

**Nada se muda en este slice.** No por pereza: cada comando residual necesita, para moverse,
o (i) una referencia viva a un global mutable que solo `main()` reasigna (`:4241`), o (ii)
editar el helper read-only. La opción (i) invierte la dirección de la dependencia — el módulo
extraído importaría al monolito en tiempo de llamada — y es justo el "tercer docstring de
documented deviation" que AC-B.6 nombra como **no** cierre.

**Ancla asignada por comando (columna 2 de la matriz de T-104; la columna 3 la produce el
implementer).** Líneas verificadas con `rg -n '^def …'` sobre `set_agents_app.py`, 2026-08-20:

| comando | ancla concreta |
|---|---|
| `cmd_route_explain` (`:550`) | `PROJECT_KEY` vía `_routing_store()` (`:68-73`) + `ROUTING_WARNINGS` vía `_routing_output()` (`:524-527`) |
| `cmd_routing_report` (`:575`) | ídem |
| `cmd_route_doctor` (`:586`) | `PROJECT_KEY` vía `_probe_cache_root()` (`:76-89`) → `_routing_store()`; **más** `ROUTING_WARNINGS` parcheado sobre el módulo en `tests/test_menu_ui.py:241` con llamada in-process en `:246` |
| `cmd_route_decide` (`:671`) | `PROJECT_KEY` + `ROUTING_WARNINGS` |
| `cmd_route_dispatched` (`:794`), `cmd_route_quota_exhausted` (`:800`), `cmd_route_terminal` (`:833`) | `PROJECT_KEY` vía `_lifecycle_command` (`:782`) |
| `cmd_routing_open_runs` (`:866`), `cmd_routing_recent_writers` (`:874`), `cmd_routing_decisions` (`:882`) | `PROJECT_KEY` vía `_routing_store()` |
| `cmd_routing_migrate` (`:3619`) | `PROJECT_KEY` |
| `_routing_output` (`:524`) | `ROUTING_WARNINGS` (`:525`) **y** `_term_width` (`:3726`) bajo `_import` (`tests/test_harness.py:5493`) |
| `cmd_vault_init` (`:2869`), `cmd_vault_link` (`:3048`) | `app_config`/`write_app_config` (`:1075`/`:1086`) → `APP_CONFIG`/`STATE_DIR`, parcheados en `tests/test_harness.py:1912-1913`, `:1968-1969`, `:2072`, `:2095-2096` |
| `find_vault` (`:2900`), `_resolve_vault` (`:3148`) | `app_config()` (`:3154`) |
| `vault_link_private` (`:2989`) | cadena de llamada de `cmd_vault_link` (`:3048`) |
| `cmd_vault_doctor` (`:3192`) | `STATE_DIR` vía `_vault_doctor_marker_path` (`:3160-3162`) — **7** sitios de parche |
| `vault_menu` (`:3339`) | `cmd_vault_init`/`cmd_vault_link` como globals — **5** sitios de parche |

**Válvula condicional (no es una invitación).** Un comando **puede** mudarse a
`routing_cli.py` o `vault_ops.py` — los dos ya existen y están en `owned_paths` — si y solo
si se cumplen **las cuatro**:

1. su cuerpo no lee, directa ni transitivamente, `PROJECT_KEY`, `PROJECT_ROOT`, `ROOT`,
   `ROUTING_WARNINGS`, `STATE_DIR` ni `APP_CONFIG` de `set_agents_app`;
2. no necesita que este slice agregue ningún `import set_agents_app` lazy de vuelta;
3. ningún `patch.object(app, …)` ni asignación `set_agents_app.<X> = …` de
   `tests/test_harness.py`, `tests/test_routing.py` **o `tests/test_menu_ui.py`** lo nombra,
   ni nombra un global que lea;
4. no crea duplicación nueva (AC-B.5).

Si falla **una** sola, se queda y va con fila a la matriz. Y se mude lo que se mude:
**cero archivos nuevos** (§ 11.3).

## 11.3 Assumption 6 — módulos y firmas nuevas: **ninguno en este slice**

**No hay módulo nuevo, y no hay función pública nueva.** Razones, en orden de dureza:

1. El camino (b) no mueve residuo, así que no hay nada que alojar. Los dos destinos posibles
   ya existen: `routing_cli.py` (277 líneas) y `vault_ops.py` (455).
2. Un archivo nuevo bajo `ai/scripts/` **no** está en `owned_paths` (`PKG-B.md:10`) y la nota
   de excepciones deja la decisión al architect: *"Un archivo nuevo en ai/scripts/ se declara
   owned o exception cuando el architect lo nombre"*
   (`…035-pkg-b-owned-exceptions-uncommitted-a.md:17`). **No nombro ninguno.**
3. Un módulo nuevo bajo `ai/scripts/` entraría a dos gates que hoy no lo miran: el
   `py_compile` de `ai/scripts/*.py` (`ai/scripts/verify.sh:24`) y el guardián de encoding
   que recorre `(ROOT / "ai/scripts").rglob("*.py")` exigiendo `encoding=` en todo
   `open`/`read_text`/`write_text`/`NamedTemporaryFile` (`tests/test_harness.py:11677-11689`).
   Correcto para producción; costo innecesario por un módulo que no hace falta.
4. `build.sh --check` **no** es un riesgo por acá, y conviene decirlo para que nadie invente
   uno: itera sobre `PROYECTO/ai/scripts` (`build.sh:68`) y saltea el destino inexistente
   (`[ -e "$target" ] || continue`, `build.sh:72`), y `PROYECTO/ai/scripts/set_agents_app.py`
   no existe (medido en el context pack). El piso `checked >= 23` no baja porque nada se
   borra de `PROYECTO/`.

## 11.4 Assumption 9 — mecanismo de la comparación de tres canales (AC-B.2)

**Un script de caracterización propio del paquete, alojado en `evidence/`.** No
`tests/test_routing.py`, no archivos comparados a mano.

### Por qué no las otras dos

- **`tests/test_routing.py` extendido** (legal: está en `owned_paths`) queda descartado por
  una razón medida, no de gusto: el suite corre con un runtime **modificado**.
  `tests/__init__.py:362` instala un audit hook process-wide que rechaza toda escritura fuera
  del sandbox privado (`:271-284`), y `:195` reemplaza `subprocess.Popen` por una frontera
  bwrap (`:119-167`). Una caracterización corrida ahí mide el CLI **bajo ese runtime**, no el
  CLI. Y AC-B.2.4 exige correr flags que tocan red y credenciales
  (`--provider-verify`, `--check-update`, `--quota-failover-e2e`, `--fresh-probes`): meterlas
  al golden suite lo vuelve no hermético.
- **Archivos capturados y comparados a mano** queda descartado porque los normalizadores se
  aplicarían a ojo, que es exactamente el modo de falla que AC-B.2.3 convierte en finding.

### Layout (todo bajo `owned_paths`)

```
docs/specs/035-panel-honesto-consola-y-tips/evidence/PKG-B-characterization/
  characterize.py                      # el runner
  NORMALIZERS.md                       # lista CERRADA y fechada, escrita ANTES de comparar
  MANIFEST.md                          # set representativo: una fila por invocación
  baseline/<case-id>.stdout|.stderr|.exit
  after/<case-id>.stdout|.stderr|.exit
  RESULT.md                            # diff por caso y por canal, o "idéntico"
```

`docs/specs/…/evidence` es `owned_path` de PKG-B (`PKG-B.md:10`) y **ningún gate compila ni
lintea Python ahí**: `verify.sh:24` cubre solo `ai/scripts/*.py` más
`routing_core/`/`feature_state_lib/`, y el guardián de encoding recorre solo
`ai/scripts` (`tests/test_harness.py:11677`). El runner igual declara `encoding="utf-8"` en
cada I/O — no porque un gate lo obligue, sino porque la evidencia se lee en otra máquina.

### Contrato del runner (para que T-101 no tenga que inventarlo)

- **Tres canales, tres archivos.** `stdout`, `stderr` y exit code van a archivos
  **separados**, nunca interleaved. Un canal no puede esconderse dentro de otro, que es
  precisamente el fixture tramposo que AC-B.2 nombra (`acceptance.md:434-437`).
- **`case-id` determinístico** por invocación, y una fila en `MANIFEST.md` con: grupo de la
  tabla § Contratos públicos del spec, `argv` exacto, modo de aislamiento
  (`plain` | `disposable` | `declared-uncharacterizable`) y si usó `--dry-run`.
- **La lista de normalizadores se cierra por construcción, no por promesa.** Cada normalizador
  es una función nombrada en `characterize.py` con **una fila 1:1** en `NORMALIZERS.md`, y el
  runner **se niega a comparar** si existe una función sin fila o una fila sin función. Eso
  vuelve mecánico el "cerrada antes de la primera comparación" de AC-B.1/AC-B.2.3, en vez de
  dejarlo como disciplina. Universo permitido, cerrado (AC-B.2.3): timestamps, rutas absolutas
  de `tmp`/`$HOME`, duraciones/latencias en ms, PIDs, versiones, y orden no determinístico
  donde el comando no lo garantiza. **Nada más.**
- **`MANIFEST.md` se sella** con la fecha y el `git rev-parse HEAD` del árbol de la corrida
  baseline. Es lo que hace verificable el "previa, no una foto del resultado" de AC-B.1.
- **Aislamiento (AC-B.2.4).** `HOME` temporal desechable,
  `SET_AGENTS_STATE=$HOME/.local/state/set-agentes`, proyecto temporal; `--dry-run` donde
  exista. Nunca el árbol real. **Y la disciplina de secretos es por construcción, no por
  scrubber:** al `HOME` desechable no se le inyecta ninguna credencial viva, así que no hay
  valor que filtrar; se registra presencia/ausencia y nada más. Una flag que no se pueda
  correr sin efecto lateral se anota `declared-uncharacterizable` con la razón —
  **declararla cumple el criterio** (`acceptance.md:431-432`).
- **`--route-decide` y su familia no se corren desde este host.** El anfitrión es Cursor y la
  prohibición es de harness (no-goal 4, `context/PKG-B.md:69-70`). Van al manifest como
  `declared-uncharacterizable (host policy: Cursor never --route-decide)`. Decirlo acá evita
  las dos salidas malas: correrlo, u omitirlo en silencio.

### El regalo del camino (b): la lista de normalizadores se vuelve **verificable**

Como no se mueve código, `baseline/` y `after/` se corren contra **el mismo árbol y el mismo
binario**. Entonces todo diff que aparezca es, por definición, ruido corrida-a-corrida — que
es la única cosa que AC-B.2.3 acepta normalizar. Bajo el camino (a) no se puede separar "ruido"
de "la mudanza cambió algo"; acá sí. Un normalizador que hace falta en esa corrida es
**legítimo y probado**; uno que no haga falta ahí y aparezca después es el diff escondiéndose.
Esa es la asimetría que convierte el cierre (b) en un activo para el slice siguiente, y no en
un consuelo.

## 11.5 Integridad, concurrencia, fallas (PKG-B)

- **Atomicidad:** no aplica — cero escrituras de producción. El único escritor nuevo es el
  runner de caracterización, y escribe solo bajo `evidence/` y bajo su `HOME` desechable.
- **Concurrencia:** sin estado nuevo. `_BACKED_UP` de `vault_ops.py:39` sigue scoped
  per-module, tal como su docstring ya justifica (`:17-22`); PKG-B no lo cambia.
- **Modo de falla nuevo, dicho:** el runner puede dejar basura en el `HOME` desechable si se
  interrumpe. Es un `mktemp -d` propio; no toca el árbol ni el `STATE_DIR` real.
- **Riesgo de seguridad concreto** (por eso el panel incluye `security-auditor`): la
  caracterización de `--provider-verify`/`--check-update`/`--quota-failover-e2e`/`--fresh-probes`
  escribe `stdout`/`stderr` a disco, en un directorio **trackeado por git**. La mitigación de
  diseño es no darle credenciales al `HOME` desechable, de modo que no exista secreto que
  capturar; el reviewer verifica eso, no la presencia de un scrubber.

## 11.6 Gates que PKG-B tiene que pasar

```
wc -l ai/scripts/set_agents_app.py            # 4399 antes; se REPORTA (T-105), no es meta
python3 -m unittest tests.test_routing
python3 -m unittest tests.test_harness
python3 -m unittest tests.test_menu_ui tests.test_provider_registry tests.test_module_docs
./build.sh --check
./ai/scripts/verify.sh
```

Más la comparación de los **tres** canales contra `baseline/`, con los normalizadores de
`NORMALIZERS.md` y **ninguno** nuevo. Ningún test cambia de color (AC-B.8): rojo = defecto.
`strict_tdd` es **false** a propósito (context pack `:101-103`): la disciplina equivalente es
el gate previo de AC-B.1.

## 11.7 Qué NO puede cambiar (contrato del implementer para PKG-B)

Checklist ejecutable, sin re-derivar T-102:

- [ ] **`tests/test_harness.py` y `tests/test_menu_ui.py` son read-only.** Ninguno está en
      `owned_paths` (`PKG-B.md:10`); la excepción por PKG-A sin commitear no autoriza a
      editarlos (`…035-pkg-b-owned-exceptions-uncommitted-a.md:13`). El único test file
      editable de PKG-B es `tests/test_routing.py`, y este diseño **no** le pide cambios.
- [ ] **No se "arregla" `_import`** (`tests/test_harness.py:745-797`) ni se toca
      `TuiTests._import` (`:13918-13933`), que es otro helper con otro contrato.
- [ ] **`ai/scripts/routing_core/`** (`__init__`, `catalog`, `domain`, `gates`, `inference`,
      `service`, `store`, `usage`) **no se toca** (AC-B.7). Se mueven llamadores, no contratos.
      Tampoco la semántica de vault de ADR-0012/ADR-0056.
- [ ] **Cero archivos nuevos bajo `ai/scripts/`** (§ 11.3). Si la válvula de § 11.2 abre para
      algún comando, el destino es `routing_cli.py` o `vault_ops.py`, que ya existen.
- [ ] **Nada se muda si falla una de las cuatro condiciones de la válvula** (§ 11.2).
- [ ] **T-101 primero, y es gate duro.** `NORMALIZERS.md` y `MANIFEST.md` sellados con fecha y
      `HEAD` **antes** de cualquier movimiento. Store:
      `docs/specs/035-panel-honesto-consola-y-tips/evidence/PKG-B-characterization/`.
- [ ] **Un normalizador agregado después de ver un diff es finding**, no ajuste
      (AC-B.2.3). El runner lo hace mecánico: función sin fila ⇒ se niega a comparar.
- [ ] **Mutantes y credenciales en `HOME`/proyecto desechable**, `--dry-run` donde exista,
      cero credenciales vivas inyectadas, cero valores de secreto en la evidencia
      (AC-B.2.4). `--route-decide` y familia: `declared-uncharacterizable (host policy)`.
- [ ] **La duplicación no crece** (AC-B.5). El techo son las existentes:
      `atomic_write`/`_BACKED_UP` (`vault_ops.py:39-55`) y
      `_MAX_FEATURE_BYTES`/`_MAX_FEATURE_FILES` (`routing_cli.py:40-41`).
- [ ] **Matriz de T-104: 16 filas obligatorias**, exactamente los 16 comandos que AC-B.4
      enumera (`acceptance.md:447-453`: 11 de routing + 5 de vault), con la **tercera columna
      llena en todas** — experimento propio o lectura propia con `file:line`. Citar
      `routing_cli.py:1-31` o `vault_ops.py:1-23` **no** cierra una fila (AC-B.6). Los tres
      helpers extra de la tabla de § 11.2 (`_routing_output`, `_resolve_vault`,
      `cmd_vault_link`) están ahí porque son el ancla **de** esos comandos; no son filas
      obligatorias, y agregarlas no reemplaza ninguna de las 16.
- [ ] **La corrección de F-B-ARCH-01** es una oración por archivo en `routing_cli.py` y
      `vault_ops.py`, apuntando a la matriz; **no** cuenta como el cierre y **no** agrega un
      bloque nuevo de "documented deviation". `project_identity.py` queda intacto (fuera de
      `owned_paths`): el finding lo nombra.
- [ ] **Un bug real encontrado al mover se registra como finding y se repara aparte**
      (AC-B.3). No viaja en el diff.
- [ ] **T-105 reporta `wc -l`** antes y después, con honestidad si no bajó. No es una meta, y
      no se "cumple" borrando comentarios (AC-B.6, `acceptance.md:496-498`).
- [ ] **Fuera de alcance de PKG-B:** todo `feature_state_lib`/`feature-state.py` y
      `Global/**` (PKG-A), `TIPS-USO.md` y `docs/COMO-FUNCIONA.md` (PKG-C), `generate.py`,
      `MODE_BUDGETS`, y `PROYECTO/**` (no hay espejo de `set_agents_app.py`).
