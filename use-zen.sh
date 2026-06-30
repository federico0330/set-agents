#!/usr/bin/env bash
# use-zen.sh — Perfil SOLO ZEN: todo en opencode/* (tu plata de Zen) + free para implementar +
# Zen codex para críticos. Usalo cuando se te AGOTÓ el plan Go ('monthly usage limit reached').
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp "$ROOT/profiles/manifest.zen.tsv" "$ROOT/manifest.tsv"
# default model -> Zen
tmp="$(jq '.model = "opencode/deepseek-v4-pro"' "$ROOT/Global/_shared/opencode.json")"
printf '%s\n' "$tmp" > "$ROOT/Global/_shared/opencode.json"

bash "$ROOT/build.sh" --install >/dev/null

echo "✅ Perfil SOLO ZEN activo (no toca el plan Go agotado)."
echo "   • Planificar/auditar: opencode/deepseek-v4-pro (Zen)"
echo "   • Implementar:        opencode/*-free (gratis)"
echo "   • Críticos (db/sec):  opencode/gpt-5.3-codex (Zen codex)"
echo "   GPT Plus (openai/*) queda intacto como reserva manual."
echo "   Cuando Go vuelva a tener cupo → corré:  ./use-go-zen.sh"
