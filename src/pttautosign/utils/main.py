import os
import sys
import logging
from dotenv import load_dotenv

# Configure basic logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("pttautosign")

# Import our patches before importing any PyPtt related modules
logger.info("Applying compatibility patches...")
from pttautosign.patches import monkey_patch  # Telnetlib compatibility layer
from pttautosign.patches import pyptt_patch   # PyPtt compatibility fixes
logger.info("Patches applied, continuing with imports...")

# Load environment variables from .env file for local development
load_dotenv()

# Import modules after environment variables are loaded
from pttautosign.utils.config import ConfigValidationError
from pttautosign.utils.app_context import AppContext

def main():
    """Main entry point for the PTT Auto Sign program"""
    try:
        # Create and initialize application context
        app_context = AppContext()
        app_context.initialize()
        
        # Run the application
        app_context.run()
        
    except ConfigValidationError as e:
        logger.error(f"Configuration error: {str(e)}")
        exit(1)
    except Exception as e:
        logger.error(f"Runtime error: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
