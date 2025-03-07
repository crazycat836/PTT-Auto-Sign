import os
import logging
from logging.handlers import TimedRotatingFileHandler
from typing import Optional
from config import LogConfig

def setup_logging(config: Optional[LogConfig] = None) -> logging.Logger:
    """Setup logging configuration
    
    Args:
        config: Optional logging configuration. If None, default config will be used.
        
    Returns:
        logging.Logger: Configured logger instance
    """
    if config is None:
        config = LogConfig()

    # Create logs directory if it doesn't exist
    if not os.path.exists(config.log_dir):
        os.makedirs(config.log_dir)

    # Configure logging format
    log_format = logging.Formatter(config.log_format)

    # Setup file handler with daily rotation
    file_handler = TimedRotatingFileHandler(
        os.path.join(config.log_dir, config.log_file),
        when='midnight',  # Rotate at midnight
        interval=1,  # Every day
        backupCount=config.backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(config.log_level)

    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler.setLevel(config.log_level)

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(config.log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Clean up old log files
    try:
        for handler in root_logger.handlers:
            if isinstance(handler, TimedRotatingFileHandler):
                handler.doRollover()
    except Exception as e:
        print(f"Error during log rotation: {str(e)}")

    return root_logger 