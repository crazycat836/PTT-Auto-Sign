"""
PTT auto sign-in module for handling PTT login operations.
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple, List
from PyPtt import PTT
from PyPtt import exceptions as PTT_exceptions
from pttautosign.utils.config import PTTConfig
from pttautosign.utils.interfaces import LoginService, NotificationService

class PTTAutoSign(LoginService):
    """PTT auto sign-in handler class"""
    
    def __init__(self, telegram_bot: NotificationService, config: Optional[PTTConfig] = None):
        """Initialize the PTT auto sign-in handler
        
        Args:
            telegram_bot: Notification service for sending notifications
            config: Optional PTT configuration. If None, default config will be used.
        """
        self.ptt = PTT.API(log_level=PTT.log.INFO)
        self.telegram = telegram_bot
        self.config = config or PTTConfig()
        self.tz = timezone(timedelta(hours=self.config.timezone_hours))
        self.logger = logging.getLogger("pttautosign")
        self.retry_count = 0
        self.max_retries = 3

    def _format_success_message(self, ptt_id: str, user_info: Dict[str, Any]) -> str:
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
    
    def _format_error_message(self, ptt_id: str, error: Exception) -> str:
        """Format error message
        
        Args:
            ptt_id: PTT username
            error: Exception that occurred
            
        Returns:
            str: Formatted error message
        """
        error_message = self.config.error_messages.get(type(error), str(error))
        if isinstance(error, PTT_exceptions.UnregisteredUser):
            error_message = f"{ptt_id} {error_message}"
        
        return f"❌ {error_message}"

    def login(self, ptt_id: str, ptt_passwd: str) -> bool:
        """Perform login
        
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
            self.retry_count = 0  # Reset retry count on success
            return True
            
        except exceptions_to_catch as e:
            error_message = self._format_error_message(ptt_id, e)
            self.logger.error(f"Login failed for account {ptt_id}: {error_message}")
            
            # Handle retries for temporary errors
            if isinstance(e, (PTT_exceptions.LoginTooOften, PTT_exceptions.UseTooManyResources)) and self.retry_count < self.max_retries:
                self.retry_count += 1
                self.logger.info(f"Retrying login for {ptt_id} (attempt {self.retry_count}/{self.max_retries})")
                # Wait before retrying (exponential backoff)
                time.sleep(2 ** self.retry_count)
                return self.login(ptt_id, ptt_passwd)
            
            self.telegram.send_message(error_message)
            return False
            
        except Exception as e:
            self.logger.error(f"Unexpected error during login for account {ptt_id}: {str(e)}")
            self.telegram.send_message(f"❌ Unexpected error: {str(e)}")
            return False
            
        finally:
            try:
                # 直接嘗試登出，不檢查是否已登入
                self.ptt.logout()
                self.logger.debug(f"Logged out PTT account: {ptt_id}")
            except Exception as e:
                self.logger.debug(f"Logout not needed for account {ptt_id}: {str(e)}")
    
    def batch_login(self, accounts: Dict[str, str]) -> Dict[str, bool]:
        """Perform batch login for multiple accounts
        
        Args:
            accounts: Dictionary mapping usernames to passwords
            
        Returns:
            Dict[str, bool]: Dictionary mapping usernames to login success status
        """
        results = {}
        for ptt_id, ptt_passwd in accounts.items():
            results[ptt_id] = self.login(ptt_id, ptt_passwd)
        return results
        
    # Keep the old method name for backward compatibility
    daily_login = login 