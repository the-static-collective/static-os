#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOME_ROOT="${ROADKIT_HOME:-$HOME/.local/share/static-roadkit-001}"
ENV_FILE="$HOME_ROOT/runtime.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ROADKIT runtime is not installed. Run: bash $ROOT/scripts/roadkit-setup.sh --install" >&2
  exit 2
fi

# shellcheck disable=SC1090
source "$ENV_FILE"
export ROADKIT_RELATTE_ROOT ROADKIT_TRANCHNODE_ROOT

[[ -d "$ROADKIT_RELATTE_ROOT/.git" ]] || { echo "REFUSE: reLATTE runtime missing" >&2; exit 2; }
[[ -x "$ROADKIT_TRANCHNODE_ROOT/node_modules/.bin/tsx" ]] || { echo "REFUSE: TranchNode tsx runtime missing" >&2; exit 2; }

exec "$ROADKIT_TRANCHNODE_ROOT/node_modules/.bin/tsx" "$ROOT/interop/roadkit-001.ts" "$@"
