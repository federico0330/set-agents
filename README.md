# SET-AGENTS

Harness multi-agente que deja OpenCode (orquestación), Claude Code (review/debug) y Codex
(segunda opinión) configurados, coordinados y actualizados con **un solo comando**:
`set-agents`. Modelos ruteados por área con validación de doctrina, instalación gestionada
con backup/rollback, auto-update, y catálogo de herramientas y MCPs.

> 📖 **Leé la sección de tu sistema operativo antes de instalar** — ahí está exactamente
> qué vas a ver en pantalla, para que nada te sorprenda.

## Qué hace distinto a un CLI de IA suelto

Claude Code, Codex, Cursor, OpenCode y pi son excelentes escribiendo código. Este harness no
compite con ellos: **los usa**. Lo que agrega es el proceso alrededor, y ese proceso existe por
una razón concreta.

Cuando le pedís algo a un CLI de IA, el mismo modelo que escribió el código te dice que está
bien. Casi siempre lo está. El problema es el "casi": un modelo no puede auditar su propio
trabajo, porque el error que cometió y el criterio con el que lo revisa vienen del mismo lugar.

Este harness parte de ahí. Cuatro reglas, y las cuatro están en código, no en un prompt:

**El que escribe no aprueba.** Cada paquete lo revisa otro agente, en **otro proveedor** — es
una exclusión dura en el router (`service.py`), no una sugerencia: si el reviewer comparte
proveedor con quien escribió, la decisión se niega con `REVIEWER_INDEPENDENCE_UNAVAILABLE` y no
hay forma de saltearla desde el prompt.

**Nada se afirma sin fuente.** Un `archivo:línea` del repo, la salida de un comando que se
corrió de verdad, o un documento actual con su URL. La memoria del modelo sobre blancos móviles
—APIs, precios, límites, versiones— **no es fuente**. Cuando no hay fuente, se escribe "sin
verificar": una suposición marcada es honesta, una sin marcar es un defecto.

**Cada test tiene que demostrar que sirve.** Antes de aceptarlo se rompe a propósito lo que dice
proteger y se comprueba que se pone rojo. Suena excesivo hasta que ves cuántos no lo hacen.

**El estado vive en archivos, no en la conversación.** Specs, criterios de aceptación, gates,
hallazgos y decisiones quedan en el repo. Si la sesión se corta, se agota la cuota o cambiás de
máquina, el trabajo se retoma donde estaba en vez de reconstruirse de memoria.

### Qué encuentra eso que un CLI solo no encuentra

No es teoría. En una sola sesión de trabajo sobre este mismo repo, el proceso encontró:

- **Cinco tests que decían cubrir algo que no miraban** — pasaban en verde con el código roto.
  Uno de ellos "protegía" contra un registro corrupto comparándolo consigo mismo.
- **Un gate que informaba OK sin verificar nada**: `build.sh --check` decía "sin drift" y
  comparaba dos archivos de scaffold, nunca los cuatro árboles generados. Decenas de gates se
  habían registrado con esa evidencia.
- **Un control de alcance que no ve los archivos nuevos**, porque usa `git diff` — que sólo
  lista trackeados. Un paquete creó su archivo central y el control guardó silencio.
- **Un instalador que hacía 3153 llamadas en cinco segundos** y nunca terminaba con `--yes`.
- **Un cambio de esquema sin subir la versión** que dejó el ruteo caído — introducido por la
  *reparación* de un hallazgo, no por el hallazgo.

Ninguno salió de leer código con atención. Los cinco salieron de que un eslabón volviera a
correr lo que el anterior afirmaba.

### El flujo, en una línea

```
spec → desafío independiente → aprobación tuya → paquetes → gates → review en otro proveedor
     → reparación consolidada → delta review → aceptación → integración
```

Con presupuestos por paquete —dos ciclos de review, dos reparaciones por hallazgo— para que un
bucle de "arreglo y rompo" no se vuelva infinito, y una parada explícita
(`HUMAN_DECISION_REQUIRED`) cuando los criterios se contradicen o hay que tocar algo
irreversible.

### Cuándo NO lo quieras

Es más lento y más caro que pedirle el cambio a un CLI y listo. Para un script de diez líneas,
un experimento o algo que vas a tirar mañana, el ciclo completo es puro peso muerto — y el
propio harness tiene una lane de quick-fix para eso.

Esto sirve cuando **equivocarse sale caro**: código que otros van a mantener, cambios que tocan
datos o dinero, o trabajo largo donde perdés el hilo entre sesiones.

