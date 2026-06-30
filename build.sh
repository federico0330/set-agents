#!/usr/bin/env bash
# build.sh — Genera los archivos de agentes/skills/commands por harness desde _canonical/,
# usando manifest.tsv para mapear modelo/modo/permisos. Con --install, los copia a los dirs vivos.
#
# Uso:
#   ./build.sh            # genera Global/{opencode,claude-code,codex}/ desde _canonical/
#   ./build.sh --install  # genera e instala en ~/.config/opencode, ~/.claude, ~/.codex
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANON="$ROOT/Global/_canonical"
SHARED="$ROOT/Global/_shared"
MANIFEST="$ROOT/manifest.tsv"
INSTALL="${1:-}"

OC_DIR="$ROOT/Global/opencode"
CC_DIR="$ROOT/Global/claude-code"
CX_DIR="$ROOT/Global/codex"

rm -rf "$OC_DIR/agents" "$CC_DIR/agents" "$CX_DIR/prompts"
mkdir -p "$OC_DIR/agents" "$OC_DIR/commands" "$OC_DIR/skills" \
         "$CC_DIR/agents" "$CC_DIR/commands" "$CC_DIR/skills" \
         "$CX_DIR/prompts" "$CX_DIR/skills"

# --- description = primer "# " del cuerpo canónico, sin el "# " ---
desc_of() { rg -m1 '^# ' "$1" | sed 's/^# //'; }

# --- bloque de permisos OpenCode segun tier ---
oc_perm() {
  local tier="$1"
  # coord (orquestador): SOLO coordina/delega. No edita, no commitea, bash deny-por-defecto.
  # Mantiene la tool `task` para delegar en subagentes (cada uno con su propio modelo/sesion).
  if [ "$tier" = "coord" ]; then
    cat <<'YAML'
permission:
  edit: deny
  webfetch: allow
  websearch: ask
  task:
    "*": allow
  bash:
    "*": deny
    "git diff*": allow
    "git status*": allow
    "git log*": allow
    "git show*": allow
    "rg*": allow
    "bat*": allow
    "eza*": allow
    "fd*": allow
    "./ai/scripts/verify.sh*": allow
    "./ai/scripts/audit-readonly.sh*": allow
    "./ai/scripts/loop.sh*": allow
    "./ai/scripts/mcp.sh*": allow
    "git commit*": deny
    "git push*": deny
    "rm *": deny
    "sudo *": deny
YAML
    return
  fi
  # ro/rw/docs: workers y auditores.
  local edit="ask"; local commit="ask"
  case "$tier" in
    ro)   edit="deny";  commit="deny";;   # auditores: read-only, no commitean
    rw)   edit="allow"; commit="ask";;    # implementers: editan; commit solo con OK humano
    docs) edit="ask";   commit="deny";;   # escriben docs/specs, no commitean codigo
  esac
  cat <<YAML
permission:
  edit: $edit
  webfetch: allow
  bash:
    "*": ask
    "git diff*": allow
    "git status*": allow
    "git log*": allow
    "git show*": allow
    "rg*": allow
    "bat*": allow
    "eza*": allow
    "fd*": allow
    "npm test*": allow
    "npm run test*": allow
    "npm run lint*": allow
    "npm run typecheck*": allow
    "npm run build*": allow
    "dotnet test*": allow
    "go test*": allow
    "python -m pytest*": allow
    "./ai/scripts/verify.sh*": allow
    "./ai/scripts/audit-readonly.sh*": allow
    "git commit*": $commit
    "rm *": deny
    "sudo *": deny
    "git push*": deny
YAML
}

# --- tools Claude Code segun tier ---
cc_tools() {
  case "$1" in
    ro)    echo "Read, Grep, Glob, Bash";;
    docs)  echo "Read, Grep, Glob, Edit, Write, Bash";;
    coord) echo "Read, Grep, Glob, Bash, Task, TodoWrite";;
    rw)    echo "Read, Grep, Glob, Edit, Write, Bash";;
  esac
}

