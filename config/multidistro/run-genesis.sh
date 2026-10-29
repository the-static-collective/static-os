#!/bin/sh
# Local loopback only. Explicitly invoked by a human, never a bootloader,
# installer, autonomous project selector, auto-dialer or hardware controller.
set -eu
umask 077
export GIT_CONFIG_GLOBAL=/usr/share/static-os/genesis-gitconfig
export PYTHONDONTWRITEBYTECODE=1
ROOT=/opt/static-os/genesis-sources
RUNS="${XDG_STATE_HOME:-$HOME/.local/state}/static-genesis/runs"
mkdir -p "$RUNS"
if [ "${1:-}" = test-native ]; then
  shift
  export GENESIS_STATICOS="$ROOT/staticos" GENESIS_WEBZ="$ROOT/webz"
  export GENESIS_GRO="$ROOT/gro" GENESIS_GHOT="$ROOT/ghot"
  export GENESIS_JARVIS="$ROOT/jarvis"
  export GENESIS_WARM_CANNON="$ROOT/cannon-warm"
  export GENESIS_WARM_GHOT="$ROOT/ghot-warm"
  export GENESIS_WARM_FULL="$ROOT/full"
  export GENESIS_WARM_BAND="$ROOT/band"
  export GENESIS_WARM_GARDEN="$ROOT/garden"
  export GENESIS_OUTPUT_PARENT="$RUNS"
  exec node --test "$ROOT/cannon/test/boot-console-native.test.mjs"
fi
if [ "$#" -ne 0 ]; then
  echo "REFUSE: unknown argument or arbitrary command" >&2; exit 2
fi
echo "GENESIS BOOT / ORIGINAL SOURCE / ALPINE OR FEDORA CONTAINER"
echo "LOCAL ONLY: http://127.0.0.1:8766/ (inside this container namespace)"
echo "Opening the interface does not run BUILD or WARM automatically."
exec node "$ROOT/cannon/scripts/first-boot.mjs" \
 --staticos "$ROOT/staticos" --webz "$ROOT/webz" \
 --gro "$ROOT/gro" --ghot "$ROOT/ghot" --jarvis "$ROOT/jarvis" \
 --warm-cannon "$ROOT/cannon-warm" --warm-ghot "$ROOT/ghot-warm" \
 --warm-full "$ROOT/full" --warm-band "$ROOT/band" --warm-garden "$ROOT/garden" \
 --out-parent "$RUNS" --port 8766
