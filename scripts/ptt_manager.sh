#!/bin/bash
# PTT Auto Sign Manager Script
# 功能：提供完整的 PTT 自動登入、通知和測試功能
# 包含：單次測試、cron 測試、Docker 測試和映像構建

# Function to setup environment variables
setup_environment() {
    # Set Python environment variables
    export PYTHONDONTWRITEBYTECODE=1
    export PYTHONUNBUFFERED=1
    export PYTHONIOENCODING=utf-8
    export PYTHONWARNINGS=ignore
    export PYPTT_DISABLE_LOGS=1
    export FORCE_COLOR=1
    export PYTHONCOLORIZE=1
    export TERM=xterm-256color

    # Set data directory based on OS
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

    # Create data directory if it doesn't exist
    mkdir -p "$CRON_DATA_DIR"

    # Set Python path
    if [ -z "$PYTHONPATH" ]; then
        export PYTHONPATH=$(pwd)
    else
        export PYTHONPATH=$PYTHONPATH:$(pwd)
    fi
}

# Function to log debug messages
log_debug() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[DEBUG] [$timestamp] $message"
}

# Function to check system architecture and OS
check_system() {
    # Skip system check in cron mode
    if [ "$CRON_MODE" = "true" ]; then
        return
    fi

    local arch=$(uname -m)
    local os=$(uname -s)
    
    log_debug "System Information:"
    log_debug "Operating System: $os"
    log_debug "Architecture: $arch"
    
    case "$os" in
        Linux*)
            export OS_TYPE="linux"
            log_debug "Running on Linux"
            ;;
        Darwin*)
            export OS_TYPE="macos"
            log_debug "Running on macOS"
            ;;
        CYGWIN*|MINGW*|MSYS*)
            export OS_TYPE="windows"
            log_debug "Running on Windows"
            ;;
        *)
            export OS_TYPE="unknown"
            log_debug "Running on unknown OS"
            ;;
    esac
    log_debug "-------------------"
}

# Function to test login and Telegram notification
test_login_and_notification() {
    log_debug "Starting login and Telegram notification test..."
    
    # Call simple_runner.sh to perform the actual login and notification
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    bash "$SCRIPT_DIR/simple_runner.sh"
    
    log_debug "Login and notification test completed"
}

# Function to test login, notification and cron
test_with_cron() {
    log_debug "Starting cron test setup..."
    
    # Set test mode environment variable
    export TEST_MODE=true
    export CRON_MODE=true
    export DIRECT_EXEC=true
    
    # Get the script directory
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    
    # Call random_cron.sh to handle cron functionality
    log_debug "Calling random_cron.sh to handle cron test..."
    bash "$SCRIPT_DIR/docker/random_cron.sh"
}

# Function to run Docker test
run_docker_test() {
    log_debug "Starting Docker test..."
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        log_debug "Error: .env file not found"
        echo "Error: .env file not found!"
        echo "Please create it from .env.example"
        exit 1
    fi
    
    # Read values from .env file
    log_debug "Reading values from .env file..."
    
    # Source the .env file to get variables
    source <(grep -v '^#' .env | sed -E 's/(.*)=(.*)$/export \1="\2"/')
    
    # Build Docker image for testing
    log_debug "Building Docker image for testing using src/pttautosign/docker/Dockerfile..."
    docker build -t pttautosign:test -f src/pttautosign/docker/Dockerfile .
    
    # Run Docker container with cron enabled in test mode
    log_debug "Starting container with cron enabled (test mode)..."
    echo "Docker container will run in test mode (5 executions, once per minute)"
    echo "You can check the logs in the Docker container output"
    
    # Remove existing container if it exists
    docker rm -f pttautosign-test 2>/dev/null || true
    
    # Extract PTT credentials from ptt_id_1
    IFS=',' read -r ptt_id ptt_password <<< "${ptt_id_1:-none,none}"
    
    # Run container with test mode enabled
    docker run -d --name pttautosign-test \
        -e PTT_ID="$ptt_id" \
        -e PTT_PASSWORD="$ptt_password" \
        -e TELEGRAM_BOT_TOKEN="${bot_token:-}" \
        -e TELEGRAM_CHAT_ID="${chat_id:-}" \
        -e TEST_MODE=true \
        -e ENABLE_CRON=true \
        -e DIRECT_EXEC=true \
        -e PYTHONDONTWRITEBYTECODE=1 \
        -e PYTHONUNBUFFERED=1 \
        -e PYPTT_DISABLE_LOGS=1 \
        pttautosign:test
    
    # Follow container logs
    echo "Following container logs (press Ctrl+C to stop):"
    docker logs -f pttautosign-test
    
    # Clean up container after test
    docker rm -f pttautosign-test 2>/dev/null || true
}

