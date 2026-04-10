# Reflex needs both Python and Node.js (frontend compilation)
FROM node:20-slim

# Install Python 3.11
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv gcc libffi-dev curl \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create data directories
RUN mkdir -p data/documents data/backups

ENV PYTHONPATH=/app
ENV PORT=8080

# Init Reflex (downloads node modules, generates .web)
RUN reflex init

# Export / pre-build frontend for production
RUN reflex export --frontend-only --no-zip || echo "Export skipped"

EXPOSE 8080

CMD reflex run --env prod --backend-host 0.0.0.0 --backend-port ${PORT}
