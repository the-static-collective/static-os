#!/bin/sh
# Supports Raspberry Pi ARM64 Linux as light proposal station OR optional
# full Node24 CANNON when the 11 pre-reviewed Git roots already exist.
# No auto-download/apt/docker/privileged device controls.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
MODE="${1:-}"
OUT="${2:-}"
[ -n "$MODE" ] && [ -n "$OUT" ] && [ -d "$OUT" ] || {
 echo "Usage: $0 proposal|full PREEXISTING_OUTPUT_DIRECTORY" >&2; exit 2
}
if [ "$MODE" = proposal ]; then
 exec python3 "$ROOT/ports/terminal/genesis.py" \
   --device RASPBERRY_PI_LOCAL --out-dir "$OUT"
fi
[ "$MODE" = full ] || { echo 'REFUSE_UNKNOWN_PI_MODE' >&2; exit 2; }
R="${GENESIS_NATIVE_ROOTS:-}"
[ -n "$R" ] && [ -d "$R/cannon" ] || {
 echo 'HOLD: set GENESIS_NATIVE_ROOTS to 11 exact Git source checkouts.' >&2; exit 2
}
command -v node >/dev/null 2>&1 || { echo 'HOLD: Node24 missing'; exit 2; }
case "$(node --version)" in v24.*) : ;; *) echo 'HOLD: exact Node24 major required'; exit 2;; esac
for repo in cannon staticos webz gro ghot jarvis cannon-warm ghot-warm full band garden; do
 [ -d "$R/$repo/.git" ] || { echo "HOLD: original Git root missing: $repo" >&2; exit 2; }
done
exec node "$R/cannon/scripts/first-boot.mjs" \
 --staticos "$R/staticos" --webz "$R/webz" \
 --gro "$R/gro" --ghot "$R/ghot" --jarvis "$R/jarvis" \
 --warm-cannon "$R/cannon-warm" --warm-ghot "$R/ghot-warm" \
 --warm-full "$R/full" --warm-band "$R/band" --warm-garden "$R/garden" \
 --out-parent "$OUT" --port 8766
