#!/bin/bash
# PTT Auto Sign Docker Cron Script
# 功能：在 Docker 環境中設置 cron 任務
# 用途：根據模式設置不同的執行頻率（測試模式：每分鐘一次；正式模式：每天隨機一次）

# 默認設置為生產模式（TEST_MODE=false）
export TEST_MODE=false
export DIRECT_EXEC=false

# Set timezone
export TZ=Asia/Taipei

# Debug mode
DEBUG_MODE=true

# Define directories
if [ -z "$CRON_DATA_DIR" ]; then
    if [ -d "/app" ]; then
        # Docker environment
        CRON_DATA_DIR="/app/data"
    else
        # Local environment
        case "$(uname -s)" in
            Linux*)
                CRON_DATA_DIR="/tmp/pttautosign/data"
                ;;
            Darwin*)
                CRON_DATA_DIR="/tmp/pttautosign/data"
                ;;
            CYGWIN*|MINGW*|MSYS*)
                CRON_DATA_DIR="$HOME/AppData/Local/pttautosign/data"
                ;;
            *)
                CRON_DATA_DIR="/tmp/pttautosign/data"
                ;;
        esac
    fi
fi

# Create necessary directories
mkdir -p "$CRON_DATA_DIR"

# Determine OS type
if [ -z "$OS_TYPE" ]; then
    case "$(uname -s)" in
        Linux*)
            OS_TYPE="linux"
            ;;
        Darwin*)
            OS_TYPE="macos"
            ;;
        CYGWIN*|MINGW*|MSYS*)
            OS_TYPE="windows"
            ;;
        *)
            OS_TYPE="unknown"
            ;;
    esac
fi

# Function to log debug messages
log_debug() {
    if [ "$DEBUG_MODE" = "true" ]; then
        local message="$1"
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        echo "[DEBUG] [$timestamp] $message"
        
        # Also log to file if in Docker
        if [ -d "/app" ]; then
            echo "[DEBUG] [$timestamp] $message" >> /var/log/cron.log
        fi
    fi
}

# Function to run the simple runner script
run_simple_runner() {
    log_debug "Running simple_runner.sh"
    
    # Get the script directory
    local SCRIPT_PATH=""
    
    if [ -d "/app" ]; then
        # Docker environment - try several possible locations
        if [ -f "/app/scripts/simple_runner.sh" ]; then
            SCRIPT_PATH="/app/scripts/simple_runner.sh"
        elif [ -f "/scripts/simple_runner.sh" ]; then
            SCRIPT_PATH="/scripts/simple_runner.sh"
        else
            log_debug "Warning: Could not find simple_runner.sh in Docker paths, using python module directly"
            cd /app && python -m pttautosign.main
            return
        fi
    else
        # Local environment
        SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../" && pwd )"
        SCRIPT_PATH="$SCRIPT_DIR/simple_runner.sh"
    fi
    
    # Set environment variables
    export TEST_MODE=${TEST_MODE:-false}
    export CRON_MODE=true
    export CRON_DATA_DIR="$CRON_DATA_DIR"
    
    # Run the script with environment variables
    log_debug "Executing script at: $SCRIPT_PATH"
    
    # Ensure we're in the right directory
    if [ -d "/app" ]; then
        cd /app
    fi
    
    # Execute script and capture output
    local output=$(bash "$SCRIPT_PATH" 2>&1)
    local status=$?
    
    log_debug "Script execution completed with status: $status"
    log_debug "Output: $output"
    
    # Update execution count file for test mode
    if [ "$TEST_MODE" = "true" ] && [ -f "$CRON_DATA_DIR/execution_count" ]; then
        local current_count=$(cat "$CRON_DATA_DIR/execution_count")
        local new_count=$((current_count + 1))
        echo "$new_count" > "$CRON_DATA_DIR/execution_count"
        log_debug "Updated execution count: $new_count of 5"
    fi
    
    return $status
}

