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

# Function to run Python test
run_python_test() {
    echo "Running Python test locally..."
    
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

    # Run the script
    echo "Running PTT Auto Sign..."
    poetry run python -B main.py
}

# Check if running in Docker
if [ -f /.dockerenv ]; then
    # Running in Docker
    echo "Running PTT Auto Sign in Docker..."
    
    # Update healthcheck file
    touch /app/data/healthcheck
    
    # Run the script
    python3 main.py
else
    # Running locally
    echo "Welcome to PTT Auto Sign"
    echo "========================"
    
    # Display system architecture information
    check_architecture
    
    # Show menu
    echo "Please select an option:"
    echo "1) Run Python test locally"
    echo "2) Build and push Docker image"
    echo "3) Exit"
    
    # Read user input
    read -p "Enter your choice (1-3): " choice
    
    # Process user choice
    case $choice in
        1)
            run_python_test
            ;;
        2)
            build_and_push_docker
            ;;
        3)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid option"
            exit 1
            ;;
    esac
fi 