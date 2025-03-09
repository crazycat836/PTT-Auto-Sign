# Changelog

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