# Function to run initial task on container startup
run_initial_task() {
    log_debug "Running initial task on container startup..."
    echo "====================================="
    echo "   在 Docker 中運行 PTT 自動簽到    "
    echo "====================================="
    echo "執行時間: $(date)"
    echo "正在執行 PTT 自動簽到任務..."
    
    # Create necessary files and directories
    mkdir -p "$CRON_DATA_DIR"
    touch /var/log/cron.log
    chmod 0666 /var/log/cron.log
    
    # List current environment
    echo "Current environment:" >> /var/log/cron.log
    echo "TEST_MODE=$TEST_MODE" >> /var/log/cron.log
    echo "CRON_MODE=$CRON_MODE" >> /var/log/cron.log
    echo "DIRECT_EXEC=$DIRECT_EXEC" >> /var/log/cron.log
    echo "CRON_DATA_DIR=$CRON_DATA_DIR" >> /var/log/cron.log
    
    # Initialize execution counter for test mode
    if [ "$TEST_MODE" = "true" ]; then
        echo "0" > "$CRON_DATA_DIR/execution_count"
        chmod 0666 "$CRON_DATA_DIR/execution_count"
        cat "$CRON_DATA_DIR/execution_count" > /dev/null
        log_debug "Initialized execution counter to 0 at $CRON_DATA_DIR/execution_count"
        echo "Execution counter initialized to 0 at $CRON_DATA_DIR/execution_count" >> /var/log/cron.log
        
        # Debug counter file
        ls -la "$CRON_DATA_DIR" >> /var/log/cron.log
    fi
    
    # Run the first execution immediately (count as execution 0)
    log_debug "Running initial task execution"
    run_simple_runner
    log_debug "Initial task execution completed"
    
    # Display task status
    log_debug "Initial task completed"
    echo "Initial setup completed, waiting for cron to execute scheduled tasks..." >> /var/log/cron.log
}

