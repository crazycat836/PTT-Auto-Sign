# Changelog

## v1.4.0
- **Dependency – PyPtt 1.3.3 → 2.3.7**: 1.3.3 發布於 2025-09-26，2.3.7 發布於 2026-08-20，中間相隔 328 天、33 個版本。v1.3.5 當時判斷「2.x 改了本專案 patch 的內部實作」而刻意停在 1.x——那個判斷是對的（見下一條），但代價是整條 2.x 線被 `dependabot.yml` 的 `ignore: "*" semver-major` 擋在視線外將近一年。升級前逐項比對過本專案用到的介面：`API.__init__` / `login` / `get_user` / `logout` 四個簽章相同、`PTT.log.SILENT` 存在、用到的六個 exception 都在、`get_user` 回傳的 13 個欄位完全相同（以 AST 解析兩邊的 return dict 比對，含本專案讀的 `login_count` 與 `mail`）。
- **Bug fix – 主選單補丁在 PyPtt 2.x 會靜默失效**: `_patch_mainmenu_detection` 寫死 `marker = "[呼叫器]"` 做完全比對，但 PyPtt 各版拼法不同（1.3.3 是 `[呼叫器]`，2.3.7 是不帶方括號的 `呼叫器`）。在不認識的版本上那個 `if` 不成立，補丁什麼都不做，v1.3.5 修掉的登入誤判會無聲無息回來。改成比對子字串「呼叫器」並原地修改 list。對應的測試原本斷言 `"[呼叫器]" not in MainMenu`，在 2.3.7 上是假通過（標記其實還在，只是少了方括號），一併改成比對子字串，另補一個直接餵三種拼法的測試。
- **Dependency – 移除 `websockets` 的版本上限**: PyPtt 2.x 的 `requires_dist` 是 `websockets>=12` 且不再 import `websockets.http`，v1.3.5 加的 `websockets = "^16.0"` 上限失去存在理由，lock 跟著推到 17.1。`patch_websockets` 也改成容忍 websockets 17.x——該版本移除了 `websockets.http`，這種組合是「沒事可做」而不是失敗，不該把 `apply_patches()` 拖進降級狀態。
- **Dependency – 移除從未用到的 `setuptools`**: 它被宣告成執行期相依，但整包程式碼沒有一行用到（在拔掉 `setuptools` 與 `pkg_resources` 的乾淨環境實測，所有 import 通過）。setuptools 是 CVE 常客，本專案先前的資安警告有兩則出自它，而它的修版都落在大版本，剛好同時被 `ignore` 規則與 auto-merge 擋住，PR 就一直掛著。
- **Docker – 移除 image 裡的打包工具**: `telnetlib3` 原本用 `pip` 另外安裝，不在 `poetry.lock` 也不在 GitHub 相依圖裡，沒有人幫它看更新，而且用不到（PyPtt 預設走 WEBSOCKETS，PTT1/PTT2 不接受 TELNET）。另外 `python:3.11-alpine` base image 自帶 setuptools 79.0.1，拿掉宣告只是讓它從相依圖消失、檔案還在且版本更舊，所以在最終 image 直接移除 `setuptools` / `pkg_resources` / `pip` / `wheel`。已確認 site-packages 裡只有 `wheel` 自己會 import 它們。
- **Docker – 不再於 Dockerfile 宣告憑證類環境變數**: `ENV PTT_USERNAME="" …` 會觸發 buildkit 的 `SecretsUsedInArgOrEnv` 警告，而宣告成空字串沒有任何好處——`docker_runner.sh` 用 `[ -z "$VAR" ]` 檢查，對「未設定」與「設為空字串」行為相同。改為僅在註解中說明必須以 `-e` 或 `--env-file` 傳入。
- **CI – Dependabot 設定重寫**: 移除 `ignore: dependency-name: "*"` 的全面 major 封鎖（那條規則讓相依平常跟不上，等到 CVE 逼著升級時就變成一次跳好幾個版號、auto-merge 又拒絕的 PR，一直掛著）。改成執行期／開發工具兩個 group，只對 `websockets` 保留 major 例外；補上 `github-actions` 與 `docker` 兩個 ecosystem；拿掉會疊出 `chore(deps-dev)(deps-dev)` 的 `include: "scope"`。
- **CI – auto-merge 現在真的等 CI**: 原本用 `gh pr merge --auto`，但這個 repo 的 ruleset 只擋刪除與強推，沒有任何必要狀態檢查，`--auto` 因此不等 CI 回報就直接合併。改成輪詢匯總 check `ci-ok`，通過才合併。要人工審查的只剩 Python 執行期相依的大版本——GitHub Actions 的相依也被 `fetch-metadata` 歸類成 `direct:production`，所以判斷條件必須同時比對 `package-ecosystem`，否則 `actions/checkout` v4→v5 這種 CI 已驗過的升級也會被擋。
- **CI – 測試矩陣涵蓋 3.11 / 3.12 / 3.13**: `pyproject` 宣告 `>=3.11,<4.0`，但 CI 只測 3.11，而日常開發在 3.13 上，等於邊界完全沒測到。matrix 會讓 check 名稱變成 `test (py3.11)` 這種會浮動的名字，所以另外加一個名字固定的匯總 job `ci-ok` 給 auto-merge 當閘門。
- **CI – 新增 lock 一致性與 setuptools 守門檢查**: `poetry check --lock` 擋下 `pyproject.toml` 與 `poetry.lock` 對不起來的情況；另一步斷言執行期不會載入 `setuptools` / `pkg_resources`，避免它哪天又被當成隱性相依帶回來。Poetry 版本鎖到 2.4.1。
- **Release – 版本號自動發布**: `v1.3.4` 與 `v1.3.5` 寫進了 CHANGELOG 卻從沒被 tag，因為打 tag 是純手工步驟。新增 `release.yml`：main 上 `pyproject.toml` 的版本一變動就自動建 tag 與 GitHub Release，release notes 直接取自 CHANGELOG 對應段落；找不到該段落就讓發布失敗。
- **Chore – pyproject 遷移到 PEP 621**: metadata 從 `[tool.poetry]` 搬到 `[project]`。Poetry 2.x 對舊的鍵在每一次執行都會噴 10 條 deprecation 警告，那些噪音會蓋掉真正該讀的訊息（例如 `poetry check --lock` 的輸出）。現在 `poetry check` 只回 `All set!`。
- 驗證：82 個測試在 PyPtt 1.3.3 + websockets 16.1.1 與 PyPtt 2.3.7 + websockets 17.1 兩組環境下皆通過；`linux/amd64` image 實際建出並執行，`setuptools`/`pkg_resources`/`telnetlib3`/`pip`/`wheel` 皆不可 import，entrypoint 停在缺環境變數而非缺套件。**尚未用真帳號連上 PTT 跑過 `login()` / `get_user()`**。

