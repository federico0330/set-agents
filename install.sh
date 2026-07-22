#!/usr/bin/env bash
# Bootstrap installer for SET-AGENTS: prepares any machine (fresh or partial)
# with the base dependencies, the three harness CLIs, guided authentication,
# and the managed global configuration. Re-running it acts as an update.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

YES=0
UPDATE=0
DRY=0
SKIP_AUTH=0
SKIP_DEPS=0
NO_INSTALL=0

usage() {
  echo "usage: ./install.sh [--yes] [--update] [--dry-run] [--skip-auth] [--skip-deps] [--no-install]"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --yes) YES=1 ;;
    --update) UPDATE=1 ;;
    --dry-run) DRY=1 ;;
    --skip-auth) SKIP_AUTH=1 ;;
    --skip-deps) SKIP_DEPS=1 ;;
    --no-install) NO_INSTALL=1 ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
  shift
done

have() { command -v "$1" >/dev/null 2>&1; }

version_of() { "$1" --version 2>/dev/null | head -1 || true; }

confirm() {
  # Honors --yes. For anything that does NOT involve sudo.
  [ "$YES" -eq 1 ] && return 0
  local answer
  read -r -p "$1 [s/N] " answer
  case "$answer" in y|Y|yes|YES|s|S|si|SI|sí) return 0 ;; *) return 1 ;; esac
}

confirm_sudo() {
  # Never silent: sudo always shows the exact command and asks, even with --yes.
  local answer
  echo "Se necesita privilegio de administrador para:"
  echo "    $1"
  read -r -p "¿Ejecutar ese comando? [s/N] " answer
  case "$answer" in y|Y|yes|YES|s|S|si|SI|sí) return 0 ;; *) return 1 ;; esac
}

# ---------------------------------------------------------------- detect_os
PKG=""

detect_os() {
  case "$(uname -s)" in
    Darwin)
      if have brew; then
        PKG="brew"
      else
        echo "AVISO: falta Homebrew. Instalalo desde https://brew.sh y volvé a correr ./install.sh"
      fi
      ;;
    MINGW*|MSYS*|CYGWIN*)
      echo "Windows detectado (git-bash). El harness corre dentro de WSL:"
      echo "    abrí PowerShell y ejecutá  .\\install.ps1  desde este mismo directorio."
      exit 2
      ;;
    Linux)
      if grep -qi microsoft /proc/version 2>/dev/null; then
        echo "AVISO: WSL detectado — perfecto, el harness corre acá como en cualquier Linux."
      fi
      local ids=""
      if [ -r /etc/os-release ]; then
        ids="$(. /etc/os-release 2>/dev/null; echo "${ID:-} ${ID_LIKE:-}")"
      fi
      case " $ids " in
        *arch*|*cachyos*) PKG="pacman" ;;
        *debian*|*ubuntu*) PKG="apt" ;;
        *) echo "AVISO: distro no reconocida ($ids); las dependencias base deben instalarse a mano." ;;
      esac
      ;;
  esac
}

pkg_install_cmd() {
  # Prints the exact install command for the detected package manager.
  case "$PKG" in
    pacman) echo "sudo pacman -S --needed --noconfirm $*" ;;
    apt) echo "sudo apt-get install -y $*" ;;
    brew) echo "brew install $*" ;;
    *) echo "" ;;
  esac
}

pkg_install() {
  local packages="$1" command
  command="$(pkg_install_cmd "$packages")"
  if [ -z "$command" ]; then
    echo "Instalá a mano: $packages"
    return 1
  fi
  case "$command" in
    sudo\ *) confirm_sudo "$command" || return 1 ;;
    *) confirm "¿Ejecutar '$command'?" || return 1 ;;
  esac
  eval "$command"
}

# ------------------------------------------------------------- ensure deps
node_major() { node --version 2>/dev/null | sed 's/^v//' | cut -d. -f1 || true; }

