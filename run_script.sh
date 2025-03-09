#!/bin/bash

# Set Python environment variable to prevent __pycache__ creation
export PYTHONDONTWRITEBYTECODE=1

# Check if running in Docker
if [ -f /.dockerenv ]; then
    # Running in Docker
    echo "Running PTT Auto Sign in Docker..."
    python main.py
else
    # Running locally
    echo "Running PTT Auto Sign locally..."

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
fi 