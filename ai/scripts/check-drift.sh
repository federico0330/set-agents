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

python3 "$ROOT/ai/scripts/generate.py" --output "$STAGING" >/dev/null

PREVIEW="$(python3 "$ROOT/ai/scripts/install.py" --staging "$STAGING" --home "${DRIFT_HOME:-$HOME}" --preview 2>/dev/null | tail -5)"
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
