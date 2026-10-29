#!/bin/sh
# Deliberately *CI image only*. An isolated QEMU guest invokes this to prove
# kernel reached userspace AND the original source-native loopback app works.
set -eu
exec >/dev/ttyS0 2>&1
echo 'STATIC-OS-GENESIS-VM-PROBE-START'
case "$(/opt/static-os/node24/bin/node --version)" in
 v24.10.0) :;;
 *) echo 'STATIC-OS-GENESIS-VM-NODE-REFUSED'; exit 1;;
esac
i=0
until id user >/dev/null 2>&1; do
 i=$((i+1)); [ "$i" -lt 25 ] || { echo 'STATIC-OS-GENESIS-VM-LIVE-USER-MISSING'; exit 1; }
 sleep 2
done
STATE=/tmp/static-os-genesis-vm-fixture
mkdir -p "$STATE/runs"
chown -R user:user "$STATE"
chmod 700 "$STATE" "$STATE/runs"
BASE=/opt/static-os/genesis-sources
runuser -u user -- env \
 GIT_CONFIG_GLOBAL=/usr/share/static-os/genesis-gitconfig PYTHONDONTWRITEBYTECODE=1 \
 /opt/static-os/node24/bin/node "$BASE/cannon/scripts/first-boot.mjs" \
 --staticos "$BASE/staticos" --webz "$BASE/webz" --gro "$BASE/gro" \
 --ghot "$BASE/ghot" --jarvis "$BASE/jarvis" \
 --warm-cannon "$BASE/cannon-warm" --warm-ghot "$BASE/ghot-warm" \
 --warm-full "$BASE/full" --warm-band "$BASE/band" --warm-garden "$BASE/garden" \
 --out-parent "$STATE/runs" --port 8766 > "$STATE/console.log" 2>&1 &
PID=$!
trap 'kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true' EXIT
i=0
until curl -fsS --max-time 1 http://127.0.0.1:8766/ -o /dev/null 2>/dev/null; do
 i=$((i+1)); [ "$i" -lt 45 ] || {
  echo 'STATIC-OS-GENESIS-VM-CONSOLE-UNAVAILABLE'
  cat "$STATE/console.log" || true
  exit 1
 }
 sleep 1
done
python3 /usr/local/sbin/vm-genesis-probe.py
echo 'STATIC-OS-GENESIS-VM-NATIVE-EXECUTION-VERIFIED'
echo 'STATIC-OS-GENESIS-BIOS-BOOT-VERIFIED'
