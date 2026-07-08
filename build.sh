#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="generate"
PROFILE=""
OUTPUT=""
YES=0

usage() {
  echo "usage: ./build.sh [--check|--diff|--install] [--profile go-zen|zen|local] [--output DIR] [--yes]"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --check) MODE="check" ;;
    --diff) MODE="diff" ;;
    --install) MODE="install" ;;
    --profile) shift; PROFILE="${1:-}" ;;
    --output) shift; OUTPUT="${1:-}" ;;
    --yes) YES=1 ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
  shift
done

if [ -n "$OUTPUT" ]; then
  args=(python3 "$ROOT/ai/scripts/generate.py" --output "$OUTPUT")
  [ -z "$PROFILE" ] || args+=(--profile "$PROFILE")
  "${args[@]}"
  exit
fi

STAGING="$(mktemp -d "${TMPDIR:-/tmp}/set-agentes.XXXXXX")"
trap 'rm -rf "$STAGING"' EXIT
args=(python3 "$ROOT/ai/scripts/generate.py" --output "$STAGING")
[ -z "$PROFILE" ] || args+=(--profile "$PROFILE")
"${args[@]}"

case "$MODE" in
  check)
    ;;
  diff)
    diff -ruN "$ROOT/Global/opencode" "$STAGING/opencode" || true
    diff -ruN "$ROOT/Global/claude-code" "$STAGING/claude-code" || true
    diff -ruN "$ROOT/Global/codex" "$STAGING/codex" || true
    ;;
  generate)
    for harness in opencode claude-code codex; do
      rm -rf "$ROOT/Global/$harness"
      cp -a "$STAGING/$harness" "$ROOT/Global/$harness"
    done
    echo "Generated tracked artifacts for ${PROFILE:-$(<"$ROOT/active-profile")}."
    ;;
  install)
    python3 "$ROOT/ai/scripts/install.py" --staging "$STAGING" --home "$HOME" --preview
    if [ "$YES" -ne 1 ]; then
      read -r -p "Install this managed diff globally? [y/N] " answer
      case "$answer" in y|Y|yes|YES) ;; *) echo "Installation cancelled."; exit 1;; esac
    fi
    python3 "$ROOT/ai/scripts/install.py" --staging "$STAGING" --home "$HOME"
    ;;
esac
