"""
Logging configuration module.
"""

import logging
import platform
from typing import Optional
from pttautosign.utils.config import LogConfig

# Add TRACE level
TRACE = 5
logging.addLevelName(TRACE, "TRACE")

def trace(self, message, *args, **kwargs):
    """Log 'message' at TRACE level"""
    if self.isEnabledFor(TRACE):
        self._log(TRACE, message, args, **kwargs)

# Add method to Logger class
logging.Logger.trace = trace

def setup_logging(config: Optional[LogConfig] = None) -> logging.Logger:
    """Setup logging configuration
    
    Args:
        config: Optional logging configuration. If None, default config will be used.
        
    Returns:
        logging.Logger: Configured logger instance
    """
    if config is None:
        config = LogConfig()

    # Configure logging format
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
    
    # Use a more consistent format with shorter module name
    log_format = config.log_format
    
    # Create a custom formatter that shortens the logger name and adds colors
    class ColorShortNameFormatter(logging.Formatter):
        def format(self, record):
            # LogRecord is shared across handlers/formatters, so any field we
            # change must be restored afterwards (the original code leaked the
            # shortened name onto the record). Save → mutate → format → restore.
            original_name = record.name
            original_levelname = record.levelname
            try:
                parts = original_name.split('.')
                if len(parts) > 2:
                    # For deeply nested modules, show only the last two parts
                    record.name = '.'.join(parts[-2:])

                if original_levelname in COLORS:
                    record.levelname = (
                        f"{COLORS[original_levelname]}{original_levelname}{COLORS['RESET']}"
                    )

                return super().format(record)
            finally:
                record.name = original_name
                record.levelname = original_levelname
    
    log_formatter = ColorShortNameFormatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(config.log_level)

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(config.log_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler only
    root_logger.addHandler(console_handler)
    
    # Set PyPtt logger to a higher level to suppress its logs
    logging.getLogger('PyPtt').setLevel(logging.ERROR)

    # Force noisy third-party loggers to WARNING even when DEBUG_MODE=true.
    # Their DEBUG output dumps raw protocol frames that contain the PTT
    # username/password and the Telegram bot token URL — never let them
    # bypass our redaction discipline.
    for noisy in ("asyncio", "websockets", "websockets.client",
                  "websockets.server", "urllib3", "requests"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    
    # Log system information
    logger = logging.getLogger(__name__)
    logger.debug(f"Logging initialized: level={logging.getLevelName(config.log_level)}")
    logger.debug(f"System: {platform.system()} {platform.release()}, Python: {platform.python_version()}")

    return logger

def get_logger(name: str) -> logging.Logger:
    """Get logger with the given name
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name) 