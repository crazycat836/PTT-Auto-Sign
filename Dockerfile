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

# 執行時必須提供的環境變數（用 -e 或 --env-file 傳入，不在此宣告）：
#   PTT_USERNAME、PTT_PASSWORD、TELEGRAM_BOT_TOKEN、TELEGRAM_CHAT_ID
#
# 這裡刻意不寫 ENV FOO=""。把憑證類變數宣告在 Dockerfile 裡會觸發 buildkit 的
# SecretsUsedInArgOrEnv 警告，而且宣告成空字串沒有任何好處：
# docker_runner.sh 用 [ -z "$VAR" ] 檢查，對「未設定」與「設為空字串」行為相同。

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

# 移除只在安裝階段用得到的打包工具。python:3.11-alpine 的 base image 自帶
# setuptools（目前是 79.0.1），它不在 poetry.lock 也不在 GitHub 相依圖裡，
# 沒有人會幫它看資安更新——留著只是無人看管的表面積。
# 已確認 site-packages 裡只有 wheel 自己會 import 它，執行期相依都不碰。
RUN python -m pip uninstall -y setuptools pip wheel 2>/dev/null || true \
    && rm -rf /usr/local/lib/python3.11/site-packages/setuptools \
              /usr/local/lib/python3.11/site-packages/setuptools-* \
              /usr/local/lib/python3.11/site-packages/pkg_resources \
              /usr/local/lib/python3.11/site-packages/_distutils_hack \
              /usr/local/lib/python3.11/site-packages/distutils-precedence.pth \
              /usr/local/lib/python3.11/site-packages/pip \
              /usr/local/lib/python3.11/site-packages/pip-* \
              /usr/local/lib/python3.11/site-packages/wheel \
              /usr/local/lib/python3.11/site-packages/wheel-* \
              /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/bin/pip3.11 \
              /usr/local/bin/wheel

# 清理不必要的檔案
RUN find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true \
    && find /app -name "*.pyc" -delete

# 設定入口點
ENTRYPOINT ["/app/scripts/docker_runner.sh"]
