#!/usr/bin/env bash
# loop.sh — Package workflow guard.
# Uso:
#   ./ai/scripts/loop.sh status <FEATURE_ID>
#   ./ai/scripts/loop.sh dry-run <FEATURE_ID>
#
# This project no longer runs the old task-by-task implement→deep-audit loop.
# Start real work with OpenCode `/feature-batch`, which preserves spec approval and then advances by packages.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

cmd="${1:-}"
feature="${2:-}"

case "$cmd" in
  status)
    [ -n "$feature" ] || { echo "Uso: $0 status <FEATURE_ID>" >&2; exit 2; }
    state="ai/state/features/${feature}.json"
    [ -f "$state" ] || { echo "STATE_MISSING: $state" >&2; exit 2; }
    python3 ./ai/scripts/feature-state.py validate "$state"
    ;;
  dry-run)
    [ -n "$feature" ] || { echo "Uso: $0 dry-run <FEATURE_ID>" >&2; exit 2; }
    python3 ./ai/scripts/feature-state.py dry-run "$feature"
    ;;
  *)
    cat >&2 <<'MSG'
Uso:
  ./ai/scripts/loop.sh status <FEATURE_ID>
  ./ai/scripts/loop.sh dry-run <FEATURE_ID>

El loop autónomo tarea→auditoría profunda fue retirado. Usá /feature-batch en OpenCode para:
spec challenge → aprobación humana → paquetes → gates → package review → repair → delta review.
MSG
    exit 2
    ;;
esac
