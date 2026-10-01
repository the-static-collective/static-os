#!/usr/bin/env bash
# ROADKIT-001 user-space donor bootstrap.
# Fetches exact pinned reLATTE + TranchNode revisions into user-owned storage.
# Does not edit system packages, mount disks, open firewall ports, or overwrite
# an existing checkout with a different origin/revision.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$ROOT/manifest/roadkit-001.json"
MODE="${1:---check}"
HOME_ROOT="${ROADKIT_HOME:-$HOME/.local/share/static-roadkit-001}"
SRC_ROOT="$HOME_ROOT/sources"

case "$MODE" in
  --check|--install|--help) ;;
  *) echo "REFUSE: use --check, --install, or --help" >&2; exit 2 ;;
esac

if [[ "$MODE" = "--help" ]]; then
  cat <<'EOF'
usage: bash scripts/roadkit-setup.sh [--check|--install]

--check    inspect prerequisites and exact donor state; no mutation
--install  fetch exact pinned donor commits and install their local npm deps

The runtime lives under $ROADKIT_HOME or, by default,
~/.local/share/static-roadkit-001

Nothing is installed system-wide.
EOF
  exit 0
fi

if [[ "$(id -u)" -eq 0 ]]; then
  echo "REFUSE: ROADKIT bootstrap is user-scoped; do not run as root." >&2
  exit 2
fi

for tool in git node npm python3; do
  command -v "$tool" >/dev/null || {
    echo "MISSING: $tool" >&2
    exit 2
  }
done

node -e 'const m=Number(process.versions.node.split(".")[0]); process.exit(m>=20 ? 0 : 1)' || {
  echo "BLOCKED: ROADKIT requires Node.js 20 or newer." >&2
  exit 2
}

readarray -t PINS < <(python3 - "$MANIFEST" <<'PY'
import json,sys
d=json.load(open(sys.argv[1],encoding="utf-8"))
print(d["organs"]["relatte"]["commit"])
print(d["organs"]["tranchnode"]["commit"])
PY
)
RELATTE_SHA="${PINS[0]}"
TRANCH_SHA="${PINS[1]}"

check_checkout() {
  local name="$1" path="$2" url="$3" sha="$4"
  if [[ ! -e "$path" ]]; then
    echo "$name: absent"
    return 1
  fi
  [[ ! -L "$path" && -d "$path/.git" ]] || {
    echo "REFUSE: $path is not an ordinary Git checkout" >&2
    exit 2
  }
  local origin head
  origin="$(git -C "$path" remote get-url origin)"
  head="$(git -C "$path" rev-parse HEAD)"
  [[ "$origin" = "$url" ]] || {
    echo "REFUSE: $name origin mismatch at $path" >&2
    exit 2
  }
  [[ "$head" = "$sha" ]] || {
    echo "REFUSE: $name is at $head, expected $sha; no reset performed." >&2
    exit 2
  }
  echo "$name: exact $sha"
  return 0
}

RELATTE="$SRC_ROOT/relatte"
TRANCH="$SRC_ROOT/tranchnode"
RELATTE_URL="https://github.com/the-static-collective/reLATTE.git"
TRANCH_URL="https://github.com/the-static-collective/tranchnode.git"

if [[ "$MODE" = "--check" ]]; then
  ok=0
  check_checkout reLATTE "$RELATTE" "$RELATTE_URL" "$RELATTE_SHA" || ok=1
  check_checkout TranchNode "$TRANCH" "$TRANCH_URL" "$TRANCH_SHA" || ok=1
  [[ -x "$TRANCH/node_modules/.bin/tsx" ]] && echo "tsx runtime: ready" || { echo "tsx runtime: absent"; ok=1; }
  echo "System install / USB mount / LAN reachability: NOT CHECKED"
  exit "$ok"
fi

mkdir -p "$SRC_ROOT"

install_checkout() {
  local name="$1" path="$2" url="$3" sha="$4"
  if check_checkout "$name" "$path" "$url" "$sha"; then
    return
  fi
  git clone --no-checkout "$url" "$path"
  git -C "$path" fetch --depth=1 origin "$sha"
  [[ "$(git -C "$path" rev-parse FETCH_HEAD)" = "$sha" ]] || {
    echo "REFUSE: downloaded $name revision mismatch" >&2
    exit 2
  }
  git -C "$path" checkout --detach "$sha"
}

install_checkout reLATTE "$RELATTE" "$RELATTE_URL" "$RELATTE_SHA"
install_checkout TranchNode "$TRANCH" "$TRANCH_URL" "$TRANCH_SHA"

npm install --prefix "$RELATTE" --package-lock=false --no-audit --no-fund
npm ci --prefix "$TRANCH"

cat > "$HOME_ROOT/runtime.env" <<EOF
ROADKIT_RELATTE_ROOT=$RELATTE
ROADKIT_TRANCHNODE_ROOT=$TRANCH
EOF

echo "ROADKIT-001 runtime ready."
echo "Use: bash $ROOT/scripts/roadkit.sh --help"
