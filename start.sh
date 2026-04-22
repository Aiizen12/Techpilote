#!/bin/sh
export PATH="/opt/venv/bin:$PATH"
export PYTHONPATH=/app

PORT="${PORT:-8080}"

# ── Detect pre-built frontend location ───────────────────────────────────────
FRONTEND_DIR=""
for candidate in \
    /app/frontend_built \
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
        gzip_static on;
    }

    location / {
        root ${FRONTEND_DIR};
        try_files \$uri \$uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
}
NGINXEOF

    echo "nginx configured to serve static files from $FRONTEND_DIR"
    python /app/run_backend.py &
    sleep 3

else
    echo "WARNING: no pre-built frontend — building at runtime"
    echo "NOTE: /app/.web/ was created by 'reflex init' during Docker build"
    export NODE_OPTIONS="--max-old-space-size=1536"

    # DO NOT run 'reflex init' here — it calls npm in /app (cwd) before .web/ exists.
    # The Dockerfile already ran 'reflex init', so /app/.web/ and its package.json exist.

    echo "Running npm install in /app/.web ..."
    (cd /app/.web && npm install) || echo "npm install failed"

    echo "Running npm build in /app/.web ..."
    (cd /app/.web && npm run build) || echo "npm build failed"

    # Re-check for index.html after build
    for candidate in /app/.web/out /app/.web/build/client /app/.web/_static /app/.web/.next /app/.web/dist; do
        if [ -f "$candidate/index.html" ]; then
            FRONTEND_DIR="$candidate"
            echo "Frontend built at: $FRONTEND_DIR"
            break
        fi
    done

    if [ -n "$FRONTEND_DIR" ]; then
        cat > /etc/nginx/conf.d/default.conf <<NGINXEOF2
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
NGINXEOF2
    else
        echo "ERROR: could not build frontend. Starting backend only."
        sed -i "s/PORT_PLACEHOLDER/${PORT}/g" /etc/nginx/conf.d/default.conf
    fi

    python /app/run_backend.py &
    sleep 3
fi

# nginx as foreground process
exec nginx -g 'daemon off;'
