# Continuidad en Windows

Todo lo que hace falta para levantar este harness en una máquina Windows y seguir trabajando
con IA donde quedó. Incluye qué viaja solo, qué tenés que llevar a mano, dónde vive cada
credencial, y el estado real del proyecto: qué está hecho contra qué falta.

Medido el **2026-09-11** contra el árbol en `5193472`. Lo que no se midió dice "sin verificar".

---

## 0. Leé esto antes de commitear nada

**El repo es PÚBLICO.** Medido: `gh repo view --json visibility` devuelve `PUBLIC` para
`github.com/federico0330/set-agents`. `README.md` lo dice bien; `INSTALACION.md` y `TIPS-USO.md`
todavía afirman que es privado y que la invitación de collaborator es el control de acceso.
No lo es.

Dos consecuencias directas:

1. **Ningún secreto entra acá.** Ni cifrado, ni "lo borro después".
2. **Borrar el commit no borra el dato.** Un objeto pusheado a GitHub sigue siendo accesible
   por su SHA aunque reescribas la rama, y los forks y cachés lo conservan. Sacarlo de verdad
   requiere reescribir historia, forzar push y pedirle a GitHub que purgue. Asumí que lo que
   subís una vez es público para siempre.

Para llevarte los secretos usá la sección 4. No el repo.

---

## 1. Qué viaja solo y qué tenés que llevar

| Qué | Dónde vive hoy | Cómo llega a Windows |
|---|---|---|
| El harness (código, specs, ADRs, agentes) | este repo | `git clone` — es público, no necesita login |
| **Estado del workflow** | `ai/state/` | **NO viaja.** Está en `.gitignore` (ADR-0047). Copia manual o se pierde |
| Gustos de esta máquina (modelos, suscripciones) | `~/.local/state/set-agentes/*.toml` | copia manual, o los rehacés con el wizard |
| Credenciales de los CLIs | ver sección 3 | **no se copian**: re-login, 5 minutos |
| Vault Obsidian | `~/iey/obsidian` | Syncthing, ya configurado (carpeta `obsidian-iey`) |
| Memoria de Claude Code | `~/.claude/projects/-home-federico-SET-AGENTES/memory/` | copia manual (3 notas) |
| Notas del proyecto | `docs/notas/` | viajan por git, están trackeadas |

### El punto que más duele: `ai/state/`

Ahí viven los 36 ledgers de feature, `decisions-log.jsonl` (325 KB), la bitácora y `STATUS.md`.
Está gitignoreado a propósito: un clon nuevo arranca con `ai/state.seed/`, un esqueleto vacío
que `seed-state.py` copia solo si el directorio no existe.

Si no lo llevás, en Windows arrancás con historia cero. Para llevarlo:

```bash
# en Linux, antes de migrar
tar czf ~/set-agents-state.tgz -C ~/SET-AGENTES ai/state
```

Y en Windows (dentro de WSL), **antes** de correr nada del harness:

```bash
tar xzf /mnt/c/Users/<vos>/set-agents-state.tgz -C ~/SET-AGENTES
```

`seed-state.py` no pisa un `ai/state/` que ya existe, así que el orden importa: primero el
tar, después `./set-agents`.

---

## 2. Los primeros diez minutos en Windows

```powershell
# 1. PowerShell, en la máquina nueva. Bajá install.ps1 del repo y corrélo.
.\install.ps1
```

Instala WSL2 + Ubuntu, crea tu usuario de Linux solo, y sigue adentro. Si Windows pide
reiniciar, queda registrado para continuar al volver a iniciar sesión. Vas a ver un UAC
pidiendo administrador: es para instalar WSL.

Después, dentro de WSL:

```bash
git clone https://github.com/federico0330/set-agents.git ~/SET-AGENTES
cd ~/SET-AGENTES

tar xzf /mnt/c/Users/<vos>/set-agents-state.tgz -C .     # el estado, ANTES de arrancar
mkdir -p ~/.local/state/set-agentes
cp /mnt/c/Users/<vos>/set-agentes-overlay/*.toml ~/.local/state/set-agentes/

./set-agents          # menú → "Instalar / Reparar"
```

