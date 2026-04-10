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

# Init Reflex (generates .web/ and config)
RUN reflex init

# Pre-build the Next.js frontend with the correct api_url
RUN reflex export --frontend-only --no-zip || echo "Export warning: continuing"

# Copy nginx config template
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Make startup script executable
RUN chmod +x /start.sh

EXPOSE 8080

CMD ["/start.sh"]