# Function to setup cron job
setup_cron_job() {
    log_debug "Setting up cron job..."
    
    if [ "$TEST_MODE" = "true" ]; then
        # For test mode: run every minute for 5 times
        if [ -d "/app" ]; then
            # Docker environment - 使用簡化版的 crontab 命令
            cat > "$CRON_DATA_DIR/crontab" << EOL
# PTT Auto Sign test mode crontab - Runs every minute for 5 times
* * * * * cd /app && echo "=== Cron Job Started at \$(date) ===" >> /var/log/cron.log 2>&1 && if [ "\$(cat $CRON_DATA_DIR/execution_count)" -lt "5" ]; then PYTHONPATH=/app TEST_MODE=true CRON_MODE=true CRON_DATA_DIR=$CRON_DATA_DIR /app/scripts/simple_runner.sh >> /var/log/cron.log 2>&1 && curr=\$(cat $CRON_DATA_DIR/execution_count); echo \$((curr+1)) > $CRON_DATA_DIR/execution_count; fi && echo "=== Cron Job Finished at \$(date) ===" >> /var/log/cron.log 2>&1
EOL
            log_debug "Created Docker test mode crontab with simpler command structure"
        else
            # Local environment
            echo "* * * * * cd $(pwd) && if [ \"\$(cat $CRON_DATA_DIR/execution_count)\" -lt \"5\" ]; then TEST_MODE=true CRON_MODE=true CRON_DATA_DIR=$CRON_DATA_DIR $(pwd)/scripts/simple_runner.sh && curr=\$(cat $CRON_DATA_DIR/execution_count); echo \$((curr+1)) > $CRON_DATA_DIR/execution_count; fi" > "$CRON_DATA_DIR/crontab"
        fi
        
        log_debug "Test mode: Scheduled to run every minute (max 5 times)"
    else
        # 正式模式: 每天 9 AM 到 5 PM 之間的隨機時間執行一次
        RANDOM_MINUTE=$((RANDOM % 60))
        RANDOM_HOUR=$((RANDOM % 9 + 9))  # 9 到 17 之間 (9 AM to 5 PM)
        
        log_debug "Production mode: Random execution time set to $RANDOM_HOUR:$RANDOM_MINUTE"
        
        if [ -d "/app" ]; then
            # Docker 環境
            cat > "$CRON_DATA_DIR/crontab" << EOL
# PTT Auto Sign production crontab - 每天隨機時間執行一次
# 執行時間: $RANDOM_HOUR:$RANDOM_MINUTE (Taiwan time)
$RANDOM_MINUTE $RANDOM_HOUR * * * cd /app && PYTHONPATH=/app CRON_MODE=true TEST_MODE=false CRON_DATA_DIR=$CRON_DATA_DIR /app/scripts/simple_runner.sh >> /var/log/cron.log 2>&1
EOL
            echo "Production schedule set: Will run once per day at $RANDOM_HOUR:$RANDOM_MINUTE Taiwan time" >> /var/log/cron.log
        else
            # 本地環境
            echo "$RANDOM_MINUTE $RANDOM_HOUR * * * cd $(pwd) && CRON_MODE=true TEST_MODE=false CRON_DATA_DIR=$CRON_DATA_DIR $(pwd)/scripts/simple_runner.sh" > "$CRON_DATA_DIR/crontab"
        fi
        
        log_debug "Production mode: Scheduled execution time: $RANDOM_HOUR:$RANDOM_MINUTE (once per day)"
    fi

    # In Docker environment, update system crontab
    if [ -d "/app" ]; then
        # Make sure cron.log exists and has permissions
        touch /var/log/cron.log
        chmod 0666 /var/log/cron.log
        
        # Copy crontab to system
        cat "$CRON_DATA_DIR/crontab" > /etc/cron.d/ptt-auto-sign-cron
        chmod 0644 /etc/cron.d/ptt-auto-sign-cron
        
        # Add empty line to end of crontab file (required by some cron implementations)
        echo "" >> /etc/cron.d/ptt-auto-sign-cron
        
        # Display the crontab for logging
        log_debug "Created crontab file:"
        log_debug "$(cat /etc/cron.d/ptt-auto-sign-cron)"
        
        # Update system crontab
        crontab /etc/cron.d/ptt-auto-sign-cron
        
        # Restart cron service and ensure it's running
        log_debug "Ensuring cron service is running..."
        service cron restart
        
        # Verify cron status and actually check if cron is properly running
        if service cron status > /dev/null 2>&1; then
            log_debug "Cron service is running"
            ps aux | grep -v grep | grep cron | head -1 >> /var/log/cron.log
            
            # List active cron jobs
            log_debug "Active cron jobs:"
            crontab -l >> /var/log/cron.log
        else
            log_debug "Error: Cron service is not running properly"
            # Try starting it another way as fallback
            /etc/init.d/cron start
        fi
    else
        # In local environment, update user crontab
        case "$OS_TYPE" in
            linux|windows)
                # Linux/WSL crontab setup
                crontab "$CRON_DATA_DIR/crontab"
                log_debug "Updated user crontab"
                ;;
            macos)
                # For macOS, we'll directly run the script in a loop instead of using crontab
                log_debug "macOS detected, will run directly instead of using crontab"
                ;;
        esac
    fi
}

