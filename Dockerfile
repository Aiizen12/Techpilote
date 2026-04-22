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

# Build frontend — show full output so we can debug failures
RUN cd /app/.web && npm run build 2>&1 || echo "=== WARNING: npm build failed — will use next start without pre-build ==="

# /app/package.json: Reflex calls npm in /app — delegate to .web/
RUN printf '{"name":"techpilot","version":"1.0.0","private":true,"scripts":{"start":"npm --prefix /app/.web start","build":"npm --prefix /app/.web run build","dev":"npm --prefix /app/.web run dev"}}\n' > /app/package.json

COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN chmod +x /app/start.sh

EXPOSE 8080

CMD ["/app/start.sh"]
