#!/bin/sh
set -eu
[ -f .env ] && { set -a; . ./.env; set +a; }
python3 monitor.py &
MON=$!
trap 'kill $MON 2>/dev/null || true' EXIT INT TERM
node server.js
