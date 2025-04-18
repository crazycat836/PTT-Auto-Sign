# Use Python 3.11 slim image
FROM python:3.11-slim

# Set build arguments for environment variables
ARG TEST_MODE=true
ARG ENABLE_CRON=true
ARG DIRECT_EXEC=true

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    TEST_MODE=${TEST_MODE} \
    ENABLE_CRON=${ENABLE_CRON} \
    DIRECT_EXEC=${DIRECT_EXEC}

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

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_VERSION=${POETRY_VERSION} python3 -

# Add Poetry to PATH
ENV PATH="${POETRY_HOME}/bin:$PATH"

# Copy project files
COPY pyproject.toml poetry.lock README.md README_zh-TW.md ./
COPY .env ./

# Regenerate lock file and install dependencies
RUN poetry lock --no-update \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# Copy the rest of the application
COPY src/ ./src/

# Copy script files to their proper locations
COPY scripts/ ./scripts/

# Copy Docker-specific files
COPY src/pttautosign/docker/entrypoint.sh /entrypoint.sh
COPY scripts/docker/random_cron.sh /usr/local/bin/random_cron.sh

# Create necessary directories
RUN mkdir -p /app/scripts /app/data /var/log

# Make scripts executable
RUN chmod +x /entrypoint.sh /usr/local/bin/random_cron.sh \
    && find /app/scripts -type f -name "*.sh" -exec chmod +x {} \;

# Install the package in development mode
RUN pip install -e .

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