#!/bin/bash
# PTT Auto Sign Simple Runner Script
# 功能：簡單執行 PTT 自動登入和通知功能
# 用途：作為基本的執行腳本，供 cron 或其他簡單場景使用

# 設置環境變數
setup_env() {
    # Set Python environment variables
    export PYTHONDONTWRITEBYTECODE=1
    export PYTHONUNBUFFERED=1
    export PYTHONIOENCODING=utf-8
    export PYTHONWARNINGS=ignore
    export PYPTT_DISABLE_LOGS=1
    export FORCE_COLOR=1
    export PYTHONCOLORIZE=1
    export TERM=xterm-256color

    # Activate virtual environment if it exists
    if [ -f "$HOME/.poetry/env" ]; then
        source "$HOME/.poetry/env"
    fi

    # Get the directory of the script
    DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    PARENT_DIR="$( cd "$DIR/.." && pwd )"

    # Set Python path
    if [ -z "$PYTHONPATH" ]; then
        export PYTHONPATH=$PARENT_DIR
    else
        export PYTHONPATH=$PYTHONPATH:$PARENT_DIR
    fi

    # Set data directory
    if [ -z "$CRON_DATA_DIR" ]; then
        if [ -d "/app" ]; then
            # Docker environment
            export CRON_DATA_DIR="/app/data"
        else
            # Local environment
            case "$(uname -s)" in
                Linux*)
                    export CRON_DATA_DIR="/tmp/pttautosign/data"
                    ;;
                Darwin*)
                    export CRON_DATA_DIR="/tmp/pttautosign/data"
                    ;;
                CYGWIN*|MINGW*|MSYS*)
                    export CRON_DATA_DIR="$HOME/AppData/Local/pttautosign/data"
                    ;;
                *)
                    export CRON_DATA_DIR="/tmp/pttautosign/data"
                    ;;
            esac
        fi
        mkdir -p "$CRON_DATA_DIR"
    fi

    # Log script start with timestamp
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Simple runner started (TEST_MODE=${TEST_MODE:-false}, CRON_MODE=${CRON_MODE:-false})"
}

# 執行 PTT 登入和通知
run_ptt_login() {
    # Check if poetry is installed
    if ! command -v poetry &> /dev/null; then
        echo "Poetry is not installed. Please install it first."
        echo "You can install it using:"
        echo "curl -sSL https://install.python-poetry.org | python3 -"
        exit 1
    fi

    # Check if .env file exists
    if [ ! -f "$PARENT_DIR/.env" ]; then
        echo ".env file not found. Please create it first."
        echo "You can copy from .env.example:"
        echo "cp .env.example .env"
        exit 1
    fi

    # Run login test with notification
    echo "Running PTT login and notification..."
    cd "$PARENT_DIR"
    
    # Determine whether to send Telegram notification based on TEST_MODE
    if [ "$TEST_MODE" = "true" ]; then
        # In test mode, only run login test without notification
        login_output=$(poetry run python -W ignore src/pttautosign/main.py --test-login 2>&1 | grep -v "^\[.*\]\[PyPtt\]")
    else
        # In normal mode, run both login test and notification
        login_output=$(poetry run python -W ignore src/pttautosign/main.py --test-login --test-notification 2>&1 | grep -v "^\[.*\]\[PyPtt\]")
    fi
    login_status=$?
    
    # Filter and display the output (removing redundant messages)
    filtered_output=$(echo "$login_output" | grep -v "登入測試完成\|登入成功：\|登入失敗：")
    echo "$filtered_output"
    
    # Extract login statistics
    successful_logins=$(echo "$login_output" | grep -o "登入成功：[0-9]*" | grep -o "[0-9]*")
    failed_logins=$(echo "$login_output" | grep -o "登入失敗：[0-9]*" | grep -o "[0-9]*")
    total_accounts=$((successful_logins + failed_logins))
    
    # Display consolidated login result
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 登入測試完成: 總共 $total_accounts 個帳號, 成功 $successful_logins, 失敗 $failed_logins"
    
    # Log the execution status
    if [ $login_status -eq 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] PTT Auto Sign executed successfully"
        
        # Add test result to log
        if [ "$TEST_MODE" = "true" ]; then
            test_result="🧪 PTT Auto Sign Test\n\n✅ Login test completed successfully\nAccounts: $total_accounts\nSuccessful: $successful_logins"
            echo -e "$test_result"
        fi
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] PTT Auto Sign execution failed with status $login_status"
        
        # Add test failure to log
        if [ "$TEST_MODE" = "true" ]; then
            test_result="🧪 PTT Auto Sign Test\n\n❌ Login test failed\nAccounts: $total_accounts\nSuccessful: $successful_logins"
            echo -e "$test_result"
        fi
    fi

    # Update execution count if in test mode
    if [ "$TEST_MODE" = "true" ]; then
        if [ -f "$CRON_DATA_DIR/execution_count" ]; then
            count=$(cat "$CRON_DATA_DIR/execution_count")
            new_count=$((count + 1))
            echo $new_count > "$CRON_DATA_DIR/execution_count"
            echo "Test execution $new_count of 5 completed"
            
            # If this is the last execution, log it
            if [ $new_count -ge 5 ]; then
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] All test executions completed"
            fi
        else
            # Initialize counter if it doesn't exist
            echo "1" > "$CRON_DATA_DIR/execution_count"
            echo "Test execution 1 of 5 completed"
        fi
    fi
}

# 主函數
main() {
    setup_env
    run_ptt_login
}

# 執行主函數
main 