# Function to build and push Docker image
build_and_push_docker() {
    log_debug "Building and pushing Docker image..."
    log_debug "This will build for both AMD64 and ARM64 architectures"
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_debug "Error: Docker is not installed"
        echo "Error: Docker is not installed"
        exit 1
    fi
    
    # Find Dockerfile path
    DOCKERFILE_PATH="src/pttautosign/docker/Dockerfile"
    if [ ! -f "$DOCKERFILE_PATH" ]; then
        log_debug "Error: Dockerfile not found at $DOCKERFILE_PATH"
        echo "Error: Dockerfile not found at $DOCKERFILE_PATH"
        exit 1
    fi
    
    # Check if .env file exists for credentials
    if [ ! -f ".env" ]; then
        log_debug "Warning: .env file not found, continuing anyway"
        echo "Warning: .env file not found"
        echo "The Docker image will be built, but you will need to provide credentials when running it"
    else
        log_debug "Using credentials from .env file"
    fi
    
    echo "This will build a production Docker image that runs once per day at a random time"
    echo "between 9 AM and 5 PM (Taiwan time)."
    read -p "Continue? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        log_debug "Build cancelled by user"
        echo "Build cancelled"
        return
    fi
    
    # Build and push multi-arch image with production mode environment variables
    if docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --build-arg TEST_MODE=false \
        --build-arg ENABLE_CRON=true \
        --build-arg DIRECT_EXEC=false \
        -t crazycat836/pttautosign:latest \
        -f "$DOCKERFILE_PATH" \
        --push .; then
        
        log_debug "Successfully built and pushed Docker image"
        echo "Successfully built and pushed Docker image"
        echo "Image: crazycat836/pttautosign:latest"
        echo "This image will run once per day at a random time between 9 AM and 5 PM (Taiwan time)"
        echo ""
        echo "To run the image, use:"
        echo "docker run -d --name pttautosign \\"
        echo "    -e PTT_ID=your_ptt_id \\"
        echo "    -e PTT_PASSWORD=your_ptt_password \\"
        echo "    -e TELEGRAM_BOT_TOKEN=your_telegram_bot_token \\"
        echo "    -e TELEGRAM_CHAT_ID=your_telegram_chat_id \\"
        echo "    -e TEST_MODE=false \\"
        echo "    -e ENABLE_CRON=true \\"
        echo "    crazycat836/pttautosign:latest"
    else
        log_debug "Error: Failed to build and push Docker image"
        echo "Error: Failed to build and push Docker image"
        exit 1
    fi
}

# Main menu
echo "Welcome to PTT Auto Sign"
echo "========================"

# Initialize environment
setup_environment
check_system

# Check if running in cron mode
if [ "$1" = "run_cron" ]; then
    # This mode is deprecated, use simple_runner.sh directly
    log_debug "Warning: run_cron mode is deprecated, redirecting to simple_runner.sh"
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    bash "$SCRIPT_DIR/simple_runner.sh"
    exit 0
fi

# Show menu
echo "Please select an option:"
echo "1) Test login and Telegram notification"
echo "2) Test login, notification and cron job (runs every minute for 5 times)"
echo "3) Run Docker test with cron (runs every minute for 5 times)"
echo "4) Build and push Docker image (runs once per day at random time)"
echo "5) Exit"

# Read user input
read -p "Enter your choice (1-5): " choice

# Process user choice
case $choice in
    1)
        test_login_and_notification
        ;;
    2)
        test_with_cron
        ;;
    3)
        run_docker_test
        ;;
    4)
        build_and_push_docker
        ;;
    5)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac 