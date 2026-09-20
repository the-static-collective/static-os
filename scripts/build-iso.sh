#!/usr/bin/env bash
# Execute only in a disposable Debian bookworm build VM/container with live-build.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$ROOT/manifest/genesis-001.json"
python3 "$ROOT/scripts/validate-manifest.py" "$MANIFEST"
if [[ "${EUID}" -ne 0 ]]; then
  echo "REFUSE: live-build needs root; run in a dedicated build VM, not the Zorin host." >&2
  exit 2
fi
for command in lb git python3 tar sha256sum; do
  command -v "$command" >/dev/null || { echo "Missing build prerequisite: $command" >&2; exit 2; }
done
BUILD_DIR="${STATIC_OS_BUILD_DIR:-$ROOT/.build/genesis-001}"
[[ ! -e "$BUILD_DIR" ]] || { echo "REFUSE: build directory already exists: $BUILD_DIR" >&2; exit 2; }
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"
lb config --distribution bookworm --architectures amd64 --binary-images iso-hybrid \
  --debian-installer none --archive-areas main
cp -a "$ROOT/config/." "$BUILD_DIR/config/"
HOUSE_URL="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["house"]["url"])' "$MANIFEST")"
HOUSE_SHA="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["house"]["commit"])' "$MANIFEST")"
# A named mutable branch is never a sufficient source reference for this occurrence.
git init -q house-fetch
git -C house-fetch remote add origin "$HOUSE_URL"
git -C house-fetch -c protocol.version=2 fetch --depth=1 origin "$HOUSE_SHA"
test "$(git -C house-fetch rev-parse FETCH_HEAD)" = "$HOUSE_SHA" || {
  echo "REFUSE: HOUSE source SHA mismatch" >&2; exit 2;
}
mkdir -p config/includes.chroot/opt/static-os/workbench-src \
  config/includes.chroot/usr/share/static-os
git -C house-fetch archive "$HOUSE_SHA" | tar -xf - -C config/includes.chroot/opt/static-os/workbench-src
install -m 0644 "$MANIFEST" config/includes.chroot/usr/share/static-os/genesis-001.json
printf '%s\n' "$HOUSE_SHA" > config/includes.chroot/usr/share/static-os/house-source-commit
# Removes the fetch checkout from the distribution build tree before the ISO stage.
rm -rf house-fetch
lb build
mapfile -t images < <(find . -maxdepth 1 -type f -name '*.iso' -print)
[[ "${#images[@]}" -eq 1 ]] || { echo "REFUSE: expected one ISO, got ${#images[@]}" >&2; exit 2; }
sha256sum "${images[0]}" > image.sha256
printf 'BUILD CANDIDATE: %s\nSHA-256: %s\n' "$BUILD_DIR/${images[0]#./}" "$(cat image.sha256)"
printf 'Next gates: VM boot, offline HOUSE launch, shutdown/reboot, hardware boot. None is implied by build success.\n'
