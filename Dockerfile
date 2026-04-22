FROM node:20-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv gcc libffi-dev curl unzip nginx \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data/documents data/backups

ENV PYTHONPATH=/app
ENV PORT=8080
ENV NODE_OPTIONS="--max-old-space-size=2048"

# Init Reflex — creates /app/.web/ with Next.js scaffold
RUN reflex init

# Show what the generated package.json looks like
RUN echo "=== .web/package.json ===" && cat /app/.web/package.json || echo "(not found)"

# Install frontend deps
RUN cd /app/.web && npm install

# Add missing start script to .web/package.json (Reflex 0.8.x doesn't generate one)
RUN cd /app/.web && npm pkg set scripts.start="next start -p 3000"

# Build frontend — show full output so we can debug failures
RUN cd /app/.web && npm run build 2>&1 || echo "=== WARNING: npm build failed — will try at runtime ==="

# Verify next binary exists
RUN ls /app/.web/node_modules/.bin/next && echo "next OK" || echo "next MISSING — checking package.json"

# /app/package.json: Reflex calls npm in /app — use absolute path to next binary
RUN printf '{"name":"techpilot","version":"1.0.0","private":true,"scripts":{"start":"cd /app/.web && node_modules/.bin/next start -p 3000","build":"cd /app/.web && node_modules/.bin/next build","dev":"cd /app/.web && node_modules/.bin/next dev -p 3000"}}\n' > /app/package.json

COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN chmod +x /app/start.sh

EXPOSE 8080

CMD ["/app/start.sh"]
