#!/usr/bin/env sh
set -euo pipefail

# start.sh - runs the built SvelteKit app using Bun
# Behavior:
#  - Detects `bun` binary (respecting $BUN_INSTALL)
#  - Uses $START_ENTRYPOINT if provided, otherwise searches common build paths
#  - Logs which entrypoint it picks for easier debugging

detect_bun() {
  if [ -n "${BUN_INSTALL:-}" ] && [ -x "${BUN_INSTALL}/bin/bun" ]; then
    echo "${BUN_INSTALL}/bin/bun"
  elif [ -x "/usr/local/bin/bun" ]; then
    echo "/usr/local/bin/bun"
  elif command -v bun >/dev/null 2>&1; then
    command -v bun
  else
    return 1
  fi
}

BUN_BIN=$(detect_bun) || {
  echo "bun not found. Please install Bun or set BUN_INSTALL to its install dir." >&2
  exit 1
}

cd /app || true

# If a base64-encoded favicon is provided, ensure a decoded PNG exists
if [ -f static/favicon.png.b64 ] && [ ! -f static/favicon.png ]; then
  echo "Decoding static/favicon.png from base64..."
  base64 -d static/favicon.png.b64 > static/favicon.png || base64 -D static/favicon.png.b64 > static/favicon.png || true
fi

# Allow overriding the entrypoint via environment variable
if [ -n "${START_ENTRYPOINT:-}" ]; then
  ENTRYPOINT="$START_ENTRYPOINT"
else
  if [ -f build/index.js ]; then
    ENTRYPOINT="build/index.js"
  elif [ -f build/server/index.js ]; then
    ENTRYPOINT="build/server/index.js"
  elif [ -f build/index.mjs ]; then
    ENTRYPOINT="build/index.mjs"
  elif [ -f build/server/index.mjs ]; then
    ENTRYPOINT="build/server/index.mjs"
  else
    echo "Cannot find server entrypoint in build/" >&2
    exit 1
  fi
fi

echo "Starting frontend with Bun: $BUN_BIN $ENTRYPOINT"
exec "$BUN_BIN" "$ENTRYPOINT" "$@"
