# PTT Auto Sign

[![License](https://img.shields.io/github/license/crazycat836/ptt-auto-sign?style=for-the-badge&color=5D6D7E)](LICENSE)
[![Issues](https://img.shields.io/github/issues/crazycat836/ptt-auto-sign?style=for-the-badge&color=5D6D7E)](https://github.com/crazycat836/ptt-auto-sign/issues)
[![Release](https://img.shields.io/github/v/release/crazycat836/ptt-auto-sign?style=for-the-badge&color=5D6D7E)](https://github.com/crazycat836/ptt-auto-sign/releases)
[![Python Version](https://img.shields.io/badge/Python-3.13%2B-5D6D7E?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Docker Pulls](https://img.shields.io/docker/pulls/crazycat836/pttautosign?style=for-the-badge&color=5D6D7E)](https://hub.docker.com/r/crazycat836/pttautosign)

English | [繁體中文](README_zh-TW.md)

An automated sign-in tool for PTT (BBS) with multi-account support and Telegram notifications. Easily achieve daily automatic sign-ins through Docker containerized deployment.

## ✨ Features

- 🔄 Automated sign-in for multiple PTT accounts
- 📱 Telegram notifications for real-time status updates
- 🐳 Docker containerization for easy deployment
- 🎲 Random daily execution time (9 AM to 5 PM)
- 📝 Comprehensive logging system
- ⚙️ Flexible environment variable configuration
- 🔒 Secure account management
- 🐍 Python 3.13 support with telnetlib compatibility layer
- 🧪 Comprehensive test suite with high code coverage
- 🏗️ Modular code architecture for maintainability

## 🚀 Quick Start

### Using Docker (Recommended)

1. Pull the Docker image:
   ```bash
   docker pull crazycat836/pttautosign:latest
   ```

2. Prepare environment variables:
   ```bash
   # Copy example file
   cp .env.example .env
   
   # Edit .env file with your settings
   vim .env
   ```

3. Run container:
   ```bash
   docker run -d \
     --name ptt-auto-sign \
     --restart unless-stopped \
     --env-file .env \
     crazycat836/pttautosign:latest
   ```

### Local Development

1. Install Python 3.13+ and Poetry:
   ```bash
   # macOS
   brew install python@3.13 poetry
   
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3.13
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file
   ```

4. Run the script:
   ```bash
   ./run_script.sh
   ```

## ⚙️ Environment Variables

### Telegram Settings
| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| bot_token | Telegram Bot Token | ✅ | 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz |
| chat_id | Channel or Group ID for notifications | ✅ | -1001234567890 |

### PTT Account Settings
| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| ptt_id_1 | Primary account | ✅ | username,password |
| ptt_id_2 ~ ptt_id_5 | Additional accounts | ❌ | username,password or none,none |

## 📝 Logging

### Log Levels
- INFO: General execution information
- WARNING: Warning messages
- ERROR: Error messages
- DEBUG: Debug information (development only)

All logs are output to the console only. No log files are created locally.

## 🧪 Testing

The project includes a comprehensive test suite to ensure code quality and reliability.

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run tests with coverage report
poetry run pytest --cov=. --cov-report=term-missing

# Run specific test file
poetry run pytest tests/test_telegram.py
```

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
├── config.py           # Configuration classes and functions
├── main.py             # Main entry point
├── monkey_patch.py     # Telnetlib compatibility layer for Python 3.13
├── utils/
│   ├── __init__.py
│   ├── logger.py       # Logging configuration
│   ├── ptt.py          # PTT auto sign-in functionality
│   └── telegram.py     # Telegram notification functionality
├── tests/
│   ├── __init__.py
│   ├── test_config.py  # Tests for configuration
│   ├── test_ptt.py     # Tests for PTT functionality
│   └── test_telegram.py # Tests for Telegram functionality
├── Dockerfile          # Docker configuration
├── pyproject.toml      # Project metadata and dependencies
└── run_script.sh       # Script for local execution
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

4. Python 3.13 Compatibility
   - The project includes a compatibility layer for the `telnetlib` module which was removed in Python 3.13
   - If you encounter issues with `telnetlib`, ensure the `monkey_patch.py` file is properly loaded before importing PyPtt

## 🤝 Contributing

We welcome all contributions! Here's how you can help:

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