Los cuatro `.toml` del overlay que conviene traer, todos de `~/.local/state/set-agentes/`:

| Archivo | Qué guarda |
|---|---|
| `config.toml` | auto-update, modo experto, postura, metodología, ruta del vault |
| `models.local.toml` | tu pin de modelo por área o rol (ADR-0071) |
| `subscriptions.local.toml` | qué proveedores tenés contratados |
| `model-preference.toml` | el pin del orquestador |

Ninguno tiene secretos. Son preferencias.

Dos advertencias sobre esa copia. La ruta del vault que trae `config.toml` hoy está rota
—apunta a `/var/tmp/tmpb11obg_s/empresa/obsidian`, un temporal de un test que ya no existe—
así que rehacela en Windows con `set-agents --vault-init`. Y la carpeta de memoria de Claude
Code lleva la ruta del proyecto en el nombre: si tu usuario de WSL no es `federico`, el
directorio destino cambia, copiá las notas al que corresponda.

Verificación de que quedó bien:

```bash
set-agents --doctor-all     # harnesses, CLIs y proveedores autenticados
./ai/scripts/check-drift.sh # tiene que dar DRIFT_OK
./ai/scripts/verify.sh      # el gate completo, ~15 min
```

**Ojo con Windows nativo:** el harness corre *dentro* de WSL, no en Windows. En Windows nativo
se saltean 669 de 1326 tests porque `CreateProcess` no entiende shebangs (`.github/workflows/ci.yml:66-70`).
CI en `windows-latest` sólo verifica el bootstrap; el gate que de verdad cubre Windows es el de Linux.

---

## 3. Dónde vive cada credencial

Nada de esto se commitea y nada de esto hace falta copiar: cada CLI te vuelve a loguear por
navegador en un par de minutos. La tabla es para que sepas qué vas a tener que rehacer.

| CLI | Archivo en Linux | Cómo se rehace |
|---|---|---|
| OpenCode | `~/.local/share/opencode/auth.json` | `opencode auth login` |
| Claude Code | `~/.claude/.credentials.json` | `/login` dentro de `claude` |
| Codex | `~/.codex/auth.json` | `codex login` |
| GitHub CLI | `~/.config/gh/hosts.yml` | `gh auth login` (device flow) |
| pi | `~/.pi/agent/auth.json` | login del CLI |
| Cursor | `~/.cursor/` | login de la app |

El instalador detecta cuáles faltan y lanza los logins que correspondan. El OAuth lo completás
vos en el navegador, siempre.

`models.toml` y `tools.toml` **no** tienen claves: son catálogos de nombres de modelo y de
herramientas. Se commitean sin problema.

---

## 4. Si querés llevarte los secretos igual

No por el repo. Tres caminos, de mejor a peor:

1. **Re-loguearte.** Es lo que recomienda el propio instalador y tarda menos que cifrar.
2. **Por el vault.** Syncthing ya sincroniza `~/iey/obsidian` entre tus máquinas, P2P, sin
   nube. Un archivo cifrado ahí llega solo. Requiere que las dos máquinas estén prendidas a
   la vez.
3. **Cifrado a mano, fuera de git.** `gpg` ya está instalado en esta máquina:

```bash
# en Linux: rutas relativas al home, para que entren en cualquier home del otro lado
tar czf - -C ~ .local/share/opencode/auth.json .codex/auth.json .config/gh/hosts.yml \
  | gpg --symmetric --cipher-algo AES256 -o ~/creds.tgz.gpg

# en Windows, dentro de WSL
gpg -d ~/creds.tgz.gpg | tar xzf - -C ~
```

Llevalo en un pendrive o por el vault. **No al repo**, por lo de la sección 0: un blob cifrado
en un repo público es un blob que cualquiera puede bajar y atacar offline para siempre.

`gh secret` no sirve para esto: son variables de GitHub Actions, no un llavero.

---

## 5. El proyecto, en una pantalla

SET-AGENTES es un harness multi-agente que configura y coordina cinco CLIs de IA —
OpenCode, Claude Code, Codex, Cursor y pi — desde un solo comando, `set-agents`.