## Acceso

El repo es **público**: cualquiera puede clonarlo y usarlo. No hace falta invitación ni
`gh auth login` para instalar — `gh` sólo se usa para el auto-update por HTTPS y podés
reemplazarlo por `git pull` normal.

Si lo forkeás, apuntá el upstream con `SET_AGENTS_UPSTREAM=<remoto>/<rama>`; sin esa variable
el default sigue siendo `origin/main`.

## Instalación

### Lo que necesitás, en cualquier sistema

| Requisito | Por qué | Si falta |
|---|---|---|
| **Python ≥ 3.11** | los scripts usan `tomllib`, que entró en 3.11 | el instalador lo ofrece |
| **Node ≥ 18** | los CLIs de IA se instalan por npm | el instalador lo ofrece |
| **git** y **bash** | clonar, versionar, correr el instalador | preinstalados en Linux/macOS |
| `gh` *(opcional)* | sólo para el auto-update por HTTPS | podés usar `git pull` |

El instalador **detecta lo que falta y te lo ofrece**; no instala nada por su cuenta sin
preguntar, salvo que le pases `--yes`.

| Tu sistema | Camino |
|---|---|
| Linux (Arch/CachyOS, Debian/Ubuntu, Fedora) | nativo |
| WSL con cualquier distro | nativo, igual que Linux |
| macOS (Intel y Apple Silicon) | nativo, necesita [Homebrew](https://brew.sh) |
| Windows 10/11 | `install.ps1` → WSL administrado (no hace falta saber qué es WSL) |

Los tres sistemas se prueban en CI en cada cambio: `ubuntu-latest`, `macos-latest` y
`windows-latest` (`.github/workflows/ci.yml`).

### Linux, macOS y WSL

```bash
git clone https://github.com/federico0330/set-agents.git ~/SET-AGENTS
cd ~/SET-AGENTS && ./set-agents        # menú → "Instalar / Reparar"
```

En **Debian/Ubuntu**, el `node` de los repos suele ser viejo; si el instalador falla ahí, usá
[NodeSource](https://github.com/nodesource/distributions).

En **macOS** necesitás Homebrew antes de empezar: el instalador lo usa para `python3` y `node`.

Si preferís no usar el menú, `./install.sh` acepta `--yes`, `--update`, `--dry-run`,
`--skip-auth`, `--skip-deps`, `--no-install` y `--harness claude|opencode|codex|pi|all`.

### Windows 10/11

```powershell
.\install.ps1
```

Bajás `install.ps1` del repo desde el navegador y lo corrés. Instala WSL, crea tu usuario de
Linux y sigue desde adentro — la sección de abajo te dice **exactamente** qué vas a ver, incluido
el diálogo de permisos y el posible reinicio.

### No querés instalar todo

`./set-agents` → "Instalar / Reparar" te deja elegir **a qué CLI** aplicarle el harness. Podés
usarlo sólo sobre OpenCode y dejar los demás vírgenes.

Detalle completo por sistema en [INSTALACION.md](INSTALACION.md).

## Qué vas a ver la primera vez (sin sorpresas)

### 🪟 Windows

1. **Un diálogo de Windows pidiendo permiso de administrador (UAC)** — el instalador se
   re-lanza elevado solo para instalar WSL; hacé clic en "Sí".
2. **Posiblemente un reinicio** — si Windows lo pide, reiniciá tranquilo: el instalador
   queda registrado para **continuar solo** cuando volvés a iniciar sesión.
3. **Tu usuario de Linux se crea automáticamente** (mismo nombre que tu usuario de Windows,
   en minúsculas) — sin pantallas de configuración. Queda con **sudo sin password SOLO para
   instalar paquetes** (`apt`/`pacman`) dentro de WSL; cualquier otro sudo requiere root
   (`wsl -u root`). Para revertirlo: `wsl -u root -- rm /etc/sudoers.d/set-agents` y
   `wsl -u root -- passwd <tu-usuario>` para ponerle contraseña.
4. **Una ventana del navegador para iniciar sesión en GitHub** (`gh auth login`) — este es
   el control de acceso real; necesitás estar invitado al repo.
5. Al final tenés el comando **`set-agents`** disponible en cmd y PowerShell (abrí una
   terminal nueva la primera vez). Los CLIs de IA viven dentro de WSL; no necesitás
   tocarlo nunca directamente.

### 🐧 Linux

- Todo comando que necesite **sudo se muestra completo y te pide confirmación** — nunca
  hay sudo silencioso, ni siquiera en modo `--yes`.
- Si un directorio de binarios falta en tu PATH, el instalador **te muestra la línea
  exacta** para tu shell (fish/bash/zsh) — nunca edita tus archivos de configuración.
- Los logins de los CLIs (OpenCode/Claude/Codex) se abren en el navegador cuando toca;
  el instalador solo te guía.

### 🍎 macOS

- Necesitás [Homebrew](https://brew.sh) instalado antes de empezar (el instalador te avisa
  si falta). El resto es idéntico a Linux (sin sudo: brew no lo usa).

### 🔷 WSL ya existente

- Si ya usás WSL con la distro que sea, es el camino Linux normal — el instalador lo
  detecta y te lo confirma con un aviso.

## Auto-update

Al abrir `set-agents`, la app chequea el repo: si hay novedades las muestra y las aplica
sola (siempre con backup y rollback automático ante fallas). Nunca toca un repo con
cambios locales sin commitear. Para desactivarlo: `set-agents --auto-update off`.

**Modelo de confianza, sin vueltas**: el auto-update **ejecuta lo que esté en `main` del
upstream al que apuntes**. El repo es público —cualquiera puede leerlo y forkearlo— pero el
acceso de escritura a `main` de este upstream es sólo de su dueño. En criollo: al dejar el
auto-update prendido estás confiando en quien controla esa rama, igual que con cualquier
gestor de paquetes.

Si eso no te cierra, tenés dos salidas: `set-agents --auto-update off`, o forkear y apuntar
`SET_AGENTS_UPSTREAM` a **tu** fork, donde el que controla `main` sos vos.

Los CLIs (opencode/claude/codex, gcloud) se instalan con sus instaladores oficiales vía
`curl | bash` **sin pinning de versión**: es el mecanismo oficial de cada vendor y se acepta
ese riesgo a cambio de recibir siempre la última versión.

**Perfil de permisos (OpenCode)**: el repo se distribuye en modo **yolo** — los agentes y la
sesión principal ejecutan bash/edits sin pedir confirmación, para que un run no se frene por
prompts de autorización. Lo irreversible sigue bloqueado SIEMPRE (sudo, `rm -rf`,
`git push --force`, borrar repos, leer `.env`/secretos) y la separación de deberes se
mantiene (reviewers/gates no pueden editar; el orchestrator sigue deny-by-default). Si
preferís aprobar cada comando: en `models.toml` poné `[permissions] profile = "guarded"` y
corré `./build.sh --install`.

## El menú

`./set-agents` abre un selector de flechas (stdlib puro, sin librerías de terceros): ↑↓ para
moverte, Enter para elegir, `/` para buscar (con texto libre donde tiene sentido, ej. el picker
de modelos), Esc o Ctrl-C para volver/cancelar sin dejar rastro de error. Las opciones, en orden:

- 🩺 Estado general — el doctor completo, formateado: harnesses con versión y auth, lane pi,
  alcance de instalación, catálogo de CLIs y proveedores autenticados (probe)
- 📦 Instalar / Reparar — primero elegís qué CLI de IA instalar o aplicarle el harness
  (Todos / Claude Code+pi / OpenCode / Codex / Pi)
- 🔄 Actualizar
- 🧠 Modelos — panel compacto + fijar modelo por área/rol, suscripciones tri-estado
  (pin/off/auto por probe) y proveedores descubiertos (ADR-0029). La tabla que muestra son
  los **defaults curados (fallback)**: el router decide en vivo por spawn para los 28 roles
  y la pisa donde el lane lo permite (ADR-0030)
- 🧰 Herramientas (CLIs) — con método de instalación y nota por herramienta
- 🔌 MCPs
- 🧩 Plugins Claude Code
- 🗒 Vault Obsidian
- ⏻ Salir

Todo tiene equivalente scripteable (`set-agents --help`): `--status`, `--update`,
`--tools-install gcloud`, `--mcp-add supabase --harness opencode`, etc.

## Documentación viva (Obsidian)

Los agentes documentan mientras trabajan: cada proyecto mantiene `docs/notas/` (hub con
"qué falta", una nota por feature, por paquete y por decisión, enlazadas con `[[wikilinks]]`)
**regeneradas automáticamente** por el workflow — nadie las escribe a mano. Un vault por
empresa/cliente las junta en un solo grafo navegable:

```bash
set-agents --vault-init ~/acme --company ACME          # una vez por empresa/cliente
set-agents --vault-link ~/acme/mi-proyecto              # notas dentro del repo (default)
set-agents --vault-link ~/acme/mi-proyecto --private    # notas dentro del vault, fuera del git
```

Abrís `~/acme/obsidian` en Obsidian: `00 - INICIO` es la nota del café ☕ (tu rol, cómo se
trabaja, qué falta por proyecto) y desde ahí navegás hasta cualquier paquete. Lo que escribas
fuera de los bloques `notas:auto` nunca se pisa. Las decisiones que trascienden un paquete se
registran con `feature-state.py log-decision`. El vault también trae `Casos/` con una
plantilla de caso de una página por proyecto terminado (tu portfolio).

**¿Default o `--private`?** En el default las notas viven versionadas en `docs/notas/` del
repo (bien para repos propios). Con `--private` las notas viven **dentro del vault** y el
repo queda con un symlink local excluido de git (`.git/info/exclude`): nada llega jamás al
remoto del proyecto — usalo cuando el repo es de un tercero (empresa/cliente) y las notas
son tuyas. El motor de notas escribe igual en ambos modos.

## Trabajar en dos máquinas

Cada cosa viaja por su canal — nada se copia a mano:

| Qué | Cómo viaja |
|---|---|
| El harness (SET-AGENTS) | auto-update al abrir `set-agents` |
| Los proyectos (código) | git normal (clone/pull/push) |
| El estado del workflow | `ai/state/` dentro del repo de cada proyecto (git) |
| Las notas Obsidian (vault) | **Syncthing** entre tus máquinas (P2P, open source, sin nube) |

Setup una sola vez (en ambas máquinas):

```bash
set-agents --tools-install syncthing
systemctl --user enable --now syncthing
```

Abrí `http://localhost:8384` en cada máquina: **Actions → Show ID** en una, **Add Remote
Device** en la otra (en la misma red se autodescubren), aceptá en ambas, y compartí la
carpeta `~/acme/obsidian` (Add Folder → path exacto en las dos). Un cliente freelance nuevo =
Add Folder de su vault; sin repos nuevos.

- ⚠️ Syncthing es P2P: sincroniza cuando **ambas máquinas están prendidas** (típicamente en
  tu LAN antes de salir y al volver). Dejá la que editaste prendida un minuto junto a la otra.
- ⚠️ **Nunca** sincronices repos git por Syncthing (corrompe `.git`); solo el vault.
- En una máquina nueva, después del primer sync corré `set-agents --vault-link <proyecto>
  --private` en cada proyecto: el symlink y el exclude de git son por-máquina.

## Matriz de soporte (medida, no prometida)

Los tres harnesses no tienen el mismo nivel de soporte — esto es lo que se pudo **confirmar**
hasta hoy, no una promesa de paridad. Lo que no está en esta tabla no se midió.

| Harness | Estado medido |
|---|---|
| **opencode** | De primera clase. 47 agentes instalados (`~/.config/opencode/agents/*.md`, y en la fuente `Global/opencode/agents/`); de esos, solo `orchestrator.md` declara `mode: primary` — los otros 46 son `mode: subagent`. Consecuencia (medida el 2026-08-13, al intentar despachar un `package-reviewer`): `opencode run --agent <rol>` **no despacha un subagent** — cae al agente por defecto con un warning, porque `run --agent` solo sabe arrancar un `primary`. *(Medido: 2026-08-14, última fila 2026-08-13.)* |
| **codex** | **Cero comandos.** `Global/codex/` no tiene directorio `commands/` (a diferencia de `Global/opencode/commands/`); en una instalación real, `~/.codex/commands` no existe. *(Medido: 2026-08-14.)* |
| **pi** | **Cero hooks**, y su lane de dispatch corre con `--no-skills` (guard incondicional, `ai/scripts/set_agents_spawn.py:249-261`). `Global/pi/` no tiene directorio `hooks/`; en una instalación real, `~/.pi` no tiene subdirectorio `hooks` (a diferencia de `~/.codex/hooks` y `~/.config/opencode/hooks`, que sí existen). *(Medido: 2026-08-14.)* |

## Más documentación

- [INSTALACION.md](INSTALACION.md) — instalación en detalle y flags del instalador.
- [TIPS-USO.md](TIPS-USO.md) — flujo de trabajo del harness (control plane, lanes, drift).
- [COMO-CAMBIAR-MODELO.md](COMO-CAMBIAR-MODELO.md) — modelos por área/suscripción.
