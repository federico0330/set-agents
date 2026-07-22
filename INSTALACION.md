# Instalación desde cero

Para dejar SET-AGENTS funcionando en cualquier máquina (nueva o a medio configurar):

```bash
git clone https://github.com/federico0330/SET-AGENTS.git
cd SET-AGENTS
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
