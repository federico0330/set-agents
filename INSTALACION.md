# Instalación desde cero

## Acceso (el repo es privado)

El repo privado ES el control de acceso: solo entra quien Federico invitó como collaborator
(GitHub → Settings → Collaborators → Add people, rol Read). Sin invitación no se puede clonar
ni actualizar; al revocar el acceso, el próximo auto-update de esa persona falla y listo.
Cada usuario se autentica una sola vez con `gh auth login` (device flow) — el auto-update
reutiliza esas credenciales.

## Sistemas soportados

| OS | Camino |
|---|---|
| Linux (Arch/CachyOS, Debian/Ubuntu) | nativo |
| WSL (cualquier distro) | nativo dentro de WSL |
| macOS | nativo (Homebrew) |
| Windows 10/11 | `install.ps1` → WSL administrado (invisible para el usuario) |

## Linux / macOS / WSL

```bash
gh auth login        # una vez (instalá gh primero si no está: pacman/apt/brew install gh)
gh repo clone federico0330/SET-AGENTS ~/SET-AGENTS
cd ~/SET-AGENTS
./set-agents         # abre la app de consola → opción [1] Instalar
```

## Windows 10/11 (PowerShell, sin necesidad de saber qué es WSL)

Recibís `install.ps1` (o lo bajás del repo si ya tenés acceso desde el navegador) y:

```powershell
.\install.ps1
```

El script hace todo solo: se **auto-eleva** si necesita Administrador (un clic en el UAC),
instala WSL2+Ubuntu si falta, y si Windows pide reiniciar queda **registrado para continuar
automáticamente** al volver a iniciar sesión. El **usuario de Linux se crea solo** (sin
pantallas de configuración; queda con sudo sin password dentro de WSL — reversible, ver
README.md). Adentro instala git+gh, te guía por el login de GitHub, clona el repo y abre la
app. Además instala el comando `set-agents` para cmd/PowerShell: desde ahí en adelante
escribís `set-agents` en cualquier terminal de Windows y listo. Los CLIs
(opencode/claude/codex) viven dentro de WSL. Qué vas a ver en pantalla: README.md.

`./set-agents` es la puerta de entrada a todo (instala también el comando global
`set-agents` para usarlo desde cualquier directorio):

```
[1] Instalar / Reparar    [5] MCPs
[2] Actualizar            [6] Plugins Claude Code
[3] Modelos               [7] Estado
[4] Herramientas (CLIs)   [8] Salir
```

- **Auto-update**: al abrirla chequea el repo; si hay novedades las aplica sola mostrando qué
  cambió (backup + rollback de siempre). Se desactiva con `set-agents --auto-update off`.
  Nunca toca un repo con cambios locales sin commitear.
- **Herramientas**: catálogo opcional (supabase, vercel, gcloud, gh, docker, jq, obsidian,
  syncthing) definido en `tools.toml` — agregar una herramienta es un bloque de datos, no código.
- **MCPs**: agrega servers (supabase, context7, playwright) a los harnesses que detecte
  instalados: opencode, claude, codex, y también cursor y gemini CLI si están. En opencode se
  agregan apagados (política del repo) y se togglean desde el menú.
- Todo tiene equivalente scripteable: `set-agents --status | --update | --tools |
  --tools-install X --dry-run | --mcp-add X --harness h | --plugins` (ver `--help`).

Si preferís el instalador directo sin menú:

```bash
./install.sh
```

## Qué hace

1. **Detecta el sistema** (Arch/CachyOS → pacman, Debian/Ubuntu → apt, macOS → brew).
2. **Dependencias base**: git, curl, python3 (≥3.11), node (≥18) y npm. Si falta algo lo
   instala con el gestor de paquetes — **siempre muestra el comando exacto y pide
   confirmación antes de cualquier sudo**, incluso con `--yes`.
3. **CLIs de los harnesses** (solo si faltan): OpenCode, Claude Code y Codex, con sus
   instaladores oficiales. Si algún directorio de binarios no está en el PATH, te muestra la
   línea exacta para tu shell (fish/bash/zsh) — nunca edita tus archivos de configuración.
4. **Autenticación guiada**: chequea qué CLI ya tiene sesión y lanza los logins que falten
   (`opencode auth login`, `codex login`, `/login` en Claude Code). El OAuth siempre lo
   completás vos en el navegador.
5. **Configuración gestionada**: corre `./build.sh --check` y después `./build.sh --install`
   (te muestra el diff y pide confirmación; hace backup y rollback automático si algo falla).
6. **Verificación final**: `check-drift.sh` tiene que dar `DRIFT_OK`, y se imprime una tabla
   resumen de componentes.

## Re-ejecutarlo es actualizar

El script es idempotente: chequea el estado antes de cada paso. En una máquina ya instalada
solo aplica lo que cambió. Con `--update` fuerza la actualización de los CLIs.

## Flags

| Flag | Efecto |
|---|---|
| `--dry-run` | Muestra qué haría (`BOOTSTRAP_PLAN`/`BOOTSTRAP_SKIP`) sin tocar nada ni usar la red |
| `--yes` | No pregunta en pasos sin sudo (el sudo SIEMPRE pregunta) |
| `--update` | Fuerza actualización de los CLIs aunque ya estén |
| `--skip-auth` | Salta la fase de autenticación |
| `--skip-deps` | Salta las dependencias base |
| `--no-install` | Hace todo menos el `build.sh --install` final |

## Después de instalar

- La regla de idioma y el flujo de trabajo están en `TIPS-USO.md`.
- Para cambiar los modelos por área/suscripción: `COMO-CAMBIAR-MODELO.md`.
