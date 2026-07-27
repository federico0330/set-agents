# Context pack — P1-portable-core (feature 005, contract 1.1.0)

Objetivo: que el ruteo adaptativo que entregó la 004 sea **alcanzable y correctamente scopeado desde
cualquier proyecto, en cualquier máquina, con el harness clonado en cualquier path**. Hoy sólo funciona
parado dentro de `~/SET-AGENTES`, porque el harness asume que "el proyecto" y "el harness" son el mismo
directorio.

## Leé primero (en este orden)

1. `docs/specs/005-portable-harness/spec.md` — contrato 1.1.0. **Leé el `Amendment log`**: el contrato pasó
   por un desafío independiente que devolvió `revision_required` con 15 bloqueantes. Casi todos los errores
   obvios ya están cerrados ahí; si "se te ocurre" una solución simple, revisá primero si el challenger ya la
   descartó con evidencia.
2. `docs/specs/005-portable-harness/acceptance.md` — AC-00..AC-09 son los tuyos, con escenario BDD y método
   de verificación por cada uno.
3. `docs/specs/005-portable-harness/plan.md` §P1 — T-100..T-111.
4. `docs/adr/0008-two-roots-portability.md` — **lo escribe el architect ANTES que vos** (AC-00 es bloqueante).
   Es la fuente de verdad de todo el HOW. No arranques sin él.
5. ADRs heredados que NO se tocan: `0004` (routing/permisos son de SET-AGENTES), `0005` (la DB de ruteo vive
   en un root fijo inmune al entorno), `0006` (AM-1/AM-2).

## La idea central: dos raíces, escritas hoy con la misma sintaxis

El prompt del orquestador dice `ai/scripts/set_agents_app.py` (vive en el **HARNESS**) y también
`ai/scripts/feature-state.py`, `ai/state/`, `docs/` (viven en el **PROYECTO**). Ningún directorio tiene los
dos. Todo P1 sale de separar eso:

- **`HARNESS_HOME`** — el clon. Absoluto, resuelto **en install-time**, horneado en los artefactos
  **instalados**.
- **`PROJECT_ROOT`** — descubierto por invocación desde el `cwd`.

## Trampas verificadas (cada una hundió una versión anterior del contrato)

**1. El horneo NO puede pasar en build-time.** `ai/scripts/verify.sh:14-16` hace
`diff -ruN "Global/$harness" "$STAGING/$harness"`: lo trackeado tiene que ser byte-idéntico a lo que
regenera `generate.py`. Y `generate.py:429` copia `coord_policy.py` verbatim a `Global/claude-code/hooks/`
(trackeado). Si horneás el path absoluto ahí, `Global/**` queda con el path de **quien buildeó** y `verify.sh`
**no puede pasar en ninguna otra máquina** — justo el escenario que AC-09 prueba.
→ La sustitución vive **sólo en el write path de `install.py`**. `Global/**` trackeado conserva
`__SET_AGENTS_ROOT__` **siempre**. Hay una regresión nueva que lo assertea (T-101).

**2. `install.py:69-72` hoy sustituye SÓLO dentro de `merged_json`** — o sea, sólo en los JSON "special".
Los managed-files (`.py`, `.md`, `.toml`) se copian verbatim. Hay que extender la sustitución a una
byte-substitution genérica aplicada al `hooks/coord_policy.py` instalado y a los `agents/orchestrator.{md,toml}`
instalados (T-102). El escape existente (`json.dumps(str(REPO_ROOT))[1:-1]`) es **específico de JSON**: para
archivos no-JSON necesitás el valor crudo, no el escapado. No reuses el escape por inercia.

**3. El allowlist matchea el STRING CRUDO del comando.** `coord_policy.py:55-63` corre `re.fullmatch` sobre el
comando tal cual. Consecuencias medidas:
- Un `HARNESS_HOME` **con espacio** obliga a invocar `python3 "/mi path/ai/scripts/..."` → el patrón `SAFE`
  **nunca** matchea → ruteo denegado en toda máquina con path con espacios (el caso normal en macOS/Windows).
- `FORBIDDEN_SYNTAX` (`coord_policy.py:37`) bloquea `; | && $( > <` etc.: un path con esos bytes queda
  hard-denied para siempre.
