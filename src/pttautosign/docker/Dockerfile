# Use Python 3.11 slim image
FROM python:3.11-slim

# Set build arguments for environment variables
ARG TEST_MODE=true
ARG ENABLE_CRON=true
ARG DIRECT_EXEC=false

# 只保留核心必要的環境變數
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TEST_MODE=${TEST_MODE} \
    ENABLE_CRON=${ENABLE_CRON} \
    DIRECT_EXEC=${DIRECT_EXEC} \
    PTT_USERNAME="" \
    PTT_PASSWORD="" \
    TELEGRAM_BOT_TOKEN="" \
    TELEGRAM_CHAT_ID=""

# 設定時區
ENV TZ=Asia/Taipei
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        cron \
        procps \
    && rm -rf /var/lib/apt/lists/*

# 使用pip直接安裝套件，簡化依賴安裝
COPY pyproject.toml ./
RUN pip install --no-cache-dir poetry && \
    poetry export -f requirements.txt --output requirements.txt && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir telnetlib3

# Copy the application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Copy Docker-specific files
COPY src/pttautosign/docker/entrypoint.sh /entrypoint.sh
COPY scripts/docker/random_cron.sh /usr/local/bin/random_cron.sh

# Create necessary directories
RUN mkdir -p /app/scripts /app/data /var/log

# Make scripts executable
RUN chmod +x /entrypoint.sh /usr/local/bin/random_cron.sh \
    && find /app/scripts -type f -name "*.sh" -exec chmod +x {} \;

# Set environment variables for the application
ENV PYTHONPATH=/app

# Print build information
RUN echo "Build info:" && \
    echo "TEST_MODE: ${TEST_MODE}" && \
    echo "ENABLE_CRON: ${ENABLE_CRON}" && \
    echo "DIRECT_EXEC: ${DIRECT_EXEC}" && \
    echo "Python version:" && python --version

# Expose port for health check
EXPOSE 8000

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"] 