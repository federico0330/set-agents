#!/usr/bin/env bash
# Isolated local Brave CDP lifecycle for the brave-cdp MCP.
set -euo pipefail

CDP_HOST="127.0.0.1"
CDP_PORT="9222"
CDP_URL="http://${CDP_HOST}:${CDP_PORT}"
START_TIMEOUT_SECONDS="${BRAVE_CDP_START_TIMEOUT_SECONDS:-15}"
STATE_DIR="${XDG_RUNTIME_DIR:-/tmp}/set-agentes-brave-cdp-${UID}"
PID_FILE="${STATE_DIR}/brave.pid"
PROFILE_FILE="${STATE_DIR}/profile.dir"
LOG_FILE="${STATE_DIR}/brave.log"

fail() {
  printf '%s\n' "BRAVE_CDP_FAIL: $1" >&2
  exit "${2:-2}"
}

usage() {
  printf '%s\n' "usage: $0 start|stop|status|run-mcp"
}

find_brave() {
  local bin
  for bin in brave-browser brave brave-browser-stable; do
    if command -v "$bin" >/dev/null 2>&1; then
      command -v "$bin"
      return 0
    fi
  done
  return 1
}

endpoint_ready() {
  curl --fail --silent --show-error --connect-timeout 1 --max-time 2 \
    "${CDP_URL}/json/version" >/dev/null 2>&1
}

pid_is_our_brave() {
  local pid="$1" profile="$2" cmdline
  if [ -r "/proc/${pid}/cmdline" ]; then
    cmdline="$(tr '\0' ' ' < "/proc/${pid}/cmdline")"
  else
    # macOS/BSD: no /proc — ps exposes the full command line.
    cmdline="$(ps -p "$pid" -o command= 2>/dev/null)" || return 1
    [ -n "$cmdline" ] || return 1
  fi
  [[ "$cmdline" == *"--remote-debugging-address=${CDP_HOST}"* ]] && \
    [[ "$cmdline" == *"--remote-debugging-port=${CDP_PORT}"* ]] && \
    [[ "$cmdline" == *"--user-data-dir=${profile}"* ]]
}

clear_stale_state() {
  if [ -f "$PID_FILE" ] && [ -f "$PROFILE_FILE" ]; then
    local pid profile
    pid="$(<"$PID_FILE")"
    profile="$(<"$PROFILE_FILE")"
    if ! pid_is_our_brave "$pid" "$profile"; then
      rm -f "$PID_FILE" "$PROFILE_FILE"
      [ -d "$profile" ] && rm -rf -- "$profile"
    fi
  fi
}

start() {
  mkdir -p -m 700 "$STATE_DIR"
  chmod 700 "$STATE_DIR"
  clear_stale_state

  if endpoint_ready; then
    if [ -f "$PID_FILE" ] && [ -f "$PROFILE_FILE" ] && \
      pid_is_our_brave "$(<"$PID_FILE")" "$(<"$PROFILE_FILE")"; then
      printf '%s\n' "BRAVE_CDP_READY url=${CDP_URL}"
      return 0
    fi
    fail "local debugging endpoint is already in use; refusing to attach"
  fi

  local browser profile pid deadline
  browser="$(find_brave)" || fail "Brave is not available on PATH"
  profile="$(mktemp -d "${XDG_RUNTIME_DIR:-/tmp}/set-agentes-brave-profile.XXXXXX")"
  chmod 700 "$profile"
  printf '%s\n' "$profile" > "$PROFILE_FILE"

  "$browser" \
    --remote-debugging-address="$CDP_HOST" \
    --remote-debugging-port="$CDP_PORT" \
    --user-data-dir="$profile" \
    --no-first-run \
    --no-default-browser-check \
    --disable-background-networking \
    --disable-component-update \
    --disable-default-apps \
    --new-window about:blank >"$LOG_FILE" 2>&1 &
  pid=$!
  printf '%s\n' "$pid" > "$PID_FILE"
  deadline=$((SECONDS + START_TIMEOUT_SECONDS))
  while [ "$SECONDS" -lt "$deadline" ]; do
    if endpoint_ready; then
      printf '%s\n' "BRAVE_CDP_READY url=${CDP_URL}"
      return 0
    fi
    if ! kill -0 "$pid" 2>/dev/null; then
      rm -f "$PID_FILE"
      rm -rf -- "$profile"
      rm -f "$PROFILE_FILE"
      fail "browser exited before the local debugging endpoint was ready"
    fi
    sleep 1
  done

  stop
  fail "local debugging endpoint did not become ready before timeout"
}

stop() {
  [ -f "$PID_FILE" ] && [ -f "$PROFILE_FILE" ] || return 0
  local pid profile deadline
  pid="$(<"$PID_FILE")"
  profile="$(<"$PROFILE_FILE")"
  if pid_is_our_brave "$pid" "$profile"; then
    kill -TERM "$pid" 2>/dev/null || true
    deadline=$((SECONDS + 10))
    while kill -0 "$pid" 2>/dev/null && [ "$SECONDS" -lt "$deadline" ]; do sleep 1; done
    kill -0 "$pid" 2>/dev/null && kill -KILL "$pid" 2>/dev/null || true
  fi
  rm -f "$PID_FILE" "$PROFILE_FILE" "$LOG_FILE"
  [ -d "$profile" ] && rm -rf -- "$profile"
  rmdir "$STATE_DIR" 2>/dev/null || true
  printf '%s\n' "BRAVE_CDP_STOPPED"
}

status() {
  if endpoint_ready && [ -f "$PID_FILE" ] && [ -f "$PROFILE_FILE" ] && \
    pid_is_our_brave "$(<"$PID_FILE")" "$(<"$PROFILE_FILE")"; then
    printf '%s\n' "BRAVE_CDP_RUNNING url=${CDP_URL}"
  else
    printf '%s\n' "BRAVE_CDP_STOPPED"
  fi
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  status) status ;;
  run-mcp)
    start
    mcp_pid=""
    cleanup_mcp() {
      trap - EXIT INT TERM
      if [ -n "$mcp_pid" ]; then
        kill -TERM "$mcp_pid" 2>/dev/null || true
        wait "$mcp_pid" 2>/dev/null || true
      fi
      stop
    }
    trap cleanup_mcp EXIT INT TERM
    npx -y @playwright/mcp@latest --cdp-endpoint "$CDP_URL" &
    mcp_pid=$!
    wait "$mcp_pid"
    ;;
  *) usage; exit 2 ;;
esac
