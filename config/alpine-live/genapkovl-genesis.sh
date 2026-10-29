#!/bin/sh -eu
# Alpine aports apkovl hook called with hostname, no machine-wide installer.
# GENESIS_PAYLOAD is a build-time image of eleven source-owned Git objects;
# only public-safe source/specimens may be embedded in the distributed ISO.
HOSTNAME="${1:-}"
[ "$HOSTNAME" = genesis ] || exit 2
[ -d "${GENESIS_PAYLOAD:-/nonexistent}" ] || {
    echo "REFUSE: original 11 Git source histories must be staged" >&2
    exit 2
}
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp"/etc/apk "$tmp"/etc/local.d "$tmp"/etc/runlevels/default \
 "$tmp"/etc/runlevels/sysinit "$tmp"/etc/runlevels/boot \
 "$tmp"/etc/runlevels/shutdown "$tmp"/usr/local/bin \
 "$tmp"/usr/local/sbin "$tmp"/usr/share/static-os \
 "$tmp"/opt/static-os/genesis-sources
printf '%s\n' 'genesis' > "$tmp"/etc/hostname
# Alpine diskless boot installs from the local ISO repository (no network).
printf '%s\n' alpine-base nodejs npm python3 git ca-certificates curl bash \
 > "$tmp"/etc/apk/world
for service in devfs dmesg mdev hwdrivers modloop; do
  ln -s "/etc/init.d/$service" "$tmp/etc/runlevels/sysinit/$service"
done
for service in hwclock modules sysctl hostname bootmisc; do
  ln -s "/etc/init.d/$service" "$tmp/etc/runlevels/boot/$service"
done
ln -s /etc/init.d/local "$tmp"/etc/runlevels/default/local
for service in mount-ro killprocs savecache; do
  ln -s "/etc/init.d/$service" "$tmp/etc/runlevels/shutdown/$service"
done
cp -a "${GENESIS_PAYLOAD}/." "$tmp/opt/static-os/genesis-sources/"
# Base git config explicitly trusts these immutable original Git objects.
cp /work/manifest/genesis-boot-003.json \
 "$tmp/usr/share/static-os/genesis-boot-003.json"
python3 - "$tmp/usr/share/static-os/genesis-boot-003.json" \
 "$tmp/usr/share/static-os/genesis-gitconfig" <<'PY'
import json,sys
m=json.load(open(sys.argv[1]))
assert len(m['sources'])==11
with open(sys.argv[2],'w') as f:
    f.write('[safe]\n')
    for s in m['sources']:
        f.write('    directory = /opt/static-os/genesis-sources/'+s['id']+'\n')
PY
install -m 0755 /work/config/alpine-live/static-genesis-start \
 "$tmp/usr/local/bin/static-genesis-start"
install -m 0755 /work/config/alpine-live/genesis-local.start \
 "$tmp/etc/local.d/genesis.start"
if [ "${GENESIS_CI_VM_PROBE:-0}" = 1 ]; then
    install -m 0755 /work/tests/vm-genesis-probe.py \
        "$tmp/usr/local/sbin/vm-genesis-probe.py"
    printf '%s\n' CI_VM_PROBE_ENABLED > "$tmp/usr/share/static-os/CI-ONLY-NOT-FOR-FIELD-PILOT"
fi
printf '%s\n' 'STATIC OS GENESIS — Alpine Live' \
  'First boot is a locally controlled computer; nothing is built without approval.' \
  'Local console: static-genesis-start' \
  'Developer console: http://127.0.0.1:8766/ (same machine only).' \
 > "$tmp"/etc/motd
# The overlay is installed at boot into RAM. No live source download occurs.
tar -C "$tmp" -czf "$HOSTNAME.apkovl.tar.gz" etc opt usr
