#!/bin/bash

# Set timezone
export TZ=Asia/Taipei

# Define directories
CRON_DATA_DIR=/app/data

# Create necessary directories
mkdir -p "$CRON_DATA_DIR"

# Generate random minute (0-59)
RANDOM_MINUTE=$((RANDOM % 60))

# Generate random hour (9-17, representing 9 AM to 5 PM)
RANDOM_HOUR=$((RANDOM % 9 + 9))

# Create crontab entry
echo "$RANDOM_MINUTE $RANDOM_HOUR * * * /app/run_script.sh" > "$CRON_DATA_DIR/crontab"

# Log the scheduled time
echo "Scheduled execution time: $RANDOM_HOUR:$RANDOM_MINUTE"

# Copy crontab to system
cp "$CRON_DATA_DIR/crontab" /etc/cron.d/ptt-auto-sign-cron
chmod 0644 /etc/cron.d/ptt-auto-sign-cron

# Update system crontab
crontab /etc/cron.d/ptt-auto-sign-cron

# Start cron service
service cron start

# Create a healthcheck file
touch "$CRON_DATA_DIR/healthcheck"

# Keep container running
while true; do
    sleep 3600
done 