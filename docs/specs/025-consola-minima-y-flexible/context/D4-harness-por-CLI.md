# Context pack — D4-harness-por-CLI

Spec: `docs/specs/025-consola-minima-y-flexible/spec.md`, **AC-09, AC-10, AC-11**. Depende de D3.

## Las cuatro afirmaciones del plan, verificadas una por una

| Afirmación | Veredicto | Evidencia |
|---|---|---|
| manifiesto de archivos gestionados | **CIERTA** | `MANIFEST = STATE_DIR / "managed-files.json"` `install.py:47`; se escribe recién tras los smoke checks, :524-536. Y hay un segundo: `JSON_MANIFEST = "managed-json-paths.json"` :58 |
| poda de huérfanos | **CIERTA** | `previous_targets()` :326-342 con cerca de seguridad ("never prune anything outside a managed harness root", :339-340); `orphans` :380-383; borrado :488-491; `prune_empty_dirs` :345-359; reporta `PRUNED_ORPHANS=` :493 |
| backup con rotación | **CIERTA** | `backups_root` :449, dir por timestamp :448-451, `chmod 0700` :453-454, **rotación a 20**: `for old in sorted(backups_root.iterdir())[:-20]: shutil.rmtree(...)` :455 |
| rollback | **CIERTA** | `rollback()` :470-477, `except Exception: rollback(); print("INSTALL_ROLLED_BACK …")` :572-575; `missing.json` :467 para saber qué no existía |

**Las cuatro son ciertas.** Pero el tamaño del paquete cambia igual, por lo de abajo.

## Lo que YA existe de AC-09 (y el plan no dice)

**Instalar en un solo CLI ya funciona, de punta a punta.** Cadena completa medida:

- `install.py:24` — `--target`, `action="append"`, `choices=("opencode","claude-code","codex","pi")`;
  `selected`/`targets` :36-37 filtran todo el resto del script.
- `build.sh:15` (usage), :45 (`--target` acumula), :148-155 (los pasa a `install.py`).
- `install.sh:18` (`--harness claude|opencode|codex|pi|all`), :29-32, y el mapeo :387-392
  (`claude` → `--target claude-code --target pi`, "pi rides on the same Anthropic auth").

**AC-09 es, en su mayor parte, verificar y exponer, no construir.** Lo que falta es la superficie en
el menú/CLI de `set_agents_app.py` y la prueba de que los otros tres quedan realmente vírgenes.

## Lo que NO existe (medido)

`grep -n "uninstall\|desinstal" ai/scripts/*.py *.sh` → **0 resultados en todo el repo.** No hay
desinstalación de ningún tipo, ni total ni selectiva. AC-10 es superficie nueva completa.

## El registro de scope, y su lado filoso

`install-targets.json` — escrito en `install.py:562-571`, leído por `check-drift.sh:26-40` y por
`_install_scope()` en `set_agents_app.py:886-893` (que lo muestra en `--doctor-all`).

Dos comportamientos que **una desinstalación tiene que revertir a mano**:

- `install.py:562-568` — el scope se **fusiona, nunca se angosta**: *"a later `--target` run extends
  the scope, it never silently narrows it"*. Desinstalar exige la operación opuesta.
- `install.py:569-570` — **`if not args.target: scope = set(all_targets)`**: un install sin
  `--target` reescribe el scope a los cuatro.

Si AC-10 borra archivos y no angosta `install-targets.json`, `check-drift.sh` sigue comparando
contra un árbol que ya no está instalado → **DRIFT_DETECTED permanente y fantasma**. Lo mismo con
`MANIFEST`: `install.py:525-535` **preserva** las entradas fuera de los roots seleccionados, así que
una desinstalación que no limpia las entradas de su root deja huérfanos que un install futuro va a
intentar podar (o peor, que un `previous_targets()` va a considerar suyos).

## La trampa

**Los tres archivos más importantes de cada árbol no son archivos gestionados: son merges dentro de
archivos del usuario, y el manifiesto no los conoce.**

`SPECIAL` (`install.py:38-42`) saca de `managed_files()` (:126) a `opencode.json`,
`settings.overlay.json` y `config.snippet.toml`. `effective_specials()` :184-196 los **fusiona**
sobre el archivo vivo del usuario: `~/.config/opencode/opencode.json`, `~/.claude/settings.json`,
`~/.codex/config.toml`. Y `new_targets` :378 sale sólo de `files`, así que **los specials nunca
entran a `MANIFEST`** (:535). Consecuencia dura:

> Desinstalar claude-code requiere **des-fusionar** claves de `~/.claude/settings.json` **sin ningún
> registro de cuáles puso el instalador**. Borrar el archivo es destruir configuración del usuario.

La única excepción es opencode: `JSON_MANIFEST` (:58) registra los ids bajo `provider.*` que este
instalador escribió, con la disciplina explicada en `apply_provider_registry` :145-181 — "un id que
este instalador escribió y el registry ya no tiene es seguro de borrar; cualquier otra clave viva ni
se lee". **Ese es el patrón a extender para AC-10**, y extenderlo a `settings.json`/`config.toml` es
el verdadero trabajo del paquete. Presupuestalo.

