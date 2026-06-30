#!/usr/bin/env bash
# verify.sh — Gate determinístico. Detecta el stack, corre lint/typecheck/test/build y
# un guardarraíl contra tests debilitados. Sale 0 = VERIFY_PASS, !=0 = falla (ver ai/state/verify.log).
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
mkdir -p ai/state
LOG="ai/state/verify.log"
: > "$LOG"
FAIL=0

run() { echo "+ $*" | tee -a "$LOG"; "$@" 2>&1 | tee -a "$LOG"; return "${PIPESTATUS[0]}"; }
has_npm() { node -e "const p=require('./package.json');process.exit(p.scripts&&p.scripts['$1']?0:1)" 2>/dev/null; }

# ── Node / TS ──────────────────────────────────────────────
if [ -f package.json ]; then
  [ -f package-lock.json ] && run npm ci || true
  has_npm lint      && { run npm run lint      || FAIL=1; }
  has_npm typecheck && { run npm run typecheck || FAIL=1; }
  has_npm test      && { run npm test          || FAIL=1; }
  has_npm build     && { run npm run build     || FAIL=1; }
fi

# ── .NET ───────────────────────────────────────────────────
if ls ./*.sln ./**/*.csproj >/dev/null 2>&1; then
  run dotnet build --nologo || FAIL=1
  run dotnet test  --nologo || FAIL=1
fi

# ── Go ─────────────────────────────────────────────────────
[ -f go.mod ] && { run go vet ./... || FAIL=1; run go test ./... || FAIL=1; }

# ── Python ─────────────────────────────────────────────────
{ [ -f pyproject.toml ] || [ -f pytest.ini ]; } && { run python -m pytest -q || FAIL=1; }

# ── Guardarraíl anti-tests-debilitados ─────────────────────
if command -v rg >/dev/null 2>&1; then
  echo "+ rg guardrail (tests debilitados)" | tee -a "$LOG"
  if rg -n '\.skip\(|\.only\(|it\.only|test\.only|describe\.only|xit\(|xdescribe\(|\[Skip|\[Ignore|@pytest\.mark\.skip|TODO_WEAKEN_TEST' \
        --glob '!node_modules' --glob '!**/bin/**' --glob '!**/obj/**' . 2>/dev/null | tee -a "$LOG" | grep -q .; then
    echo "VERIFY_FAIL: marcador de test debilitado/omitido encontrado" | tee -a "$LOG"
    FAIL=1
  fi
fi

if [ "$FAIL" -eq 0 ]; then echo "VERIFY_PASS" | tee -a "$LOG"; exit 0
else echo "VERIFY_FAIL" | tee -a "$LOG"; exit 1; fi
