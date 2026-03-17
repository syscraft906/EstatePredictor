# Vietnam Real Estate Web Crawler - Docker Configuration

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    sqlite3 \
    chromium-browser \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data/{raw,processed} /app/logs

# Create non-root user for security
RUN useradd -m -u 1000 scraper && chown -R scraper:scraper /app

USER scraper

# Health check
HEALTHCHECK --interval=300s --timeout=60s --start-period=10s --retries=3 \
    CMD python -c "import sqlite3; sqlite3.connect('/app/data/estate_crawler.db').execute('SELECT 1')"

# Default command: run scheduler
CMD ["python", "-c", "from scheduler import start_scheduler; start_scheduler()"]

# Labels for documentation
LABEL maintainer="Estate Crawler Team"
LABEL description="Vietnam Real Estate Web Crawler"
LABEL version="1.0.0"
