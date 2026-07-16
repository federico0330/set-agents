#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="generate"
PROFILE=""
OUTPUT=""
YES=0
TARGETS=()

usage() {
  echo "usage: ./build.sh [--check|--diff|--install] [--profile go-zen|zen|local] [--output DIR] [--target opencode|claude-code|codex] [--yes]"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --check) MODE="check" ;;
    --diff) MODE="diff" ;;
    --install) MODE="install" ;;
    --profile) shift; PROFILE="${1:-}" ;;
    --output) shift; OUTPUT="${1:-}" ;;
    --target) shift; TARGETS+=("${1:-}") ;;
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

ensure_drift_hook() {
  local hook="$ROOT/.git/hooks/post-commit"
  [ -d "$ROOT/.git/hooks" ] || return 0
  if [ ! -e "$hook" ] || grep -q "set-agentes drift check" "$hook" 2>/dev/null; then
    cat > "$hook" <<'HOOK'
#!/usr/bin/env bash
# set-agentes drift check (managed by build.sh) — warns when the live install lags the repo.
ROOT="$(git rev-parse --show-toplevel)"
"$ROOT/ai/scripts/check-drift.sh" || true
HOOK
    chmod +x "$hook"
  fi
}

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
    ensure_drift_hook
    ;;
  install)
    target_args=()
    for target in "${TARGETS[@]}"; do
      target_args+=(--target "$target")
    done
    python3 "$ROOT/ai/scripts/install.py" --staging "$STAGING" --home "$HOME" "${target_args[@]}" --preview
    if [ "$YES" -ne 1 ]; then
      read -r -p "Install this managed diff globally? [y/N] " answer
      case "$answer" in y|Y|yes|YES) ;; *) echo "Installation cancelled."; exit 1;; esac
    fi
    python3 "$ROOT/ai/scripts/install.py" --staging "$STAGING" --home "$HOME" "${target_args[@]}"
    ensure_drift_hook
    ;;
esac
