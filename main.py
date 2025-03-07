import os
import requests
from dotenv import load_dotenv
from PyPtt import PTT
from PyPtt import exceptions as PTT_exceptions
from datetime import datetime, timezone, timedelta
from typing import Union
from dataclasses import dataclass

# Load environment variables from .env file for local development
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


class TelegramBot:
    """Telegram Bot handler class"""
    def __init__(self, config: TelegramConfig):
        self.config = config
        self.api_url = f"https://api.telegram.org/bot{config.token}"

    def send_message(self, text: str) -> bool:
        """Send message to Telegram
        
        Args:
            text: Message content to send
            
        Returns:
            bool: Whether the message was sent successfully
        """
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.config.chat_id,
                    "text": text,
                    "parse_mode": "html"
                }
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to send Telegram message: {e}")
            return False


class PTTAutoSign:
    """PTT auto sign-in handler class"""
    
    # Error message mapping
    ERROR_MESSAGES = {
        PTT_exceptions.NoSuchUser: "PTT login failed!\nUser not found",
        PTT_exceptions.WrongIDorPassword: "PTT login failed!\nIncorrect username or password",
        PTT_exceptions.WrongPassword: "PTT login failed!\nIncorrect password",
        PTT_exceptions.LoginTooOften: "PTT login failed!\nToo many login attempts",
        PTT_exceptions.UseTooManyResources: "PTT login failed!\nToo many resources used",
        PTT_exceptions.UnregisteredUser: "Unregistered user"
    }
    
    def __init__(self, telegram_bot: TelegramBot):
        self.ptt = PTT.API(log_level=PTT.log.INFO)
        self.telegram = telegram_bot
        self.tz = timezone(timedelta(hours=+8))  # Set timezone to UTC+8

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
        try:
            self.ptt.login(ptt_id, ptt_passwd, kick_other_session=True)
            user_info = self.ptt.get_user(ptt_id)
            success_message = self._format_success_message(ptt_id, user_info)
            self.telegram.send_message(success_message)
            return True
            
        except tuple(self.ERROR_MESSAGES.keys()) as e:
            error_message = self.ERROR_MESSAGES[type(e)]
            if isinstance(e, PTT_exceptions.UnregisteredUser):
                error_message = f"{ptt_id} {error_message}"
            self.telegram.send_message(error_message)
            return False
            
        finally:
            try:
                self.ptt.logout()
            except:
                pass  # Ignore logout errors


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


def main():
    """Main program entry point"""
    try:
        # Initialize configurations
        telegram_config = TelegramConfig.from_env()
        telegram_bot = TelegramBot(telegram_config)
        ptt_auto_sign = PTTAutoSign(telegram_bot)
        
        # Get account list and perform login
        accounts = get_ptt_accounts()
        for ptt_id, ptt_passwd in accounts:
            ptt_auto_sign.daily_login(ptt_id, ptt_passwd)
            
    except ValueError as e:
        print(f"Configuration error: {e}")
        exit(1)
    except Exception as e:
        print(f"Runtime error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
