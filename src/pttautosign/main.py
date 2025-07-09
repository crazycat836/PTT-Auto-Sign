#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import argparse
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

# Basic logging setup (will be reconfigured by AppContext)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# Create a null handler for PyPtt logger to suppress its output
class NullHandler(logging.Handler):
    def emit(self, record):
        pass

# Set up a null handler for PyPtt logger
pyptt_logger = logging.getLogger('PyPtt')
pyptt_logger.addHandler(NullHandler())
pyptt_logger.propagate = False
pyptt_logger.setLevel(logging.CRITICAL)

# Import our patches before importing any PyPtt related modules
logger.info("PTT 自動簽到程式啟動")
logger.debug("正在套用相容性修補...")
from pttautosign.patches import pyptt_patch
logger.debug("修補套用完成")

# Import modules after environment variables are loaded
from pttautosign.utils.config import ConfigValidationError
from pttautosign.utils.app_context import AppContext
from pttautosign.utils.config import get_ptt_accounts

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="PTT Auto Sign")
    parser.add_argument("--test-login", action="store_true", help="Test login functionality")
    return parser.parse_args()

def main():
    """Main entry point for the PTT Auto Sign program"""
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Create and initialize application context
        app_context = AppContext()
        app_context.initialize()
        
        # Check if we're running in test mode
        if args.test_login:
            logger.debug("正在執行測試模式")
            
            # Get login service
            login_service = app_context.get_login_service()
            
            logger.info("開始登入測試")
            
            # Get accounts and perform batch login
            accounts = get_ptt_accounts()
            results = login_service.batch_login(accounts)
            
            # Print results
            success_count = sum(1 for success in results.values() if success)
            logger.info("登入測試完成")
            logger.debug(f"帳號總數：{len(accounts)}")
            logger.info(f"登入成功：{success_count}")
            logger.info(f"登入失敗：{len(accounts) - success_count}")
            
            if success_count < len(accounts):
                failed_accounts = [account for account, success in results.items() if not success]
                logger.warning(f"失敗帳號：{', '.join(failed_accounts)}")
            
            # Exit with appropriate status code
            if success_count == 0:
                exit(1)
        else:
            # Run the application normally
            app_context.run()
        
    except ConfigValidationError as e:
        logger.error(f"設定錯誤：{str(e)}", exc_info=True)
        exit(1)
    except Exception as e:
        logger.error(f"執行時錯誤：{str(e)}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()