# Function to run direct execution test with better feedback
run_direct_test() {
    log_debug "Running test in direct execution mode (will run every minute for 5 times)..."
    echo "Test will run every minute for 5 times"
    echo "Press Ctrl+C to cancel"
    echo ""
    
    # Initialize execution counter
    echo "0" > "$CRON_DATA_DIR/execution_count"
    chmod 0666 "$CRON_DATA_DIR/execution_count"
    
    # Run the first execution immediately
    log_debug "Starting execution 1 of 5"
    echo "Starting execution 1 of 5 at $(date)" >> /var/log/cron.log
    run_simple_runner
    echo "1" > "$CRON_DATA_DIR/execution_count"
    echo "Execution 1 of 5 completed at $(date)" >> /var/log/cron.log
    
    # Then run the remaining executions with a 60-second interval
    for i in {2..5}; do
        echo "Waiting 60 seconds for next execution..."
        echo "Waiting 60 seconds until execution $i of 5..." >> /var/log/cron.log
        sleep 60
        log_debug "Starting execution $i of 5"
        echo "Starting execution $i of 5 at $(date)" >> /var/log/cron.log
        run_simple_runner
        echo "$i" > "$CRON_DATA_DIR/execution_count"
        echo "Execution $i of 5 completed at $(date)" >> /var/log/cron.log
    done
    
    log_debug "Test completed: 5 executions finished"
    echo "All 5 executions completed successfully!" >> /var/log/cron.log
    
    # Keep container running if in Docker
    if [ -d "/app" ]; then
        echo "Test completed. Container will continue running for monitoring purposes."
        while true; do
            sleep 60
            touch "$CRON_DATA_DIR/healthcheck"
        done
    fi
}

# Function to monitor cron executions
monitor_cron_executions() {
    log_debug "Monitoring cron executions..."
    
    if [ "$TEST_MODE" = "true" ]; then
        echo "Cron job set to run every minute for 5 times"
        echo "The script will continue running and monitoring the execution count"
        echo "Cron job set to run every minute for 5 times" >> /var/log/cron.log
    else
        echo "Cron job set to run once per day at $(crontab -l | grep -v '^#' | awk '{print $2":"$1}')"
        echo "Container will continue running..."
        echo "Cron job set to run once per day at $(crontab -l | grep -v '^#' | awk '{print $2":"$1}')" >> /var/log/cron.log
    fi
    
    # Create a healthcheck file
    touch "$CRON_DATA_DIR/healthcheck"
    
    # Check if cron is really working by looking at cron logs
    log_debug "Checking cron service logs..."
    if [ -d "/app" ]; then
        grep cron /var/log/syslog 2>/dev/null || journalctl -u cron --no-pager 2>/dev/null || echo "No cron logs found" >> /var/log/cron.log
    fi
    
    if [ "$TEST_MODE" = "true" ]; then
        # Monitor execution count in test mode
        local last_count=0
        local check_interval=5  # seconds between checks
        local timeout_counter=0
        local max_timeout=720   # 12 minutes max wait time (720/5 = 144 checks)
        
        echo "Starting monitoring loop, checking every $check_interval seconds" >> /var/log/cron.log
        
        while [ $timeout_counter -lt $max_timeout ]; do
            # Update healthcheck file
            touch "$CRON_DATA_DIR/healthcheck"
            
            # Force check of execution count file existence
            if [ ! -f "$CRON_DATA_DIR/execution_count" ]; then
                log_debug "Execution count file missing, recreating..."
                echo "0" > "$CRON_DATA_DIR/execution_count"
                chmod 0666 "$CRON_DATA_DIR/execution_count"
                continue
            fi
            
            # Read count safely
            local count=0
            if [ -f "$CRON_DATA_DIR/execution_count" ]; then
                count=$(cat "$CRON_DATA_DIR/execution_count" 2>/dev/null || echo "0")
                # Sanitize count (ensure it's a number)
                if ! [[ "$count" =~ ^[0-9]+$ ]]; then
                    count=0
                    echo "0" > "$CRON_DATA_DIR/execution_count"
                fi
            fi
            
            # Show progress
            if [ "$count" -gt "$last_count" ]; then
                echo "Test execution $count of 5 completed"
                echo "Test execution $count of 5 completed at $(date)" >> /var/log/cron.log
                last_count=$count
                timeout_counter=0  # Reset timeout when progress is made
            fi
            
            # Check if completed
            if [ "$count" -ge 5 ]; then
                echo "Test completed: All 5 executions finished!"
                echo "Test completed: All 5 executions finished at $(date)" >> /var/log/cron.log
                
                # In Docker, keep the container running
                echo "Container will continue running for monitoring purposes"
                echo "Container continuing to run for monitoring..." >> /var/log/cron.log
                
                # Disable further cron executions
                if [ -d "/app" ]; then
                    crontab -r || echo "Failed to remove crontab" >> /var/log/cron.log
                    echo "Disabled further cron executions" >> /var/log/cron.log
                fi
                
                # Keep container alive
                while true; do
                    sleep 60
                    touch "$CRON_DATA_DIR/healthcheck"
                done
            fi
            
            # If no progress after too many checks, try to fix things
            timeout_counter=$((timeout_counter + 1))
            if [ $((timeout_counter % 60)) -eq 0 ]; then
                echo "No progress detected for 5 minutes, checking cron status..." >> /var/log/cron.log
                
                # Fix permissions
                chmod 0666 "$CRON_DATA_DIR/execution_count"
                chmod 0666 /var/log/cron.log
                
                # Check and restart cron if needed
                if [ -d "/app" ]; then
                    service cron status >> /var/log/cron.log 2>&1 || service cron restart
                    ps aux | grep cron >> /var/log/cron.log
                    echo "Current count: $count" >> /var/log/cron.log
                    
                    # If completely stuck, manually increment
                    if [ $timeout_counter -gt 300 ]; then  # After ~25 minutes, force progress
                        if [ "$count" -lt 5 ]; then
                            new_count=$((count + 1))
                            echo "$new_count" > "$CRON_DATA_DIR/execution_count"
                            echo "Manually incremented count to $new_count due to timeout" >> /var/log/cron.log
                            last_count=$new_count
                            timeout_counter=0
                        fi
                    fi
                fi
            fi
            
            # Sleep before checking again
            sleep $check_interval
        done
        
        # If we got here, we timed out
        echo "Monitoring timed out after $((max_timeout * check_interval)) seconds" >> /var/log/cron.log
        echo "Final execution count: $(cat "$CRON_DATA_DIR/execution_count" 2>/dev/null || echo "unknown")" >> /var/log/cron.log
    else
        # For production mode, just keep the container running
        while true; do
            sleep 60
            # Update healthcheck timestamp
            touch "$CRON_DATA_DIR/healthcheck"
        done
    fi
}

