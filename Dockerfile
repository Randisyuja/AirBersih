# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Set environment variables for Python & Django
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DJANGO_SETTINGS_MODULE=airBersih.settings \
    DATABASE_URL=sqlite:////app/db.sqlite3 \
    SECRET_KEY=django-insecure-default-key-change-in-production

# Set working directory
WORKDIR /app

# Install system dependencies required for:
# - PostgreSQL / psycopg2: libpq-dev, build-essential
# - WeasyPrint & ReportLab: libpango-1.0-0, libpangoft2-1.0-0, libharfbuzz0b, libffi-dev, shared-mime-info, fonts-dejavu-core
# - Networking & health checks: netcat-openbsd, curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu-core \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first to leverage Docker build cache
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script and normalize line endings for Linux execution
COPY entrypoint.sh /app/entrypoint.sh
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Copy application source code
COPY . /app/

# Create a non-root system user and configure permissions
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/staticfiles && \
    chown -R appuser:appuser /app

USER appuser

# Expose default HTTP port
EXPOSE 8000

# Set entrypoint and default container command
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-3} airBersih.wsgi:application"]
