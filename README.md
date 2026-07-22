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

## El menú

```
[1] 📦 Instalar / Reparar    [5] 🔌 MCPs
[2] 🔄 Actualizar            [6] 🧩 Plugins Claude Code
[3] 🧠 Modelos               [7] 📊 Estado
[4] 🧰 Herramientas (CLIs)   [8] ⏻  Salir
```

Todo tiene equivalente scripteable (`set-agents --help`): `--status`, `--update`,
`--tools-install gcloud`, `--mcp-add supabase --harness opencode`, etc.

## Más documentación

- [INSTALACION.md](INSTALACION.md) — instalación en detalle y flags del instalador.
- [TIPS-USO.md](TIPS-USO.md) — flujo de trabajo del harness (control plane, lanes, drift).
- [COMO-CAMBIAR-MODELO.md](COMO-CAMBIAR-MODELO.md) — modelos por área/suscripción.
