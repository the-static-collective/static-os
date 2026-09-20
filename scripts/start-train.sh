#!/usr/bin/env bash
# LAUNCHPAD-001: explicitly invoked, user-scoped local HOUSE setup and launch.
# Never formats disks, starts VM/ISO builds, installs OS packages or edits an
# existing Workbench config. This is not an untrusted-code sandbox.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODE="--start"
if [[ "$#" -gt 0 ]]; then MODE="$1"; fi
case "$MODE" in
  --help)
    printf '%s\n' "usage: ./scripts/start-train.sh [--start|--check|--help]" \
      "--start: explicitly install a pinned local HOUSE checkout and launch it." \
      "--check: report local user-scope prerequisites only; no mutations." \
      "Run on your ordinary Zorin/Linux account, NOT as root or inside a live ISO."
    exit 0 ;;
  --start|--check) ;;
  *) echo "REFUSE: unknown launch mode" >&2; exit 2 ;;
esac
if [[ "$(id -u)" -eq 0 ]]; then
  echo "REFUSE: local bootstrap must not run as root" >&2
  exit 2
fi
for tool in git python3; do
  command -v "$tool" >/dev/null || { echo "MISSING: $tool; install using your distro package manager first." >&2; exit 2; }
done
MANIFEST="$ROOT/manifest/genesis-001.json"
python3 "$ROOT/scripts/validate-manifest.py" "$MANIFEST"
HOUSE_SHA="$(python3 - "$MANIFEST" <<'PY'
import json, sys
value=json.load(open(sys.argv[1],encoding="utf-8"))
if value["house"]["owner"] != "the-static-collective/static-workbench":
    raise SystemExit("REFUSE: unexpected source owner")
if value["house"]["url"] != "https://github.com/the-static-collective/static-workbench.git":
    raise SystemExit("REFUSE: unexpected source URL")
if value["elf"]["source_commit"] != value["house"]["commit"]:
    raise SystemExit("REFUSE: HOUSE/ELF source drift")
print(value["house"]["commit"])
PY
)"
WORKTREE="$HOME/static/static-workbench-flight1"
VENV="$WORKTREE/.venv"
CONFIG="$HOME/.config/static-workbench/config.toml"
if [[ -e "$WORKTREE" || -L "$WORKTREE" ]]; then
  [[ ! -L "$WORKTREE" && -d "$WORKTREE/.git" ]] || {
    echo "REFUSE: expected an ordinary existing checkout; inspect $WORKTREE manually" >&2; exit 2;
  }
  observed="$(git -C "$WORKTREE" rev-parse HEAD)"
  origin="$(git -C "$WORKTREE" remote get-url origin)"
  [[ "$observed" = "$HOUSE_SHA" && "$origin" = "https://github.com/the-static-collective/static-workbench.git" ]] || {
    echo "REFUSE: existing checkout is a different revision/origin; no overwrite or reset" >&2; exit 2;
  }
else
  if [[ "$MODE" = "--check" ]]; then
    echo "HOUSE source checkout: absent (would create $WORKTREE)"
  else
    [[ ! -L "$HOME/static" ]] || { echo "REFUSE: ~/static must not be symlinked" >&2; exit 2; }
    mkdir -p "$HOME/static"
    git clone --no-checkout https://github.com/the-static-collective/static-workbench.git "$WORKTREE"
    git -C "$WORKTREE" fetch --depth=1 origin "$HOUSE_SHA"
    [[ "$(git -C "$WORKTREE" rev-parse FETCH_HEAD)" = "$HOUSE_SHA" ]] || {
      echo "REFUSE: downloaded revision mismatch" >&2; exit 2;
    }
    git -C "$WORKTREE" checkout --detach "$HOUSE_SHA"
  fi
fi
echo "HOUSE source: $HOUSE_SHA"
if [[ "$MODE" = "--check" ]]; then
  [[ -f "$CONFIG" ]] && echo "Config: existing (left unchanged)" || echo "Config: absent (would create)"
  [[ -x "$VENV/bin/python" ]] && echo "Environment: present" || echo "Environment: absent (would create)"
  echo "VM build, boot, guest offline operation, cross-boot state: NOT CHECKED"
  exit 0
fi
# The operator deliberately invokes --start; dependencies are installed and
# source executed as the current Linux user, not as root or in a sandbox.
if [[ ! -x "$VENV/bin/python" ]]; then python3 -m venv "$VENV"; fi
"$VENV/bin/python" -m pip install --no-input -e "$WORKTREE"
if [[ ! -e "$CONFIG" && ! -L "$CONFIG" ]]; then
  mkdir -p "$(dirname "$CONFIG")"
  cp "$WORKTREE/config.example.toml" "$CONFIG"
fi
if [[ -L "$CONFIG" || ! -f "$CONFIG" ]]; then
  echo "REFUSE: existing configuration is not a regular file" >&2
  exit 2
fi
STATIC_WORKBENCH_CONFIG="$CONFIG" "$VENV/bin/python" - <<'PY'
from static_workbench.config import load_config
import os
from pathlib import Path
config = load_config(Path(os.environ["STATIC_WORKBENCH_CONFIG"]))
assert config.bind_host in ("localhost","127.0.0.1","::1")
print("HOUSE URL: http://127.0.0.1:%d/" % config.port)
print("Existing user state is not cleared.")
PY
echo "Starting HOUSE in this terminal; Ctrl+C stops it. Open the URL above."
exec env STATIC_WORKBENCH_CONFIG="$CONFIG" "$VENV/bin/static-workbench"
