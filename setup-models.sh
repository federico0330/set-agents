#!/usr/bin/env bash
# Wizard / CLI to remap models per area, role, and subscription. See COMO-CAMBIAR-MODELO.md.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$ROOT/ai/scripts/setup_models.py" "$@"
