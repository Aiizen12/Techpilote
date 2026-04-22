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

# Reflex init + export (the proper way to build the frontend)
RUN reflex init
RUN reflex export --frontend-only --no-zip 2>&1 || echo "WARNING: reflex export failed"

# Copy built frontend to canonical location
RUN FOUND=$(find /app/.web /app/frontend -name "index.html" 2>/dev/null | head -1); \
    if [ -n "$FOUND" ]; then \
      cp -r "$(dirname $FOUND)" /app/frontend_built; \
      echo "Frontend built at: $(dirname $FOUND)"; \
    else \
      echo "No pre-built frontend found"; \
    fi

# Reflex calls "npm start" in /app at runtime — provide a stub that serves
# the static frontend on port 3000 using Python (always available, no next needed)
RUN printf '{\n  "name": "techpilot",\n  "version": "1.0.0",\n  "private": true,\n  "scripts": {\n    "start": "python3 -m http.server 3000 --directory /app/frontend_built",\n    "build": "echo ok",\n    "dev": "echo ok"\n  }\n}\n' > /app/package.json

COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN chmod +x /app/start.sh

EXPOSE 8080
CMD ["/app/start.sh"]
