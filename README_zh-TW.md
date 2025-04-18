# PTT Auto Sign

[![License](https://img.shields.io/github/license/crazycat836/ptt-auto-sign?style=for-the-badge&color=5D6D7E)](LICENSE)
[![Issues](https://img.shields.io/github/issues/crazycat836/ptt-auto-sign?style=for-the-badge&color=5D6D7E)](https://github.com/crazycat836/ptt-auto-sign/issues)
[![Release](https://img.shields.io/github/v/release/crazycat836/ptt-auto-sign?style=for-the-badge&color=5D6D7E)](https://github.com/crazycat836/ptt-auto-sign/releases)
[![Python Version](https://img.shields.io/badge/Python-3.11-5D6D7E?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Docker Pulls](https://img.shields.io/docker/pulls/crazycat836/pttautosign?style=for-the-badge&color=5D6D7E)](https://hub.docker.com/r/crazycat836/pttautosign)

[English](README.md) | 繁體中文

PTT Auto Sign 是一個自動化的 PTT (BBS) 簽到工具，支援多帳號管理和 Telegram 通知功能。透過 Docker 容器化部署，讓你輕鬆實現每日自動簽到，再也不用擔心漏簽。

## 🌟 主要特點

- 🔄 支援多個 PTT 帳號自動簽到
- 📱 整合 Telegram 通知，即時掌握簽到狀態
- 🐳 Docker 容器化支援，部署更加便捷
- 🎲 每日隨機執行時間（上午 9 點至下午 5 點）
- 📝 完整的日誌記錄系統
- ⚙️ 彈性的環境變數配置
- 🔒 安全的帳號管理機制
- 🐍 支援 Python 3.11
- 🏗️ 模組化架構設計，提高可維護性

## 🚀 快速開始

### 使用 Docker（推薦）

1. 拉取 Docker 映像：
   ```bash
   docker pull crazycat836/pttautosign:latest
   ```

2. 準備環境變數檔案：
   ```bash
   # 複製範例檔案
   cp .env.example .env
   
   # 編輯 .env 檔案，填入你的設定
   vim .env
   ```

3. 運行容器：
   ```bash
   # 選項 1：直接使用環境變數
   docker run -d \
     --name ptt-auto-sign \
     --restart unless-stopped \
     -e PTT_USERNAME=你的用戶名 \
     -e PTT_PASSWORD=你的密碼 \
     -e TELEGRAM_BOT_TOKEN=你的Bot令牌 \
     -e TELEGRAM_CHAT_ID=你的聊天ID \
     crazycat836/pttautosign:latest
     
   # 選項 2：使用 .env 檔案
   docker run -d \
     --name ptt-auto-sign \
     --restart unless-stopped \
     --env-file .env \
     crazycat836/pttautosign:latest
   ```

### 本地開發

1. 安裝 Python 3.13+ 和 Poetry：
   ```bash
   # macOS
   brew install python@3.13 poetry
   
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3.13
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. 安裝專案依賴：
   ```bash
   poetry install
   ```

3. 設定環境變數：
   ```bash
   cp .env.example .env
   # 編輯 .env 檔案
   ```

4. 執行程式：
   ```bash
   ./run_script.sh
   ```

## ⚙️ 環境變數設定

### Telegram 設定
| 變數名稱 | 說明 | 必填 | 範例 |
|---------|------|------|------|
| TELEGRAM_BOT_TOKEN | Telegram Bot Token | ✅ | 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz |
| TELEGRAM_CHAT_ID | 通知訊息接收群組/頻道 ID | ✅ | -1001234567890 |

### PTT 帳號設定
| 變數名稱 | 說明 | 必填 | 範例 |
|---------|------|------|------|
| PTT_USERNAME | PTT 帳號用戶名 | ✅ | your_username |
| PTT_PASSWORD | PTT 帳號密碼 | ✅ | your_password |

## 📝 日誌系統

### 日誌等級
- INFO：一般執行資訊
- WARNING：警告訊息
- ERROR：錯誤訊息
- DEBUG：除錯資訊（僅開發環境）

所有日誌僅輸出到控制台，不會在本地創建日誌檔案。

## 🧪 測試

專案包含全面的測試套件，確保程式碼品質和可靠性。

### 執行測試

```bash
# 執行所有測試
poetry run pytest

# 執行測試並產生覆蓋率報告
poetry run pytest --cov=. --cov-report=term-missing

# 執行特定測試檔案
poetry run pytest tests/test_telegram.py
```

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
├── config.py           # 配置類別和函數
├── main.py             # 主程式進入點
├── utils/
│   ├── __init__.py
│   ├── logger.py       # 日誌配置
│   ├── ptt.py          # PTT 自動簽到功能
│   └── telegram.py     # Telegram 通知功能
├── Dockerfile          # Docker 配置
├── pyproject.toml      # 專案元數據和依賴
└── run_script.sh       # 本地執行腳本
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