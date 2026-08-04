#!/usr/bin/env bash
# check-drift.sh — Detecta si la instalación global quedó atrás del repo.
# Regenera a staging desde la fuente actual y compara con lo instalado (install.py --preview).
# Uso: ai/scripts/check-drift.sh [--quiet]
# Salida: DRIFT_OK (exit 0) o DRIFT_DETECTED (exit 1).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
QUIET="${1:-}"

STAGING="$(mktemp -d "${TMPDIR:-/tmp}/set-agentes-drift.XXXXXX")"
trap 'rm -rf "$STAGING"' EXIT

# Generation failure is an internal error (2), never "stale" (1): the caller's
# badge must not read a broken generator as a drifted install.
if ! python3 "$ROOT/ai/scripts/generate.py" --output "$STAGING" >/dev/null; then
  echo "DRIFT_UNKNOWN: generate.py falló; corré ./build.sh --check para ver el detalle." >&2
  exit 2
fi

# Scope-aware: a machine that installed only some harness trees (install.py records
# them in install-targets.json) is compared only against those trees. No record (or a
# full record) keeps the historical behavior: compare everything.
DRIFT_HOME_DIR="${DRIFT_HOME:-$HOME}"
TARGET_ARGS=()
SCOPE_FILE="$DRIFT_HOME_DIR/.local/state/set-agentes/install-targets.json"
if [ -f "$SCOPE_FILE" ]; then
  while IFS= read -r target; do
    [ -n "$target" ] && TARGET_ARGS+=(--target "$target")
  done < <(python3 - "$SCOPE_FILE" <<'PY'
import json, sys
try:
    scope = json.load(open(sys.argv[1]))
except Exception:
    scope = []
known = {"opencode", "claude-code", "codex", "pi"}
scope = [t for t in scope if t in known]
if scope and set(scope) != known:
    print("\n".join(scope))
PY
)
fi

PREVIEW="$(python3 "$ROOT/ai/scripts/install.py" --staging "$STAGING" --home "$DRIFT_HOME_DIR" ${TARGET_ARGS[@]+"${TARGET_ARGS[@]}"} --preview 2>/dev/null | tail -5)"
COUNT="$(sed -n 's/^MANAGED_DIFF_FILES=//p' <<<"$PREVIEW")"

if [ -z "$COUNT" ]; then
  echo "DRIFT_UNKNOWN: no pude calcular el preview de instalación." >&2
  exit 2
fi

if [ "$COUNT" -gt 0 ]; then
  echo "DRIFT_DETECTED: $COUNT archivos gestionados difieren entre el repo y la instalación."
  echo "  → corré: cd $ROOT && ./build.sh --install"
  echo "  (una instalación atrasada ya costó una semana de cuota: revisores huérfanos caros + MCP prendido.)"
  exit 1
fi

[ "$QUIET" = "--quiet" ] || echo "DRIFT_OK: instalación al día con el repo."
