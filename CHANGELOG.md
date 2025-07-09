# Changelog

## v1.3.1
- **Code Refactoring and Optimization**:
  - Unified logging configuration management by removing duplicate `ShortNameFormatter` in `main.py`
  - Centralized all logging configuration through `logger.py` with `ColorShortNameFormatter`
  - Simplified main program initialization logic

- **Configuration Management Improvements**:
  - Added `debug_mode` support in `LogConfig` class
  - Added `test_mode` support in `AppConfig` class  
  - Unified environment variable naming conventions (`LOG_FORMAT`, `LOG_LEVEL`)
  - Automatic log level setting based on `DEBUG_MODE`

- **Environment Variable Handling**:
  - Removed duplicate `DISABLE_NOTIFICATIONS` reading in `ptt.py`
  - Unified notification disable setting through configuration system and dependency injection
  - Centralized service creation management in `ServiceFactory`

- **Warning Handling Simplification**:
  - Removed duplicate warning suppression code in `main.py`
  - Unified all PyPtt-related warning handling in `pyptt_patch.py`

- **Code Structure Improvements**:
  - Enhanced service dependency relationships
  - Improved configuration validation and error handling
  - Better separation of concerns across modules

## v1.3.0
- **Code Optimization and Cleanup**: Removed unused functions and variables
- Removed `validate_all_configs()` function, simplified configuration validation process
- Removed unused `use_json_format` and `include_hostname` parameters from `LogConfig`
- Removed unused `daily_login` method alias in `ptt.py`
- Removed `JsonFormatter` class and related functionality, centralized to colored text formatting
- Removed unused `log_initial_config()` function in `docker_runner.sh`
- **Environment Variable Modernization**: Updated to follow Docker conventions
- **PTT Account Management**: Simplified to support single account configuration mode
- **Localization Improvements**: Enhanced Chinese language support including error messages and notification content localization
- **Documentation Updates**: Provided clearer operational guidance and usage instructions

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