Trampa secundaria, y es un defecto real de hoy: **`cmd_update` reinstala los cuatro árboles.**
`set_agents_app.py:1252` arma `install = [str(ROOT / "build.sh"), "--install"]` **sin `--target`** →
`install.py:569-570` → un usuario que instaló con `install.sh --harness claude` y después usa
"Actualizar" en el menú **recibe los cuatro árboles y su scope vuelve a los cuatro**. Esto es
lectura de código, **no lo ejecuté** (prohibido tocar `~`): verificalo en un `--home` temporal antes
de citarlo como bug. Si se confirma, AC-09 no está cumplido aunque `--target` exista.

Y la guarda que te va a frenar si improvisás: `install.py:397-416`,
`INSTALL_ABORTED_UNSAFE_COLLISION` — en `~/.pi/agent/agents/`, un archivo preexistente que el
instalador no registró haber escrito **aborta con exit 2 y sin flag de override**. Un reinstall tras
una desinstalación mal hecha se topa con esto.

## AC-11 — "usar un CLI virgen por esta vez"

No hay nada. Los dos ejes que ya existen y hay que decidir cuál usás: el árbol instalado en `~`
(estático, horneado) versus lo que el proceso lee en tiempo de ejecución. Los CLIs aceptan `--cwd`
y los spawns ya manejan `--spawn-cwd`/`--cwd` (`coord_policy.py:96-118`). Un "virgen por esta vez"
que borre y reponga archivos en `~` **no es aceptable**: tiene que ser una sesión que no los lea.
Definilo en el ADR antes de escribir código.

## La mordida exigida

Nueve guardas falsas-verdes en este repo. Todo esto se prueba con `--home` en un **tmpdir**, nunca
contra `~` (`install.py:23-24` toma `--staging` y `--home` como argumentos obligatorios: usalos):

1. **Aislamiento (AC-09/AC-10)**: instalá dos árboles en un home falso, desinstalá uno, y assertá
   que el otro queda **byte-idéntico** (hash de cada archivo, antes y después). Rojo: hacé que la
   desinstalación toque un path del otro árbol, confirmá el fallo, revertí.
2. **El scope se angosta**: tras desinstalar, `install-targets.json` ya **no** lista ese target, y
   `check-drift.sh` no lo reporta. Rojo: no toques el scope y confirmá el drift fantasma. **Este es
   el test que nadie va a escribir solo.**
3. **Des-merge no destructivo**: una clave que el usuario puso a mano en `settings.json` /
   `config.toml` / `opencode.json` **sobrevive** a la desinstalación. Rojo: borrá el archivo entero
   en vez de des-fusionar, confirmá el fallo.
4. **El manifiesto queda consistente**: reinstalar después de desinstalar termina en `INSTALL_PASS`
   y sin `INSTALL_ABORTED_UNSAFE_COLLISION`. Rojo: dejá las entradas del MANIFEST y mirá qué pasa.
5. **AC-11**: el CLI virgen no lee el árbol instalado **y no lo modifica** — assert de ambas mitades.

## Restricciones

- **ADR reservado: 0055** (`ls docs/adr/`; 0050 reservado sin escribir por D1, 0052 tomado por
  027/P4, 0053 D2, 0054 D3). Indexalo en `docs/adr/README.md`.
- `owned_paths`: `ai/scripts/install.py`, `install.sh`, `ai/scripts/set_agents_app.py`, `tests`,
  `docs/adr`. `build.sh` no está declarado: si necesitás tocarlo, **avisá antes**.
- **No toques nada bajo `~`. Nunca corras `./build.sh --install` ni `./install.sh`.** Todo con
  `--home <tmpdir>`.
- **Nunca borres un archivo que el manifiesto no registre como propio.** Es la doctrina de
  ADR-0008 D2 que `install.py:385-396` ya cita; una desinstalación no la relaja, la hereda.
- No cambies el orden de los smoke checks (:497-521) ni el "escribir sólo en el camino feliz"
  (:522-524): es lo que hace seguro el rollback.
- No uses `git checkout`/`restore`/`stash`.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**) · `./ai/scripts/verify.sh` →
`VERIFY_PASS` · `./build.sh --check` → `GLOBAL_TREE_SYNC_OK` + `BUILD_CHECK_PASS` ·
`git diff --check`. Manual: `install.py --preview --home <tmpdir>` → `MANAGED_DIFF_FILES=<n>`.

**Comandos largos: `ai/scripts/heartbeat-run.py --interval 20 -- <comando>`** (ADR-0041).

## Evidencia

`docs/specs/025-consola-minima-y-flexible/evidence/D4-implementer.md`, primer minuto: tabla AC →
cambio (`archivo:línea`) → prueba; **el veredicto sobre `cmd_update` sin `--target`** (confirmado o
descartado, con la corrida en `--home` temporal pegada); **la estrategia de des-merge de los tres
specials**, clave por clave; los hashes antes/después del árbol que no se toca; y las cinco pruebas
de mordida con su rojo. Cada bloque literal o marcado como recortado.

## Fuera de alcance

Menú/flags/`--json` (D1) · spinner (D2) · posturas (D3) · vault (D5) · el ruteo y el sort key ·
rediseñar el merge de `config.toml` · el codename de cliente de 024, bloqueado esperando decisión.
