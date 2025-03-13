"""
Configuration module for PTT Auto Sign.
"""

import os
import re
import json
import logging
from typing import Union, Dict, Type, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from dotenv import load_dotenv
from PyPtt import exceptions as PTT_exceptions

# Load environment variables
load_dotenv()

class ConfigValidationError(Exception):
    """Exception raised for configuration validation errors"""
    pass

@dataclass
class TelegramConfig:
    """Telegram configuration"""
    token: str
    chat_id: Union[str, int]
    disable_notification: bool = False
    retry_count: int = 3
    timeout: int = 10
    
    def validate(self) -> None:
        """Validate configuration
        
        Raises:
            ConfigValidationError: If configuration is invalid
        """
        if not self.token:
            raise ConfigValidationError("Telegram bot token is required")
        
        if not re.match(r'^\d+:[A-Za-z0-9_-]+$', self.token):
            raise ConfigValidationError("Invalid Telegram bot token format")
        
        if not self.chat_id:
            raise ConfigValidationError("Telegram chat ID is required")
        
        if self.retry_count < 0:
            raise ConfigValidationError("Retry count must be non-negative")
        
        if self.timeout <= 0:
            raise ConfigValidationError("Timeout must be positive")
    
    @classmethod
    def from_env(cls) -> 'TelegramConfig':
        """Load configuration from environment variables
        
        Returns:
            TelegramConfig: Telegram configuration
            
        Raises:
            ConfigValidationError: If required environment variables are missing
        """
        token = os.getenv("bot_token")
        chat_id = os.getenv("chat_id")
        disable_notification = os.getenv("disable_notification", "false").lower() == "true"
        retry_count = int(os.getenv("telegram_retry_count", "3"))
        timeout = int(os.getenv("telegram_timeout", "10"))
        
        if not token or not chat_id:
            raise ConfigValidationError("Telegram bot token or chat id not set in environment variables")
        
        config = cls(
            token=token,
            chat_id=chat_id,
            disable_notification=disable_notification,
            retry_count=retry_count,
            timeout=timeout
        )
        
        config.validate()
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary
        
        Returns:
            Dict[str, Any]: Configuration as dictionary
        """
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert configuration to JSON
        
        Returns:
            str: Configuration as JSON string
        """
        return json.dumps(self.to_dict(), indent=2)

@dataclass
class PTTConfig:
    """PTT configuration"""
    timezone_hours: int = 8
    error_messages: Dict[Type[Exception], str] = field(default_factory=dict)
    max_retries: int = 3
    retry_delay: int = 2
    connection_timeout: int = 30
    kick_other_session: bool = True
    
    def __post_init__(self):
        """Initialize error messages after instance creation"""
        if not self.error_messages:
            self.error_messages = {
                PTT_exceptions.NoSuchUser: "PTT login failed!\nUser not found",
                PTT_exceptions.WrongIDorPassword: "PTT login failed!\nIncorrect username or password",
                PTT_exceptions.WrongPassword: "PTT login failed!\nIncorrect password",
                PTT_exceptions.LoginTooOften: "PTT login failed!\nToo many login attempts",
                PTT_exceptions.UseTooManyResources: "PTT login failed!\nToo many resources used",
                PTT_exceptions.UnregisteredUser: "Unregistered user"
            }
    
    def validate(self) -> None:
        """Validate configuration
        
        Raises:
            ConfigValidationError: If configuration is invalid
        """
        if not -12 <= self.timezone_hours <= 14:
            raise ConfigValidationError("Timezone hours must be between -12 and 14")
        
        if self.max_retries < 0:
            raise ConfigValidationError("Max retries must be non-negative")
        
        if self.retry_delay <= 0:
            raise ConfigValidationError("Retry delay must be positive")
        
        if self.connection_timeout <= 0:
            raise ConfigValidationError("Connection timeout must be positive")
    
    @classmethod
    def from_env(cls) -> 'PTTConfig':
        """Load configuration from environment variables
        
        Returns:
            PTTConfig: PTT configuration
        """
        timezone_hours = int(os.getenv("timezone_hours", "8"))
        max_retries = int(os.getenv("ptt_max_retries", "3"))
        retry_delay = int(os.getenv("ptt_retry_delay", "2"))
        connection_timeout = int(os.getenv("ptt_connection_timeout", "30"))
        kick_other_session = os.getenv("ptt_kick_other_session", "true").lower() == "true"
        
        config = cls(
            timezone_hours=timezone_hours,
            max_retries=max_retries,
            retry_delay=retry_delay,
            connection_timeout=connection_timeout,
            kick_other_session=kick_other_session
        )
        
        config.validate()
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary
        
        Returns:
            Dict[str, Any]: Configuration as dictionary
        """
        result = asdict(self)
        # Remove error_messages as it contains exception types that can't be serialized
        result.pop("error_messages", None)
        return result
    
    def to_json(self) -> str:
        """Convert configuration to JSON
        
        Returns:
            str: Configuration as JSON string
        """
        return json.dumps(self.to_dict(), indent=2)

@dataclass
class LogConfig:
    """Logging configuration"""
    log_format: str = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    log_level: int = logging.INFO
    use_json_format: bool = False
    include_hostname: bool = True
    
    def validate(self) -> None:
        """Validate configuration
        
        Raises:
            ConfigValidationError: If configuration is invalid
        """
        # No validation needed for console-only logging
        pass
    
    @classmethod
    def from_env(cls) -> 'LogConfig':
        """Load configuration from environment variables
        
        Returns:
            LogConfig: Logging configuration
        """
        log_format = os.getenv("log_format", '%(asctime)s [%(name)s] %(levelname)s: %(message)s')
        
        log_level_str = os.getenv("log_level", "INFO").upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        
        use_json_format = os.getenv("log_json_format", "false").lower() == "true"
        include_hostname = os.getenv("log_include_hostname", "true").lower() == "true"
        
        config = cls(
            log_format=log_format,
            log_level=log_level,
            use_json_format=use_json_format,
            include_hostname=include_hostname
        )
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary
        
        Returns:
            Dict[str, Any]: Configuration as dictionary
        """
        result = asdict(self)
        # Convert log level to string
        result["log_level"] = logging.getLevelName(self.log_level)
        return result
    
    def to_json(self) -> str:
        """Convert configuration to JSON
        
        Returns:
            str: Configuration as JSON string
        """
        return json.dumps(self.to_dict(), indent=2)

