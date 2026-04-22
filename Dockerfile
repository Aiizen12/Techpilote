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

# Allow Node.js to use up to 2 GB heap during the frontend build
ENV NODE_OPTIONS="--max-old-space-size=2048"

# Init Reflex (generates .web/ scaffold and config)
RUN reflex init

# Build the frontend at image-build time
RUN reflex export --frontend-only --no-zip || echo "WARNING: reflex export failed, frontend will be built at runtime"

# Discover where index.html ended up and copy to canonical location
RUN FOUND=$(find /app/.web /app/frontend -name "index.html" 2>/dev/null | head -1); \
    if [ -n "$FOUND" ]; then \
      DIR=$(dirname "$FOUND"); \
      echo "Frontend built at: $DIR"; \
      cp -r "$DIR" /app/frontend_built; \
    else \
      echo "No pre-built frontend found — will build at runtime"; \
    fi

# Copy nginx config template
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Make startup script executable
RUN chmod +x /app/start.sh

EXPOSE 8080

CMD ["/app/start.sh"]
