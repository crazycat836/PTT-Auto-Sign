"""
PTT auto sign-in module for handling PTT login operations.
"""

import time
import logging
import concurrent.futures
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple, List
from PyPtt import PTT
from PyPtt import exceptions as PTT_exceptions
from pttautosign.utils.config import PTTConfig
from pttautosign.utils.interfaces import LoginService, NotificationService

class PTTAutoSign(LoginService):
    """PTT auto sign-in handler class"""

    def __init__(self, telegram_bot: NotificationService, config: PTTConfig | None = None, disable_notifications: bool = False):
        """Initialize the PTT auto sign-in handler

        Args:
            telegram_bot: Notification service for sending notifications
            config: Optional PTT configuration. If None, default config will be used.
            disable_notifications: Whether to disable notifications
        """
        self.telegram = telegram_bot
        self.config = config or PTTConfig()
        self.tz = timezone(timedelta(hours=self.config.timezone_hours))
        self.logger = logging.getLogger(__name__)
        self.max_retries = 3
        self.disable_notifications = disable_notifications

    def _format_success_message(self, ptt_id: str, user_info: Dict[str, Any]) -> str:
        """Format successful login message
        
        Args:
            ptt_id: PTT username
            user_info: User information dictionary
            
        Returns:
            str: Formatted success message
        """
        now = datetime.now(self.tz)
        
        # 將英文郵件訊息翻譯為中文
        mail_msg = user_info.get('mail', '')
        if mail_msg == 'No new mails':
            mail_msg = '最近無新信件'
        elif 'New mails' in mail_msg:
            # 將 'You have 3 new mails' 轉換為 '您有 3 封新信件'
            count = mail_msg.split()[2]
            mail_msg = f'您有 {count} 封新信件'
        
        return (
            f"✅ PTT {ptt_id} 登入成功\n"
            f"📆 登入天數: {user_info.get('login_count')} 天\n"
            f"📫 {mail_msg}\n"
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
        
        # 如果是未知錯誤類型，加上中文前綴
        if type(error) not in self.config.error_messages:
            error_message = f"未知錯誤: {error_message}"
        
        return f"❌ {error_message}"

    def _safe_logout(self, ptt_bot, ptt_id: str) -> None:
        """Safely logout a PTT bot instance."""
        try:
            ptt_bot.logout()
            self.logger.debug(f"已登出 PTT 帳號：{ptt_id}")
        except Exception as e:
            self.logger.warning(f"帳號 {ptt_id} 登出時發生錯誤：{e}")

    def login(self, ptt_id: str, ptt_passwd: str, send_notification: bool = True) -> bool:
        """Perform login with retries.

        Args:
            ptt_id: PTT username
            ptt_passwd: PTT password
            send_notification: Whether to send notification on success/failure

        Returns:
            bool: Whether login was successful
        """
        exceptions_to_catch = tuple(self.config.error_messages.keys())

        for attempt in range(self.max_retries + 1):
            ptt_bot = None
            try:
                ptt_bot = PTT.API(log_level=PTT.log.SILENT)
                ptt_bot.login(ptt_id, ptt_passwd, kick_other_session=True)
                user_info = ptt_bot.get_user(ptt_id)
                success_message = self._format_success_message(ptt_id, user_info)

                if send_notification and not self.disable_notifications:
                    self.telegram.send_message(success_message)

                return True

            except exceptions_to_catch as e:
                error_message = self._format_error_message(ptt_id, e)
                self.logger.error(f"帳號 {ptt_id} 登入失敗：{error_message}", exc_info=True)

                # Retry for temporary errors
                if isinstance(e, (PTT_exceptions.LoginTooOften, PTT_exceptions.UseTooManyResources)) and attempt < self.max_retries:
                    self.logger.debug(f"正在重試帳號 {ptt_id} 的登入（第 {attempt + 1}/{self.max_retries} 次嘗試）")
                    time.sleep(2 ** (attempt + 1))
                    continue

                if send_notification and not self.disable_notifications:
                    self.telegram.send_message(error_message)

                return False

            except Exception as e:
                self.logger.error(f"帳號 {ptt_id} 登入時發生未預期的錯誤：{e}", exc_info=True)

                if send_notification and not self.disable_notifications:
                    self.telegram.send_message(f"❌ 發生未預期的錯誤: {e}")

                return False

            finally:
                if ptt_bot:
                    self._safe_logout(ptt_bot, ptt_id)

        return False
    
    def batch_login(self, accounts: List[Tuple[str, str]]) -> Dict[str, bool]:
        """Batch login to PTT accounts using concurrent threads.

        Args:
            accounts: List of (username, password) tuples

        Returns:
            Dict[str, bool]: Dictionary of login results (username -> success)
        """
        results = {}
        
        if not accounts:
            self.logger.warning("未設定 PTT 帳號")
            return results
        
        self.logger.info(f"開始批次登入 {len(accounts)} 個帳號")
        
        # Use ThreadPoolExecutor for concurrent logins
        # This prevents one account's retry delay from blocking others
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(accounts), 5)) as executor:
            future_to_account = {
                executor.submit(self.login, username, password): username 
                for username, password in accounts
            }
            
            for future in concurrent.futures.as_completed(future_to_account):
                username = future_to_account[future]
                try:
                    self.logger.debug(f"正在嘗試登入 PTT 帳號：{username}")
                    success = future.result()
                    results[username] = success
                    
                    if success:
                        self.logger.debug(f"PTT 帳號 {username} 登入成功")
                    else:
                        self.logger.error(f"PTT 帳號 {username} 登入失敗")
                        
                except Exception as e:
                    self.logger.error(f"PTT 帳號 {username} 登入時發生錯誤：{str(e)}")
                    results[username] = False
        
        # Log summary
        success_count = sum(1 for success in results.values() if success)
        self.logger.info(f"批次登入完成：{success_count}/{len(results)} 個帳號成功")
        
        return results 