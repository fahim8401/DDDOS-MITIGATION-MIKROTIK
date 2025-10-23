# Backend Dockerfile for MikroTik DDoS Monitor
FROM python:3.11-slim

LABEL maintainer="MikroTik DDoS Monitor"
LABEL description="DDoS monitoring and mitigation for MikroTik routers"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY mt_ddos_monitor.py .
COPY api/ ./api/
COPY config.yml .

# Create data directory for database
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CONFIG_FILE=/app/config.yml
ENV DATABASE_PATH=/app/data/ddos_events.db

# Expose API port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/health')" || exit 1

# Run the application
CMD ["python", "api/app.py"]
