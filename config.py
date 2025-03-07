import os
from typing import Union, Dict, Type
from dataclasses import dataclass
from dotenv import load_dotenv
from PyPtt import exceptions as PTT_exceptions
import logging

# Load environment variables
load_dotenv()

@dataclass
class TelegramConfig:
    """Telegram configuration"""
    token: str
    chat_id: Union[str, int]
    
    @classmethod
    def from_env(cls) -> 'TelegramConfig':
        """Load configuration from environment variables"""
        token = os.getenv("bot_token")
        chat_id = os.getenv("chat_id")
        if not token or not chat_id:
            raise ValueError("Telegram bot token or chat id not set")
        return cls(token=token, chat_id=chat_id)

@dataclass
class PTTConfig:
    """PTT configuration"""
    timezone_hours: int = 8
    error_messages: Dict[Type[Exception], str] = None

    def __post_init__(self):
        """Initialize error messages after instance creation"""
        if self.error_messages is None:
            self.error_messages = {
                PTT_exceptions.NoSuchUser: "PTT login failed!\nUser not found",
                PTT_exceptions.WrongIDorPassword: "PTT login failed!\nIncorrect username or password",
                PTT_exceptions.WrongPassword: "PTT login failed!\nIncorrect password",
                PTT_exceptions.LoginTooOften: "PTT login failed!\nToo many login attempts",
                PTT_exceptions.UseTooManyResources: "PTT login failed!\nToo many resources used",
                PTT_exceptions.UnregisteredUser: "Unregistered user"
            }

@dataclass
class LogConfig:
    """Logging configuration"""
    log_dir: str = "logs"
    log_file: str = "ptt_auto_sign.log"
    backup_count: int = 7
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_level: int = logging.INFO

def get_ptt_accounts() -> list[tuple[str, str]]:
    """Get PTT account information from environment variables
    
    Returns:
        list[tuple[str, str]]: List of PTT username and password tuples
    """
    accounts = []
    
    # Check main account
    main_account = os.getenv("ptt_id_1")
    if not main_account:
        raise ValueError("Main PTT account not set")
    if main_account.lower() not in ["none", "none,none"]:
        accounts.append(tuple(main_account.split(",")))
    
    # Check additional accounts
    for i in range(2, 6):
        account = os.getenv(f"ptt_id_{i}")
        if account and account.lower() not in ["none", "none,none"]:
            accounts.append(tuple(account.split(",")))
    
    return accounts 