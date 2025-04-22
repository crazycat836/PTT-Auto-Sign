# 第一階段：構建環境
FROM python:3.11-slim AS builder

# 設定工作目錄
WORKDIR /app

# 安裝構建依賴
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製專案檔案
COPY pyproject.toml README.md ./
COPY src/ ./src/

# 安裝 Python 依賴
RUN pip install --no-cache-dir pip setuptools wheel && \
    pip install --no-cache-dir -e . && \
    pip install --no-cache-dir telnetlib3

# 第二階段：執行環境
FROM python:3.11-slim

# 需要使用者提供的環境變數 (默認為空，運行時必須提供)
ENV PTT_USERNAME="" \
    PTT_PASSWORD="" \
    TELEGRAM_BOT_TOKEN="" \
    TELEGRAM_CHAT_ID=""

# 設定時區
ENV TZ=Asia/Taipei
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 設定工作目錄
WORKDIR /app

# 安裝運行時必要的系統依賴
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        cron \
        procps \
        rsyslog \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /etc/rsyslog.d /app/data /var/log \
    && if [ -f /etc/rsyslog.d/50-default.conf ]; then \
        sed -i 's/^\s*#\?\s*cron\.\*.*$/cron.* \/var\/log\/cron.log/' /etc/rsyslog.d/50-default.conf; \
    else \
        echo 'cron.* /var/log/cron.log' > /etc/rsyslog.d/cron.conf; \
    fi

# 從建構環境複製 Python 套件和應用程式程式碼
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /app/src/ /app/src/

# 複製腳本並設定執行權限
COPY scripts/ ./scripts/
RUN chmod +x /app/scripts/*.sh

# 設定環境變數
ENV PYTHONPATH=/app \
    CRON_DATA_DIR=/app/data \
    PYTHONDONTWRITEBYTECODE=1

# 清理不必要的檔案
RUN find /app -name "__pycache__" -type d -exec rm -rf {} +  2>/dev/null || true && \
    find /app -name "*.pyc" -delete && \
    find /app -name "*.pyo" -delete && \
    find /app -name "*.pyd" -delete

# 暴露健康檢查端口
EXPOSE 8000

# 設定入口點
ENTRYPOINT ["/app/scripts/docker_runner.sh"] 