- Matiz verificado (no repitas la formulación cruda del hallazgo): `ALWAYS_DENY` usa
  `(?:^|\s)sudo(?:\s|$)` — exige **borde de espacio**, así que un componente de directorio llamado `sudo`
  entre barras NO dispara ese deny. El problema real es el del espacio, no el de `sudo`.
→ Doble fix (T-103): `install.py` **rechaza** un `HARNESS_HOME` con metacaracteres de shell, con error claro;
y el matcher gana comparación **post-`shlex.split`** para que los espacios no rompan nada.

**4. `.parents` excluye el propio directorio.** `find_vault` (`set_agents_app.py:1018-1029`) itera
`Path(project).resolve().parents`, que **nunca** devuelve el path sobre el que se lo llamó. Clonarlo tal cual
hace que, **parado en la raíz del proyecto** (el caso normal), no se encuentre el proyecto.
→ La lista de candidatos es `[start] + list(start.resolve().parents)` (T-104).

**5. El orden de los markers es un vector de ataque.** "Buscar primero `ai/state/features/` y después `.git`"
tiene dos lecturas; en la mala, un `ai/state/features/` plantado en un ancestro lejano (ej. `$HOME`) **le gana**
al `.git` del repo real y ensancha el ancla de confinamiento a todo el home.
→ **nearest-ancestor-wins**: en CADA nivel se evalúan los DOS markers antes de subir. Parada explícita en `/`.
Y dejá escrito que la raíz descubierta es **frontera de confinamiento, nunca concesión de confianza**.

**6. Cambia el nivel de confianza, no sólo el path.** Hoy `ROOT` es el harness instalado (controlado por el
operador). Post-cambio, `PROJECT_ROOT` y todo `ai/state/features/*.json` bajo él son contenido de **un repo de
terceros** en el que el usuario simplemente hizo `cd`. Re-derivar SEC-A02 sólo para traversal es insuficiente
(T-105): también van rutas exactas legibles, tope de bytes, y encuadre explícito de ese contenido como
**datos, nunca instrucciones**.

**7. `project_key` derivado del path se rompe al mover el proyecto.** Por eso el primario es un **id
persistido** por proyecto (escrito en el scaffold), con hash del path resuelto sólo como fallback (T-106).
Normalización: `realpath` resuelto + case-normalizado donde el FS sea case-insensitive (macOS/Windows, justo
los SO que la portabilidad promete). **Fail-CLOSED**: ante cualquier mismatch la independencia de reviewer
**niega**, nunca concede.

**8. La migración SQLite toca una DB viva con runs reales de la 004.** T-107: backup de la DB antes de nada,
`BEGIN EXCLUSIVE`/`COMMIT` en una sola transacción, backfill de **todas** las filas preexistentes (incluidas
las no-terminales) con el `project_key` del propio harness — que es el proyecto donde se generaron. Y dejá
documentada la **incompatibilidad hacia atrás**: `store.py:150` es fail-closed ante `schema_version != SCHEMA`,
así que un checkout pre-005 sobre una DB schema-5 degrada a `ROUTING_UNAVAILABLE` (comportamiento correcto,
pero hay que decirlo).

**9. P1 NO depende del vault.** El scaffold de P1 (T-108) hace `ai/state/features/` + copia de scripts
genéricos + id de proyecto. **Sin** link de vault: eso es P2. El contrato original los mezclaba y hacía
imposible aceptar P1 solo.

**10. AC-05 congela un archivo que P2 va a editar.** El self-scaffold (T-109) hace de
`ai/scripts/feature-state.py` una copia byte-idéntica del template `PROYECTO/ai/scripts/feature-state.py`.
P2 edita ese template (`notes_root`), así que **P2 tiene la obligación de re-sincronizar la copia**. Está en el
plan de P2; no es tu problema resolverlo, pero sí saber que el drift check que agregás es el que se lo va a
exigir.

## Piezas existentes a REUSAR (no inventes paralelas)

