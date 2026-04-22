#!/bin/sh
export PATH="/opt/venv/bin:$PATH"
export PYTHONPATH=/app

PORT="${PORT:-8080}"
echo "[start.sh] PORT=$PORT"
echo "[start.sh] PYTHONPATH=$PYTHONPATH"

# ── Detect pre-built frontend ─────────────────────────────────────────────────
FRONTEND_DIR=""
for candidate in /app/frontend_built /app/.web/build/client /app/.web/_static /app/.web/out /app/frontend; do
    if [ -f "$candidate/index.html" ]; then
        FRONTEND_DIR="$candidate"
        echo "[start.sh] Frontend found: $FRONTEND_DIR"
        break
    fi
done

if [ -z "$FRONTEND_DIR" ]; then
    echo "[start.sh] WARNING: no frontend found"
fi

# ── Write nginx config ────────────────────────────────────────────────────────
if [ -n "$FRONTEND_DIR" ]; then
    cat > /etc/nginx/conf.d/default.conf <<NGINXEOF
map \$http_upgrade \$connection_upgrade {
    default upgrade;
    ''      close;
}
server {
    listen ${PORT} default_server;
    port_in_redirect off;

    location ~* ^/(_event|_upload|_ping|backend_health) {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \$connection_upgrade;
        proxy_set_header Host \$host;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    location ~* \.(js|css|png|svg|ico|woff2?|ttf|map|json)$ {
        root ${FRONTEND_DIR};
        try_files \$uri =404;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    location / {
        root ${FRONTEND_DIR};
        try_files \$uri \$uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
}
NGINXEOF
    echo "[start.sh] nginx configured with static files from $FRONTEND_DIR"
else
    sed -i "s/PORT_PLACEHOLDER/${PORT}/g" /etc/nginx/conf.d/default.conf
    echo "[start.sh] nginx configured from template (proxy to :3000)"
fi

# ── Validate nginx config ─────────────────────────────────────────────────────
echo "[start.sh] Testing nginx config..."
nginx -t
if [ $? -ne 0 ]; then
    echo "[start.sh] ERROR: nginx config invalid!"
    cat /etc/nginx/conf.d/default.conf
fi

# ── Start backend ─────────────────────────────────────────────────────────────
echo "[start.sh] Starting Reflex backend..."
reflex run --env prod --backend-only --backend-host 127.0.0.1 --backend-port 8000 &
REFLEX_PID=$!
echo "[start.sh] Reflex PID=$REFLEX_PID, sleeping 10s..."

sleep 10

echo "[start.sh] Starting nginx on port ${PORT}..."
exec nginx -g 'daemon off;'
