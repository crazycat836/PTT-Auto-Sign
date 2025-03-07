# PTT Auto Sign

A Python-based tool for automatic PTT (BBS) sign-in with Telegram notifications.

## Features

- Automatic sign-in for multiple PTT accounts
- Telegram notifications for sign-in results
- Docker containerization support
- Environment variable configuration
- Support for multiple accounts with "none" option

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
   docker run --rm pttautosign
   ```

## Environment Variables

### Telegram Configuration
- `bot_token`: Your Telegram Bot Token
- `chat_id`: Channel or group ID for notifications

### PTT Account Configuration
- `ptt_id_1`: Primary account (format: username,password)
- `ptt_id_2` ~ `ptt_id_5`: Additional accounts (format: username,password, or none,none)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
