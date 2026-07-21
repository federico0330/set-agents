#!/usr/bin/env bash
# sync-project.sh — Sincroniza los scripts genéricos del template PROYECTO/ai/scripts a un proyecto.
# Uso: ai/scripts/sync-project.sh <project-dir> [--force]
#
# Copia SOLO los scripts genéricos (feature-state.py, check-owned-paths.py, mcp.sh, e2e.sh, loop.sh,
# audit-readonly.sh, brave-cdp-mcp.sh). NO toca run.sh ni verify.sh, que son específicos del proyecto.
#
# Seguridad: si el proyecto tiene features en curso (fase no terminal) cuyo estado NO valida con el
# feature-state.py nuevo, aborta — sincronizar dejaría el estado huérfano. Cerrá la feature o usá --force
# a conciencia. Los archivos pisados quedan backupeados en <proyecto>/ai/state/sync-backup-<ts>/.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEMPLATE="$ROOT/PROYECTO/ai/scripts"
PROJECT="${1:?Uso: ai/scripts/sync-project.sh <project-dir> [--force]}"
FORCE="${2:-}"
GENERIC=(feature-state.py check-owned-paths.py mcp.sh e2e.sh loop.sh audit-readonly.sh brave-cdp-mcp.sh)

[ -d "$PROJECT" ] || { echo "SYNC_FAIL: no existe $PROJECT" >&2; exit 2; }
PROJECT="$(cd "$PROJECT" && pwd)"

# 1. Pre-check: estados de features activos deben validar con el feature-state.py NUEVO.
blockers=0
if compgen -G "$PROJECT/ai/state/features/*.json" >/dev/null; then
  for state in "$PROJECT"/ai/state/features/*.json; do
    if ! python3 - "$TEMPLATE/feature-state.py" "$state" <<'PY'
import json
import subprocess
import sys

script, state = sys.argv[1], sys.argv[2]
try:
    phase = json.load(open(state)).get("phase")
except (OSError, ValueError):
    sys.exit(1)  # unreadable state counts as incompatible
if phase in ("DONE", "BLOCKED"):
    sys.exit(0)  # terminal: syncing cannot break it
# Migration runs before validation: bring a compatible older file up to the new schema in place
# (additive — schema_version + per-package phase). A genuinely divergent schema stays invalid and blocks.
subprocess.run(
    ["python3", script, "migrate", "--state-file", state],
    capture_output=True, text=True,
)
proc = subprocess.run(
    ["python3", script, "validate", "--state-file", state],
    capture_output=True, text=True,
)
try:
    errors = json.loads(proc.stdout).get("errors", [])
except ValueError:
    errors = ["unparseable validate output"]
if errors:
    print(f"  {len(errors)} errores contra el esquema nuevo (fase {phase})")
    sys.exit(1)
sys.exit(0)
PY
    then
      echo "SYNC_BLOCKER: $state es una feature activa incompatible con el esquema nuevo."
      blockers=$((blockers + 1))
    fi
  done
fi
if [ "$blockers" -gt 0 ] && [ "$FORCE" != "--force" ]; then
  echo "SYNC_ABORTED: $blockers feature(s) activas con esquema incompatible. Cerrá la feature (o --force)." >&2
  exit 1
fi

# 2. Backup + copia.
STAMP="$(date +%Y%m%dT%H%M%S)"
BACKUP="$PROJECT/ai/state/sync-backup-$STAMP"
mkdir -p "$PROJECT/ai/scripts"
copied=()
for script in "${GENERIC[@]}"; do
  src="$TEMPLATE/$script"
  dst="$PROJECT/ai/scripts/$script"
  [ -f "$src" ] || continue
  if [ -f "$dst" ] && cmp -s "$src" "$dst"; then
    continue
  fi
  if [ -f "$dst" ]; then
    mkdir -p "$BACKUP"
    cp -a "$dst" "$BACKUP/"
  fi
  install -m 0755 "$src" "$dst"
  copied+=("$script")
done

# 3. Conocimiento global por dominio: se refresca SIEMPRE (es de solo lectura en el proyecto).
#    El conocimiento del proyecto (docs/ai/knowledge/*.md) no se toca: lo escribe memory-scribe.
GLOBAL_KNOWLEDGE="$ROOT/knowledge"
if compgen -G "$GLOBAL_KNOWLEDGE/*.md" >/dev/null; then
  mkdir -p "$PROJECT/docs/ai/knowledge/_global"
  synced_knowledge=0
  for doc in "$GLOBAL_KNOWLEDGE"/*.md; do
    dst="$PROJECT/docs/ai/knowledge/_global/$(basename "$doc")"
    if [ ! -f "$dst" ] || ! cmp -s "$doc" "$dst"; then
      install -m 0644 "$doc" "$dst"
      synced_knowledge=$((synced_knowledge + 1))
    fi
  done
  [ "$synced_knowledge" -gt 0 ] && echo "SYNC_KNOWLEDGE: $synced_knowledge documento(s) globales refrescados en docs/ai/knowledge/_global/"
fi

if [ "${#copied[@]}" -eq 0 ]; then
  echo "SYNC_OK: $PROJECT ya estaba al día."
else
  echo "SYNC_OK: actualizados en $PROJECT: ${copied[*]}"
  [ -d "$BACKUP" ] && echo "  backup de los reemplazados: $BACKUP"
fi
echo "  (run.sh y verify.sh no se tocan: son del proyecto.)"
