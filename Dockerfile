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

# Reflex 0.8.x calls "npm start" with cwd=/app — provide a stub that starts a static
# file server on port 3000 so Reflex is satisfied and can proceed.
RUN printf '{\n  "name": "techpilot",\n  "version": "1.0.0",\n  "private": true,\n  "scripts": {\n    "start": "python3 -m http.server 3000 --directory /app/frontend_built 2>/dev/null || python3 -m http.server 3000 --directory /app/.web/out",\n    "build": "echo build-handled-by-docker",\n    "dev": "echo dev-not-supported"\n  }\n}\n' > /app/package.json

# Init Reflex — creates /app/.web/ with package.json and Next.js scaffold
RUN reflex init

# Build frontend explicitly in .web/ (no npm calls in /app)
RUN cd /app/.web && npm install
RUN cd /app/.web && npm run build || echo "WARNING: npm build failed — will retry at runtime"

# Copy built frontend to canonical location if index.html was produced
RUN FOUND=$(find /app/.web -name "index.html" 2>/dev/null | head -1); \
    if [ -n "$FOUND" ]; then \
      DIR=$(dirname "$FOUND"); \
      echo "Frontend built at: $DIR"; \
      cp -r "$DIR" /app/frontend_built; \
    else \
      echo "No pre-built frontend found — will build at runtime"; \
    fi

COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN chmod +x /app/start.sh

EXPOSE 8080

CMD ["/app/start.sh"]
