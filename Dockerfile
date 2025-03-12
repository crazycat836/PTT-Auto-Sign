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

# Copy only the files needed for installing dependencies
COPY pyproject.toml poetry.lock ./

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

# Set timezone
ENV TZ=Asia/Taipei \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

# Copy application files
COPY --chown=pttuser:pttuser . .

# Set up execution script
RUN chmod +x /app/random_cron.sh /app/run_script.sh

# Switch to non-root user
USER pttuser

# Set entrypoint
ENTRYPOINT ["/app/random_cron.sh"]

# Health check
HEALTHCHECK --interval=5m --timeout=3s \
  CMD test -f /app/data/healthcheck || (touch /app/data/healthcheck && exit 0) 