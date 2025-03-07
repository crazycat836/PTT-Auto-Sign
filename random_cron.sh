#!/bin/bash

# Set timezone
export TZ=Asia/Taipei

# Define directories
CRON_DATA_DIR=/app/data
CRON_LOG_DIR=/app/logs

# Create necessary directories
mkdir -p "$CRON_DATA_DIR"

# Generate random minute (0-59)
RANDOM_MINUTE=$((RANDOM % 60))

# Generate random hour (9-17, representing 9 AM to 5 PM)
RANDOM_HOUR=$((RANDOM % 9 + 9))

# Create crontab entry
echo "$RANDOM_MINUTE $RANDOM_HOUR * * * /app/run_script.sh >> $CRON_LOG_DIR/cron.log 2>&1" > "$CRON_DATA_DIR/crontab"

# Log the scheduled time
echo "Scheduled execution time: $RANDOM_HOUR:$RANDOM_MINUTE" >> "$CRON_LOG_DIR/cron.log"

# Copy crontab to system
cp "$CRON_DATA_DIR/crontab" /etc/cron.d/ptt-auto-sign-cron
chmod 0644 /etc/cron.d/ptt-auto-sign-cron

# Update system crontab
crontab /etc/cron.d/ptt-auto-sign-cron

# Start cron service
service cron start

# Keep container running
tail -f "$CRON_LOG_DIR/cron.log" 