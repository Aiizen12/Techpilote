#!/bin/sh
export PATH="/opt/venv/bin:$PATH"

# Inject PORT into nginx config
sed -i "s/PORT_PLACEHOLDER/${PORT:-8080}/g" /etc/nginx/conf.d/default.conf

# Start Reflex (backend on 8000, frontend on 3000)
reflex run --env prod --backend-host 127.0.0.1 --backend-port 8000 --frontend-port 3000 &

# Wait up to 120s for the Next.js frontend to be ready
echo "Waiting for Reflex to start..."
i=0
while [ $i -lt 60 ]; do
    if curl -sf http://127.0.0.1:3000/ > /dev/null 2>&1; then
        echo "Reflex ready."
        break
    fi
    sleep 2
    i=$((i+1))
done

# Start nginx as main foreground process
exec nginx -g 'daemon off;'
