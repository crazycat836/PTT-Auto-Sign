#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
import argparse

# Lightweight, side-effect-free imports only. Anything that pulls in PyPtt
# (app_context -> factory -> ptt) is imported inside main(), AFTER the
# compatibility patches are applied. config is PyPtt-free at import time.
from pttautosign.utils.config import ConfigValidationError

logger = logging.getLogger(__name__)

_LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="PTT Auto Sign")
    parser.add_argument("--test-login", action="store_true", help="Test login functionality")
    return parser.parse_args()


def _bootstrap_logging() -> None:
    """Minimal logging before AppContext reconfigures it via setup_logging().

    Kept inside main() (not at import time) so that importing this module has
    no global side effects. setup_logging() later replaces these handlers.
    """
    logging.basicConfig(level=logging.INFO, format=_LOG_FORMAT, datefmt=_DATE_FORMAT)
    # Silence PyPtt's own logger until setup_logging() applies the full policy.
    logging.getLogger("PyPtt").setLevel(logging.ERROR)


def main():
    """Main entry point for the PTT Auto Sign program"""
    args = parse_args()

    _bootstrap_logging()

    # Load environment variables from .env for local development.
    from dotenv import load_dotenv

    load_dotenv()

    logger.info("PTT 自動簽到程式啟動")

    # Apply PyPtt compatibility patches BEFORE importing anything that imports
    # PyPtt (app_context -> factory -> ptt).
    logger.debug("正在套用相容性修補...")
    from pttautosign.patches.pyptt_patch import apply_patches

    if not apply_patches():
        logger.warning("部分 PyPtt 相容性修補未套用，可能影響登入流程")
    logger.debug("修補套用完成")

    from pttautosign.utils.app_context import AppContext

    try:
        app_context = AppContext()
        app_context.initialize()

        if args.test_login:
            _run_test_login(app_context)
        else:
            app_context.run()

    except ConfigValidationError as e:
        logger.error(f"設定錯誤：{e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"執行時錯誤：{e}", exc_info=True)
        sys.exit(1)


def _run_test_login(app_context) -> None:
    """Run the login flow in test mode and exit non-zero if every login failed."""
    logger.debug("正在執行測試模式")

    login_service = app_context.get_login_service()
    accounts = app_context.get_accounts()

    logger.info("開始登入測試")
    results = login_service.batch_login(accounts)

    success_count = sum(1 for success in results.values() if success)
    logger.info("登入測試完成")
    logger.debug(f"帳號總數：{len(accounts)}")
    logger.info(f"登入成功：{success_count}")
    logger.info(f"登入失敗：{len(accounts) - success_count}")

    if success_count < len(accounts):
        failed_accounts = [account for account, success in results.items() if not success]
        logger.warning(f"失敗帳號：{', '.join(failed_accounts)}")

    if success_count == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
