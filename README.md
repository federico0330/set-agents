# SET-AGENTS

Harness multi-agente que deja OpenCode (orquestación), Claude Code (review/debug) y Codex
(segunda opinión) configurados, coordinados y actualizados con **un solo comando**:
`set-agents`. Modelos ruteados por área con validación de doctrina, instalación gestionada
con backup/rollback, auto-update, y catálogo de herramientas y MCPs.

> 📖 **Leé la sección de tu sistema operativo antes de instalar** — ahí está exactamente
> qué vas a ver en pantalla, para que nada te sorprenda.

## Acceso

El repo es **privado**: solo pueden clonar/actualizar los invitados como collaborators
(se invita desde GitHub → Settings → Collaborators, rol Read). Cada usuario se autentica
una única vez con `gh auth login`; el auto-update reutiliza esas credenciales. Si se revoca
el acceso, la próxima actualización de esa persona falla — así de simple.

## Instalación

| Tu sistema | Camino |
|---|---|
| Linux (Arch/CachyOS, Debian/Ubuntu) | nativo |
| WSL con cualquier distro | nativo (igual que Linux) |
| macOS | nativo (necesita [Homebrew](https://brew.sh)) |
| Windows 10/11 | `install.ps1` → WSL administrado (no hace falta saber qué es WSL) |

### Linux / macOS / WSL

```bash
# si no tenés gh: pacman -S github-cli / apt install gh / brew install gh
gh auth login                                        # una vez
gh repo clone federico0330/SET-AGENTS ~/SET-AGENTS
cd ~/SET-AGENTS && ./set-agents                      # menú → [1] Instalar
```

### Windows 10/11

Con el archivo `install.ps1` (te lo pasan, o lo bajás del repo desde el navegador):

```powershell
.\install.ps1
```

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

**Modelo de confianza, sin vueltas**: el auto-update ejecuta lo que esté en `main` del repo
privado — solo Federico tiene acceso de escritura; los invitados son solo-lectura. Los CLIs
(opencode/claude/codex, gcloud) se instalan con sus instaladores oficiales vía
`curl | bash` sin pinning de versión: es el mecanismo oficial de cada vendor y se acepta
ese riesgo a cambio de recibir siempre la última versión.

**Perfil de permisos (OpenCode)**: el repo se distribuye en modo **yolo** — los agentes y la
sesión principal ejecutan bash/edits sin pedir confirmación, para que un run no se frene por
prompts de autorización. Lo irreversible sigue bloqueado SIEMPRE (sudo, `rm -rf`,
`git push --force`, borrar repos, leer `.env`/secretos) y la separación de deberes se
mantiene (reviewers/gates no pueden editar; el orchestrator sigue deny-by-default). Si
preferís aprobar cada comando: en `models.toml` poné `[permissions] profile = "guarded"` y
corré `./build.sh --install`.

## El menú

```
[1] 📦 Instalar / Reparar    [5] 🔌 MCPs
[2] 🔄 Actualizar            [6] 🧩 Plugins Claude Code
[3] 🧠 Modelos               [7] 📊 Estado
[4] 🧰 Herramientas (CLIs)   [8] ⏻  Salir
```

Todo tiene equivalente scripteable (`set-agents --help`): `--status`, `--update`,
`--tools-install gcloud`, `--mcp-add supabase --harness opencode`, etc.

## Documentación viva (Obsidian)

Los agentes documentan mientras trabajan: cada proyecto mantiene `docs/notas/` (hub con
"qué falta", una nota por feature, por paquete y por decisión, enlazadas con `[[wikilinks]]`)
**regeneradas automáticamente** por el workflow — nadie las escribe a mano. Un vault por
empresa/cliente las junta en un solo grafo navegable:

```bash
set-agents --vault-init ~/iey --company IEY            # una vez por empresa/cliente
set-agents --vault-link ~/iey/mi-proyecto               # notas dentro del repo (default)
set-agents --vault-link ~/iey/mi-proyecto --private     # notas dentro del vault, fuera del git
```

Abrís `~/iey/obsidian` en Obsidian: `00 - INICIO` es la nota del café ☕ (tu rol, cómo se
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
carpeta `~/iey/obsidian` (Add Folder → path exacto en las dos). Un cliente freelance nuevo =
Add Folder de su vault; sin repos nuevos.

- ⚠️ Syncthing es P2P: sincroniza cuando **ambas máquinas están prendidas** (típicamente en
  tu LAN antes de salir y al volver). Dejá la que editaste prendida un minuto junto a la otra.
- ⚠️ **Nunca** sincronices repos git por Syncthing (corrompe `.git`); solo el vault.
- En una máquina nueva, después del primer sync corré `set-agents --vault-link <proyecto>
  --private` en cada proyecto: el symlink y el exclude de git son por-máquina.

## Más documentación

- [INSTALACION.md](INSTALACION.md) — instalación en detalle y flags del instalador.
- [TIPS-USO.md](TIPS-USO.md) — flujo de trabajo del harness (control plane, lanes, drift).
- [COMO-CAMBIAR-MODELO.md](COMO-CAMBIAR-MODELO.md) — modelos por área/suscripción.
