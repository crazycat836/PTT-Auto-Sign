# Use Python 3.13 slim image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR='/var/cache/pypoetry'

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        cron \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to latest version
RUN pip install --no-cache-dir --upgrade pip

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_VERSION=${POETRY_VERSION} python3 -

# Add Poetry to PATH
ENV PATH="${POETRY_HOME}/bin:$PATH"

# Copy project files
COPY pyproject.toml poetry.lock README.md README_zh-TW.md ./
COPY .env ./
COPY src/pttautosign/patches/fake_telnetlib3.py ./src/pttautosign/patches/

# Regenerate lock file and install dependencies
RUN poetry lock --no-update \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# Copy the rest of the application
COPY src/ ./src/

# Copy Docker-specific files
COPY src/pttautosign/docker/entrypoint.sh /entrypoint.sh
COPY scripts/docker/random_cron.sh /usr/local/bin/random_cron.sh

# Make scripts executable
RUN chmod +x /entrypoint.sh /usr/local/bin/random_cron.sh

# Install the package in development mode
RUN pip install -e .

# Set environment variables for the application
ENV PYTHONPATH=/app

# Expose port for health check
EXPOSE 8000

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"] 