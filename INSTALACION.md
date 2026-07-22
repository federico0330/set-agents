# Instalación desde cero

Para dejar SET-AGENTS funcionando en cualquier máquina (nueva o a medio configurar):

```bash
git clone https://github.com/federico0330/SET-AGENTS.git
cd SET-AGENTS
./set-agents        # abre la app de consola → opción [1] Instalar
```

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
- **Herramientas**: catálogo opcional (supabase, vercel, gcloud, gh, docker, jq) definido en
  `tools.toml` — agregar una herramienta es un bloque de datos, no código.
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
