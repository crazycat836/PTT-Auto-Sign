#!/bin/bash

# Set Python environment variable to prevent __pycache__ creation
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

# Function to check system architecture
check_architecture() {
    local arch=$(uname -m)
    local os=$(uname -s)
    
    echo "System Information:"
    echo "Operating System: $os"
    echo "Architecture: $arch"
    
    case "$arch" in
        "x86_64")
            echo "Running on AMD64/x86_64 architecture"
            ;;
        "arm64" | "aarch64")
            echo "Running on ARM64 architecture"
            ;;
        *)
            echo "Warning: Running on unsupported architecture: $arch"
            ;;
    esac
    echo "-------------------"
}

# Function to test login and Telegram notification
test_login_and_notification() {
    echo "Testing login and Telegram notification..."
    
    # Check if poetry is installed
    if ! command -v poetry &> /dev/null; then
        echo "Poetry is not installed. Please install it first."
        echo "You can install it using:"
        echo "curl -sSL https://install.python-poetry.org | python3 -"
        exit 1
    fi

    # Check if .env file exists
    if [ ! -f .env ]; then
        echo ".env file not found. Please create it first."
        echo "You can copy from .env.example:"
        echo "cp .env.example .env"
        exit 1
    fi

    # Install dependencies
    echo "Installing dependencies..."
    poetry install

    # Run login test without notification
    echo "Running login test without Telegram notification..."
    poetry run python -W ignore src/pttautosign/main.py --test-login
}

# Function to test login, notification and cron
test_with_cron() {
    echo "Testing login, notification and cron job..."
    
    # First run the login and notification test
    test_login_and_notification
    
    # Now set up a temporary cron job for testing
    echo "Setting up a test cron job (will run in 1 minute)..."
    
    # Get absolute path of this script
    local script_path=$(readlink -f "$0")
    local temp_script="/tmp/ptt_test_cron.sh"
    
    # Create a temporary script that will run the test
    cat > "$temp_script" << EOF
#!/bin/bash
cd "$(dirname "$script_path")/.."
echo "\$(date): PTT Auto Sign cron test executed" >> /tmp/ptt_cron_test.log
poetry run python -W ignore src/pttautosign/main.py --test-login --test-notification > /tmp/ptt_cron_output.log 2>&1
EOF
    
    chmod +x "$temp_script"
    
    # Add temporary cron job to run in 1 minute
    (crontab -l 2>/dev/null; echo "$(date -d '+1 minute' '+%M %H %d %m *') $temp_script") | crontab -
    
    echo "Temporary cron job set to run in 1 minute"
    echo "You can check the log at: /tmp/ptt_cron_test.log"
    echo "Cron output will be saved to: /tmp/ptt_cron_output.log"
    echo ""
    echo "To verify cron is working, wait at least 1 minute and then check the logs"
    echo "You can remove the temporary cron job with: crontab -r"
}

# Function to run Docker test
run_docker_test() {
    echo "Running Docker test with cron..."
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        echo "Error: Docker is not installed"
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        echo "Error: .env file not found!"
        echo "Please create it from .env.example"
        exit 1
    fi
    
    # Build the image
    echo "Building Docker image..."
    docker build -t pttautosign:test -f docker/Dockerfile .
    
    # Run the container with cron enabled
    echo "Starting container with cron enabled..."
    docker run --rm -it \
        --env-file .env \
        -e "ENABLE_CRON=true" \
        -e "CRON_SCHEDULE=* * * * *" \
        pttautosign:test
}

# Function to build and push Docker image
build_and_push_docker() {
    echo "Building and pushing Docker image..."
    echo "This will build for both AMD64 and ARM64 architectures"
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        echo "Error: Docker is not installed"
        exit 1
    fi
    
    # Build and push multi-arch image
    if docker buildx build --platform linux/amd64,linux/arm64 -t crazycat836/pttautosign:latest --push .; then
        echo "Successfully built and pushed Docker image"
        echo "Image: crazycat836/pttautosign:latest"
    else
        echo "Error: Failed to build and push Docker image"
        exit 1
    fi
}

# Main menu
echo "Welcome to PTT Auto Sign"
echo "========================"

# Display system architecture information
check_architecture

# Show menu
echo "Please select an option:"
echo "1) Test login and Telegram notification"
echo "2) Test login, notification and cron job"
echo "3) Run Docker test with cron"
echo "4) Build and push Docker image"
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