Lo que agrega sobre usar un CLI suelto son cuatro reglas, todas en código y no en un prompt:
el que escribe no aprueba, nada se afirma sin fuente, cada test tiene que demostrar que
muerde, y el estado vive en archivos y no en la conversación.

El flujo de entrega: `spec → desafío independiente → tu aprobación → paquetes → gates →
review en otro proveedor → reparación consolidada → delta review → aceptación → integración`.

Tamaño medido hoy:

| | |
|---|---|
| Roles de agente | 28 |
| Skills canónicas | 42 |
| Slash commands | 23 |
| ADRs | 74 |
| Specs | 49 |
| Tests | 1520 en 38 archivos |
| Python | ~30.800 líneas en `ai/scripts/` |

### Los cinco documentos que importan

- `README.md` — qué es y cómo se instala.
- `TIPS-USO.md` — el plano de control: lanes, drift, precedencia de contratos.
- `COMO-CAMBIAR-MODELO.md` — modelos por área y suscripción.
- `docs/specs/README.md` — la tabla de vigor: una fila por feature, qué está vivo.
- `docs/notas/BUENOS-DIAS.md` — el digest: qué quedó listo, qué falta, qué necesita tu decisión.

### Comandos que vas a usar

```bash
./set-agents                    # el menú
set-agents --status             # estado en una línea
set-agents --doctor-all         # qué detectó en la máquina
set-agents --model-state        # qué modelo está respondiendo, de verdad
./ai/scripts/verify.sh          # el gate completo
python3 ai/scripts/feature-state.py digest   # cierre de fase y de turno
```

---

## 6. Specs contra código: qué está

Primero la medición que respalda todo lo demás. `./ai/scripts/verify.sh` corrido hoy sobre
este árbol:

```
BUILD_CHECK_PASS · GLOBAL_TREE_SYNC_OK harnesses=5 · GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK · FEATURE_STATE_OK · VERIFY_PASS
1520 tests en 14m28s — fail=0 error=0 skip=4
```

Con eso como piso, el contraste contra `ai/state/features/` y `docs/specs/README.md`:

| Rango | Estado real |
|---|---|
| 001–038 | **Integrado.** Shipped en el índice. Tienen ledger en `ai/state/features/` 002–016 y 019–038; 001, 017 y 018 no |
| 039–044 | **Integrado.** Shipped, pero sólo declarado en la cabecera de cada spec: no tienen ledger ni nota |
| 045–048 | **Integrado.** El código entró en `5076dd2`. El índice todavía los marca "Approved" |
| 049 | **Cerrado.** `DONE` en el ledger, 9 de 9 criterios aceptados, con juicio adversario en verde |

Lo que el código muestra, contra lo que las specs de 045–049 prometen:

| Feature | Prueba de que está |
|---|---|
| 045 consola viva e instancia | overlay de instancia en `models_config.py`, 16 tests en `test_consola_viva_hosts.py` |
| 046 hosts descubiertos | registro de hosts en `provider_registry.py:102-104` |
| 047 lanes agy/fx/copilot | `agy_spawn.py` + `host_adapters.py`; `agy` y `copilot` en `RUNTIMES` (`models_config.py:50`) |
| 048 consola para humanos | `ui.py` y `tui.py`, 53 + 26 tests en `test_consola_ui.py` y `test_menu_ui.py` |
| 049 identidad honesta | `model_state.py`, 19 tests en `test_model_state_049.py` |

---

## 7. Qué falta

Diez ítems abiertos, cada uno con su fuente. Ninguno bloquea usar el harness.

**Del libro mayor**

1. **El índice de specs miente por omisión.** 045–049 figuran "Approved" con el código ya
   integrado. ADR-0067 dice que ese índice es la tabla de vigor: hoy no lo es.
   *(`docs/specs/README.md`, últimas cinco filas.)*
2. **Trece features no tienen ledger.** Faltan 001, 017, 018 y todo el tramo 039–048:
   ni `ai/state/features/*.json` ni nota en `docs/notas/features/`. La historia de esas
   trece vive sólo en los commits. Son 36 ledgers para 49 specs.
