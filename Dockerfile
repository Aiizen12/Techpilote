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

# Build the frontend at image-build time (Docker build containers have ~8 GB RAM)
# The output lands in .web/build/client/ (React Router v7 convention)
RUN reflex export --frontend-only --no-zip

# Discover where the built index.html ended up and print it for diagnostics
RUN find /app/.web -name "index.html" 2>/dev/null | head -5 || echo "No index.html found in .web"

# Copy nginx config template
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Make startup script executable
RUN chmod +x /app/start.sh

EXPOSE 8080

CMD ["/app/start.sh"]
