FROM python:3.11-slim

# Install basic tools and cron
RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies without creating virtual environment
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy application files
COPY main.py ./
COPY run_script.sh ./

# Setup cron job to run at 00:00 daily
RUN echo "0 0 * * * /app/run_script.sh >> /var/log/cron.log 2>&1" > /etc/cron.d/auto-sign \
    && chmod 0644 /etc/cron.d/auto-sign \
    && chmod +x /app/run_script.sh \
    && crontab /etc/cron.d/auto-sign \
    && touch /var/log/cron.log

# Start cron service and keep container running
CMD cron && tail -f /var/log/cron.log 