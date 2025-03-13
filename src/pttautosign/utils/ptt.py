"""
PTT auto sign-in module for handling PTT login operations.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple, List
from PyPtt import PTT
from PyPtt import exceptions as PTT_exceptions
from pttautosign.utils.config import PTTConfig
from pttautosign.utils.telegram import TelegramBot
from pttautosign.utils.interfaces import LoginService, NotificationService

class PTTAutoSign(LoginService):
    """PTT auto sign-in handler class"""
    
    def __init__(self, telegram_bot: NotificationService, config: Optional[PTTConfig] = None):
        """Initialize the PTT auto sign-in handler
        
        Args:
            telegram_bot: Notification service for sending notifications
            config: Optional PTT configuration. If None, default config will be used.
        """
        self.ptt = PTT.API(log_level=PTT.log.SILENT)
        self.telegram = telegram_bot
        self.config = config or PTTConfig()
        self.tz = timezone(timedelta(hours=self.config.timezone_hours))
        self.logger = logging.getLogger(__name__)
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

    def login(self, ptt_id: str, ptt_passwd: str, send_notification: bool = True) -> bool:
        """Perform login
        
        Args:
            ptt_id: PTT username
            ptt_passwd: PTT password
            send_notification: Whether to send notification on success/failure
            
        Returns:
            bool: Whether login was successful
        """
        self.logger.info(f"Attempting to login PTT account: {ptt_id}")
        exceptions_to_catch = tuple(self.config.error_messages.keys())
        
        try:
            self.ptt.login(ptt_id, ptt_passwd, kick_other_session=True)
            user_info = self.ptt.get_user(ptt_id)
            success_message = self._format_success_message(ptt_id, user_info)
            
            if send_notification:
                self.telegram.send_message(success_message)
                
            self.logger.info(f"Successfully logged in PTT account: {ptt_id}")
            self.retry_count = 0  # Reset retry count on success
            return True
            
        except exceptions_to_catch as e:
            error_message = self._format_error_message(ptt_id, e)
            self.logger.error(f"Login failed for account {ptt_id}: {error_message}", exc_info=True)
            
            # Handle retries for temporary errors
            if isinstance(e, (PTT_exceptions.LoginTooOften, PTT_exceptions.UseTooManyResources)) and self.retry_count < self.max_retries:
                self.retry_count += 1
                self.logger.info(f"Retrying login for {ptt_id} (attempt {self.retry_count}/{self.max_retries})")
                # Wait before retrying (exponential backoff)
                import time
                time.sleep(2 ** self.retry_count)
                return self.login(ptt_id, ptt_passwd, send_notification)
            
            if send_notification:
                self.telegram.send_message(error_message)
                
            return False
            
        except Exception as e:
            self.logger.error(f"Unexpected error during login for account {ptt_id}: {str(e)}", exc_info=True)
            
            if send_notification:
                self.telegram.send_message(f"❌ Unexpected error: {str(e)}")
                
            return False
            
        finally:
            try:
                # Check if the ptt object has the is_login method
                if hasattr(self.ptt, 'is_login') and callable(self.ptt.is_login) and self.ptt.is_login():
                    self.ptt.logout()
                    self.logger.debug(f"Logged out PTT account: {ptt_id}")
                else:
                    # Attempt to logout directly if is_login method is not available
                    try:
                        self.ptt.logout()
                        self.logger.debug(f"Logged out PTT account: {ptt_id}")
                    except Exception:
                        pass
            except Exception as e:
                self.logger.warning(f"Error during logout for account {ptt_id}: {str(e)}")
    
    def batch_login(self, accounts: List[Tuple[str, str]], send_notification: bool = True) -> Dict[str, bool]:
        """Perform batch login for multiple accounts
        
        Args:
            accounts: List of (username, password) tuples
            send_notification: Whether to send notification on success/failure
            
        Returns:
            Dict[str, bool]: Dictionary mapping usernames to login success status
        """
        results = {}
        for ptt_id, ptt_passwd in accounts:
            results[ptt_id] = self.login(ptt_id, ptt_passwd, send_notification)
        return results
        
    # Keep the old method name for backward compatibility
    daily_login = login 