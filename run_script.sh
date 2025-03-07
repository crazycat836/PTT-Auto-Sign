#!/bin/bash

# 檢查是否已安裝 poetry
if ! command -v poetry &> /dev/null; then
    echo "Poetry is not installed. Please install it first."
    echo "You can install it using:"
    echo "curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# 檢查 .env 檔案是否存在
if [ ! -f .env ]; then
    echo ".env file not found. Please create it first."
    echo "You can copy from .env.example:"
    echo "cp .env.example .env"
    exit 1
fi

# 安裝依賴
echo "Installing dependencies..."
poetry install

# 執行程式
echo "Running PTT Auto Sign..."
poetry run python main.py 