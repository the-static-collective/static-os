#!/usr/bin/env bash
# STATIC OS GENESIS BOOT 003 — create a candidate hybrid ISO in isolated Debian VM.
# This is a distinct, inspectable build occurrence, not installation or boot proof.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$ROOT/scripts/validate-manifest.py" "$ROOT/manifest/genesis-001.json"
python3 "$ROOT/scripts/validate-boot-image.py" "$ROOT/manifest/genesis-boot-003.json"
[[ ${EUID} -eq 0 ]] || { echo "REFUSE: use disposable root build VM, never user's everyday host" >&2; exit 2; }
for binary in lb git python3 tar sha256sum curl xz; do
 command -v "$binary" >/dev/null || { echo "MISSING: $binary" >&2; exit 2; }
done
BUILD_DIR="${STATIC_OS_BOOT_BUILD_DIR:-$ROOT/.build/genesis-boot-003}"
[[ ! -e "$BUILD_DIR" ]] || { echo "REFUSE: prior build directory already exists" >&2; exit 2; }
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"
lb config --mode debian --distribution bookworm --architectures amd64 \
 --mirror-bootstrap https://deb.debian.org/debian --mirror-chroot https://deb.debian.org/debian \
 --mirror-binary https://deb.debian.org/debian --binary-images iso-hybrid \
 --debian-installer none --archive-areas main --security false --linux-packages none
cp -a "$ROOT/config/." config/
# Hosted Ubuntu live-build's legacy kernel lookup points at obsolete
# /dists/bookworm/Contents-amd64.gz (404). The official Debian kernel
# metapackage is installed directly, so auto Contents detection is unnecessary.
printf '%s\n' 'linux-image-amd64' >> config/package-lists/static.list.chroot
# Explicit Bookworm security pocket: live-build's distro-agnostic old default
# otherwise points at obsolete bookworm/updates under security.debian.org.
mkdir -p config/archives
printf '%s\n' 'deb https://security.debian.org/debian-security bookworm-security main' \
 > config/archives/official-bookworm-security.list.chroot
# Preserve original HOUSE source ownership and exact commit: GENESIS is the
# human-facing starting door, and Workbench stays available as a separate organ.
HOUSE_URL="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["house"]["url"])' "$ROOT/manifest/genesis-001.json")"
HOUSE_SHA="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["house"]["commit"])' "$ROOT/manifest/genesis-001.json")"
git init -q house-fetch
git -C house-fetch remote add origin "$HOUSE_URL"
git -C house-fetch -c protocol.version=2 fetch -q --depth=1 origin "$HOUSE_SHA"
test "$(git -C house-fetch rev-parse FETCH_HEAD)" = "$HOUSE_SHA"
mkdir -p config/includes.chroot/opt/static-os/workbench-src \
 config/includes.chroot/usr/share/static-os
git -C house-fetch archive "$HOUSE_SHA" | tar -xf - -C config/includes.chroot/opt/static-os/workbench-src
install -m 0644 "$ROOT/manifest/genesis-001.json" config/includes.chroot/usr/share/static-os/genesis-001.json
printf '%s\n' "$HOUSE_SHA" > config/includes.chroot/usr/share/static-os/house-source-commit
rm -rf house-fetch
# Unlike a static README demo, ship all original Git source objects used by
# CANNON's runtime. Signatures/authorship are still not established by pins.
bash "$ROOT/scripts/stage-genesis-boot.sh"
# Offer a CI-only VM smoke probe when explicitly requested; do not include
# probe code or root service in the normal distribution image.
if [[ "${STATIC_OS_CI_VM_PROBE:-0}" == 1 ]]; then
 mkdir -p config/includes.chroot/usr/local/sbin \
   config/includes.chroot/etc/systemd/system/multi-user.target.wants \
   config/includes.chroot/etc/systemd/system
 install -m 0755 "$ROOT/tests/vm-genesis-probe.sh" \
   config/includes.chroot/usr/local/sbin/vm-genesis-probe
 install -m 0755 "$ROOT/tests/vm-genesis-probe.py" \
   config/includes.chroot/usr/local/sbin/vm-genesis-probe.py
 install -m 0644 "$ROOT/tests/vm-genesis-probe.service" \
   config/includes.chroot/etc/systemd/system/vm-genesis-probe.service
 ln -s ../vm-genesis-probe.service \
   config/includes.chroot/etc/systemd/system/multi-user.target.wants/vm-genesis-probe.service
fi
lb build
mapfile -t imgs < <(find . -maxdepth 1 -type f -name '*.iso' -print)
[[ ${#imgs[@]} -eq 1 ]] || { echo "REFUSE: expected one ISO, found ${#imgs[@]}" >&2; exit 2; }
sha256sum "${imgs[0]}" > image.sha256
# Boot evidence comes from independent VM execution, not the existence of an ISO.
python3 - "${imgs[0]}" <<'PY'
import json,os,sys,hashlib
from pathlib import Path
p=Path(sys.argv[1])
root=Path.cwd()
h=hashlib.sha256()
with p.open('rb') as reader:
    for chunk in iter(lambda:reader.read(1024*1024), b''):
        h.update(chunk)
result={"schema":"static-os.genesis-boot-image-occurrence/v0",
        "status":"IMAGE_BUILT_NOT_BOOT_CONFIRMED",
        "iso_file":p.name,"iso_size_bytes":p.stat().st_size,
        "iso_sha256":h.hexdigest(),
        "installed":False,"human_field_test":False,
        "iso_boot_observed":False,"source_selection":"EXACT_GIT_OPEN_BRANCHES_NOT_CANON"}
(root/"image-build-receipt.json").write_text(json.dumps(result,indent=2)+"\n")
PY
printf 'ISO BUILD CANDIDATE: %s\n' "$BUILD_DIR/${imgs[0]#./}"
printf 'Evidence file: %s/image-build-receipt.json\n' "$BUILD_DIR"
printf 'Next gates: BIOS/UEFI QEMU boot, offline launch, graphical XFCE and real hardware.\n'
