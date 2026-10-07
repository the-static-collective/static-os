#!/usr/bin/env bash
# Execute only in a disposable Debian bookworm build VM/container with live-build.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$ROOT/manifest/genesis-001.json"
WHOLE_BODY_MANIFEST="$ROOT/manifest/whole-body-001.json"
PERSISTENT_ROOT_MANIFEST="$ROOT/manifest/persistent-root-001.json"
BARDO_GENERALITY_MANIFEST="$ROOT/manifest/bardo-generality-002.json"

python3 "$ROOT/scripts/validate-manifest.py" "$MANIFEST"
python3 "$ROOT/scripts/validate-whole-body.py" "$WHOLE_BODY_MANIFEST"
python3 "$ROOT/scripts/validate-persistent-root.py" "$PERSISTENT_ROOT_MANIFEST"
python3 "$ROOT/scripts/validate-bardo-generality.py" "$BARDO_GENERALITY_MANIFEST"

if [[ "${EUID}" -ne 0 ]]; then
  echo "REFUSE: live-build needs root; run in a dedicated build VM, not the Zorin host." >&2
  exit 2
fi

for command in lb git python3 tar sha256sum; do
  command -v "$command" >/dev/null || {
    echo "Missing build prerequisite: $command" >&2
    exit 2
  }
done

BUILD_DIR="${STATIC_OS_BUILD_DIR:-$ROOT/.build/genesis-001}"
[[ ! -e "$BUILD_DIR" ]] || {
  echo "REFUSE: build directory already exists: $BUILD_DIR" >&2
  exit 2
}
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
  echo "REFUSE: HOUSE source SHA mismatch" >&2
  exit 2
}

mkdir -p config/includes.chroot/opt/static-os/workbench-src \
  config/includes.chroot/usr/share/static-os
git -C house-fetch archive "$HOUSE_SHA" | \
  tar -xf - -C config/includes.chroot/opt/static-os/workbench-src
install -m 0644 "$MANIFEST" config/includes.chroot/usr/share/static-os/genesis-001.json
printf '%s\n' "$HOUSE_SHA" > config/includes.chroot/usr/share/static-os/house-source-commit

# WHOLE-BODY-001 carries exact inspected source cuts without auto-starting them.
mkdir -p config/includes.chroot/opt/static-os/organs \
  config/includes.chroot/usr/share/static-os/organs
install -m 0644 "$WHOLE_BODY_MANIFEST" \
  config/includes.chroot/usr/share/static-os/whole-body-001.json
install -m 0644 "$PERSISTENT_ROOT_MANIFEST" \
  config/includes.chroot/usr/share/static-os/persistent-root-001.json
install -m 0644 "$BARDO_GENERALITY_MANIFEST" \
  config/includes.chroot/usr/share/static-os/bardo-generality-002.json

python3 - "$WHOLE_BODY_MANIFEST" <<'PY' > whole-body-sources.tsv
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
for organ in data["organs"]:
    if organ.get("image_source") is True:
        print("\t".join((organ["id"], organ["repository"], organ["commit"])))
PY

while IFS=$'\t' read -r ORGAN_ID ORGAN_REPO ORGAN_SHA; do
  FETCH_DIR="organ-fetch-$ORGAN_ID"
  ORGAN_URL="https://github.com/$ORGAN_REPO.git"

  git init -q "$FETCH_DIR"
  git -C "$FETCH_DIR" remote add origin "$ORGAN_URL"
  git -C "$FETCH_DIR" -c protocol.version=2 fetch --depth=1 origin "$ORGAN_SHA"
  test "$(git -C "$FETCH_DIR" rev-parse FETCH_HEAD)" = "$ORGAN_SHA" || {
    echo "REFUSE: $ORGAN_ID source SHA mismatch" >&2
    exit 2
  }

  mkdir -p "config/includes.chroot/opt/static-os/organs/$ORGAN_ID"
  git -C "$FETCH_DIR" archive "$ORGAN_SHA" | \
    tar -xf - -C "config/includes.chroot/opt/static-os/organs/$ORGAN_ID"
  printf '%s\n' "$ORGAN_SHA" > \
    "config/includes.chroot/usr/share/static-os/organs/$ORGAN_ID.commit"
  rm -rf "$FETCH_DIR"
done < whole-body-sources.tsv

rm -f whole-body-sources.tsv
rm -rf house-fetch

# BARDO-GENERALITY-002 carries the exact second-family proof separately from
# the WHOLE-BODY reLATTE pin so historical SB-001 identity is not rewritten.
SB002_REPO="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["specimens"]["sb002"]["proof_repository"])' "$BARDO_GENERALITY_MANIFEST")"
SB002_SHA="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["specimens"]["sb002"]["proof_commit"])' "$BARDO_GENERALITY_MANIFEST")"
SB002_URL="https://github.com/$SB002_REPO.git"
git init -q sb002-proof-fetch
git -C sb002-proof-fetch remote add origin "$SB002_URL"
git -C sb002-proof-fetch -c protocol.version=2 fetch --depth=1 origin "$SB002_SHA"
test "$(git -C sb002-proof-fetch rev-parse FETCH_HEAD)" = "$SB002_SHA" || {
  echo "REFUSE: SB-002 proof SHA mismatch" >&2
  exit 2
}
mkdir -p config/includes.chroot/opt/static-os/bardo-proofs/sb002-relatte \
  config/includes.chroot/usr/share/static-os/bardo-proofs
git -C sb002-proof-fetch archive "$SB002_SHA" | \
  tar -xf - -C config/includes.chroot/opt/static-os/bardo-proofs/sb002-relatte
printf '%s\n' "$SB002_SHA" > \
  config/includes.chroot/usr/share/static-os/bardo-proofs/sb002-relatte.commit
rm -rf sb002-proof-fetch

lb build

mapfile -t images < <(find . -maxdepth 1 -type f -name '*.iso' -print)
[[ "${#images[@]}" -eq 1 ]] || {
  echo "REFUSE: expected one ISO, got ${#images[@]}" >&2
  exit 2
}
sha256sum "${images[0]}" > image.sha256
printf 'BUILD CANDIDATE: %s\nSHA-256: %s\n' \
  "$BUILD_DIR/${images[0]#./}" "$(cat image.sha256)"
printf '%s\n'   'Next gates: VM boot, offline HOUSE launch, shutdown/reboot, hardware boot. None is implied by build success.'