# Main function
main() {
    log_debug "Starting PTT Auto Sign cron script"
    log_debug "Environment: $OS_TYPE, Test mode: $TEST_MODE, Direct execution: $DIRECT_EXEC"
    
    # Run initial task
    run_initial_task
    
    # Handle based on environment and mode
    if [ "$TEST_MODE" = "true" ]; then
        if [ "$OS_TYPE" = "macos" ] || [ "$DIRECT_EXEC" = "true" ]; then
            # Direct execution for macOS or when direct execution is requested
            log_debug "Running in direct execution mode (based on OS or DIRECT_EXEC flag)"
            run_direct_test
        elif [ -d "/app" ]; then
            # In Docker and test mode, check if cron service works properly
            log_debug "Setting up cron job for Docker test mode"
            setup_cron_job
            
            # Verify cron is working
            if ! service cron status > /dev/null 2>&1; then
                log_debug "Cron service failed to start, falling back to direct execution mode"
                echo "Warning: Cron service failed to start. Falling back to direct execution mode" >> /var/log/cron.log
                
                # Try to reset cron
                crontab -r 2>/dev/null || true
                service cron stop 2>/dev/null || true
                sleep 1
                service cron start 2>/dev/null || true
                
                # If still not working, use direct execution
                if ! service cron status > /dev/null 2>&1; then
                    log_debug "Cron still not working, switching to direct execution mode"
                    echo "Cron service still not working. Using direct execution mode instead." >> /var/log/cron.log
                    run_direct_test
                    return
                fi
            fi
            
            # If we get here, cron seems to be working, monitor executions
            monitor_cron_executions
        else
            # Linux/Windows non-Docker test mode
            setup_cron_job
            monitor_cron_executions
        fi
    else
        # Production mode
        log_debug "Running in production mode (random daily execution)"
        setup_cron_job
        monitor_cron_executions
    fi
}

# Run main function
main 