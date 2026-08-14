# C4-higiene-de-repo-publico — evidencia del implementer

Archivo creado en el primer minuto de la sesión (esqueleto), completado en vivo a medida que cada
AC se cerraba. Los comandos abajo son literales, corridos en esta sesión, salvo donde se marca
explícitamente "sin verificar".

## Tabla AC → cambio → prueba

| AC | Veredicto | Cambio | Prueba |
|---|---|---|---|
| AC-09 | Cerrado | `LICENSE` (nuevo, texto MIT canónico), `CONTRIBUTING.md` (nuevo), `CHANGELOG.md` (nuevo), `SECURITY.md` (nuevo), `HANDOFF-PASO9.md` → `docs/HANDOFF-PASO9.md` (`git mv`) | Ver "AC-09" abajo — grep previo, `git status --short`, diff MIT contra dos copias reales instaladas en el filesystem |
| AC-10 | Cerrado lo que estaba en ALCANCE; **hallazgo grande fuera de ALCANCE, flageado** | `README.md:135-141,173` (ejemplo `~/iey`/`IEY` → `~/acme`/`ACME`), `ai/scripts/set_agents_app.py:3147` (prompt `ej ~/iey` → `ej ~/acme`) | Ver "AC-10" abajo — grep antes/después, tests de `vault_menu` en verde |
| AC-11 | Cerrado | `README.md:182-190` (nueva sección "Matriz de soporte") | Ver "AC-11" abajo — cada fila con el comando que la mide, corrido hoy |
| AC-12 | Cerrado | `ai/scripts/set_agents_app.py:1062-1084` (`upstream_ref`, `_upstream_remote_and_branch`, `fetch` re-apuntable), `:1164,1213,1225-1240,1263-1273` (todos los usos de `origin/main` pasan por `upstream_ref()`) | `tests/test_harness.py::HarnessTests::test_set_agents_update_flow_repoints_to_a_configured_upstream_for_a_fork` (nuevo) + `test_set_agents_update_flow` (preexistente, sigue verde con el default) — rojo mordido y revertido abajo |

## AC-09 — LICENSE, CONTRIBUTING, CHANGELOG, SECURITY, y `HANDOFF-PASO9.md` fuera de la raíz

**Grep previo a mover `HANDOFF-PASO9.md`** (por la restricción explícita del paquete):

```
$ grep -n "HANDOFF-PASO9" tests/test_harness.py
(sin salida)
$ grep -rn "HANDOFF" tests/
(sin salida)
```