## v1.3.5
- **Bug fix – logins falsely reported as failed**: PyPtt only treats a login as successful when the literal marker `[呼叫器]` appears on the post-login screen. That marker is a per-account preference — an account whose main-menu corner display is set to something else (e.g. a date/時辰 display instead of the default caller-light indicator) never shows it, so every login raised `LoginError` even though the account was actually on the main menu. `pyptt_patch.py` now strips `[呼叫器]` from PyPtt's `screens.Target.MainMenu` check at patch time; the other two markers (`離開，再見`, `人, 我是`) are already unique to the main menu on their own. Root-caused and verified against a real PTT account that was hitting this on every scheduled run.
- **Bug fix – dead ANSI-stripping patch on current PyPtt**: `PyPtt.screens` no longer exposes `get_data` as of PyPtt 1.3.3, so the `get_data` existence check was returning early and silently skipping every patch after it — including the new main-menu fix. Split into two independent patches so one missing attribute can no longer block the other.
- **Dependency – pin `websockets` below 17.0**: PyPtt (≤1.3.3) imports the deprecated `websockets.http` submodule, which was removed outright in websockets 17.0; an unconstrained `poetry update` silently resolved 17.0.1 and broke every PyPtt import with `ModuleNotFoundError`. Added an explicit `websockets = "^16.0"` constraint so this can't happen again until PyPtt drops the dependency.
- **Dependency upgrades**: `setuptools` → 84.0.0 (matches the pending Dependabot security PR and goes one patch further), `websockets` → 16.1.1, `python-dotenv` → 1.2.3, `pytest` → 9.1.1, plus routine bumps to `certifi`, `charset-normalizer`, `click`, `coverage`, `idna`, `packaging`, `pathspec`, `platformdirs`, `progressbar2`, `pygments`, `python-utils`, `typing-extensions`. `PyPtt` stays on 1.3.3 (the `^1.0.6` constraint intentionally excludes the 2.x major line, which changes internals this project patches).
- Verified end-to-end: full `pytest` suite, a real login against the live PTT account via `--test-login`, and the same test run inside the rebuilt Docker image.

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