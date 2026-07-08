#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
printf 'zen\n' > "$ROOT/active-profile"
exec "$ROOT/build.sh" --install "$@"