3. **011 quedó con AC-06 bloqueado en vivo**, declarado así en el índice desde el día uno.

**De producto**

4. **El lane `fx` está diferido.** `provider_registry.py:103` lo marca `SPAWN_DEFERRED`:
   el binario no estaba y el contrato de probe no está verificado.
   *(`docs/specs/047-lanes-agy-fx-copilot/evidence/fx-spawn-deferred.md`.)*
5. **Deuda de auditoría PR-06 y PR-10**, diferidas por decisión tuya del 2026-08-02. PR-11
   (el compare-and-swap en `mutate`) sí se cerró, en la spec 043.

**De higiene, y estos son los que tocan Windows**

6. **El codename de un cliente real sobrevive en 15 archivos de un repo público.** Lo
   grave ya se arregló: la regla de ruteo hardcodeada salió de `generate.py` y del
   `orchestrator.md` generado, así que dejó de viajar a la máquina de cada tercero que
   instala el harness. Lo que queda es el nombre suelto, como nombre de fixture en
   `tests/test_harness.py`, en un docstring de `vault_ops.py`, y en specs, evidencias e
   historia. La decisión de qué hacer con el historial de git sigue abierta desde el
   2026-08-14: sanear el árbol y aceptar el historial, reescribir con `filter-repo`, o
   volver el repo privado.
7. **Dos docs dicen que el repo es privado** y `gh` dice `PUBLIC`.
   *(`INSTALACION.md` línea 3, `TIPS-USO.md` sección "Bootstrap / compartir".)*
   En el mismo `README.md` hay además un ancla vencida: cita el guard de `--no-skills` en
   `set_agents_spawn.py:249-261` y hoy vive en las líneas 319-331. `check-anchors` sólo
   vigila `docs/modules/`, así que la raíz del repo se le escapa.
8. **El vault configurado apunta a un directorio borrado.** `config.toml` tiene
   `vault = "/var/tmp/tmpb11obg_s/empresa/obsidian"`, que es un temporal de un test.
   El vault real es `~/iey/obsidian`.
9. **SET-AGENTES no está en el registro del vault.** `~/iey/obsidian/.set-agentes-vault.json`
   lista tres proyectos y ninguno es este. En el vault hay una copia suelta de
   `Proyectos/SET-AGENTES/00 - Proyecto.md` congelada el 2026-07-29; las notas vivas están
   en `docs/notas/` del repo.
10. **Hay un directorio `$TMP/` sin trackear** en la raíz, con la variable literal en el
    nombre. Basura de un test; se borra.

---

## 8. Límites conocidos por runtime

Esto está medido, no prometido. Lo que no figura no se midió.

| Runtime | Límite |
|---|---|
| **opencode** | `run --agent <rol>` no despacha subagentes: de los 47 agentes instalados sólo `orchestrator.md` es `mode: primary`, así que cae al agente por defecto con un warning |
| **codex** | Cero slash commands: no existe `Global/codex/commands/` |
| **cursor** | Cero hooks de evento, así que `coord_policy.py` no gobierna ahí. Queda fuera de `RUNTIMES` y `--route-decide` está prohibido en ese anfitrión |
| **pi** | Cero hooks, y su lane corre con `--no-skills` por guarda incondicional (`set_agents_spawn.py:319-331`) |
| **Windows nativo** | No es un runtime, es un target de bootstrap. El harness vive en WSL |

Tres notas de máquina que vas a querer tener a mano, hoy en
`~/.claude/projects/-home-federico-SET-AGENTES/memory/`:

- **codex no arranca si el sandbox tiene que sellar dos o más archivos** — bug de file
  descriptor en `bwrap`. La config quedó en `default_permissions = ":workspace"`.
- **pi y opencode son instalaciones reales desde 2026-08-06**, no wrappers `pnpm dlx`.
  `pi update` y `opencode upgrade` funcionan.
- **El error "out of extra usage" de Anthropic en pi no es la cuota del plan**: las apps de
  terceros facturan contra un balde prepago aparte.
