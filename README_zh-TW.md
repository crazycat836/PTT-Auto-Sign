# PTT Auto Sign

[![License](https://img.shields.io/github/license/crazycat836/ptt-auto-sign?style=for-the-badge&color=5D6D7E)](LICENSE)
[![Issues](https://img.shields.io/github/issues/crazycat836/ptt-auto-sign?style=for-the-badge&color=5D6D7E)](https://github.com/crazycat836/ptt-auto-sign/issues)
[![Release](https://img.shields.io/github/v/release/crazycat836/ptt-auto-sign?style=for-the-badge&color=5D6D7E)](https://github.com/crazycat836/ptt-auto-sign/releases)
[![Python Version](https://img.shields.io/badge/Python-3.11-5D6D7E?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Docker Pulls](https://img.shields.io/docker/pulls/crazycat836/pttautosign?style=for-the-badge&color=5D6D7E)](https://hub.docker.com/r/crazycat836/pttautosign)

[English](README.md) | 繁體中文

PTT Auto Sign 是一個自動化的 PTT (BBS) 簽到工具，支援 Telegram 通知功能。透過 Docker 容器化部署，讓你輕鬆實現每日自動簽到，再也不用擔心漏簽。

## 🌟 主要特點

- 🔄 支援 PTT 帳號自動簽到
- 📱 整合 Telegram 通知，即時掌握簽到狀態
- 🐳 Docker 容器化支援，部署更加便捷
- 🎲 每日隨機執行時間（上午 9 點至下午 5 點）
- 📝 完整的日誌記錄系統
- ⚙️ 彈性的環境變數配置
- 🔒 安全的帳號管理機制
- 🐍 支援 Python 3.11
- 🌏 完整中文化介面，包含日誌和通知訊息
- 🏗️ 模組化架構設計，提高可維護性

## 🚀 快速開始

### 使用 Docker（推薦）

1. 拉取 Docker 映像：
   ```bash
   docker pull crazycat836/pttautosign:latest
   ```

2. 運行容器：
   ```bash
   # 選項 1：直接使用環境變數（生產模式 - 每天執行一次）
   docker run -d \
     --name ptt-auto-sign \
     --restart unless-stopped \
     -e PTT_USERNAME=你的用戶名 \
     -e PTT_PASSWORD=你的密碼 \
     -e TELEGRAM_BOT_TOKEN=你的Bot令牌 \
     -e TELEGRAM_CHAT_ID=你的聊天ID \
     crazycat836/pttautosign:latest
     
   # 選項 2：使用測試模式（每分鐘執行一次，共3次）
   docker run -d \
     --name ptt-auto-sign-test \
     --restart unless-stopped \
     -e PTT_USERNAME=你的用戶名 \
     -e PTT_PASSWORD=你的密碼 \
     -e TELEGRAM_BOT_TOKEN=你的Bot令牌 \
     -e TELEGRAM_CHAT_ID=你的聊天ID \
     -e TEST_MODE=true \
     crazycat836/pttautosign:latest
   ```

### Docker 運行模式

容器支援兩種運行模式：

1. **生產模式**（預設）：容器每天在上午9點到下午5點之間的隨機時間執行一次（台灣時間）。
2. **測試模式**：容器每分鐘執行一次，共執行3次，適用於測試您的設置。

在任一模式下，容器都會：
1. **驗證憑證**：在設置 cron 任務前，先執行一次登入測試和通知，確保設置正確
2. **設置 cron 任務**：根據所選模式設置相應的排程
3. **保持運行**：監控並執行排程任務

查看容器日誌：
```bash
docker logs -f ptt-auto-sign
```

### 本地開發

1. 安裝 Python 3.11+ 和 Poetry：
   ```bash
   # macOS
   brew install python@3.11 poetry
   
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3.11
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. 安裝專案依賴：
   ```bash
   poetry install
   ```

3. 設定環境變數：
   ```bash
   # PTT 帳號設定
   export PTT_USERNAME="你的用戶名"
   export PTT_PASSWORD="你的密碼"
   
   # Telegram 設定
   export TELEGRAM_BOT_TOKEN="你的Bot令牌"
   export TELEGRAM_CHAT_ID="你的聊天ID"
   ```

4. 執行程式：
   ```bash
   # 僅測試登入
   python -m pttautosign.main --test-login
   
   # 正常執行
   python -m pttautosign.main
   ```

## ⚙️ 環境變數設定

### 必要設定
| 變數名稱 | 說明 | 必填 | 範例 |
|---------|------|------|------|
| PTT_USERNAME | PTT 帳號用戶名 | ✅ | your_username |
| PTT_PASSWORD | PTT 帳號密碼 | ✅ | your_password |
| TELEGRAM_BOT_TOKEN | Telegram Bot Token | ✅ | 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz |
| TELEGRAM_CHAT_ID | 通知訊息接收群組/頻道 ID | ✅ | -1001234567890 |

### 選用設定
| 變數名稱 | 說明 | 預設值 | 範例 |
|---------|------|--------|------|
| TEST_MODE | 啟用測試模式 | false | true |
| DEBUG_MODE | 啟用詳細日誌 | false | true |
| RANDOM_DAILY_TIME | 每天產生新隨機時間 | true | false |
| DISABLE_NOTIFICATIONS | 停用 Telegram 通知 | false | true |

## 📝 日誌系統

### 日誌等級
- INFO：一般執行資訊
- WARNING：警告訊息
- ERROR：錯誤訊息
- DEBUG：除錯資訊（當 DEBUG_MODE=true 時）

所有日誌輸出為彩色格式，並使用中文顯示，提高可讀性。系統不會在本地創建日誌檔案。

## 🛠️ 開發

### 程式碼格式化

專案使用 Black 和 isort 進行程式碼格式化：

```bash
# 使用 Black 格式化程式碼
poetry run black .

# 使用 isort 排序 import 語句
poetry run isort .
```

## 🏗️ 專案結構

```
pttautosign/
├── __init__.py            # 套件元數據
├── main.py                # 主程式進入點
├── patches/
│   └── pyptt_patch.py     # PyPtt 相容性修補
├── utils/
│   ├── app_context.py     # 應用程式上下文
│   ├── config.py          # 配置類別
│   ├── factory.py         # 服務工廠
│   ├── interfaces.py      # 服務接口
│   ├── logger.py          # 日誌配置
│   ├── ptt.py             # PTT 自動簽到功能
│   └── telegram.py        # Telegram 通知功能
├── Dockerfile             # Docker 配置
├── pyproject.toml         # 專案元數據和依賴
└── scripts/
    └── docker_runner.sh   # Docker 入口腳本
```

## ❗️ 故障排除

### 常見問題

1. Docker 容器無法啟動
   - 檢查環境變數是否正確設定
   - 確認 Docker 服務是否正常運行
   - 查看容器日誌：`docker logs ptt-auto-sign`

2. 簽到失敗
   - 確認 PTT 帳號密碼是否正確
   - 檢查網路連線狀態
   - 查看程式日誌檔案

3. Telegram 通知未收到
   - 確認 bot_token 是否有效
   - 檢查 chat_id 是否正確
   - 確認 Bot 是否已加入群組/頻道

## 🤝 貢獻指南

我們歡迎任何形式的貢獻！如果你想要協助改善這個專案，可以：

1. Fork 這個專案
2. 建立你的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟一個 Pull Request

## 📄 授權條款

本專案採用 Apache License 2.0 授權 - 詳見 [LICENSE](LICENSE) 檔案。

此授權允許你自由使用、修改和分發本軟體，包括商業用途，但需要包含原始版權聲明和授權文字。

## 📝 更新日誌

詳細的更新記錄請參考 [CHANGELOG.md](CHANGELOG.md)。 