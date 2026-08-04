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

# Harness backend (ADR-0025): OpenCode se maneja acá con jq (comportamiento histórico);
# en una máquina solo-Claude-Code se delega en `set-agents --mcp-on/--mcp-off --harness claude`,
# así el mismo verbo funciona en ambos harnesses y e2e.sh no depende de OpenCode.
HARNESS="opencode"
if [ ! -f "$CFG" ]; then
  if command -v claude >/dev/null 2>&1 && command -v set-agents >/dev/null 2>&1; then
    HARNESS="claude"
  else
    echo "MCP_FAIL: no existe $CFG (y no hay claude+set-agents como alternativa)"; exit 2
  fi
fi
if [ "$HARNESS" = "opencode" ]; then
  command -v jq >/dev/null 2>&1 || { echo "MCP_FAIL: falta jq"; exit 127; }
fi

server_exists() {
  jq -e --arg s "$1" '.mcp[$s]' "$CFG" >/dev/null
}

set_enabled() {
  local server="$1" value="$2"
  if [ "$HARNESS" = "claude" ]; then
    if [ "$value" = "true" ]; then
      set-agents --mcp-on "$server" --harness claude
    else
      set-agents --mcp-off "$server" --harness claude
    fi
    return
  fi
  server_exists "$server" || { echo "MCP_FAIL: server desconocido: $server"; exit 2; }
  local temp
  temp="$(mktemp "${TMPDIR:-/tmp}/set-agentes-mcp.XXXXXX")"
  jq --arg s "$server" --argjson v "$value" '.mcp[$s].enabled = $v' "$CFG" > "$temp"
  mv "$temp" "$CFG"
  echo "MCP_SET server=$server enabled=$value config=$CFG"
}

print_status() {
  if [ "$HARNESS" = "claude" ]; then
    set-agents --mcp --harness claude
    return
  fi
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
    if [ "$HARNESS" = "claude" ]; then
      for server in engram context7 playwright brave-cdp; do
        set_enabled "$server" false || true
      done
    else
      jq -r '.mcp | keys[]' "$CFG" | while read -r server; do
        set_enabled "$server" false
      done
    fi
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
        # En Claude Code el server brave-cdp no está en el catálogo global (su wrapper es
        # un script del proyecto) — el gate usa playwright directo.
        if [ "$HARNESS" != "claude" ] && ensure_brave_cdp; then
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
