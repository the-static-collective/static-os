#!/data/data/com.termux/files/usr/bin/sh
# Termux Android front door; never root, never phones home or installs packages.
set -eu
SELF="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
OUT="${1:-}"
[ -n "$OUT" ] && [ -d "$OUT" ] || {
 echo "Choose a pre-existing writable directory: $0 PATH" >&2
 exit 2
}
if command -v python3 >/dev/null 2>&1; then
 PY=python3
elif command -v python >/dev/null 2>&1; then
 PY=python
else
 echo "Python 3 not available in Termux; no package installed automatically." >&2
 exit 2
fi
exec "$PY" "$SELF/ports/terminal/genesis.py" --device ANDROID_TERMUX_LOCAL --out-dir "$OUT"
