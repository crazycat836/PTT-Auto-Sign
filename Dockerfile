# 第一階段：構建環境
FROM python:3.11-alpine AS builder

WORKDIR /app

# 編譯型相依套件可能需要的建構工具（僅存在於 builder 階段，不進入最終 image）
RUN apk add --no-cache build-base

# 複製專案檔案
COPY pyproject.toml README.md ./
COPY src/ ./src/

# 將套件與相依安裝到獨立 prefix，方便整包複製到最終 image
# 只裝 pyproject 宣告的東西。用 pip 另外塞套件會讓它不在 poetry.lock 也不在
# GitHub 的相依圖裡，等於沒有人在幫它看資安更新。
# （原本這裡多裝了 telnetlib3：PyPtt 預設走 WEBSOCKETS，且 PTT1/PTT2 這兩個
#   host 根本不接受 TELNET 模式，本專案也沒有指定 connect_mode，用不到。）
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install .

# 第二階段：執行環境
FROM python:3.11-alpine

# OCI image labels — surfaced on Docker Hub.
LABEL org.opencontainers.image.title="PTTAutoSign" \
      org.opencontainers.image.description="Automatically sign in to PTT BBS daily and report via Telegram." \
      org.opencontainers.image.source="https://github.com/crazycat836/PTTAutoSign" \
      org.opencontainers.image.licenses="Apache-2.0"

# 需要使用者提供的環境變數 (默認為空，運行時必須提供)
ENV PTT_USERNAME="" \
    PTT_PASSWORD="" \
    TELEGRAM_BOT_TOKEN="" \
    TELEGRAM_CHAT_ID=""

# 設定時區
ENV TZ=Asia/Taipei

# 執行時必要的系統依賴：
#   - bash：docker_runner.sh 使用 bash 專屬語法（alpine 預設只有 ash）
#   - tzdata：提供 /usr/share/zoneinfo 以套用 Asia/Taipei
#   - ca-certificates：HTTPS（Telegram / PTT）TLS 驗證
# 排程改由腳本內建 sleep loop 處理，不再安裝 cron。
RUN apk add --no-cache bash tzdata ca-certificates \
    && cp /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo "$TZ" > /etc/timezone \
    && mkdir -p /app/data

# 設定工作目錄
WORKDIR /app

# 從建構環境複製已安裝的 Python 套件（含 pttautosign 與相依）
COPY --from=builder /install /usr/local

# 複製腳本並設定執行權限（root-only 0700，避免他人讀取/執行）
COPY scripts/ ./scripts/
RUN chmod 0700 /app/scripts/*.sh

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1

# 清理不必要的檔案
RUN find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true \
    && find /app -name "*.pyc" -delete

# 設定入口點
ENTRYPOINT ["/app/scripts/docker_runner.sh"]
