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

RUN reflex init

# Build frontend — reflex export creates /app/.web/build/client/
RUN reflex export --frontend-only --no-zip 2>&1 || echo "WARNING: reflex export failed"

# Copy the build output root directly (not a subdirectory found by find)
RUN if [ -d /app/.web/build/client ]; then \
      cp -r /app/.web/build/client /app/frontend_built; \
      echo "Frontend copied from /app/.web/build/client"; \
    elif [ -d /app/.web/out ]; then \
      cp -r /app/.web/out /app/frontend_built; \
      echo "Frontend copied from /app/.web/out"; \
    else \
      echo "No pre-built frontend found"; \
    fi

# Reflex calls "npm start" in /app at runtime — provide a harmless stub
RUN printf '{\n  "name": "techpilot",\n  "version": "1.0.0",\n  "private": true,\n  "scripts": {\n    "start": "echo frontend-ok",\n    "build": "echo ok",\n    "dev": "echo ok"\n  }\n}\n' > /app/package.json

COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN chmod +x /app/start.sh

EXPOSE 8080
CMD ["/app/start.sh"]
