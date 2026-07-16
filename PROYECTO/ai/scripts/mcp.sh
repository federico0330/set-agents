#!/usr/bin/env bash
# mcp.sh — Enciende/apaga MCPs de OpenCode bajo demanda y diagnostica browser gates.
# Uso:
#   ai/scripts/mcp.sh on|off|status <engram|context7|playwright|brave-cdp>
#   ai/scripts/mcp.sh off-all
#   ai/scripts/mcp.sh browser-gate <playwright|brave-cdp|auto>
#   ai/scripts/mcp.sh ensure-brave-cdp|stop-brave-cdp
#
# Los MCP arrancan apagados. El runtime/E2E gate es la excepción autorizada: el agente puede prender el MCP
# de navegador que necesita, usarlo, registrar evidencia y apagarlo al terminar.
set -euo pipefail

CFG="${OPENCODE_CONFIG:-$HOME/.config/opencode/opencode.json}"
ACTION="${1:-}"
SERVER="${2:-}"
BRAVE_CDP_WRAPPER="$(dirname "$0")/brave-cdp-mcp.sh"

usage() {
  cat <<'EOF'
usar:
  ai/scripts/mcp.sh on|off|status <engram|context7|playwright|brave-cdp>
  ai/scripts/mcp.sh off-all
  ai/scripts/mcp.sh browser-gate <playwright|brave-cdp|auto>
  ai/scripts/mcp.sh ensure-brave-cdp|stop-brave-cdp
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

ensure_brave_cdp() {
  [ -x "$BRAVE_CDP_WRAPPER" ] || { echo "MCP_FAIL: falta lifecycle wrapper"; return 2; }
  "$BRAVE_CDP_WRAPPER" start
}

case "$ACTION" in
  on)
    [ -n "$SERVER" ] || { usage; exit 2; }
    set_enabled "$SERVER" true
    print_status
    echo "MCP_REMINDER: apagalo al terminar (ai/scripts/mcp.sh off $SERVER) — un MCP que queda prendido inyecta sus tools en TODAS las sesiones de TODOS los proyectos."
    ;;
  off-all)
    jq -r '.mcp | keys[]' "$CFG" | while read -r server; do
      set_enabled "$server" false
    done
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
  stop-brave-cdp)
    "$BRAVE_CDP_WRAPPER" stop
    set_enabled brave-cdp false
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
        echo "BROWSER_GATE_READY mode=brave-cdp url=http://127.0.0.1:9222"
        ;;
      auto)
        if ensure_brave_cdp; then
          set_enabled brave-cdp true
          print_status
          echo "BROWSER_GATE_READY mode=brave-cdp url=http://127.0.0.1:9222"
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
