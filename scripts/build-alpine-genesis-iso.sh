#!/bin/sh
# Executed inside alpine:3.23 build container; not on the user's daily OS.
# Native Alpine aports/mkimage, NOT Debian live-build or Ubuntu remaster.
set -eu
test "$(id -u)" = 0 || { echo "REFUSE: disposable container root only" >&2; exit 2; }
test -d /work/config/alpine-live && test -d /payload/cannon || exit 2
test ! -e /work/alpine-images || { echo "REFUSE: output already exists" >&2; exit 2; }
apk add --no-cache abuild alpine-conf alpine-sdk git fakeroot syslinux \
 xorriso squashfs-tools grub mtools dosfstools bash curl python3 \
 nodejs npm ca-certificates
node --version
case "$(node --version)" in v24.*) : ;; *) echo 'REFUSE: Alpine must run Node24' >&2; exit 2;; esac
# Aports official release branch is a build tool dependency, not operator canon.
git clone --depth=1 --branch 3.23-stable \
 https://gitlab.alpinelinux.org/alpine/aports.git /tmp/aports
cp /work/config/alpine-live/mkimg.genesis.sh /tmp/aports/scripts/
cp /work/config/alpine-live/genapkovl-genesis.sh /tmp/aports/scripts/
chmod +x /tmp/aports/scripts/genapkovl-genesis.sh
mkdir -p /work/alpine-images
# Sign the on-image local APKINDEX using an ephemeral build-only abuild key,
# not a user's personal or future steward signing identity.
export PACKAGER='STATIC OS CI Alpine Builder <ci@localhost.invalid>'
abuild-keygen -a -i -n
cd /tmp/aports
export GENESIS_PAYLOAD=/payload
# CI-only test images include a probe. The normal invocation leaves it absent.
export GENESIS_CI_VM_PROBE="${GENESIS_CI_VM_PROBE:-0}"
sh scripts/mkimage.sh --arch x86_64 --profile genesis --tag 005 \
 --outdir /work/alpine-images \
 --repository https://dl-cdn.alpinelinux.org/alpine/v3.23/main \
 --repository https://dl-cdn.alpinelinux.org/alpine/v3.23/community
set -- /work/alpine-images/*.iso
test "$#" = 1 && test -s "$1" || { echo "NO_SINGLE_ALPINE_ISO" >&2; exit 2; }
sha256sum "$1" > /work/alpine-images/iso.sha256
printf '%s\n' 'ALPINE_NATIVE_ISO_CREATED_NOT_BOOT_WITNESSED'