count=0
# saltar header (NR==1) y comentarios/blancos
while IFS=$'\t' read -r role mode temp perm ocm ccm cxm; do
  [ -z "${role:-}" ] && continue
  case "$role" in '＃'*|'#'*) continue;; esac
  body="$CANON/agents/$role.md"
  [ -f "$body" ] || { echo "WARN: falta $body — salteo"; continue; }
  desc="$(desc_of "$body")"

  # ---------- OpenCode ----------
  {
    echo "---"
    echo "description: $desc"
    echo "mode: $mode"
    echo "model: $ocm"
    echo "temperature: $temp"
    oc_perm "$perm"
    echo "---"
    echo
    cat "$body"
  } > "$OC_DIR/agents/$role.md"

  # ---------- Claude Code ----------
  {
    echo "---"
    echo "name: $role"
    echo "description: $desc"
    echo "tools: $(cc_tools "$perm")"
    echo "model: $ccm"
    echo "---"
    echo
    cat "$body"
  } > "$CC_DIR/agents/$role.md"

  # ---------- Codex (prompt invocable /role) ----------
  {
    echo "<!-- Codex prompt: /$role  |  modelo recomendado: $cxm  |  tier: $perm -->"
    echo "<!-- En loops no interactivos: codex exec -m $cxm --prompt-file este_archivo -->"
    echo
    cat "$body"
  } > "$CX_DIR/prompts/$role.md"

  count=$((count+1))
done < "$MANIFEST"

# ---------- Commands (canónicos -> opencode/claude; codex via prompts) ----------
if [ -d "$CANON/commands" ]; then
  cp -f "$CANON"/commands/*.md "$OC_DIR/commands/" 2>/dev/null || true
  cp -f "$CANON"/commands/*.md "$CC_DIR/commands/" 2>/dev/null || true
fi

# ---------- Skills (portables: mismo SKILL.md en los 3) ----------
for H in "$OC_DIR" "$CC_DIR" "$CX_DIR"; do
  rm -rf "$H/skills"; mkdir -p "$H/skills"
  if [ -d "$CANON/skills" ]; then
    cp -a "$CANON"/skills/. "$H/skills/" 2>/dev/null || true
  fi
done

# ---------- Configs compartidas ----------
[ -f "$SHARED/opencode.json" ] && cp -f "$SHARED/opencode.json" "$OC_DIR/opencode.json"
[ -f "$SHARED/AGENTS.opencode.md" ] && cp -f "$SHARED/AGENTS.opencode.md" "$OC_DIR/AGENTS.md"
[ -f "$SHARED/CLAUDE.md" ] && cp -f "$SHARED/CLAUDE.md" "$CC_DIR/CLAUDE.md"
[ -f "$SHARED/AGENTS.codex.md" ] && cp -f "$SHARED/AGENTS.codex.md" "$CX_DIR/AGENTS.md"
[ -f "$SHARED/config.codex.snippet.toml" ] && cp -f "$SHARED/config.codex.snippet.toml" "$CX_DIR/config.snippet.toml"

echo "Generados $count agentes en cada harness."

# ============================ INSTALL ============================
if [ "$INSTALL" = "--install" ]; then
  echo ">> Instalando en dirs vivos..."

  # OpenCode
  mkdir -p "$HOME/.config/opencode/agents" "$HOME/.config/opencode/commands" "$HOME/.config/opencode/skills"
  cp -f "$OC_DIR"/agents/*.md "$HOME/.config/opencode/agents/"
  cp -f "$OC_DIR"/commands/*.md "$HOME/.config/opencode/commands/" 2>/dev/null || true
  cp -a "$OC_DIR"/skills/. "$HOME/.config/opencode/skills/" 2>/dev/null || true
  [ -f "$OC_DIR/opencode.json" ] && cp -f "$OC_DIR/opencode.json" "$HOME/.config/opencode/opencode.json"
  [ -f "$OC_DIR/AGENTS.md" ] && cp -f "$OC_DIR/AGENTS.md" "$HOME/.config/opencode/AGENTS.md"

  # Claude Code
  mkdir -p "$HOME/.claude/agents" "$HOME/.claude/commands" "$HOME/.claude/skills"
  cp -f "$CC_DIR"/agents/*.md "$HOME/.claude/agents/"
  cp -f "$CC_DIR"/commands/*.md "$HOME/.claude/commands/" 2>/dev/null || true
  cp -a "$CC_DIR"/skills/. "$HOME/.claude/skills/" 2>/dev/null || true
  [ -f "$CC_DIR/CLAUDE.md" ] && cp -f "$CC_DIR/CLAUDE.md" "$HOME/.claude/CLAUDE.md"

  # Codex
  mkdir -p "$HOME/.codex/prompts" "$HOME/.codex/skills"
  cp -f "$CX_DIR"/prompts/*.md "$HOME/.codex/prompts/"
  cp -a "$CX_DIR"/skills/. "$HOME/.codex/skills/" 2>/dev/null || true
  [ -f "$CX_DIR/AGENTS.md" ] && cp -f "$CX_DIR/AGENTS.md" "$HOME/.codex/AGENTS.md"

  echo ">> Instalado. Recordá: el config.toml de Codex se ajusta a mano (ver config.snippet.toml)."
fi
