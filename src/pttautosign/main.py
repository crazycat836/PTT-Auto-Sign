import os
import sys
import logging
import argparse
from dotenv import load_dotenv

# Configure basic logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our patches before importing any PyPtt related modules
logger.info("Applying compatibility patches...")
from pttautosign.patches import monkey_patch, pyptt_patch
logger.info("Patches applied, continuing with imports...")

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
        
        # Test login (without sending notifications for each login)
        accounts = get_ptt_accounts()
        results = login_service.batch_login(accounts, send_notification=False)
        
        # Print results
        success_count = sum(1 for success in results.values() if success)
        print(f'\nLogin Test Results:')
        print(f'Total accounts: {len(accounts)}')
        print(f'Successful logins: {success_count}')
        print(f'Failed logins: {len(accounts) - success_count}')
        
        if success_count < len(accounts):
            failed_accounts = [account for account, success in results.items() if not success]
            print(f'\nFailed accounts: {", ".join(failed_accounts)}')
        
        # Test Telegram notification if requested
        if args.test_notification:
            print('\nSending test notification to Telegram...')
            message = f'🧪 PTT Auto Sign Test\n\n✅ Login test completed successfully\nAccounts: {len(accounts)}\nSuccessful: {success_count}'
            result = notification_service.send_message(message)
            
            if result:
                print('✅ Telegram notification sent successfully')
            else:
                print('❌ Failed to send Telegram notification')
                
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
