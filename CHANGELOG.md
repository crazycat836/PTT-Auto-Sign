# Changelog

## v1.3.0
- 程式碼優化與清理：移除未使用的函數和變數
- 移除 `validate_all_configs()` 函數，簡化配置驗證流程
- 移除 `LogConfig` 中未使用的 `use_json_format` 和 `include_hostname` 參數
- 移除 `ptt.py` 中未使用的 `daily_login` 方法別名
- 移除 `JsonFormatter` 類別和相關功能，集中使用彩色文字格式化
- 移除 `docker_runner.sh` 中未使用的 `log_initial_config()` 函數
- 現代化環境變數名稱，更符合 Docker 慣例
- 簡化PTT帳號管理，支援單一帳號設定模式
- 改進中文語系支援，包括錯誤訊息和通知內容的本地化
- 更新文檔與使用說明，提供更清楚的操作指引

## v1.2.0
- Simplified Docker configuration with cleaner environment variables
- Removed unnecessary configuration options (TEST_MODE, ENABLE_CRON, DIRECT_EXEC)
- Improved entrypoint script to verify parameters immediately on container startup
- Enhanced documentation with clearer instructions for Docker deployment
- Separated system Python settings from user-configurable environment variables
- Optimized random cron job scheduling for more reliable execution
- Focused support on Python 3.11, removing Python 3.13 compatibility layer

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