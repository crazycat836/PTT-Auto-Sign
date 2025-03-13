# Build stage
FROM python:3.13-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install --no-cache-dir poetry

# Copy project files needed for installing dependencies
COPY pyproject.toml poetry.lock README*.md ./
COPY src src/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# Final stage
FROM python:3.13-slim

# Create non-root user
RUN groupadd -r pttuser && useradd -r -g pttuser -m -d /home/pttuser pttuser

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /app/data \
    && chown -R pttuser:pttuser /app

# Set timezone and Python environment
ENV TZ=Asia/Taipei \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

# Copy application files
COPY --chown=pttuser:pttuser . .

# Install the package in development mode
RUN pip install -e .

# Set up execution script
RUN chmod +x /app/scripts/random_cron.sh /app/scripts/run_script.sh

# Create a wrapper script to start cron and then run as non-root user
RUN echo '#!/bin/bash\n\
echo "Starting cron service as root..."\n\
service cron start\n\
echo "Cron service started successfully."\n\
echo "Switching to non-root user (pttuser) for application execution..."\n\
exec su -c "/app/scripts/random_cron.sh" pttuser\n\
' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Set entrypoint to the wrapper script (running as root)
ENTRYPOINT ["/app/entrypoint.sh"]

# Health check
HEALTHCHECK --interval=5m --timeout=3s \
  CMD test -f /app/data/healthcheck || (touch /app/data/healthcheck && exit 0) 