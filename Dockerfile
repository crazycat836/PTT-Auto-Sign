# 第一階段：構建環境
FROM python:3.11-alpine AS builder

WORKDIR /app

# 編譯型相依套件可能需要的建構工具（僅存在於 builder 階段，不進入最終 image）
RUN apk add --no-cache build-base

# 複製專案檔案
COPY pyproject.toml poetry.lock README.md ./
COPY src/ ./src/

# 將套件與相依安裝到獨立 prefix，方便整包複製到最終 image
# 只裝 pyproject 宣告的東西。用 pip 另外塞套件會讓它不在 poetry.lock 也不在
# GitHub 的相依圖裡，等於沒有人在幫它看資安更新。
# （原本這裡多裝了 telnetlib3：PyPtt 預設走 WEBSOCKETS，且 PTT1/PTT2 這兩個
#   host 根本不接受 TELNET 模式，本專案也沒有指定 connect_mode，用不到。）
#
# 相依版本照 poetry.lock 裝，不在 build 當下重新解析。直接 `pip install .`
# 會抓「build 當下最新的相容版本」，裝出來的東西跟 CI 測過、Dependabot 在維護的
# lock 對不上，而且每次 build 都可能不一樣。這裡先把 lock 匯出成含 hash 的
# requirements，用 --require-hashes 逐一核對檔案雜湊，再以 --no-deps 裝本專案。
# lock 與 pyproject 對不起來時 poetry export 會直接失敗，不會默默裝出別的版本。
#
# Poetry 裝在獨立的 venv，只存在於 builder 階段；版本與 CI
# （.github/workflows/ci.yml）一致，要升級時兩邊一起改。不能跟系統環境混裝：
# Poetry 自己也依賴 requests、certifi、urllib3，混在一起時 pip 用 --prefix
# 安裝會判定這些「已經裝過」而跳過，/install 就少了它們，image 跑不起來。
# --ignore-installed 是同一個用意：不管 builder 的系統環境已有什麼，lock 裡的
# 每個執行期套件都要實際裝進 /install。
RUN pip install --no-cache-dir --upgrade pip \
    && python -m venv /opt/poetry \
    && /opt/poetry/bin/pip install --no-cache-dir "poetry==2.4.1" "poetry-plugin-export==1.10.1" \
    && /opt/poetry/bin/poetry export --only main --format requirements.txt --output /tmp/requirements.txt \
    && pip install --no-cache-dir --prefix=/install --ignore-installed --require-hashes -r /tmp/requirements.txt \
    && pip install --no-cache-dir --prefix=/install --no-deps .

# 第二階段：執行環境
FROM python:3.11-alpine

# OCI image labels — surfaced on Docker Hub.
LABEL org.opencontainers.image.title="PTTAutoSign" \
      org.opencontainers.image.description="Automatically sign in to PTT BBS daily and report via Telegram." \
      org.opencontainers.image.source="https://github.com/crazycat836/PTT-Auto-Sign" \
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

# 設定環境變數
# 要排在下面的清理步驟之前：base image 已把 .pyc 全數刪掉，清理時執行的
# `python -m pip` 若沒有這個設定，會重新寫出約 6 MB 的 .pyc 進 image。
ENV PYTHONDONTWRITEBYTECODE=1

# 移除只在安裝階段用得到的打包工具。python:3.11-alpine 的 base image 自帶
# setuptools（目前是 79.0.1）、pip、wheel，以及 wheel 帶進來的 packaging
# （目前是 26.3）。它們不在 poetry.lock 也不在 GitHub 相依圖裡，沒有人會幫它們
# 看資安更新——留著只是無人看管的表面積。
# 已確認執行期相依沒有任何一個會 import setuptools 或 packaging
# （base image 裡用到它們的只有這幾個打包工具自己）。
#
# 這一步刻意排在複製 /install 之前：日後若 lock 裡的執行期相依真的需要其中
# 某個套件，它會跟著 /install 複製進來，不會被這裡誤刪。
RUN python -m pip uninstall -y setuptools pip wheel packaging 2>/dev/null || true \
    && rm -rf /usr/local/lib/python3.11/site-packages/setuptools \
              /usr/local/lib/python3.11/site-packages/setuptools-* \
              /usr/local/lib/python3.11/site-packages/pkg_resources \
              /usr/local/lib/python3.11/site-packages/_distutils_hack \
              /usr/local/lib/python3.11/site-packages/distutils-precedence.pth \
              /usr/local/lib/python3.11/site-packages/pip \
              /usr/local/lib/python3.11/site-packages/pip-* \
              /usr/local/lib/python3.11/site-packages/wheel \
              /usr/local/lib/python3.11/site-packages/wheel-* \
              /usr/local/lib/python3.11/site-packages/packaging \
              /usr/local/lib/python3.11/site-packages/packaging-* \
              /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/bin/pip3.11 \
              /usr/local/bin/wheel

# 設定工作目錄
WORKDIR /app

# 從建構環境複製已安裝的 Python 套件（含 pttautosign 與相依）
COPY --from=builder /install /usr/local

# 複製腳本並設定執行權限（root-only 0700，避免他人讀取/執行）
COPY scripts/ ./scripts/
RUN chmod 0700 /app/scripts/*.sh

# 清理不必要的檔案
RUN find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true \
    && find /app -name "*.pyc" -delete

# 設定入口點
ENTRYPOINT ["/app/scripts/docker_runner.sh"]