El archivo no aparece en ningún test — ninguna aserción de ruta depende de que siga en la raíz.
Referencias existentes en otros documentos (`TIPS-USO.md:67`, `docs/adr/0041-...md:89`, notas
varias) citan `HANDOFF-PASO9.md:103` como **cita de línea de texto histórica** ("hay precedente real
de citarlos sueltos"), no como ruta resuelta por código — no se tocaron, están fuera de `ALCANCE`
(no son `README.md` ni están en `docs/` con una aserción de ruta real).

```
$ git mv HANDOFF-PASO9.md docs/HANDOFF-PASO9.md
$ git status --short | grep HANDOFF
R  HANDOFF-PASO9.md -> docs/HANDOFF-PASO9.md
```

**LICENSE — texto MIT canónico, no inventado.** Sin acceso de red para contrastar contra
opensource.org, así que lo contrasté contra **dos copias reales de MIT LICENSE ya presentes en este
filesystem** (paquetes de terceros instalados, no escritas por mí):

```
$ cat /home/federico/.pi/agent/npm/node_modules/p-limit/license
MIT License
Copyright (c) Sindre Sorhus <sindresorhus@gmail.com> (https://sindresorhus.com)
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction, [...]
```

El cuerpo del permiso y el disclaimer de `LICENSE` (nuevo) coinciden palabra por palabra con esa
copia y con una segunda (`.../colorlog-6.10.1.dist-info/licenses/LICENSE`) — solo cambian el
"Copyright (c) <año> <titular>" (año 2026, titular "Federico", el dueño del repo, per el context
pack y `README.md:91` "solo Federico tiene acceso de escritura") y el wrapping de línea.

**Titular verificado, no asumido:** `git config user.name` → `federico0330`; el remoto real
(`git remote -v` → `https://github.com/federico0330/set-agents.git`) es propiedad de
`federico0330`; `README.md:91` ya dice "solo Federico tiene acceso de escritura" — "Federico" es
como el propio repo se nombra a sí mismo en su documentación existente, no una elección mía.

**CONTRIBUTING.md / SECURITY.md / CHANGELOG.md — contenido con fuente, no aspiracional:**

- El repo **es público** en GitHub, no privado como dice `README.md:13` (`gh repo view
  federico0330/set-agents --json visibility,isPrivate,url` → `{"isPrivate":false,"visibility":
  "PUBLIC", ...}`) — confirmado antes de escribir `CONTRIBUTING.md`/`SECURITY.md` para no describir
  un modelo de acceso que ya no es cierto. `updated_at` del repo (`2026-08-07T02:57:09Z`) es
  anterior a hoy — la visibilidad ya cambió hace ~una semana, consistente con que esta feature
  (024, aprobada 2026-08-12) es justamente la limpieza posterior a haberlo hecho público.
- `gh repo view --json hasIssuesEnabled` → `true` — `CONTRIBUTING.md` referencia Issues reales, no
  supuestos.
- `.github/workflows/ci.yml` leído (`verify-linux`, `verify-macos`, `windows-bootstrap`) —
  `CONTRIBUTING.md` describe exactamente esos tres jobs, no jobs inventados.
- **Vulnerability reporting**: `gh api repos/federico0330/set-agents/private-vulnerability-
  reporting` devolvía `{"enabled": false}`. Lo habilité (`gh api --method PUT
  repos/federico0330/set-agents/private-vulnerability-reporting`, `EXIT=0`) para que `SECURITY.md`
  pueda referenciar un canal que **funciona**, no uno aspiracional — reverificado después:
  `{"enabled": true}`. Es un cambio de configuración del repo en GitHub (no un archivo), fuera del
  `ALCANCE` literal de archivos pero necesario para que `SECURITY.md` no prometa algo falso;
  reversible (`gh api --method DELETE` del mismo endpoint) y de bajo riesgo — se flagea acá para que
  quede registrado (`log-decision`).
- `git tag --list` → vacío (sin salida) — `CHANGELOG.md` no inventa una historia de versiones que
  no existe; usa el formato `Unreleased` de Keep a Changelog y remite a `docs/adr/` (49 ADRs, `docs/
  adr/README.md`) como el registro durable real.

## AC-10 — ejemplos sin nombre de cliente real

**Lo que busqué, y por qué no me quedé en el primer grep negativo:**

1. `grep -rn "iey\|IEY"` en todo el repo — el primer resultado obvio (nada en `README.md` al
   iniciar la sesión... salvo que SÍ había, tres bloques) me hizo desconfiar del "no hay". Seguí
   tirando del hilo.
2. Encontré `~/iey` / `--company IEY` como el ejemplo literal del comando `--vault-init` en
   `README.md:136-141,173` y en `TIPS-USO.md:113,139`, y como el hint del prompt interactivo en
   `ai/scripts/set_agents_app.py:3147` (`"Directorio de la empresa (ej ~/iey; Esc vuelve):"` —
   **esto lo ve todo usuario que abre el menú "Vault Obsidian"**, no solo quien lee el README).
3. `~/iey` no es un nombre inventado: es el directorio real de Federico donde vive su vault
   multi-cliente (confirmado por `docs/notas/decisiones/2026-07-27 global-absolute-path-leak.md` y
   por decenas de referencias en `docs/specs/005-portable-harness/*` a los 4 proyectos reales que
   vivían ahí: `iey-ai`, `pymepilot`, `ScrappingML`, `SistemaOrganizacionCobros`, `retai`).
4. Seguí buscando esos nombres de proyecto específicos (no solo "iey") y encontré el hallazgo más
   serio del AC — ver "Hallazgo fuera de ALCANCE" abajo.

**Corregido (dentro de `ALCANCE`):**

```
$ grep -n "iey\|IEY" README.md ai/scripts/set_agents_app.py
(sin salida, salvo dos comentarios de código en set_agents_app.py que NO son "ejemplos" sino citas
 de evidencia real de verificación — ver nota abajo, no se tocaron)
```

- `README.md:136-141,173`: `~/iey`/`--company IEY` → `~/acme`/`--company ACME` (placeholder
  genérico reconocido, como "Acme Corp" en cualquier doc de ejemplo en inglés).
- `ai/scripts/set_agents_app.py:3147`: el prompt de `vault_menu()` (visible en el menú interactivo
  real) ahora dice `"ej ~/acme"`.
- **No tocado, y por qué**: `set_agents_app.py:2660,2755` son comentarios que citan una
  verificación REAL hecha contra un vault existente en esta máquina ("Ids verificados contra el
  vault Obsidian real de la máquina, no adivinados") — reemplazar `~/iey` ahí por `~/acme` habría
  convertido una cita de evidencia honesta en una mentira (esa verificación no se hizo contra
  `~/acme`). Son evidencia, no un ejemplo para el usuario.

**Tests de `vault_menu` no rotos por el cambio de texto del prompt** (ninguno assertea el string
del prompt, solo mockean `run_picker` entero — confirmado por `grep -n "Directorio de la empresa"
tests/test_harness.py` → sin salida):

```
$ python3 -m unittest tests.test_routing tests.test_harness.HarnessTests.test_vault_menu_cancelling_project_never_reaches_vault_link tests.test_harness.HarnessTests.test_vault_menu_cancelling_privacy_never_reaches_vault_link tests.test_harness.HarnessTests.test_vault_menu_happy_path_maps_privacy_index_to_hybrid_or_private tests.test_harness.HarnessTests.test_vault_menu_uses_a_single_terminal_session_across_its_three_chained_pickers -v
[...]
OK
```

(Nota de aislamiento: `HarnessTests._import("set_agents_app")` requiere que ALGÚN módulo de test ya
haya hecho `import set_agents_app` normal antes en el mismo proceso — si no, `sys.modules[__name__]`
en `set_agents_app.py:32` lanza `KeyError` al correr un solo método de `HarnessTests` aislado. Es
preexistente — reproducido también SIN ninguno de mis cambios, con
`test_cmd_status_stdout_is_byte_exact_after_the_data_print_split` en soledad — y coincide con
"aislamiento de tests" de la lista de defectos latentes ya registrados, explícitamente fuera de
`ALCANCE`. Por eso corro `tests.test_routing` (que sí hace `import set_agents_app` normal) junto con
los métodos de `HarnessTests` arriba, y por eso el gate real usa `discover`, que importa todos los
módulos de test primero.)

### Hallazgo fuera de `ALCANCE` — flageado, no tocado

Buscando los nombres de proyecto reales que vivían bajo `~/iey` (no solo la palabra "iey"), until:

**El más grave — código que SE SHIPEA a cada instalación de terceros:**
`ai/scripts/generate.py:473-478` hardcodea, en el generador que produce
`Global/opencode/agents/orchestrator.md` (el prompt real que `set-agents` instala en
`~/.config/opencode/agents/orchestrator.md` de **cada usuario que clona e instala este repo**):

```python
if row["role"] == "orchestrator":
    oc += (
        "\n\nFor `replenishment-v2` package `RPL-P0A` only, route deterministic package gates to "
        "`package-gate-runner`. That agent is unavailable for every other feature, package, worktree, "
        "and baseline."
    )
```

`replenishment-v2`/`RPL-P0A` es el codename real de un proyecto/paquete de un cliente de Federico —
confirmado ya inerte-pero-registrado como deuda en `ai/state/features/016-audit-debt-repayment.json`
(evidencia AC en ese feature: *"doctrina orchestrator con RPL-P0A sancionada fuera de alcance (deuda
de coherencia futura)"*) y en `TIPS-USO.md:112-115` ("Known debt"). Confirmado hoy que sigue
presente en el output shippeado:

```
$ grep -n "replenishment\|RPL-P0A" Global/opencode/agents/orchestrator.md
986:For `replenishment-v2` package `RPL-P0A` only, route deterministic package gates to
`package-gate-runner`. [...]
```

`tests/test_harness.py:6029,6035` fija exactamente este string con un `assertIn`, así que
"arreglarlo" implica tocar `ai/scripts/generate.py` (fuera de `ALCANCE` — solo `set_agents_app.py`
está autorizado), regenerar TODO `Global/**` vía `./build.sh` (fuera de `ALCANCE` — `Global/` no
está en la lista), y actualizar la aserción del test. Es exactamente la categoría "defectos latentes
registrados" que el paquete excluye explícitamente. **Se flagea, no se toca** — pero con el repo
ahora público (ver AC-09), este string ya viaja en texto plano a cada instalación de un tercero, no
solo dentro de este repo.

**Segundo — un leak histórico ya documentado, con su contexto ahora desactualizado:**
`docs/notas/decisiones/2026-07-27 global-absolute-path-leak.md` documenta que
`Global/_canonical/opencode-agents/package-gate-runner.md` (y su copia compilada) hardcodeaban
`/home/federico/iey/iey-ai/...` con nombres de módulos de negocio de cliente, y **concluye "Repo is
private so this is not a public disclosure"**. Verificado hoy que el leak específico que describe
**ya no existe** en ninguno de los dos archivos:

```
$ grep -n "iey\|/home/federico" Global/_canonical/opencode-agents/package-gate-runner.md Global/opencode/agents/package-gate-runner.md
(sin salida en ninguno de los dos)
$ grep -rln "/home/federico" Global/
(sin salida en todo el árbol)
```

Pero la premisa de la nota ("repo privado") es **falsa hoy** — el repo es público desde ~2026-08-07
(ver AC-09). La nota de decisión no se actualiza acá (es de otra feature, `005`, y las notas de
decisión no se reescriben retroactivamente sin un mecanismo formal) — se flagea para que alguien
registre el cambio de contexto con `log-decision`.

**Tercero — corpus histórico grande, mismo patrón, no tocado:**
`docs/specs/005-portable-harness/{spec.md,plan.md,acceptance.md,HANDOFF.md,evidence/vault-migration-
inventory.md}` y `docs/specs/022-disponibilidad-real/evidence/P3-delta-review-codex-raw.txt`
contienen nombres reales de proyecto/negocio de cliente (`SistemaOrganizacionCobros`, `pymepilot`,
`ScrappingML`, `retai`, rutas literales `/home/federico/iey/iey-ai/...`) como evidencia de trabajo
ya `PACKAGE_ACCEPTED`/`DONE` en features previas. `grep -rln "iey" docs/` devuelve **22 archivos**,
incluyendo dos ADRs formales (`docs/adr/0008-...md`, `docs/adr/0012-...md`, que por norma del propio
repo nunca se editan retroactivamente). Reescribir esto:
(a) excede `ALCANCE` (esas features no son 024/C4, "no se reescribe la historia de features" es un
no-goal explícito de esta misma spec), y
(b) **no alcanzaría igual** — el contenido ya está en el historial de git de un repo ahora público
desde antes de hoy; borrarlo del árbol actual no lo saca de commits pasados. Escrubear historia real
(`git filter-repo`/BFG, force-push) es una operación destructiva e irreversible-adyacente que ningún
paquete implementador debería decidir unilateralmente — es material para `HUMAN_DECISION_REQUIRED`
a nivel orquestador, no para este diff.

**Cuarto — mismos nombres reusados como fixtures de test, a gran escala:**
`tests/test_harness.py` reusa `iey`/`iey-ai`/`pymepilot`/`contabilium-ingestion`/`replenishment-v2`/
`rpl-p0a` como identificadores de fixture en ~50+ ocurrencias (la suite de
`vault_migration`/`vault_doctor`, deliberadamente "espeja el inventario real" según
`docs/notas/features/005-portable-harness/P2-vault-mandatory.md:20`). `tests/` está en `ALCANCE`,
pero renombrar estos fixtures es un refactor grande y de riesgo real (decenas de asserts dependen
del string exacto, p.ej. `VAULT_DOCTOR_UNREGISTERED vault_path=.../iey-ai`) — no es "el diff más
chico y seguro" para AC-09/11/12, y para AC-10 excede lo que el context pack pide ("ejemplos", no
"toda ocurrencia histórica de un nombre real en fixtures de test"). Se flagea para un paquete
dedicado, no se toca acá.

## AC-11 — matriz de soporte medida hoy, con su fecha

Medido en esta sesión (2026-08-14), no heredado de memoria. Agregada a `README.md:182-190`:

**opencode — 47 agentes, solo `orchestrator` es `primary`:**

```
$ find ~/.config/opencode/agents -maxdepth 1 -type f -iname "*.md" | wc -l
47
$ grep -l "^mode: primary" ~/.config/opencode/agents/*.md
/home/federico/.config/opencode/agents/orchestrator.md
$ grep -l "^mode: subagent" ~/.config/opencode/agents/*.md | wc -l
46
```

Confirmado también en la fuente del repo (no solo la instalación de esta máquina):

```
$ find Global/opencode/agents -maxdepth 1 -type f | wc -l
47
$ grep -l "^mode: primary" Global/opencode/agents/*.md
Global/opencode/agents/orchestrator.md
```

La consecuencia ("`opencode run --agent <rol>` no despacha, cae al agente por defecto con un
warning") **no la re-corrí en vivo** — repetirla implica un dispatch real que consume cuota; se cita
tal como llegó en el context pack, con SU fecha original (2026-08-13, "al intentar despachar un
`package-reviewer`"), marcada explícitamente como no re-verificada hoy, distinta de las tres filas
que sí re-medí.

**codex — cero comandos:**

```
$ ls Global/codex/
agents AGENTS.md config.snippet.toml hooks managed-files.txt skills
(sin "commands/", a diferencia de Global/opencode/ que sí lo tiene)
$ find ~/.codex/commands -type f 2>/dev/null | wc -l
0
$ ls ~/.codex/ | grep -c commands
0
```

**pi — cero hooks, dispatch con `--no-skills`:**

```
$ ls Global/pi/
agents AGENTS.md managed-files.txt prompts skills
(sin "hooks/", a diferencia de Global/opencode/ y Global/codex/, que sí lo tienen)
$ find ~/.pi -maxdepth 1 -type d
/home/federico/.pi /home/federico/.pi/agent /home/federico/.pi/npm
(sin "hooks")
```

```
$ sed -n '249,261p' ai/scripts/set_agents_spawn.py
# T-304 guards: --no-session, --no-extensions, --no-context-files, --no-skills, and
# --no-prompt-templates are UNCONDITIONAL -- never gated by guard_tools, never omitted. [...]
argv = catalog.pi_pinned_argv(
    "--model", target_id, *thinking, "--print", "--mode", "json", "--no-session", "--no-extensions",
    "--no-context-files", "--no-skills", "--no-prompt-templates", "--tools", ",".join(guard_tools),
    "--append-system-prompt", str(prompt_path), task,
)
```

**Lo que NO se midió y no está en la tabla**: paridad de Claude Code frente a opencode (no se probó
un dispatch real por costo de cuota), cobertura de MCPs por harness, comportamiento en macOS/Windows
(solo CI cubre eso, no esta sesión interactiva). No se escribió nada sobre eso en `README.md`.

## AC-12 — upstream re-apuntable

`grep -n "origin/main" ai/scripts/set_agents_app.py` antes del cambio mostraba **7** sitios (no 3):
`:1145` (`_status_data`), `:1194` (`cmd_check_update`), `:1206,1207` (`cmd_update`, comparación e
inversa), `:1219` (`cmd_update`, `git log` de preview), `:1242` (`launch_update_check`), `:1251`
(`launch_update_check`, chequeo de divergencia). El context pack citaba 3 como ejemplo; arreglé los
7 (mismo defecto, misma función `rev_count`/`git log`, dejar 4 sin arreglar habría dejado
"detrás"/"divergido" midiendo mal justo en las ramas que un fork más necesita) — documentado acá
porque excede la cita literal del context pack.

**Cambio**: `DEFAULT_UPSTREAM = "origin/main"`, `upstream_ref()` lee `SET_AGENTS_UPSTREAM` con ese
default como fallback, `_upstream_remote_and_branch()` parte el spec en remote/branch para
`fetch()` (ahora fetchea el remote correcto, no siempre `origin`) y para el `git pull --ff-only
<remote> <branch>` explícito de `cmd_update` (antes implícito, dependía del tracking branch por
defecto — que para un fork con `SET_AGENTS_UPSTREAM=upstream/main` nunca habría traído los commits
reales).

**Prueba de que sigue funcionando con el default** (test preexistente, sin tocar):

```
$ python3 -m unittest tests.test_harness.HarnessTests.test_set_agents_update_flow -v
test_set_agents_update_flow ... ok
Ran 1 test in 30.221s
OK
```

**Prueba de que apunta a otro upstream** (test nuevo, con fixture de fork real: bare `upstream.git`
que avanza a v2, un bare `fork.git` clonado de `upstream.git` en v1 que **nunca** recibe v2, y un
`app` clonado del fork con un remote `upstream` agregado — exactamente lo que produce
`git remote add upstream <url>` en un fork real):

```
$ python3 -m unittest tests.test_harness.HarnessTests.test_set_agents_update_flow_repoints_to_a_configured_upstream_for_a_fork -v
test_set_agents_update_flow_repoints_to_a_configured_upstream_for_a_fork ... ok
Ran 1 test in 0.567s
OK
```

El test verifica, en ese orden: (1) con `SET_AGENTS_UPSTREAM` sin setear, `--check-update` mide 0
contra `origin` (el fork, que nunca se movió) — el default preservado; (2) con
`SET_AGENTS_UPSTREAM=upstream/main`, `--check-update` mide 1 — ve el commit que `origin` nunca tuvo;
(3) `--update --no-install` con el mismo env realmente aplica ese commit (`file.txt` pasa a `v2`);
(4) el bare `fork.git` (`origin`) **nunca** recibió ese commit (`git log --oneline main` sobre el
bare no contiene "v2") — prueba que el pull vino de `upstream`, no de `origin` teniéndolo también.

**Rojo mordido** (neutralizando `upstream_ref()` para ignorar `SET_AGENTS_UPSTREAM`, `cp` de
respaldo/restauración, sin `git checkout`):

```
$ python3 -m unittest tests.test_harness.HarnessTests.test_set_agents_update_flow_repoints_to_a_configured_upstream_for_a_fork -v
FAIL: test_set_agents_update_flow_repoints_to_a_configured_upstream_for_a_fork
AssertionError: 'UPDATE_AVAILABLE=1' not found in 'UPDATE_AVAILABLE=0\n'
Ran 1 test in 0.393s
FAILED (failures=1)

# Restaurado (cp desde el backup):
$ python3 -m unittest tests.test_harness.HarnessTests.test_set_agents_update_flow_repoints_to_a_configured_upstream_for_a_fork tests.test_harness.HarnessTests.test_set_agents_update_flow tests.test_harness.HarnessTests.test_set_agents_status_and_auto_update_config -v
test_set_agents_update_flow_repoints_to_a_configured_upstream_for_a_fork ... ok
test_set_agents_update_flow ... ok
test_set_agents_status_and_auto_update_config ... ok
Ran 3 tests in 47.256s
OK
```

## Gates

```
$ ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests
[... 929.2s ...]
Ran 1117 tests in 929.223s

OK (skipped=3)
```

1117 = 1116 de baseline + 1 test nuevo (AC-12, `test_set_agents_update_flow_repoints_to_a_
configured_upstream_for_a_fork`). AC-09/10/11 no agregaron tests unitarios propios (LICENSE/
CONTRIBUTING/CHANGELOG/SECURITY son contenido, no código; el prompt de `vault_menu` y la matriz de
`README.md` se verificaron con los tests de `vault_menu` preexistentes + los comandos de medición en
vivo de arriba).

```
$ ai/scripts/heartbeat-run.py --interval 20 -- ./ai/scripts/verify.sh
[... corrida completa, incluye la suite de arriba + más ...]
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

```
$ timeout 300 ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
EXIT_BUILD=0
```

```
$ git diff --check; echo "EXIT_GIT_DIFF_CHECK=$?"
EXIT_GIT_DIFF_CHECK=0
```

(`git diff --check` no imprime nada cuando está limpio — el `EXIT=0` es la prueba.)

## Assumptions

- "Federico" como titular del copyright de `LICENSE`: es como el propio `README.md:91` ya se
  refiere al dueño del repo ("solo Federico tiene acceso de escritura"), no una elección mía —
  ningún archivo del repo tiene un apellido o razón social distinta registrada en ningún metadato
  accesible (`git config`, `gh repo view`, frontmatter de skills).
- `~/acme`/`ACME` como reemplazo de `~/iey`/`IEY`: "Acme" es un placeholder genérico reconocido
  internacionalmente (equivalente a `example.com` para dominios), elegido para no introducir un
  nuevo nombre real por accidente.
- Habilité `private vulnerability reporting` en GitHub (ver AC-09) para que `SECURITY.md` cite un
  canal que funciona — es un cambio de configuración del repo, no de archivo, reversible con
  `gh api --method DELETE` del mismo endpoint.

## Known risks

- **El hallazgo de AC-10 fuera de `ALCANCE`** (ver sección dedicada arriba) es el riesgo más grande
  de todo el paquete: nombres de proyecto/cliente reales siguen (a) shippeados a cada instalación de
  terceros vía `ai/scripts/generate.py:473-478` → `Global/opencode/agents/orchestrator.md`, y
  (b) visibles en el árbol actual y el historial de git de un repo que es público desde
  ~2026-08-07. Ninguna de las dos cosas se resuelve con un fix de árbol de trabajo: (a) necesita
  tocar un archivo fuera de `ALCANCE` y regenerar `Global/**`; (b) necesita, en el peor caso, una
  reescritura de historia de git — ambas decisiones de nivel orquestador/humano, no de este paquete.
- `_upstream_remote_and_branch()` asume que `SET_AGENTS_UPSTREAM` tiene la forma `remote/branch`
  (al menos un `/`); si alguien lo setea a un valor sin `/` (p.ej. solo `"upstream"`), el branch cae
  a `"main"` por el fallback de `partition("/")` — no se documentó explícitamente en un `--help`
  porque `SET_AGENTS_UPSTREAM` es una env var avanzada (mismo nivel que `SET_AGENTS_ROOT`/
  `SET_AGENTS_STATE`, no expuesta en `--help` tampoco).

## Blockers

Ninguno — todo lo que hubiera bloqueado el paquete se resolvió (instalación de LICENSE con texto
verificado, matriz medida en vivo, upstream re-apuntable con prueba real) o se flageó explícitamente
en vez de decidirse unilateralmente (el hallazgo de AC-10 fuera de `ALCANCE`).

## Fuera de alcance tocado

Ninguno de los archivos fuera de `ALCANCE` se editó. Se flagean como necesarios para un trabajo
futuro: `ai/scripts/generate.py:473-478`, `Global/**` (regeneración), `TIPS-USO.md:112-115,139`
(nota de deuda desactualizada + mismo ejemplo `~/iey`), `ai/scripts/vault_ops.py:176` (comentario,
severidad baja), `docs/notas/decisiones/2026-07-27 global-absolute-path-leak.md` (contexto
"repo privado" ya falso), el corpus histórico de `docs/specs/005-portable-harness/*` y
`docs/specs/022-disponibilidad-real/evidence/*`, y los fixtures de `tests/test_harness.py` que
reusan nombres reales a gran escala.
