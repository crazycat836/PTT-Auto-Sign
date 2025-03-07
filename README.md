# PTT Auto Sign

[![License](https://img.shields.io/github/license/crazycat836/ptt-auto-sign?style=for-the-badge&color=5D6D7E)](LICENSE)
[![Issues](https://img.shields.io/github/issues/crazycat836/ptt-auto-sign?style=for-the-badge&color=5D6D7E)](https://github.com/crazycat836/ptt-auto-sign/issues)

A Python-based tool for automatic PTT (BBS) sign-in with Telegram notifications.

## Features

- Automatic sign-in for multiple PTT accounts
- Telegram notifications for sign-in results
- Docker containerization support with random daily execution time
- Environment variable configuration
- Support for multiple accounts with "none" option
- Comprehensive logging system
- Local development and Docker deployment support

## Requirements

- Python 3.11+
- Docker (optional)

## Local Development Setup

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Set up environment variables:
   Copy `.env.example` to `.env` and fill in your settings:
   ```bash
   cp .env.example .env
   ```

3. Run the script:
   ```bash
   ./run_script.sh
   ```

## Docker Deployment

1. Build the image:
   ```bash
   docker build -t pttautosign .
   ```

2. Run the container:
   ```bash
   docker run -d \
     --name ptt-auto-sign \
     --env-file .env \
     pttautosign
   ```

### Docker Features
- Random execution time between 9 AM and 5 PM daily
- Automatic timezone setting (Asia/Taipei)
- Comprehensive logging system
- Container restart support

## Environment Variables

### Telegram Configuration
- `bot_token`: Your Telegram Bot Token
- `chat_id`: Channel or group ID for notifications

### PTT Account Configuration
- `ptt_id_1`: Primary account (format: username,password)
- `ptt_id_2` ~ `ptt_id_5`: Additional accounts (format: username,password, or none,none)

## Logging

Logs are stored in the following locations:
- Docker: Inside the container at `/app/logs`
- Local: In the `logs` directory of the project

## License

This project is licensed under the GNU Affero General Public License v3 (AGPL-3.0) - see the [LICENSE](LICENSE) file for details.

This license requires that if you run a modified version of this program on a server and let other users communicate with it there, your server must also allow them to download the source code corresponding to the modified version running there.

## Changelog

### v1.0.1
- Added random daily execution time (9 AM - 5 PM)
- Improved logging system
- Enhanced Docker support
- Added local development support
- Fixed container restart issues
- Changed license to GNU Affero General Public License v3 (AGPL-3.0)
