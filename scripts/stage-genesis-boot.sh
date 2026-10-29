#!/usr/bin/env bash
# Called solely inside an isolated live-build staging directory by root.
# GitHub commits are *sources* to run: neither merge status nor main selects canon.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$ROOT/manifest/genesis-boot-003.json"
python3 "$ROOT/scripts/validate-boot-image.py" "$MANIFEST"
[[ ${EUID} -eq 0 ]] || { echo "REFUSE: isolated build root required" >&2; exit 2; }
[[ -d config/includes.chroot ]] || { echo "REFUSE: run from a live-build directory" >&2; exit 2; }
for bin in git python3 curl sha256sum tar; do
  command -v "$bin" >/dev/null || { echo "MISSING BUILD TOOL: $bin" >&2; exit 2; }
done

CHROOT="$PWD/config/includes.chroot"
BASE="$CHROOT/opt/static-os"
REPOS="$BASE/genesis-sources"
[[ ! -e "$REPOS" ]] || { echo "REFUSE: source staging already exists" >&2; exit 2; }
mkdir -p "$REPOS" "$BASE/node24" "$CHROOT/usr/share/static-os"

NODE_VERSION=v24.10.0
NODE_FILE=node-v24.10.0-linux-x64.tar.xz
NODE_SHA=2642f4428869aca32443660fd71b3918e2be1277a899bdcaeb64c93b54b5af17
curl --proto '=https' --tlsv1.2 --fail --location --retry 3 --silent --show-error \
 "https://nodejs.org/dist/$NODE_VERSION/$NODE_FILE" -o "$NODE_FILE"
printf '%s  %s\n' "$NODE_SHA" "$NODE_FILE" | sha256sum -c -
tar -xJf "$NODE_FILE" -C "$BASE/node24" --strip-components=1
rm -f "$NODE_FILE"
NODE="$BASE/node24/bin/node"
NPM="$BASE/node24/bin/npm"
test "$("$NODE" --version)" = "$NODE_VERSION" || { echo "REFUSE: runtime version mismatch" >&2; exit 2; }

# The source matrix is an explicit list; no name/branch/default history discovery.
python3 - "$MANIFEST" > .genesis-source-list.tsv <<'PY'
import json,sys
v=json.load(open(sys.argv[1]))
for x in v['sources']:
    print(x['id'],x['url'],x['commit'],sep='\t')
PY
SAFE="$CHROOT/usr/share/static-os/genesis-gitconfig"
printf '[safe]\n' > "$SAFE"
while IFS=$'\t' read -r id url sha; do
  [[ "$id" =~ ^[a-z0-9-]+$ && "$sha" =~ ^[a-f0-9]{40}$ ]] || exit 2
  dest="$REPOS/$id"
  git init -q "$dest"
  git -C "$dest" remote add origin "$url"
  git -C "$dest" -c protocol.version=2 fetch -q --depth=1 origin "$sha"
  test "$(git -C "$dest" rev-parse FETCH_HEAD)" = "$sha" || exit 2
  git -C "$dest" -c advice.detachedHead=false checkout -q --detach "$sha"
  test "$(git -C "$dest" rev-parse HEAD)" = "$sha" || exit 2
  printf '    directory = /opt/static-os/genesis-sources/%s\n' "$id" >> "$SAFE"
  printf 'PINNED ORIGINAL SOURCE: %s %s\n' "$id" "$sha"
done < .genesis-source-list.tsv
rm -f .genesis-source-list.tsv

# Dependencies downloaded during ISO build, never at operating-system first boot.
# node_modules are untracked package bytes; the lockfile and npm outputs are
# included in the image's inventory. No lifecycle installation scripts run.
PATH="$BASE/node24/bin:$PATH" "$NPM" ci --prefix "$REPOS/garden" \
 --ignore-scripts --no-audit --no-fund --loglevel=error
test -f "$REPOS/garden/node_modules/tsx/dist/cli.mjs" || exit 2

# Set immutable code source and reviewed node runtime; user HOME remains private.
install -m 0644 "$MANIFEST" "$CHROOT/usr/share/static-os/genesis-boot-003.json"
cp "$ROOT/config/genesis-boot/static-genesis.service" \
 "$CHROOT/etc/systemd/user/static-genesis.service"
mkdir -p "$CHROOT/etc/xdg/autostart" "$CHROOT/usr/local/bin"
install -m 0644 "$ROOT/config/genesis-boot/static-genesis.desktop" \
 "$CHROOT/etc/xdg/autostart/static-genesis.desktop"
install -m 0755 "$ROOT/config/genesis-boot/static-genesis-start" \
 "$CHROOT/usr/local/bin/static-genesis-start"
install -m 0755 "$ROOT/config/genesis-boot/static-genesis-launch" \
 "$CHROOT/usr/local/bin/static-genesis-launch"
# Keep HOUSE, but don't open two browsers competing for first attention.
printf '%s\n' '[Desktop Entry]' 'Type=Application' 'Name=STATIC OS HOUSE (manual)' \
 'Hidden=true' > "$CHROOT/etc/xdg/autostart/static-house.desktop"
# Actual selected local service is not automatically active until XFCE login;
# the desktop autostart is exclusively a local browser/one-user service launch.
# Nothing automatically invokes the BUILD or WARM actions.
printf 'STAGED: 11 exact Git source histories, Node %s, local-first boot only\n' "$NODE_VERSION"
