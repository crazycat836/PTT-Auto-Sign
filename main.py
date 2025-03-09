import os
import requests
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from dotenv import load_dotenv
from PyPtt import PTT
from PyPtt import exceptions as PTT_exceptions
from datetime import datetime, timezone, timedelta
from typing import Union, Optional
from dataclasses import dataclass
from config import TelegramConfig, PTTConfig, get_ptt_accounts
from utils.logger import setup_logging

# Load environment variables from .env file for local development
load_dotenv()

class TelegramBot:
    """Telegram Bot handler class"""
    def __init__(self, config: TelegramConfig):
        self.config = config
        self.api_url = f"https://api.telegram.org/bot{config.token}"
        self.logger = logging.getLogger(__name__)

    def send_message(self, text: str) -> bool:
        """Send message to Telegram
        
        Args:
            text: Message content to send
            
        Returns:
            bool: Whether the message was sent successfully
        """
        try:
            self.logger.info(f"Sending Telegram message: {text[:50]}...")
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.config.chat_id,
                    "text": text,
                    "parse_mode": "html"
                }
            )
            response.raise_for_status()
            self.logger.info("Telegram message sent successfully")
            return True
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send Telegram message: {str(e)}", exc_info=True)
            return False


class PTTAutoSign:
    """PTT auto sign-in handler class"""
    
    def __init__(self, telegram_bot: TelegramBot, config: Optional[PTTConfig] = None):
        self.ptt = PTT.API(log_level=PTT.log.INFO)
        self.telegram = telegram_bot
        self.config = config or PTTConfig()
        self.tz = timezone(timedelta(hours=self.config.timezone_hours))
        self.logger = logging.getLogger(__name__)

    def _format_success_message(self, ptt_id: str, user_info: dict) -> str:
        """Format successful login message
        
        Args:
            ptt_id: PTT username
            user_info: User information dictionary
            
        Returns:
            str: Formatted success message
        """
        now = datetime.now(self.tz)
        return (
            f"✅ PTT {ptt_id} signed in successfully\n"
            f"📆 Login streak: {user_info.get('login_count')} days\n"
            f"📫 {user_info.get('mail')}\n"
            f"#ptt #{now.strftime('%Y%m%d')}"
        )

    def daily_login(self, ptt_id: str, ptt_passwd: str) -> bool:
        """Perform daily login
        
        Args:
            ptt_id: PTT username
            ptt_passwd: PTT password
            
        Returns:
            bool: Whether login was successful
        """
        self.logger.info(f"Attempting to login PTT account: {ptt_id}")
        exceptions_to_catch = tuple(self.config.error_messages.keys())
        try:
            self.ptt.login(ptt_id, ptt_passwd, kick_other_session=True)
            user_info = self.ptt.get_user(ptt_id)
            success_message = self._format_success_message(ptt_id, user_info)
            self.telegram.send_message(success_message)
            self.logger.info(f"Successfully logged in PTT account: {ptt_id}")
            return True
            
        except exceptions_to_catch as e:
            error_message = self.config.error_messages.get(type(e), str(e))
            if isinstance(e, PTT_exceptions.UnregisteredUser):
                error_message = f"{ptt_id} {error_message}"
            self.logger.error(f"Login failed for account {ptt_id}: {error_message}", exc_info=True)
            self.telegram.send_message(error_message)
            return False
            
        finally:
            try:
                self.ptt.logout()
                self.logger.debug(f"Logged out PTT account: {ptt_id}")
            except Exception as e:
                self.logger.warning(f"Error during logout for account {ptt_id}: {str(e)}")


def main():
    """Main program entry point"""
    logger = setup_logging()
    try:
        logger.info("Starting PTT Auto Sign program")
        # Initialize configurations
        telegram_config = TelegramConfig.from_env()
        telegram_bot = TelegramBot(telegram_config)
        ptt_auto_sign = PTTAutoSign(telegram_bot)
        
        # Get account list and perform login
        accounts = get_ptt_accounts()
        for ptt_id, ptt_passwd in accounts:
            ptt_auto_sign.daily_login(ptt_id, ptt_passwd)
            
        logger.info("PTT Auto Sign program completed successfully")
            
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}", exc_info=True)
        exit(1)
    except Exception as e:
        logger.error(f"Runtime error: {str(e)}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()
