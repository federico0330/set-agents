#!/usr/bin/env bash
# use-go-zen.sh — Perfil GO + ZEN (como antes): plan Go para planificar/auditar, free (Zen) para
# implementar, GPT Plus (openai) para los gates críticos. Usalo cuando tu plan Go TENGA cupo mensual.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp "$ROOT/profiles/manifest.go-zen.tsv" "$ROOT/manifest.tsv"
# default model -> Go
tmp="$(jq '.model = "opencode-go/deepseek-v4-pro"' "$ROOT/Global/_shared/opencode.json")"
printf '%s\n' "$tmp" > "$ROOT/Global/_shared/opencode.json"

bash "$ROOT/build.sh" --install >/dev/null

echo "✅ Perfil GO+ZEN activo."
echo "   • Planificar/auditar: opencode-go/* (plan Go)"
echo "   • Implementar:        opencode/*-free (gratis)"
echo "   • Críticos (db/sec):  openai/gpt-5.5 (GPT Plus)"
echo "   Si Go te dice 'monthly usage limit reached' → corré:  ./use-zen.sh"
