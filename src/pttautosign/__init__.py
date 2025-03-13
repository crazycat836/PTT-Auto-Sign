"""
PTT Auto Sign - A tool for automatic PTT login with Telegram notifications.
"""

__version__ = "1.1.0"
__author__ = "crazycat836"
__email__ = "crazycat836@gmail.com"

# Import patches first to ensure compatibility
from pttautosign.patches import monkey_patch, pyptt_patch

# Import main modules
from pttautosign.utils.config import AppConfig, ConfigValidationError
from pttautosign.utils.app_context import AppContext
from pttautosign.main import main

# Define what's available when importing the package
__all__ = [
    'AppConfig',
    'ConfigValidationError',
    'AppContext',
    'main',
]
