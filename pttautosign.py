#!/usr/bin/env python3
"""
PTT Auto Sign - Entry point script.
"""

import sys
import logging
import os
from dotenv import load_dotenv

# Configure basic logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("pttautosign")

def main():
    """Main entry point for the PTT Auto Sign program."""
    try:
        # Print a simple message for testing
        logger.info("PTT Auto Sign program started")
        logger.info(f"Python path: {sys.path}")
        logger.info(f"Current directory: {os.getcwd()}")
        logger.info(f"Directory contents: {os.listdir('.')}")
        
        # Add src directory to Python path if not already there
        src_path = os.path.join(os.getcwd(), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
            logger.info(f"Added {src_path} to Python path")
        
        # Load environment variables
        load_dotenv()
        
        try:
            # Import modules
            from src.pttautosign.utils.config import AppConfig, ConfigValidationError, get_ptt_accounts
            from src.pttautosign.utils.logger import setup_logging
            from src.pttautosign.utils.factory import ServiceFactory
            
            # Create configuration
            app_config = AppConfig.from_env()
            
            # Setup logging
            setup_logging(
                config=app_config.log,
                use_json=app_config.log.use_json_format,
                include_hostname=app_config.log.include_hostname
            )
            
            # Create service factory
            service_factory = ServiceFactory(app_config)
            
            # Get login service
            login_service = service_factory.get_login_service()
            
            # Get account list and perform batch login
            accounts = get_ptt_accounts()
            results = login_service.batch_login(accounts)
            
            # Log results summary
            success_count = sum(1 for success in results.values() if success)
            logger.info(f"Login results: {success_count}/{len(results)} accounts successful")
            
            # Log failed accounts if any
            if success_count < len(results):
                failed_accounts = [account for account, success in results.items() if not success]
                logger.warning(f"Failed accounts: {', '.join(failed_accounts)}")
            
        except ImportError as e:
            logger.error(f"Import error: {str(e)}")
            raise
        
        logger.info("PTT Auto Sign program completed successfully")
        
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 