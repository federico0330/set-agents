#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="generate"
OUTPUT=""
YES=0
TARGETS=()

usage() {
  echo "usage: ./build.sh [--check|--diff|--install] [--output DIR] [--target opencode|claude-code|codex|pi|cursor] [--yes]"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --check) MODE="check" ;;
    --diff) MODE="diff" ;;
    --install) MODE="install" ;;
    --output) shift; OUTPUT="${1:-}" ;;
    --target) shift; TARGETS+=("${1:-}") ;;
    --yes) YES=1 ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
  shift
done

if [ -n "$OUTPUT" ]; then
  python3 "$ROOT/ai/scripts/generate.py" --output "$OUTPUT"
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

# check never reads this generic STAGING (it always compared self-scaffold files directly, and
# now also diffs a SEPARATE tree below, per ADR-0041 point 1) -- build it only for the modes
# that actually consume it, so `--check` doesn't run generate.py twice.
if [ "$MODE" != "check" ]; then
  STAGING="$(mktemp -d "${TMPDIR:-/tmp}/set-agentes.XXXXXX")"
  trap 'rm -rf "$STAGING"' EXIT
  python3 "$ROOT/ai/scripts/generate.py" --output "$STAGING"
fi

case "$MODE" in
  check)
    # Every file that lives in BOTH trees, not a hand-written pair. Until 2026-08-18 this
    # named exactly two, and the drift that mattered happened in the ones nobody named:
    # PROYECTO/ still shipped render_bitacora.py truncating narration at 300 chars (the
    # N3b-F01 finding of feature 028, closed as repaired) and an axes.py missing
    # validate_row entirely (feature 029, also closed). Two features in DONE were half
    # delivered and the gate said SELF_SCAFFOLD_SYNC_OK. `verify.sh` is the ONE declared
    # exception: the harness copy gates this repo, the template copy sniffs a generic
    # project's stack. Mirrored by tests/test_narracion_contrato.py's parity test.
    drift=0
    checked=0
    while IFS= read -r source; do
      rel="${source#"$ROOT/PROYECTO/ai/scripts/"}"
      case "$rel" in verify.sh|*/__pycache__/*|__pycache__/*) continue ;; esac
      target="$ROOT/ai/scripts/$rel"
      [ -e "$target" ] || continue
      checked=$((checked + 1))
      if ! cmp -s "$source" "$target"; then
        echo "SELF_SCAFFOLD_DRIFT file=ai/scripts/$rel template=PROYECTO/ai/scripts/$rel reason=differs"
        drift=1
      fi
    done <<EOF
$(find "$ROOT/PROYECTO/ai/scripts" -type f | sort)
EOF
    if [ "$checked" -lt 23 ]; then
      echo "SELF_SCAFFOLD_DRIFT reason=mirror-shrank checked=$checked expected>=23"
      drift=1
    fi
    [ "$drift" -eq 0 ] || exit 1
    echo "SELF_SCAFFOLD_SYNC_OK files=$checked"

    # AC-01 (ADR-0041): the self-scaffold comparison above never looked at Global/ -- this is
    # the check that was missing. Reuses verify.sh's diff pattern (a real gate, no `|| true`),
    # not --diff's (which always exits 0 and stays untouched as the "show me" mode).
    CHECK_STAGING="$(mktemp -d "${TMPDIR:-/tmp}/set-agentes-check.XXXXXX")"
    trap 'rm -rf "$CHECK_STAGING"' EXIT
    python3 "$ROOT/ai/scripts/generate.py" --output "$CHECK_STAGING" >/dev/null
    tree_drift=0
    for harness in opencode claude-code codex pi cursor; do
      if ! diff -ruN "$ROOT/Global/$harness" "$CHECK_STAGING/$harness"; then
        tree_drift=1
      fi
    done
    if [ "$tree_drift" -eq 0 ]; then
      echo "GLOBAL_TREE_SYNC_OK harnesses=5"
    else
      echo "GLOBAL_TREE_DRIFT"
      exit 1
    fi
    echo "BUILD_CHECK_PASS"
    ;;
  diff)
    diff -ruN "$ROOT/Global/opencode" "$STAGING/opencode" || true
    diff -ruN "$ROOT/Global/claude-code" "$STAGING/claude-code" || true
    diff -ruN "$ROOT/Global/codex" "$STAGING/codex" || true
    diff -ruN "$ROOT/Global/pi" "$STAGING/pi" || true
    diff -ruN "$ROOT/Global/cursor" "$STAGING/cursor" || true
    ;;
  generate)
    for harness in opencode claude-code codex pi cursor; do
      rm -rf "$ROOT/Global/$harness"
      cp -a "$STAGING/$harness" "$ROOT/Global/$harness"
    done
    echo "Generated tracked artifacts."
    ensure_drift_hook
    ;;
  install)
    target_args=()
    # bash 3.2 -- still /bin/bash on macOS -- treats "${EMPTY[@]}" as an unbound
    # variable under `set -u` (fixed upstream only in 4.4).  With no --target flag
    # TARGETS is empty, so the plain expansion aborted every macOS `--install`; the
    # `+` form expands to nothing at all when the array is unset or empty.
    for target in ${TARGETS[@]+"${TARGETS[@]}"}; do
      target_args+=(--target "$target")
    done
    python3 "$ROOT/ai/scripts/install.py" --staging "$STAGING" --home "$HOME" ${target_args[@]+"${target_args[@]}"} --preview
    if [ "$YES" -ne 1 ]; then
      read -r -p "Install this managed diff globally? [y/N] " answer
      case "$answer" in y|Y|yes|YES) ;; *) echo "Installation cancelled."; exit 1;; esac
    fi
    python3 "$ROOT/ai/scripts/install.py" --staging "$STAGING" --home "$HOME" ${target_args[@]+"${target_args[@]}"}
    ensure_drift_hook
    ;;
esac
