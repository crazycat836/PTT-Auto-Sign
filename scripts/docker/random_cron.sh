#!/bin/bash
# PTT Auto Sign Docker Cron Script
# 功能：在 Docker 環境中設置 cron 任務
# 用途：根據模式設置不同的執行頻率（測試模式：每分鐘一次；正式模式：每天隨機一次）

# Set timezone
export TZ=Asia/Taipei

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
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[DEBUG] [$timestamp] $message"
}

# Function to run the simple runner script
run_simple_runner() {
    # Get the script directory
    if [ -d "/app" ]; then
        # Docker environment
        SCRIPT_DIR="/app/scripts"
        cd /app
    else
        # Local environment
        SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../" && pwd )"
        cd "$(dirname "$SCRIPT_DIR")"
    fi
    
    # Set environment variables
    export TEST_MODE=${TEST_MODE:-false}
    export CRON_MODE=true
    export CRON_DATA_DIR=$CRON_DATA_DIR
    
    # Run the script
    log_debug "Running simple_runner.sh"
    bash "$SCRIPT_DIR/simple_runner.sh"
}

# Function to run initial task on container startup
run_initial_task() {
    echo "Running initial task on container startup..."
    echo "====================================="
    echo "   在 Docker 中運行 PTT 自動簽到    "
    echo "====================================="
    echo "執行時間: $(date)"
    echo "正在執行 PTT 自動簽到任務..."
    
    # Use the correct module path
    if [ -d "/app" ]; then
        cd /app
        if poetry run python -W ignore src/pttautosign/main.py --test-login; then
            echo "任務成功完成"
        else
            echo "任務失敗"
        fi
    else
        echo "不在 Docker 環境中，跳過初始任務"
    fi
}

# Function to setup cron job
setup_cron_job() {
    if [ "$TEST_MODE" = "true" ]; then
        # For test mode: run every minute for 5 times
        if [ -d "/app" ]; then
            # Docker environment
            echo "* * * * * cd /app && PYTHONPATH=/app TEST_MODE=true CRON_MODE=true CRON_DATA_DIR=$CRON_DATA_DIR /app/scripts/simple_runner.sh" > "$CRON_DATA_DIR/crontab"
        else
            # Local environment
            echo "* * * * * cd $(pwd) && TEST_MODE=true CRON_MODE=true CRON_DATA_DIR=$CRON_DATA_DIR $(pwd)/scripts/simple_runner.sh" > "$CRON_DATA_DIR/crontab"
        fi
        log_debug "Test mode: Scheduled to run every minute"
        
        # Initialize execution counter for test mode
        echo "0" > "$CRON_DATA_DIR/execution_count"
        log_debug "Initialized execution counter"
    else
        # Normal mode: random time between 9 AM to 5 PM
        RANDOM_MINUTE=$((RANDOM % 60))
        RANDOM_HOUR=$((RANDOM % 9 + 9))
        
        if [ -d "/app" ]; then
            # Docker environment
            echo "$RANDOM_MINUTE $RANDOM_HOUR * * * cd /app && PYTHONPATH=/app CRON_DATA_DIR=$CRON_DATA_DIR /app/scripts/simple_runner.sh" > "$CRON_DATA_DIR/crontab"
        else
            # Local environment
            echo "$RANDOM_MINUTE $RANDOM_HOUR * * * cd $(pwd) && CRON_DATA_DIR=$CRON_DATA_DIR $(pwd)/scripts/simple_runner.sh" > "$CRON_DATA_DIR/crontab"
        fi
        log_debug "Production mode: Scheduled execution time: $RANDOM_HOUR:$RANDOM_MINUTE (once per day)"
    fi

    # In Docker environment, update system crontab
    if [ -d "/app" ]; then
        # Copy crontab to system
        cp "$CRON_DATA_DIR/crontab" /etc/cron.d/ptt-auto-sign-cron
        chmod 0644 /etc/cron.d/ptt-auto-sign-cron
        
        # Update system crontab
        crontab /etc/cron.d/ptt-auto-sign-cron
        
        # Start cron service
        service cron start
        log_debug "Cron service started"
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

# Function to run direct execution test (for macOS or when requested)
run_direct_test() {
    log_debug "Running test in direct execution mode (will run every minute for 5 times)..."
    echo "Test will run every minute for 5 times"
    echo "Press Ctrl+C to cancel"
    echo ""
    
    # Initialize execution counter
    echo "0" > "$CRON_DATA_DIR/execution_count"
    
    # Run the first execution immediately
    log_debug "Starting execution 1 of 5"
    run_simple_runner
    echo "1" > "$CRON_DATA_DIR/execution_count"
    
    # Then run the remaining executions with a 60-second interval
    for i in {2..5}; do
        echo "Waiting 60 seconds for next execution..."
        sleep 60
        log_debug "Starting execution $i of 5"
        run_simple_runner
        echo "$i" > "$CRON_DATA_DIR/execution_count"
    done
    
    log_debug "Test completed: 5 executions finished"
}

# Function to monitor cron executions
monitor_cron_executions() {
    log_debug "Monitoring cron executions..."
    echo "Cron job set to run every minute for 5 times"
    echo "The script will continue running and monitoring the execution count"
    
    # Create a healthcheck file
    touch "$CRON_DATA_DIR/healthcheck"
    
    # Monitor execution count without blocking
    local last_count=0
    while true; do
        if [ "$TEST_MODE" = "true" ] && [ -f "$CRON_DATA_DIR/execution_count" ]; then
            count=$(cat "$CRON_DATA_DIR/execution_count")
            if [ "$count" -gt "$last_count" ]; then
                # Show execution count
                log_debug "Test execution $count of 5 completed"
                last_count=$count
            fi
            if [ "$count" -ge 5 ]; then
                log_debug "Test completed: 5 executions finished"
                log_debug "Container will continue running for monitoring purposes"
                
                # In local environment, clean up cron job
                if [ ! -d "/app" ]; then
                    case "$OS_TYPE" in
                        linux|windows)
                            crontab -l | grep -v "simple_runner.sh" | crontab -
                            log_debug "Cleaned up cron job"
                            return
                            ;;
                    esac
                fi
                
                # In Docker, just continue monitoring
                sleep 60
                continue
            fi
        fi
        
        # Sleep for a minute before checking again
        sleep 5
    done
}

# Main function
main() {
    log_debug "Starting PTT Auto Sign cron script"
    
    # Run initial task if in Docker environment
    if [ -d "/app" ]; then
        run_initial_task
    fi
    
    # For direct test execution on macOS
    if [ "$TEST_MODE" = "true" ] && [ "$OS_TYPE" = "macos" ] && [ "$DIRECT_EXEC" = "true" ]; then
        run_direct_test
        return
    fi
    
    # Setup cron job
    setup_cron_job
    
    # For Docker or Linux/Windows, monitor executions
    if [ -d "/app" ] || [ "$OS_TYPE" = "linux" ] || [ "$OS_TYPE" = "windows" ]; then
        monitor_cron_executions
    fi
}

# Run main function
main 