@dataclass
class AppConfig:
    """Application configuration"""
    telegram: TelegramConfig
    ptt: PTTConfig
    log: LogConfig
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Load configuration from environment variables
        
        Returns:
            AppConfig: Application configuration
        """
        return cls(
            telegram=TelegramConfig.from_env(),
            ptt=PTTConfig.from_env(),
            log=LogConfig.from_env()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary
        
        Returns:
            Dict[str, Any]: Configuration as dictionary
        """
        return {
            "telegram": self.telegram.to_dict(),
            "ptt": self.ptt.to_dict(),
            "log": self.log.to_dict()
        }
    
    def to_json(self) -> str:
        """Convert configuration to JSON
        
        Returns:
            str: Configuration as JSON string
        """
        return json.dumps(self.to_dict(), indent=2)

def get_ptt_accounts() -> List[Tuple[str, str]]:
    """Get PTT account information from environment variables
    
    Returns:
        List[Tuple[str, str]]: List of PTT username and password tuples
        
    Raises:
        ConfigValidationError: If no valid accounts are found
    """
    accounts = []
    
    # Check main account
    main_account = os.getenv("ptt_id_1")
    if not main_account:
        raise ConfigValidationError("Main PTT account not set in environment variables")
    
    if main_account.lower() not in ["none", "none,none"]:
        parts = main_account.split(",")
        if len(parts) != 2:
            raise ConfigValidationError(f"Invalid account format for ptt_id_1: {main_account}")
        username, password = parts
        if not username or not password:
            raise ConfigValidationError(f"Username and password cannot be empty for ptt_id_1")
        accounts.append((username, password))
    
    # Check additional accounts
    for i in range(2, 6):
        account = os.getenv(f"ptt_id_{i}")
        if account and account.lower() not in ["none", "none,none"]:
            parts = account.split(",")
            if len(parts) != 2:
                raise ConfigValidationError(f"Invalid account format for ptt_id_{i}: {account}")
            username, password = parts
            if not username or not password:
                raise ConfigValidationError(f"Username and password cannot be empty for ptt_id_{i}")
            accounts.append((username, password))
    
    if not accounts:
        raise ConfigValidationError("No valid PTT accounts found in environment variables")
    
    return accounts

def validate_all_configs() -> None:
    """Validate all configurations
    
    Raises:
        ConfigValidationError: If any configuration is invalid
    """
    # Validate Telegram config
    TelegramConfig.from_env()
    
    # Validate PTT config
    PTTConfig.from_env()
    
    # Validate Log config
    LogConfig.from_env()
    
    # Validate PTT accounts
    get_ptt_accounts()
    
    # If we get here, all configurations are valid
    return True 