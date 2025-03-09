FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Set timezone
ENV TZ=Asia/Taipei
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy and set up random execution script
COPY random_cron.sh /app/random_cron.sh
RUN chmod +x /app/random_cron.sh

# Set PYTHONDONTWRITEBYTECODE environment variable
ENV PYTHONDONTWRITEBYTECODE=1

# Set entrypoint
ENTRYPOINT ["/app/random_cron.sh"] 