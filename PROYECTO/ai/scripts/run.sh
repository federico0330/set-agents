#!/usr/bin/env bash
# run.sh — Launch backend + frontend for app-runner / runtime-verifier.
# Subcommands: up | down | status | logs. Backgrounds servers, waits for readiness, prints URLs.
# Fill BACKEND_CMD / FRONTEND_CMD with this project's real start commands
# (project-bootstrapper infers them from the stack when it can; otherwise `up` exits 2 with a clear message —
#  it never hangs and never guesses).
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$ROOT"
STATE="ai/state"; mkdir -p "$STATE"

# ── Configure me (o dejá que el project-bootstrapper los complete) ──────────────────────────
BACKEND_CMD=""     # e.g. dotnet run --project src/Api   |   python -m uvicorn app.main:app --port 8000
FRONTEND_CMD=""    # e.g. npm run dev                     |   npm start
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

start_one() { # name cmd
  local name="$1" cmd="$2"
  [ -z "$cmd" ] && return 0
  if [ -f "$STATE/$name.pid" ] && kill -0 "$(cat "$STATE/$name.pid")" 2>/dev/null; then
    echo "$name ya está corriendo (pid $(cat "$STATE/$name.pid"))"; return 0
  fi
  echo "▶ $name: $cmd"
  nohup bash -lc "$cmd" > "$STATE/$name.log" 2>&1 &
  echo $! > "$STATE/$name.pid"
}
stop_one() { # name
  local name="$1" pid
  [ -f "$STATE/$name.pid" ] || return 0
  pid="$(cat "$STATE/$name.pid")"
  if kill -0 "$pid" 2>/dev/null; then kill "$pid" 2>/dev/null; sleep 1; kill -9 "$pid" 2>/dev/null || true; fi
  rm -f "$STATE/$name.pid"; echo "■ $name detenido"
}
wait_url() { # url timeout_s
  local url="$1" t="${2:-40}" i=0
  while [ "$i" -lt "$t" ]; do curl -fsS "$url" >/dev/null 2>&1 && return 0; sleep 1; i=$((i+1)); done
  return 1
}

case "${1:-}" in
  up)
    if [ -z "$BACKEND_CMD" ] && [ -z "$FRONTEND_CMD" ]; then
      echo "run.sh sin configurar: definí BACKEND_CMD/FRONTEND_CMD para este stack." >&2; exit 2
    fi
    start_one backend  "$BACKEND_CMD"
    start_one frontend "$FRONTEND_CMD"
    [ -n "$BACKEND_CMD" ]  && { wait_url "$BACKEND_URL" 40  && echo "backend  ready: $BACKEND_URL"  || echo "⚠ backend no respondió a tiempo ($BACKEND_URL)"; }
    [ -n "$FRONTEND_CMD" ] && { wait_url "$FRONTEND_URL" 40 && echo "frontend ready: $FRONTEND_URL" || echo "⚠ frontend no respondió a tiempo ($FRONTEND_URL)"; }
    ;;
  down)   stop_one frontend; stop_one backend ;;
  status)
    for n in backend frontend; do
      if [ -f "$STATE/$n.pid" ] && kill -0 "$(cat "$STATE/$n.pid")" 2>/dev/null; then
        echo "$n: up (pid $(cat "$STATE/$n.pid"))"; else echo "$n: down"; fi
    done ;;
  logs)   tail -n 100 "$STATE"/backend.log "$STATE"/frontend.log 2>/dev/null || true ;;
  *) echo "Uso: run.sh up|down|status|logs" >&2; exit 2 ;;
esac
