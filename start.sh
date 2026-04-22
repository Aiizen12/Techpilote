#!/bin/sh
export PATH="/opt/venv/bin:$PATH"
export PYTHONPATH=/app

PORT="${PORT:-8080}"

# Replace placeholder in nginx config
sed -i "s/PORT_PLACEHOLDER/${PORT}/g" /etc/nginx/conf.d/default.conf

echo "Starting Reflex production server (frontend :3000 + backend :8000)..."

# reflex run --env prod: starts Next.js on :3000 (via npm start) + uvicorn on :8000
# Our /app/package.json delegates npm calls to /app/.web/
reflex run --env prod --backend-host 127.0.0.1 --backend-port 8000 &

echo "Waiting 20s for servers to initialize..."
sleep 20

echo "Starting nginx on port ${PORT}..."
exec nginx -g 'daemon off;'
