#!/usr/bin/env bash
# mcp.sh — Enciende/apaga un MCP de OpenCode bajo demanda (lo usa la IA TRAS pedirte permiso).
# Uso: ai/scripts/mcp.sh on|off <engram|context7|playwright|brave-cdp> [--all]
# Off por defecto: la idea es prenderlo, usarlo y APAGARLO al terminar para no consumir al pedo.
set -euo pipefail
CFG="$HOME/.config/opencode/opencode.json"
ACTION="${1:?on|off}"; SERVER="${2:?nombre del server}"
case "$ACTION" in on) VAL=true;; off) VAL=false;; *) echo "usar: on|off"; exit 1;; esac
[ -f "$CFG" ] || { echo "no existe $CFG"; exit 1; }

tmp="$(jq --arg s "$SERVER" --argjson v "$VAL" '
  if (.mcp[$s]) then .mcp[$s].enabled = $v
  else error("server desconocido: " + $s) end' "$CFG")"
printf '%s\n' "$tmp" > "$CFG"
echo "MCP '$SERVER' -> enabled=$VAL"
echo "Estado MCP:"; jq -r '.mcp | to_entries[] | "  \(.key): \(.value.enabled)"' "$CFG"
echo "NOTA: si OpenCode no toma el cambio en caliente, reabrí la sesión una vez."
