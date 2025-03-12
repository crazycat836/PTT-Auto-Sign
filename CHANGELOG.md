# Changelog

## v1.1.1
- Fixed Python command in Docker environment (changed from `python` to `python3`)

## v1.1.0
- Refactored code architecture with modular design and dependency injection pattern
- Added application context (AppContext) for lifecycle and dependency management
- Enhanced error handling and logging system with structured JSON logging support
- Improved Telegram notifications with detailed error reports
- Added configuration validation and additional configuration options
- Fixed Python 3.13 compatibility issues:
  - Optimized telnetlib compatibility layer
  - Resolved PyPtt and websockets compatibility issues
  - Patched invalid regex escape sequences
- Improved Docker container with non-root user and health check
- Added unit tests and code formatting tools (Black and isort)
- Updated documentation with testing and project structure information

## v1.0.3
- Added support for Python 3.13 by implementing a telnetlib compatibility layer
- Added monkey_patch.py to provide telnetlib functionality using telnetlib3
- Updated dependencies to include telnetlib3 and websockets
- Updated documentation to reflect Python 3.13 compatibility

## v1.0.2
- Refactored logging configuration by removing duplicate implementations and centralizing settings in utils/logger.
- Removed duplicate TelegramConfig definition from main.py.
- Improved exception handling in PTTAutoSign.daily_login.
- Updated random_cron.sh to ensure CRON_LOG_DIR is created.

## v1.0.1
- Added random daily execution time (9 AM - 5 PM)
- Improved logging system
- Enhanced Docker support
- Added local development support
- Fixed container restart issues
- Changed license to Apache License 2.0 