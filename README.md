# PTT Auto Sign

[![License](https://img.shields.io/github/license/crazycat836/ptt-auto-sign?style=for-the-badge&color=5D6D7E)](LICENSE)
[![Issues](https://img.shields.io/github/issues/crazycat836/ptt-auto-sign?style=for-the-badge&color=5D6D7E)](https://github.com/crazycat836/ptt-auto-sign/issues)
[![Release](https://img.shields.io/github/v/release/crazycat836/ptt-auto-sign?style=for-the-badge&color=5D6D7E)](https://github.com/crazycat836/ptt-auto-sign/releases)
[![Python Version](https://img.shields.io/badge/Python-3.11-5D6D7E?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Docker Pulls](https://img.shields.io/docker/pulls/crazycat836/pttautosign?style=for-the-badge&color=5D6D7E)](https://hub.docker.com/r/crazycat836/pttautosign)

English | [繁體中文](README_zh-TW.md)

An automated sign-in tool for PTT (BBS) with Telegram notifications. Easily achieve daily automatic sign-ins through Docker containerized deployment.

## ✨ Features

- 🔄 Automated sign-in for PTT accounts
- 📱 Telegram notifications for real-time status updates
- 🐳 Docker containerization for easy deployment
- 🎲 Random daily execution time (9 AM to 5 PM)
- 📝 Comprehensive logging system
- ⚙️ Flexible environment variable configuration
- 🔒 Secure account management
- 🐍 Python 3.11 support
- 🌏 Chinese localization for messages and notifications
- 🏗️ Modular code architecture for maintainability

## 🚀 Quick Start

### Using Docker (Recommended)

1. Pull the Docker image:
   ```bash
   docker pull crazycat836/pttautosign:latest
   ```

2. Run container:
   ```bash
   # Option 1: Using environment variables directly (Production mode - runs once daily)
   docker run -d \
     --name ptt-auto-sign \
     --restart unless-stopped \
     -e PTT_USERNAME=your_username \
     -e PTT_PASSWORD=your_password \
     -e TELEGRAM_BOT_TOKEN=your_bot_token \
     -e TELEGRAM_CHAT_ID=your_chat_id \
     crazycat836/pttautosign:latest
     
   # Option 2: Using Test Mode (runs every minute, 3 times total)
   docker run -d \
     --name ptt-auto-sign-test \
     --restart unless-stopped \
     -e PTT_USERNAME=your_username \
     -e PTT_PASSWORD=your_password \
     -e TELEGRAM_BOT_TOKEN=your_bot_token \
     -e TELEGRAM_CHAT_ID=your_chat_id \
     -e TEST_MODE=true \
     crazycat836/pttautosign:latest
   ```

### Docker Modes

The container supports two operation modes:

1. **Production Mode** (default): Container runs once per day at a random time between 9 AM and 5 PM (Taiwan time).
2. **Test Mode**: Container runs every minute for 3 times, useful for testing your setup.

In either mode, the container will:
1. **Verify credentials** by performing an initial login test and notification before setting up the cron job
2. **Set up a cron job** based on the selected mode
3. **Keep running** to monitor and execute the scheduled tasks

To view container logs:
```bash
docker logs -f ptt-auto-sign
```

### Local Development

1. Install Python 3.11+ and Poetry:
   ```bash
   # macOS
   brew install python@3.11 poetry
   
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3.11
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Set up environment variables:
   ```bash
   # PTT credentials
   export PTT_USERNAME="your_username"
   export PTT_PASSWORD="your_password"
   
   # Telegram settings
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   export TELEGRAM_CHAT_ID="your_chat_id"
   ```

4. Run the program:
   ```bash
   # Test login only
   python -m pttautosign.main --test-login
   
   # Regular run
   python -m pttautosign.main
   ```

## ⚙️ Environment Variables

### Required Settings
| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| PTT_USERNAME | PTT account username | ✅ | your_username |
| PTT_PASSWORD | PTT account password | ✅ | your_password |
| TELEGRAM_BOT_TOKEN | Telegram Bot Token | ✅ | 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz |
| TELEGRAM_CHAT_ID | Channel or Group ID for notifications | ✅ | -1001234567890 |

### Optional Settings
| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| TEST_MODE | Enable test mode | false | true |
| DEBUG_MODE | Enable debug logging | false | true |
| RANDOM_DAILY_TIME | Generate new random time daily | true | false |
| DISABLE_NOTIFICATIONS | Disable Telegram notifications | false | true |

## 📝 Logging

### Log Levels
- INFO: General execution information
- WARNING: Warning messages
- ERROR: Error messages
- DEBUG: Debug information (when DEBUG_MODE=true)

All logs are output to the console in colorized format. Log messages are localized in Chinese for better readability.

## 🛠️ Development

### Code Formatting

The project uses Black and isort for code formatting:

```bash
# Format code with Black
poetry run black .

# Sort imports with isort
poetry run isort .
```

## 🏗️ Project Structure

```
pttautosign/
├── __init__.py            # Package metadata
├── main.py                # Main entry point
├── patches/
│   └── pyptt_patch.py     # Compatibility patches for PyPtt
├── utils/
│   ├── app_context.py     # Application context
│   ├── config.py          # Configuration classes
│   ├── factory.py         # Service factory
│   ├── interfaces.py      # Service interfaces
│   ├── logger.py          # Logging configuration
│   ├── ptt.py             # PTT auto sign-in functionality
│   └── telegram.py        # Telegram notification functionality
├── Dockerfile             # Docker configuration
├── pyproject.toml         # Project metadata and dependencies
└── scripts/
    └── docker_runner.sh   # Docker entrypoint script
```

## ❗️ Troubleshooting

### Common Issues

1. Docker Container Won't Start
   - Check if environment variables are set correctly
   - Verify Docker service is running
   - View container logs: `docker logs ptt-auto-sign`

2. Sign-in Failure
   - Verify PTT account credentials
   - Check network connectivity
   - Review application logs

3. Telegram Notifications Not Received
   - Verify bot_token is valid
   - Check chat_id is correct
   - Ensure Bot is added to group/channel

## 🤝 Contributing

We welcome all contributions! Here's how you can help:

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
