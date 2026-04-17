#!/bin/sh
export PATH="/opt/venv/bin:$PATH"
export PYTHONPATH=/app

PORT="${PORT:-8080}"

# ── Detect pre-built frontend location ───────────────────────────────────────
FRONTEND_DIR=""
for candidate in \
    /app/.web/build/client \
    /app/.web/_static \
    /app/.web/out \
    /app/frontend; do
    if [ -f "$candidate/index.html" ]; then
        FRONTEND_DIR="$candidate"
        echo "Pre-built frontend found at: $FRONTEND_DIR"
        break
    fi
done

# ── Write nginx config ────────────────────────────────────────────────────────
if [ -n "$FRONTEND_DIR" ]; then
    # Serve static files directly — no proxy to port 3000 needed
    cat > /etc/nginx/conf.d/default.conf <<NGINXEOF
map \$http_upgrade \$connection_upgrade {
    default upgrade;
    ''      close;
}
server {
    listen ${PORT} default_server;
    port_in_redirect off;

    # Backend API / WebSocket
    location ~* ^/(_event|_upload|_ping|backend_health) {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \$connection_upgrade;
        proxy_set_header Host \$host;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    # Static assets with long-term caching
    location ~* \.(js|css|png|svg|ico|woff2?|ttf|map|json)$ {
        root ${FRONTEND_DIR};
        try_files \$uri =404;
        add_header Cache-Control "public, max-age=31536000, immutable";
        gzip_static on;
    }

    # SPA catch-all
    location / {
        root ${FRONTEND_DIR};
        try_files \$uri \$uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
}
NGINXEOF

    echo "nginx configured to serve static files from $FRONTEND_DIR"
    # Backend only — frontend already built
    reflex run --env prod --backend-only --backend-host 127.0.0.1 --backend-port 8000 &
    sleep 3

else
    echo "WARNING: no pre-built frontend — running full reflex (may be slow/OOM)"
    # Fallback: proxy to Reflex's own frontend server on port 3000
    sed -i "s/PORT_PLACEHOLDER/${PORT}/g" /etc/nginx/conf.d/default.conf
    export NODE_OPTIONS="--max-old-space-size=1536"
    reflex run --env prod --backend-host 127.0.0.1 --backend-port 8000 --frontend-port 3000 &
    # Wait up to 3 min for frontend
    i=0
    while [ $i -lt 90 ]; do
        if curl -sf http://127.0.0.1:3000/ > /dev/null 2>&1; then
            echo "Reflex frontend ready."
            break
        fi
        sleep 2
        i=$((i+1))
    done
fi

# nginx as foreground process
exec nginx -g 'daemon off;'
