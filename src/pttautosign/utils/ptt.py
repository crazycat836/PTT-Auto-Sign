"""
PTT auto sign-in module for handling PTT login operations.
"""

import re
import time
import logging
import traceback
import concurrent.futures
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple, List
from PyPtt import PTT
from PyPtt import exceptions as PTT_exceptions
from pttautosign.utils.config import PTTConfig
from pttautosign.utils.interfaces import LoginService, NotificationService

# Upper bound for the exponential retry backoff so a misconfigured
# ``ptt_retry_delay`` / ``ptt_max_retries`` cannot produce multi-minute sleeps.
MAX_BACKOFF_SECONDS = 60

# Matches PTT's English "You have N new mails" status line.
_NEW_MAIL_RE = re.compile(r"(\d+)\s+new mails", re.IGNORECASE)


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
        self.max_retries = self.config.max_retries
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

        # 將英文郵件訊息翻譯為中文。使用正規表示式擷取數字，避免在訊息格式
        # 非預期時（例如缺少數字）發生 IndexError 而讓成功登入變成例外。
        mail_msg = user_info.get('mail', '') or ''
        if mail_msg == 'No new mails':
            mail_msg = '最近無新信件'
        else:
            match = _NEW_MAIL_RE.search(mail_msg)
            if match:
                mail_msg = f'您有 {match.group(1)} 封新信件'

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

    def _notify(self, message: str, ptt_id: str, send_notification: bool) -> None:
        """Send a notification, honouring the disable flags and surfacing failures.

        Args:
            message: Message body to send
            ptt_id: Account the notification relates to (for log context)
            send_notification: Per-call gate from the caller
        """
        if not send_notification or self.disable_notifications:
            return
        if not self.telegram.send_message(message):
            self.logger.warning(f"帳號 {ptt_id} 的通知發送失敗")

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
                ptt_bot.login(
                    ptt_id,
                    ptt_passwd,
                    kick_other_session=self.config.kick_other_session,
                )
                user_info = ptt_bot.get_user(ptt_id)
                success_message = self._format_success_message(ptt_id, user_info)

                self._notify(success_message, ptt_id, send_notification)

                return True

            except exceptions_to_catch as e:
                # Known auth/PTT errors — log message only, not the full
                # traceback (avoid leaking sensitive frame locals into logs).
                error_message = self._format_error_message(ptt_id, e)
                self.logger.error(f"帳號 {ptt_id} 登入失敗：{error_message}")

                # Retry for temporary errors, with a capped exponential backoff.
                if isinstance(e, (PTT_exceptions.LoginTooOften, PTT_exceptions.UseTooManyResources)) and attempt < self.max_retries:
                    self.logger.debug(f"正在重試帳號 {ptt_id} 的登入（第 {attempt + 1}/{self.max_retries} 次嘗試）")
                    backoff = min(self.config.retry_delay * (2 ** attempt), MAX_BACKOFF_SECONDS)
                    time.sleep(backoff)
                    continue

                self._notify(error_message, ptt_id, send_notification)

                return False

            except Exception as e:
                # Do NOT use exc_info here: the traceback's frame locals include
                # ``ptt_passwd``. Log type + message, plus a password-sanitised
                # traceback at debug level only.
                self.logger.error(f"帳號 {ptt_id} 登入時發生未預期的錯誤：{type(e).__name__}: {e}")
                sanitized_tb = traceback.format_exc().replace(ptt_passwd, "***")
                self.logger.debug(f"未預期錯誤詳細追蹤：\n{sanitized_tb}")

                self._notify(f"❌ 發生未預期的錯誤: {e}", ptt_id, send_notification)

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

        # Bound the total wait so an unresponsive PTT server cannot hang the
        # process forever. Logins run concurrently, so a single-account worst
        # case (all retries + capped backoff) is a sufficient overall budget.
        batch_timeout = (self.config.connection_timeout + MAX_BACKOFF_SECONDS) * (self.max_retries + 1)

        # Use ThreadPoolExecutor for concurrent logins; this prevents one
        # account's retry delay from blocking others. The executor is managed
        # manually (not via ``with``) so that on timeout we can shut down with
        # ``wait=False`` instead of blocking on a hung worker thread.
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=min(len(accounts), 5))
        future_to_account = {
            executor.submit(self.login, username, password): username
            for username, password in accounts
        }
        timed_out = False
        try:
            for future in concurrent.futures.as_completed(future_to_account, timeout=batch_timeout):
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
                    # future.result() may surface a worker-thread exception;
                    # log type+message (no exc_info — its frames hold the
                    # password) and record the account as failed.
                    self.logger.error(f"PTT 帳號 {username} 登入時發生錯誤：{type(e).__name__}: {e}")
                    results[username] = False
        except concurrent.futures.TimeoutError:
            # Mark any account that did not finish within the budget as failed
            # instead of blocking indefinitely.
            timed_out = True
            for username in future_to_account.values():
                if username not in results:
                    results[username] = False
                    self.logger.error(f"PTT 帳號 {username} 登入逾時（超過 {batch_timeout} 秒）")
        finally:
            # On timeout, do not block on the (possibly hung) worker threads.
            executor.shutdown(wait=not timed_out, cancel_futures=True)

        # Log summary
        success_count = sum(1 for success in results.values() if success)
        self.logger.info(f"批次登入完成：{success_count}/{len(results)} 個帳號成功")
        
        return results 