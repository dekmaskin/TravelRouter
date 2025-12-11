# TravelNet Portal - Production Docker Image
FROM python:3.11-slim-bullseye

# Metadata
LABEL maintainer="TravelNet Team"
LABEL version="2.0.0"
LABEL description="Secure Travel Router Management Portal"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Create non-root user
RUN groupadd -r travelnet && useradd -r -g travelnet travelnet

# Install system dependencies
RUN apt-get update && apt-get install -y \
    network-manager \
    wireless-tools \
    iproute2 \
    iptables \
    dnsutils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs backups && \
    chown -R travelnet:travelnet /app

# Set secure permissions
RUN chmod 755 /app && \
    chmod 644 /app/*.py && \
    chmod 600 /app/.env.* 2>/dev/null || true

# Switch to non-root user
USER travelnet

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

# Expose port
EXPOSE 80

# Run application
CMD ["python", "app.py"]