plan_or_install() {
  # $1 marker name, $2 packages for the package manager
  if [ "$DRY" -eq 1 ]; then
    echo "BOOTSTRAP_PLAN $1"
    return 0
  fi
  pkg_install "$2" && echo "BOOTSTRAP_OK $1"
}

ensure_base_deps() {
  [ "$SKIP_DEPS" -eq 1 ] && return 0
  local tool
  for tool in git curl; do
    if have "$tool"; then
      echo "BOOTSTRAP_SKIP $tool ($(version_of "$tool"))"
    else
      plan_or_install "$tool" "$tool"
    fi
  done

  if have python3 && python3 -c "import tomllib" 2>/dev/null; then
    echo "BOOTSTRAP_SKIP python3 ($(version_of python3))"
  else
    # tomllib probe: the repo scripts require python >= 3.11
    plan_or_install "python3" "python3"
  fi

  local major
  major="$(node_major)"
  if have node && [ -n "$major" ] && [ "$major" -ge 18 ] 2>/dev/null; then
    echo "BOOTSTRAP_SKIP node ($(version_of node))"
  else
    if [ "$PKG" = "apt" ]; then
      echo "AVISO: en Debian/Ubuntu el node del repo puede ser viejo; si falla, usá NodeSource: https://github.com/nodesource/distributions"
    fi
    plan_or_install "node" "nodejs npm"
  fi
  if have npm; then
    echo "BOOTSTRAP_SKIP npm ($(version_of npm))"
  elif have pnpm; then
    echo "BOOTSTRAP_SKIP npm (pnpm $(version_of pnpm))"
  elif have node; then
    plan_or_install "npm" "npm"
  fi
}

# -------------------------------------------------------- ensure agent CLIs
install_opencode() { curl -fsSL https://opencode.ai/install | bash; }

install_claude() {
  curl -fsSL https://claude.ai/install.sh | bash || npm install -g @anthropic-ai/claude-code
}

install_codex() {
  local npm_cli="npm"
  have npm || npm_cli="pnpm"
  if [ "$UPDATE" -eq 1 ] && have codex; then
    "$npm_cli" update -g @openai/codex
  else
    "$npm_cli" install -g @openai/codex
  fi
}

ensure_cli() {
  # $1 name, $2 install function
  if have "$1" && [ "$UPDATE" -eq 0 ]; then
    echo "BOOTSTRAP_SKIP $1 ($(version_of "$1"))"
    return 0
  fi
  local label="$1"
  have "$1" && label="$1 (update)"
  if [ "$DRY" -eq 1 ]; then
    echo "BOOTSTRAP_PLAN $label"
    return 0
  fi
  confirm "¿Instalar/actualizar $1 con el instalador oficial?" || return 0
  "$2" && echo "BOOTSTRAP_OK $label"
}

path_hint() {
  # $1 directory that should be on PATH. Print (never edit) the per-shell line.
  case ":$PATH:" in *":$1:"*) return 0 ;; esac
  echo "AVISO: $1 no está en tu PATH. Agregalo con:"
  case "${SHELL:-}" in
    */fish) echo "    fish_add_path $1" ;;
    *) echo "    export PATH=\"$1:\$PATH\"   # en tu ~/.bashrc o ~/.zshrc" ;;
  esac
}

ensure_agent_clis() {
  ensure_cli opencode install_opencode
  ensure_cli claude install_claude
  if have npm || have pnpm || [ "$DRY" -eq 1 ]; then
    ensure_cli codex install_codex
  else
    echo "AVISO: sin npm/pnpm no se puede instalar codex; resolvé node/npm primero."
  fi
  [ "$DRY" -eq 1 ] && return 0
  path_hint "$HOME/.local/bin"
  path_hint "$HOME/.opencode/bin"
  if have npm; then
    local npm_bin
    npm_bin="$(npm prefix -g 2>/dev/null)/bin" && path_hint "$npm_bin"
  fi
}

# --------------------------------------------------------------- guide_auth
claude_authed() {
  # Claude Code has no stable auth-status command; keep the heuristic here only.
  [ -s "$HOME/.claude/.credentials.json" ]
}

