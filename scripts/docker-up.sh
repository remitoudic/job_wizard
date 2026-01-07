#!/usr/bin/env bash
set -euo pipefail

# Wrapper to auto-detect whether we are on the remote machine
# and export docker-compose environment variables accordingly,
# then run docker compose up.

REMOTE_IP=${REMOTE_IP:-147.93.111.113}

detect_public_ip() {
  # try common external IP services, fall back to hostname -I
  for url in https://ifconfig.me https://ipinfo.io/ip https://icanhazip.com; do
    if PUBLIC_IP=$(curl -s --max-time 5 "$url" 2>/dev/null); then
      PUBLIC_IP=$(echo "$PUBLIC_IP" | tr -d '\n' | tr -d '\r')
      if [ -n "$PUBLIC_IP" ]; then
        echo "$PUBLIC_IP"
        return 0
      fi
    fi
  done
  # fallback: local interface
  ip=$(hostname -I 2>/dev/null | awk '{print $1}') || true
  echo "${ip:-}" 
}

PUBLIC_IP=$(detect_public_ip)

if [ -z "$PUBLIC_IP" ]; then
  echo "Could not detect public IP; defaulting to localhost behavior"
  PUBLIC_IP="localhost"
fi

if [ "$PUBLIC_IP" = "$REMOTE_IP" ]; then
  echo "Detected remote host (${PUBLIC_IP}). Exporting remote URLs."
  export VITE_API_URL="http://${PUBLIC_IP}:8000"
  export CORS_ORIGINS="http://localhost:3000,http://localhost:5173,http://${PUBLIC_IP}:5173,http://${PUBLIC_IP}:3000"
else
  echo "Detected local host (${PUBLIC_IP}). Exporting localhost URLs."
  export VITE_API_URL="http://localhost:8000"
  export CORS_ORIGINS="http://localhost:3000,http://localhost:5173"
fi

# If a .env file exists, load it but do not override variables we've just exported
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

echo "Using VITE_API_URL=$VITE_API_URL"
echo "Using CORS_ORIGINS=$CORS_ORIGINS"

# Use docker-compose if available, else docker compose
if command -v docker-compose >/dev/null 2>&1; then
  docker-compose up -d --build
else
  docker compose up -d --build
fi

echo "Containers started. Access frontend on http://localhost:5173 or the configured host." 
