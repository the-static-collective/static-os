#!/bin/sh
# x86 32-bit, old laptop, thin Linux computer: no Node24 needed for proposal.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
OUT="${1:-}"
[ -n "$OUT" ] && [ -d "$OUT" ] || {
 echo "Usage: $0 PREEXISTING_OUTPUT_DIRECTORY" >&2; exit 2
}
command -v python3 >/dev/null 2>&1 || {
 echo "Requires locally installed Python 3. No automatic installation." >&2; exit 2
}
exec python3 "$ROOT/ports/terminal/genesis.py" \
 --device LEGACY_LINUX_PYTHON3 --out-dir "$OUT"
