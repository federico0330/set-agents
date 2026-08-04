#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="generate"
# Env override honored (PROFILE=zen ./build.sh); --profile flag wins below.
PROFILE="${PROFILE:-}"
OUTPUT=""
YES=0
TARGETS=()

usage() {
  echo "usage: ./build.sh [--check|--diff|--install] [--profile go-zen|zen|local] [--output DIR] [--target opencode|claude-code|codex|pi] [--yes]"
}

ensure_active_profile() {
  # The lane is auto-derived from the probe (models_config.auto_profile); the old
  # use-go-zen.sh/use-zen.sh/use-local.sh scripts are gone. Only a MISSING
  # active-profile is written here — an existing one (earlier auto run, or a
  # deliberate hand edit / --profile override) is never flipped silently, so
  # tracked artifacts can't churn because a probe changed its mind.
  [ -n "$PROFILE" ] && return 0
  [ -f "$ROOT/active-profile" ] && return 0
  local lane
  lane="$(python3 - "$ROOT" <<'PY'
import sys
sys.path.insert(0, sys.argv[1] + "/ai/scripts")
import models_config
print(models_config.auto_profile() or "")
PY
)" || lane=""
  if [ -n "$lane" ]; then
    printf '%s\n' "$lane" > "$ROOT/active-profile"
    echo "PROFILE_AUTO $lane"
  fi
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

ensure_active_profile

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
    drift=0
    for name in feature-state.py check-owned-paths.py; do
      source="$ROOT/PROYECTO/ai/scripts/$name"
      target="$ROOT/ai/scripts/$name"
      if [ ! -e "$source" ] || [ ! -e "$target" ]; then
        echo "SELF_SCAFFOLD_DRIFT file=ai/scripts/$name template=PROYECTO/ai/scripts/$name reason=missing"
        drift=1
      elif ! cmp -s "$source" "$target"; then
        echo "SELF_SCAFFOLD_DRIFT file=ai/scripts/$name template=PROYECTO/ai/scripts/$name reason=differs"
        drift=1
      fi
    done
    [ "$drift" -eq 0 ] || exit 1
    echo "SELF_SCAFFOLD_SYNC_OK files=2"
    ;;
  diff)
    diff -ruN "$ROOT/Global/opencode" "$STAGING/opencode" || true
    diff -ruN "$ROOT/Global/claude-code" "$STAGING/claude-code" || true
    diff -ruN "$ROOT/Global/codex" "$STAGING/codex" || true
    diff -ruN "$ROOT/Global/pi" "$STAGING/pi" || true
    ;;
  generate)
    for harness in opencode claude-code codex pi; do
      rm -rf "$ROOT/Global/$harness"
      cp -a "$STAGING/$harness" "$ROOT/Global/$harness"
    done
    echo "Generated tracked artifacts for ${PROFILE:-$(cat "$ROOT/active-profile" 2>/dev/null || echo go-zen)}."
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
