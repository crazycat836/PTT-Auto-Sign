# Changelog

## v1.3.4
- **Security – credentials never on disk in cron files**: `cron_wrapper.sh` and `daily_time_updater.sh` are now generated from quoted heredocs that contain no expanded variables. Secrets are written once to `/app/.cron_env` (mode 0600) and sourced at runtime, so credentials never appear in `/app/scripts/*.sh`, in `ps`/`/proc/<pid>/cmdline`, or in `/tmp`.
- **Security – removed dangerous global `re.compile` monkey-patch**: `pyptt_patch.py` no longer replaces `re.compile` process-wide. The risky never-matches fallback (`r'(?!)'`) that could silently corrupt PyPtt's regex-based screen parsing has been removed.
- **Security – masked Telegram token in `TelegramConfig.to_dict()` / `to_json()`**: bot token is now redacted as `<bot_id>:***`, preventing accidental leakage if config is logged.
- **Security – context dict redaction**: `TelegramBot.send_error_notification` masks any context key matching `password`/`passwd`/`token`/`secret`/`api_key`. HTML output is also properly escaped.
- **Security – suppress noisy third-party DEBUG**: `websockets`, `urllib3`, and `requests` loggers are pinned to WARNING even when `DEBUG_MODE=true`, preventing raw-frame dumps that contained the PTT password.
- **Correctness – honor `PTTConfig`**: `PTTAutoSign` now uses `self.config.max_retries`, `self.config.retry_delay`, and `self.config.kick_other_session` (previously all hardcoded).
- **Correctness – align `NotificationService` interface**: removed unused `retry` parameter from `TelegramBot.send_error_notification` to match the abstract base class.
- **Correctness – fail-fast config**: invalid integer env vars now raise `ConfigValidationError` instead of bare `ValueError`.
- **Cleanup – `main.py`**: switched from REPL builtin `exit()` to `sys.exit()` and removed `exc_info=True` on user-facing config errors.
- **Cleanup – `app_context.py`**: cache `get_ptt_accounts()` result once during `initialize()` instead of re-reading env vars three times per run.
- **Docker – `.dockerignore` added**: prevents `.env`, `.git`, caches, and `__pycache__` from entering the build context.
- **Docker – slimmer runtime image**: dropped unused `rsyslog`/`procps`, added `curl`+`ca-certificates` (for Telegram fallback). Scripts now `chmod 0700`. OCI labels added for Docker Hub display.
- **Security – dependency upgrades (Dependabot)**: bumped `urllib3` → 2.7.0, `requests` → 2.34.2, `idna` → 3.18, `python-dotenv` → 1.2.2 and `black` → 26.x, clearing six open advisories (urllib3 redirect header leak & decompression-bomb, requests temp-file reuse, idna `encode()` bypass, python-dotenv symlink write, black cache-name write).
- **Security – Telegram token never logged**: error logs now redact the bot token (library exceptions such as `HTTPError` embed the full request URL); `TelegramBot.__init__` validates the token format up front.
- **Security – no password in login tracebacks**: the unexpected-error path in `PTTAutoSign.login` logs type+message and a password-sanitised traceback instead of `exc_info=True`.
- **Robustness – import hygiene / testability**: importing `pttautosign` (or `pttautosign.utils.config`) no longer triggers `load_dotenv`, `logging.basicConfig`, startup logs, or global PyPtt monkey-patching. Patches are applied explicitly via `apply_patches()` inside `main()`; `PyPtt` is imported lazily so config can be unit-tested in isolation.
- **Robustness – patch failures surface**: `apply_patches()` returns `True` only when every patch succeeds (was: any success), and `main()` warns on partial failure.
- **Robustness – login crash fixed**: `_format_success_message` parses the mail count with a regex, so a malformed "new mails" string no longer raises `IndexError` on a successful login.
- **Robustness – bounded waits**: `batch_login` now honours `ptt_connection_timeout` via an overall timeout so an unresponsive PTT server can no longer hang the process; the retry backoff is capped at 60 s; Telegram sends now retry per `TELEGRAM_RETRY_COUNT` and failures are surfaced.
- **Correctness – consistent timestamps & timezone**: error notifications use the configured timezone (matching success messages); `ptt_timezone_hours` is the new convention-consistent name (legacy `timezone_hours` still works).
- **Correctness – logging formatter no longer mutates the shared `LogRecord`** (the shortened logger name was leaking onto the record).
- **Cleanup – removed dead code**: deleted the unused `AppConfig.test_mode` field, the never-called `TelegramBot.send_with_retry`, and the empty `LogConfig.validate`. `__version__` is now read from package metadata (single source of truth) and the README/badges corrected to 1.3.4 / Python 3.11+.
- **Tests – added a `pytest` unit suite** (config validation & secret redaction, login retry/notification, batch timeout, Telegram retry, logging formatter, factory, app context, CLI) at ~84% coverage.

## v1.3.3
- **Thread Safety Fix**: Fixed `retry_count` race condition in concurrent batch logins by replacing shared instance state with local iterative loop.
- **Performance Optimization**: Replaced `inspect.currentframe()` with `sys._getframe()` in `_patched_compile` hot path, added early-exit guard in `_fix_pattern`.
- **Code Cleanup**:
  - Replaced custom `NullHandler` with stdlib `logging.NullHandler()`.
  - Extracted `_safe_logout()` helper to eliminate duplicated logout logic.
  - Removed redundant `load_dotenv()` call in `config.py`.
  - Removed unused imports across modules (`Optional`, `Dict`, `Pattern`, `TelegramBot`).
  - Removed unused `_patched_modules` field.
  - Moved inline imports (`time`, `concurrent.futures`) to module level.

## v1.3.2
- **Python 3.14 Support**: Full support for Python 3.14 environment.
- **Concurrency Improvements**: 
  - Implemented `ThreadPoolExecutor` for parallel batch logins.
  - Fixed `PyPtt` thread-safety issues by ensuring isolated API instances per thread.
- **Code Refactoring**: 
  - Refactored `pyptt_patch.py` into a structured class for better maintainability.
  - Improved error handling in patch application.
- **Documentation**: 
  - Added `.env.example` file for easier configuration.

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