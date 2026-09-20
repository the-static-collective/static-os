#!/usr/bin/env bash
# Build on Ubuntu 22.04 amd64 for glibc compatibility with Zorin 17+.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[[ "$(uname -m)" = x86_64 ]] || { echo 'amd64 builder required' >&2; exit 2; }
BUILD="$(mktemp -d)"
trap 'rm -rf "$BUILD"' EXIT
SHA="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["house"]["commit"])' "$ROOT/manifest/genesis-001.json")"
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || exit 2
python3 "$ROOT/scripts/validate-manifest.py" "$ROOT/manifest/genesis-001.json"
git clone --no-checkout https://github.com/the-static-collective/static-workbench.git "$BUILD/source"
git -C "$BUILD/source" checkout --detach "$SHA"
[[ "$(git -C "$BUILD/source" rev-parse HEAD)" = "$SHA" ]] || exit 2
python3 -m venv "$BUILD/venv"
"$BUILD/venv/bin/python" -m pip install 'pip>=23.1,<26' 'pyinstaller==6.16.0' "$BUILD/source"
"$BUILD/venv/bin/python" -m pip freeze > "$BUILD/dependencies.txt"
"$BUILD/venv/bin/pyinstaller" --noconfirm --onedir --name static-workbench-desktop \
  --collect-all static_workbench --collect-all uvicorn \
  --distpath "$BUILD/dist" --workpath "$BUILD/work" --specpath "$BUILD" \
  "$ROOT/packaging/desktop/launch.py"
GLIBC="$(getconf GNU_LIBC_VERSION | cut -d ' ' -f 2)"
PKG="$BUILD/package"
mkdir -p "$PKG/opt/static-workbench" "$PKG/usr/share/applications" "$PKG/usr/share/icons/hicolor/scalable/apps" "$PKG/DEBIAN"
cp -a "$BUILD/dist/static-workbench-desktop/." "$PKG/opt/static-workbench/"
cp "$BUILD/dependencies.txt" "$PKG/opt/static-workbench/"
printf '%s\n' "$SHA" > "$PKG/opt/static-workbench/source-commit.txt"
cp "$ROOT/packaging/desktop/static-workbench.desktop" "$PKG/usr/share/applications/"
cp "$ROOT/packaging/desktop/static-workbench.svg" "$PKG/usr/share/icons/hicolor/scalable/apps/"
cat > "$PKG/DEBIAN/control" <<EOF
Package: static-workbench-desktop
Version: 0.1.0~preview.${SHA:0:8}
Section: utils
Priority: optional
Architecture: amd64
Maintainer: The Static Collective <maintainers@thestaticcollective.invalid>
Depends: libc6 (>= $GLIBC), libstdc++6, zlib1g, libgcc-s1, zenity, xdg-utils, git
Description: Local Static Collective Workbench desktop preview
 Bundled Python runtime and pinned Workbench source. Opens in your browser.
EOF
# Construct app using the actual frozen executable before packaging.
mkdir -p "$BUILD/test-home"
HOME="$BUILD/test-home" "$PKG/opt/static-workbench/static-workbench-desktop" --self-test
mkdir -p "$ROOT/dist"
dpkg-deb --root-owner-group --build "$PKG" "$ROOT/dist/static-workbench-desktop_amd64.deb"
(cd "$ROOT/dist" && sha256sum static-workbench-desktop_amd64.deb > SHA256SUMS)