| Necesitás | Ya existe en |
|---|---|
| Sustituir la raíz absoluta en artefactos instalados | `install.py:69-72` + placeholder `__SET_AGENTS_ROOT__` (consumidor actual: `Global/_shared/opencode.json:105`; regresión: `tests/test_harness.py:1637`) |
| Walk-up por ancestros | `find_vault` en `set_agents_app.py:1018-1029` (**corregí el bug de `.parents`**) |
| Precedencia explícito > descubierto | el parámetro `explicit` de `find_vault` (`:1019-1021`) |
| Invocar el CLI con path absoluto + cwd anclado | `set_agents_spawn.py:285-291` (`_run_app_cli`: `[sys.executable, str(APP_CLI), *args]`, `cwd=ROOT`) — es el patrón correcto ya implementado |
| Seams de test por env | `SET_AGENTS_ROOT`/`SET_AGENTS_STATE` en `set_agents_app.py:28,32-34` |
| Copia create-if-missing sin pisar | el dict `FILES` de `bootstrap_project.py:23-61,94-103` |
| Lista de scripts genéricos a copiar | `sync-project.sh:14` (`GENERIC=(...)`) |
| Read-merge-write de config | `set_auto_update` en `set_agents_app.py:461-469` |

## Invariantes que NO se tocan

- **ADR-0005**: la DB de ruteo vive en `~/.local/state/set-agentes/routing-v2`, derivado de
  `pwd.getpwuid(os.getuid()).pw_dir`, **inmune a redirección por entorno** (`store.py:23-29`). Agregás una
  **columna**, nunca cambiás la ubicación. Confundir las dos cosas es non-goal explícito.
- **`metric_rollups` queda global** por diseño (la calidad de un modelo es propiedad del par
  proveedor/modelo, no del proyecto). Los chequeos de identidad/independencia leen **sólo**
  `dispatches`/`dispatches_review`, **nunca** `metric_rollups`.
- **El envelope de `--doctor --harness pi` de la 004** (`cmd_doctor`, `set_agents_app.py:359-368`, pinneado a
  schema-2) queda byte-idéntico. La superficie de vault es P2 y va aparte.
- Núcleo de la 004 intacto: ciclo autorización/dispatch/terminal, AM-1/AM-2, variantes OpenCode, lane Pi.
- El literal `set-agents` **no** entra al allowlist: la superficie sancionada sigue siendo el par explícito
  intérprete+script, auditable.
- Separación de deberes: **AC-09 (la prueba del invitado) no la valida el implementador**. La corre el
  gate-runner/package-reviewer. No la marques como verificada vos.
- Nunca loguear secretos/tokens/PII. Regresiones nunca debilitadas.

## Gates del paquete

`python3 -m unittest discover -s tests -v` (el conteo neto de asserts nunca baja) · `./build.sh --check`
(incluye el nuevo drift check interno) · `py_compile` de `ai/scripts/*.py` + `routing_core/*.py` ·
`./ai/scripts/verify.sh` → `VERIFY_PASS` (incluye la nueva aserción de placeholder / cero paths absolutos en
`Global/**`) · `git diff --check` · ownership vs baseline del paquete.

**QA en vivo (AC-09, ejecutado por el gate-runner, no por vos):** árbol temporal aislado de punta a punta
(clon, `$HOME` falso, proyecto scaffoldeado), con la matriz: nombre de directorio de clon no-default, `$HOME`
sin `~/.local/bin` en PATH, `HARNESS_HOME` **con un espacio**, proyecto scaffoldeado **que no es repo git**, y
`verify.sh` verde desde el clon invitado. Observables por caso: exit code + envelope JSON + el valor concreto
de `project_key`.

## Propiedad (owned_paths)

`ai/scripts/{install.py,generate.py,coord_policy.py,set_agents_app.py,bootstrap_project.py,sync-project.sh,verify.sh}`,
`ai/scripts/routing_core/store.py`, `ai/scripts/{feature-state.py,check-owned-paths.py}` (nuevas copias),
`build.sh`, `Global/_canonical/agents/orchestrator.md`, `docs/adr/0008-two-roots-portability.md`,
`tests/{test_harness.py,test_routing.py}`.

Read-only: `ai/catalogs/routes.v1.toml`, `roles.tsv`, `models.toml`,
`PROYECTO/ai/scripts/feature-state.py` (es el template single-source: lo **copiás**, no lo editás — editarlo
es P2).