auth_opencode() {
  if ! have opencode; then echo "AUTH_NEEDED opencode"; return 0; fi
  if [ -n "$(opencode auth list 2>/dev/null | grep -v '^\s*$' || true)" ]; then
    echo "AUTH_OK opencode"
    return 0
  fi
  echo "AUTH_NEEDED opencode"
  if [ "$DRY" -eq 0 ]; then
    echo "Iniciá sesión con cada proveedor que tengas suscripto (OpenAI, OpenCode Zen, etc.)."
    while confirm "¿Correr 'opencode auth login' (una vez por proveedor)?"; do
      opencode auth login || true
    done
  fi
}

auth_codex() {
  if ! have codex; then echo "AUTH_NEEDED codex"; return 0; fi
  if codex login status >/dev/null 2>&1; then
    echo "AUTH_OK codex"
    return 0
  fi
  echo "AUTH_NEEDED codex"
  if [ "$DRY" -eq 0 ] && confirm "¿Correr 'codex login' ahora?"; then
    codex login || true
  fi
}

auth_claude() {
  if ! have claude; then echo "AUTH_NEEDED claude"; return 0; fi
  if claude_authed; then
    echo "AUTH_OK claude"
    return 0
  fi
  echo "AUTH_NEEDED claude"
  if [ "$DRY" -eq 0 ]; then
    echo "Abrí Claude Code con 'claude' y ejecutá /login; después volvé acá."
    [ "$YES" -eq 1 ] || read -r -p "Enter para continuar... " _
  fi
}

guide_auth() {
  [ "$SKIP_AUTH" -eq 1 ] && return 0
  auth_opencode
  auth_codex
  auth_claude
}

# ----------------------------------------------------------- ensure_app_link
ensure_app_link() {
  # `set-agents` callable from anywhere; the wrapper resolves the symlink back here.
  local link="$HOME/.local/bin/set-agents"
  if [ -L "$link" ] && [ "$(readlink "$link")" = "$ROOT/set-agents" ]; then
    echo "BOOTSTRAP_SKIP set-agents-link"
    return 0
  fi
  if [ "$DRY" -eq 1 ]; then
    echo "BOOTSTRAP_PLAN set-agents-link"
    return 0
  fi
  mkdir -p "$HOME/.local/bin"
  ln -sfn "$ROOT/set-agents" "$link"
  echo "BOOTSTRAP_OK set-agents-link"
}

# -------------------------------------------------------------- repo_config
repo_config() {
  if [ "$DRY" -eq 1 ]; then
    echo "BOOTSTRAP_PLAN repo-config"
    return 0
  fi
  "$ROOT/build.sh" --check
  if [ ! -f "$HOME/.local/state/set-agentes/managed-files.json" ]; then
    echo "Primera instalación en esta máquina: se aplican los modelos por defecto del repo."
    echo "Para remapearlos por área/suscripción después: ./setup-models.sh (ver COMO-CAMBIAR-MODELO.md)."
  fi
  [ "$NO_INSTALL" -eq 1 ] && return 0
  if [ "$YES" -eq 1 ]; then
    "$ROOT/build.sh" --install --yes
  else
    "$ROOT/build.sh" --install
  fi
}

# ------------------------------------------------------------- verify_final
verify_final() {
  [ "$DRY" -eq 1 ] && return 0
  [ "$NO_INSTALL" -eq 1 ] && return 0
  "$ROOT/ai/scripts/check-drift.sh"
  echo
  echo "Componente   Versión"
  local tool
  for tool in git python3 node opencode claude codex; do
    if have "$tool"; then
      printf '%-12s %s\n' "$tool" "$(version_of "$tool")"
    else
      printf '%-12s %s\n' "$tool" "FALTA"
    fi
  done
}

echo "Detalle de todo lo que vas a ver paso a paso: README.md"
detect_os
ensure_base_deps
ensure_agent_clis
ensure_app_link
guide_auth
repo_config
verify_final
echo "BOOTSTRAP_DONE"
