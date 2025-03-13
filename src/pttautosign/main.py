import os
import sys
import logging
import argparse
import warnings
from dotenv import load_dotenv

# Suppress warnings from PyPtt modules
warnings.filterwarnings("ignore", category=SyntaxWarning, module="PyPtt.*")
warnings.filterwarnings("ignore", category=FutureWarning, module="PyPtt.*")
warnings.filterwarnings("ignore", category=SyntaxWarning, module=".*pyptt_patch.*")
warnings.filterwarnings("ignore", category=FutureWarning, module=".*pyptt_patch.*")

# Custom formatter to shorten logger names
class ShortNameFormatter(logging.Formatter):
    def format(self, record):
        # Shorten the logger name to just the last part or last two parts
        parts = record.name.split('.')
        if len(parts) > 2:
            # For deeply nested modules, show only the last two parts
            record.name = '.'.join(parts[-2:])
        
        # Define ANSI color codes for different log levels
        COLORS = {
            'DEBUG': '\033[36m',     # Cyan
            'INFO': '\033[32m',      # Green
            'WARNING': '\033[33m',   # Yellow
            'ERROR': '\033[31m',     # Red
            'CRITICAL': '\033[41m',  # Red background
            'TRACE': '\033[35m',     # Magenta
            'RESET': '\033[0m',      # Reset to default
        }
        
        # Add colors based on log level
        levelname = record.levelname
        if levelname in COLORS:
            # Store original levelname
            original_levelname = record.levelname
            # Apply color
            record.levelname = f"{COLORS[levelname]}{levelname}{COLORS['RESET']}"
            # Format the record
            result = super().format(record)
            # Restore original levelname
            record.levelname = original_levelname
            return result
        else:
            return super().format(record)

# Configure basic logging first with a consistent format
log_format = '%(asctime)s [%(name)s] [%(levelname)s] %(message)s'
formatter = ShortNameFormatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')

# Set up the handler with our formatter
handler = logging.StreamHandler()
handler.setFormatter(formatter)

# Configure the root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
# Remove existing handlers to avoid duplicates
for h in root_logger.handlers[:]:
    root_logger.removeHandler(h)
root_logger.addHandler(handler)

logger = logging.getLogger(__name__)

# Create a null handler for PyPtt logger
class NullHandler(logging.Handler):
    def emit(self, record):
        pass

# Set up a null handler for PyPtt logger
pyptt_logger = logging.getLogger('PyPtt')
pyptt_logger.addHandler(NullHandler())
pyptt_logger.propagate = False  # Prevent logs from propagating to the root logger
pyptt_logger.setLevel(logging.CRITICAL)  # Set to CRITICAL to suppress most logs

# Import our patches before importing any PyPtt related modules
logger.info("Starting PTT Auto Sign")
logger.info("Applying compatibility patches...")
from pttautosign.patches import monkey_patch, pyptt_patch
logger.info("Patches applied successfully")

# Load environment variables from .env file for local development
load_dotenv()

# Import modules after environment variables are loaded
from pttautosign.utils.config import ConfigValidationError
from pttautosign.utils.app_context import AppContext
from pttautosign.utils.config import get_ptt_accounts

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="PTT Auto Sign")
    parser.add_argument("--test-login", action="store_true", help="Test login functionality")
    parser.add_argument("--test-notification", action="store_true", help="Test notification functionality")
    return parser.parse_args()

def test_login_and_notification(app_context):
    """Test login and notification functionality"""
    try:
        # Get services
        notification_service = app_context.get_notification_service()
        login_service = app_context.get_login_service()
        
        logger.info("Starting login test")
        
        # Test login
        accounts = get_ptt_accounts()
        results = login_service.batch_login(accounts)
        
        # Print results
        success_count = sum(1 for success in results.values() if success)
        logger.info(f"Login test completed")
        logger.info(f"Total accounts: {len(accounts)}")
        logger.info(f"Successful logins: {success_count}")
        logger.info(f"Failed logins: {len(accounts) - success_count}")
        
        if success_count < len(accounts):
            failed_accounts = [account for account, success in results.items() if not success]
            logger.warning(f"Failed accounts: {', '.join(failed_accounts)}")
        
        # Test Telegram notification if requested
        if args.test_notification:
            logger.info("Sending test notification to Telegram...")
            message = f'🧪 PTT Auto Sign Test\n\n✅ Login test completed successfully\nAccounts: {len(accounts)}\nSuccessful: {success_count}'
            result = notification_service.send_message(message)
            
            if result:
                logger.info("Telegram notification sent successfully")
            else:
                logger.error("Failed to send Telegram notification")
                
    except Exception as e:
        logger.error(f"Error during test: {str(e)}", exc_info=True)
        return False
    
    return True

def main():
    """Main entry point for the PTT Auto Sign program"""
    try:
        # Parse command line arguments
        global args
        args = parse_args()
        
        # Create and initialize application context
        app_context = AppContext()
        app_context.initialize()
        
        # Check if we're running in test mode
        if args.test_login:
            logger.info("Running in test mode")
            success = test_login_and_notification(app_context)
            if not success:
                exit(1)
        else:
            # Run the application normally
            app_context.run()
        
    except ConfigValidationError as e:
        logger.error(f"Configuration error: {str(e)}", exc_info=True)
        exit(1)
    except Exception as e:
        logger.error(f"Runtime error: {str(e)}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()
