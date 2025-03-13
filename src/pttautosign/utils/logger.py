"""
Logging configuration module.
"""

import json
import logging
import platform
import socket
from typing import Optional, Dict, Any, Union
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

class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def __init__(self, include_hostname: bool = True):
        """Initialize JSON formatter
        
        Args:
            include_hostname: Whether to include hostname in logs
        """
        super().__init__()
        self.include_hostname = include_hostname
        self.hostname = socket.gethostname() if include_hostname else None
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON
        
        Args:
            record: Log record to format
            
        Returns:
            str: JSON formatted log record
        """
        log_data = {
            "timestamp": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        
        # Add hostname if enabled
        if self.include_hostname:
            log_data["hostname"] = self.hostname
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ["args", "asctime", "created", "exc_info", "exc_text", 
                          "filename", "funcName", "id", "levelname", "levelno", 
                          "lineno", "module", "msecs", "message", "msg", 
                          "name", "pathname", "process", "processName", 
                          "relativeCreated", "stack_info", "thread", "threadName"]:
                log_data[key] = value
        
        return json.dumps(log_data)

def setup_logging(config: Optional[LogConfig] = None, 
                  use_json: bool = False,
                  include_hostname: bool = True) -> logging.Logger:
    """Setup logging configuration
    
    Args:
        config: Optional logging configuration. If None, default config will be used.
        use_json: Whether to use JSON formatter for structured logging
        include_hostname: Whether to include hostname in logs (only for JSON format)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    if config is None:
        config = LogConfig()

    # Configure logging format
    if use_json:
        log_formatter = JsonFormatter(include_hostname=include_hostname)
    else:
        log_formatter = logging.Formatter(config.log_format, datefmt="%Y-%m-%d %H:%M:%S")

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
    
    # Log system information
    logger = logging.getLogger("pttautosign")
    logger.info(f"Logging initialized: level={logging.getLevelName(config.log_level)}, format={'JSON' if use_json else 'text'}")
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