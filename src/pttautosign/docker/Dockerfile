FROM python:3.8-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY src/ ./src/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy cron script
COPY scripts/run_script.sh /etc/cron.d/run_script.sh
RUN chmod 0644 /etc/cron.d/run_script.sh

# Start cron service and run the app
CMD ["pttautosign", "run"] 