#!/usr/bin/env bash
# mcp.sh — Enciende/apaga MCPs de OpenCode bajo demanda y diagnostica browser gates.
# Uso:
#   ai/scripts/mcp.sh on|off|status <engram|context7|playwright|brave-cdp>
#   ai/scripts/mcp.sh browser-gate <playwright|brave-cdp|auto>
#   ai/scripts/mcp.sh ensure-brave-cdp
#
# Los MCP arrancan apagados. El runtime/E2E gate es la excepción autorizada: el agente puede prender el MCP
# de navegador que necesita, usarlo, registrar evidencia y apagarlo al terminar.
set -euo pipefail

CFG="${OPENCODE_CONFIG:-$HOME/.config/opencode/opencode.json}"
ACTION="${1:-}"
SERVER="${2:-}"
BRAVE_CDP_URL="${BRAVE_CDP_URL:-http://127.0.0.1:9222}"
BRAVE_USER_DATA_DIR="${BRAVE_USER_DATA_DIR:-$HOME/.cache/set-agentes/brave-cdp}"
BRAVE_LOG="${BRAVE_LOG:-/tmp/set-agentes-brave-cdp.log}"

usage() {
  cat <<'EOF'
usar:
  ai/scripts/mcp.sh on|off|status <engram|context7|playwright|brave-cdp>
  ai/scripts/mcp.sh browser-gate <playwright|brave-cdp|auto>
  ai/scripts/mcp.sh ensure-brave-cdp
EOF
}

[ -n "$ACTION" ] || { usage; exit 2; }
[ -f "$CFG" ] || { echo "MCP_FAIL: no existe $CFG"; exit 2; }
command -v jq >/dev/null 2>&1 || { echo "MCP_FAIL: falta jq"; exit 127; }

server_exists() {
  jq -e --arg s "$1" '.mcp[$s]' "$CFG" >/dev/null
}

set_enabled() {
  local server="$1" value="$2"
  server_exists "$server" || { echo "MCP_FAIL: server desconocido: $server"; exit 2; }
  local temp
  temp="$(mktemp "${TMPDIR:-/tmp}/set-agentes-mcp.XXXXXX")"
  jq --arg s "$server" --argjson v "$value" '.mcp[$s].enabled = $v' "$CFG" > "$temp"
  mv "$temp" "$CFG"
  echo "MCP_SET server=$server enabled=$value config=$CFG"
}

print_status() {
  jq -r '.mcp | to_entries[] | "MCP_STATUS server=\(.key) enabled=\(.value.enabled)"' "$CFG"
}

port_ready() {
  local url="$1"
  curl -fsS --max-time 2 "$url/json/version" >/dev/null 2>&1
}

find_brave() {
  for bin in brave-browser brave brave-browser-stable chromium chromium-browser google-chrome google-chrome-stable; do
    if command -v "$bin" >/dev/null 2>&1; then
      command -v "$bin"
      return 0
    fi
  done
  return 1
}

ensure_brave_cdp() {
  if port_ready "$BRAVE_CDP_URL"; then
    echo "BRAVE_CDP_READY url=$BRAVE_CDP_URL"
    return 0
  fi

  local bin
  if ! bin="$(find_brave)"; then
    echo "BRAVE_CDP_FAIL: no encontre Brave/Chromium/Chrome en PATH"
    return 2
  fi

  mkdir -p "$BRAVE_USER_DATA_DIR"
  nohup "$bin" \
    --remote-debugging-port=9222 \
    --remote-debugging-address=127.0.0.1 \
    --user-data-dir="$BRAVE_USER_DATA_DIR" \
    --no-first-run \
    --new-window about:blank >"$BRAVE_LOG" 2>&1 &

  for _ in 1 2 3 4 5 6 7 8 9 10; do
    if port_ready "$BRAVE_CDP_URL"; then
      echo "BRAVE_CDP_READY url=$BRAVE_CDP_URL log=$BRAVE_LOG"
      return 0
    fi
    sleep 1
  done

  echo "BRAVE_CDP_FAIL: lance $bin pero $BRAVE_CDP_URL no respondio; log=$BRAVE_LOG"
  return 2
}

case "$ACTION" in
  on)
    [ -n "$SERVER" ] || { usage; exit 2; }
    set_enabled "$SERVER" true
    print_status
    ;;
  off)
    [ -n "$SERVER" ] || { usage; exit 2; }
    set_enabled "$SERVER" false
    print_status
    ;;
  status)
    print_status
    ;;
  ensure-brave-cdp)
    ensure_brave_cdp
    set_enabled brave-cdp true
    print_status
    ;;
  browser-gate)
    mode="${SERVER:-auto}"
    case "$mode" in
      playwright)
        set_enabled playwright true
        print_status
        echo "BROWSER_GATE_READY mode=playwright"
        ;;
      brave-cdp)
        ensure_brave_cdp
        set_enabled brave-cdp true
        print_status
        echo "BROWSER_GATE_READY mode=brave-cdp url=$BRAVE_CDP_URL"
        ;;
      auto)
        if ensure_brave_cdp; then
          set_enabled brave-cdp true
          print_status
          echo "BROWSER_GATE_READY mode=brave-cdp url=$BRAVE_CDP_URL"
        else
          set_enabled playwright true
          print_status
          echo "BROWSER_GATE_READY mode=playwright fallback=brave-cdp-unavailable"
        fi
        ;;
      *)
        usage
        exit 2
        ;;
    esac
    ;;
  *)
    usage
    exit 2
    ;;
esac
