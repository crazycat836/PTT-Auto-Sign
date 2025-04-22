# Use Python 3.11 slim image
FROM python:3.11-slim

# 需要使用者提供的環境變數 (默認為空，運行時必須提供)
ENV PTT_USERNAME="" \
    PTT_PASSWORD="" \
    TELEGRAM_BOT_TOKEN="" \
    TELEGRAM_CHAT_ID=""

# 設定時區
ENV TZ=Asia/Taipei
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        cron \
        procps \
        rsyslog \
    && rm -rf /var/lib/apt/lists/*

# 配置 cron 日誌 - 確保目錄存在
RUN mkdir -p /etc/rsyslog.d && \
    if [ -f /etc/rsyslog.d/50-default.conf ]; then \
        sed -i 's/^\s*#\?\s*cron\.\*.*$/cron.* \/var\/log\/cron.log/' /etc/rsyslog.d/50-default.conf; \
    else \
        echo 'cron.* /var/log/cron.log' > /etc/rsyslog.d/cron.conf; \
    fi

# 先複製所有必要檔案
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY scripts/ ./scripts/

# 使用pip直接安裝套件，簡化依賴安裝
RUN pip install --no-cache-dir pip setuptools wheel && \
    pip install --no-cache-dir -e . && \
    pip install --no-cache-dir telnetlib3

# Create necessary directories
RUN mkdir -p /app/data /var/log

# Make scripts executable
RUN chmod +x /app/scripts/*.sh

# Set environment variables for the application
ENV PYTHONPATH=/app \
    CRON_DATA_DIR=/app/data \
    PYTHONDONTWRITEBYTECODE=1

# 清理 __pycache__ 目錄和編譯文件
RUN find /app -name "__pycache__" -type d -exec rm -rf {} +  2>/dev/null || true && \
    find /app -name "*.pyc" -delete && \
    find /app -name "*.pyo" -delete && \
    find /app -name "*.pyd" -delete

# Print build information
RUN echo "Build info:" && \
    echo "Python version:" && python --version

# Expose port for health check
EXPOSE 8000

# Set the entrypoint
ENTRYPOINT ["/app/scripts/docker_runner.sh"] 