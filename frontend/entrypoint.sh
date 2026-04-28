#!/bin/sh
set -eu

APP_USERNAME="${APP_USERNAME:-admin}"
APP_PASSWORD="${APP_PASSWORD:-}"
VITE_API_URL="${VITE_API_URL:-}"
VITE_API_KEY="${VITE_API_KEY:-}"

if [ -z "$APP_PASSWORD" ]; then
  echo "APP_PASSWORD must be set" >&2
  exit 1
fi

htpasswd -bc /etc/nginx/.htpasswd "$APP_USERNAME" "$APP_PASSWORD" >/dev/null 2>&1

escape_js() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

API_URL_ESCAPED="$(escape_js "$VITE_API_URL")"
API_KEY_ESCAPED="$(escape_js "$VITE_API_KEY")"

cat <<EOF >/usr/share/nginx/html/config.js
window.__APP_CONFIG__ = {
  API_URL: "$API_URL_ESCAPED",
  API_KEY: "$API_KEY_ESCAPED",
};
EOF

exec nginx -g "daemon off;"
