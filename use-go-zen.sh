#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
printf 'go-zen\n' > "$ROOT/active-profile"
exec "$ROOT/build.sh" --install "$@"
