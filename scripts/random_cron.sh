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

# Log the scheduled time
echo "Scheduled execution time: $RANDOM_HOUR:$RANDOM_MINUTE"

# Create crontab entry in the user's crontab
(crontab -l 2>/dev/null || echo "") | grep -v "/app/scripts/run_script.sh" > "$CRON_DATA_DIR/tempcron"
echo "$RANDOM_MINUTE $RANDOM_HOUR * * * /app/scripts/run_script.sh" >> "$CRON_DATA_DIR/tempcron"
crontab "$CRON_DATA_DIR/tempcron"
rm "$CRON_DATA_DIR/tempcron"

# Verify crontab was set correctly
echo "Current crontab settings:"
crontab -l

# Start cron service in the background (if running with root, otherwise this will be skipped)
if [ "$(id -u)" -eq 0 ]; then
    echo "Running as root, starting cron service..."
    service cron start
    echo "Cron service started successfully."
else
    echo "Not running as root, skipping cron service start."
    echo "This is normal if you're using the Docker setup with the entrypoint wrapper script."
    echo "The wrapper script should have already started cron as root before switching to this user."
fi

# Create a healthcheck file
touch "$CRON_DATA_DIR/healthcheck"

# Run the task immediately on first start
echo "Running initial task on container startup..."
/app/scripts/run_script.sh

# Keep container running
echo "Container will now stay running to allow scheduled tasks to execute..."
while true; do
    sleep 3600
    # Periodically touch the healthcheck file
    touch "$CRON_DATA_DIR/healthcheck"
    echo "Healthcheck updated at $(date)"
done 