"""
Telegram bot module for sending notifications.
"""

import html
import logging
import platform
import re
import socket
import time
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

from pttautosign.utils.config import TelegramConfig
from pttautosign.utils.interfaces import NotificationService

_SENSITIVE_CONTEXT_KEYS = (
    "password",
    "passwd",
    "token",
    "secret",
    "api_key",
    "apikey",
)


def _redact_context(context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a copy of ``context`` with sensitive values masked."""
    if not context:
        return {}
    safe: Dict[str, Any] = {}
    for key, value in context.items():
        lowered = str(key).lower()
        if any(token in lowered for token in _SENSITIVE_CONTEXT_KEYS):
            safe[key] = "***"
        else:
            safe[key] = value
    return safe


_TOKEN_RE = re.compile(r"^\d+:[A-Za-z0-9_-]+$")


class TelegramBot(NotificationService):
    """Telegram Bot handler class for sending notifications"""

    def __init__(self, config: TelegramConfig, tz: Optional[timezone] = None):
        """Initialize the Telegram bot with configuration

        Args:
            config: Telegram configuration containing token and chat_id
            tz: Timezone for error-notification timestamps (defaults to the
                host's local time when None)

        Raises:
            ValueError: If the bot token is missing or malformed
        """
        if not _TOKEN_RE.match(config.token or ""):
            raise ValueError("Invalid Telegram bot token format")

        self.config = config
        self.api_url = f"https://api.telegram.org/bot{config.token}"
        self.logger = logging.getLogger(__name__)
        self.hostname = socket.gethostname()
        # At least one attempt; honour the documented TELEGRAM_RETRY_COUNT.
        self.max_retries = max(1, config.retry_count)
        self.retry_delay = 2  # base seconds for exponential backoff
        self.tz = tz

        bot_id = config.token.partition(":")[0]
        self._masked_token = f"{bot_id}:***"

    def _redact(self, text: str) -> str:
        """Strip the bot token out of a string before it is logged.

        Library exceptions (e.g. ``HTTPError``) embed the full request URL,
        which contains the bot token; never let that reach the logs.
        """
        if self.config.token and self.config.token in text:
            return text.replace(self.config.token, self._masked_token)
        return text

    def send_message(self, text: str, parse_mode: str = "html") -> bool:
        """Send a message to Telegram, retrying transient failures.

        Retries up to ``TELEGRAM_RETRY_COUNT`` times with exponential backoff.

        Args:
            text: Message content to send
            parse_mode: Message parse mode (html, markdown, etc.)

        Returns:
            bool: Whether the message was sent successfully
        """
        masked_text = text[:100] + "..." if len(text) > 100 else text
        self.logger.debug(f"正在發送 Telegram 訊息：{masked_text}")

        for attempt in range(self.max_retries):
            if attempt > 0:
                delay = self.retry_delay * (2 ** (attempt - 1))
                self.logger.debug(
                    f"正在重試發送 Telegram 訊息（第 {attempt + 1}/{self.max_retries} 次嘗試）"
                )
                time.sleep(delay)

            if self._post_message(text, parse_mode):
                return True

        self.logger.error(f"Telegram 訊息發送失敗，已嘗試 {self.max_retries} 次")
        return False

    def _post_message(self, text: str, parse_mode: str) -> bool:
        """Perform a single send attempt. Returns True on success."""
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.config.chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_notification": self.config.disable_notification,
                },
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            self.logger.debug("Telegram 訊息發送成功")
            return True

        except requests.exceptions.RequestException as e:
            # Avoid exc_info — the request URL/exception text contains the bot
            # token; redact it before logging.
            self.logger.warning(f"Telegram 訊息發送失敗：{self._redact(str(e))}")
            return False
        except Exception as e:
            self.logger.error(
                f"發送 Telegram 訊息時發生未預期的錯誤：{self._redact(str(e))}"
            )
            return False

    def send_error_notification(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send an error notification to Telegram.

        Args:
            error: Exception that occurred
            context: Additional context information (sensitive keys masked)

        Returns:
            bool: Whether the message was sent successfully
        """
        try:
            now = datetime.now(self.tz).strftime("%Y-%m-%d %H:%M:%S")
            error_type = html.escape(type(error).__name__)
            error_message = html.escape(str(error))

            parts = [
                "❌ <b>Error Notification</b>\n",
                f"<b>Time:</b> {now}",
                f"<b>Host:</b> {html.escape(self.hostname)}",
                f"<b>Error Type:</b> {error_type}",
                f"<b>Error Message:</b> {error_message}",
            ]

            safe_context = _redact_context(context)
            if safe_context:
                parts.append("\n<b>Context:</b>")
                for key, value in safe_context.items():
                    parts.append(
                        f"• <b>{html.escape(str(key))}:</b> {html.escape(str(value))}"
                    )

            tb = traceback.format_exc()
            if tb and tb != "NoneType: None\n":
                tb_lines = tb.split("\n")
                if len(tb_lines) > 12:
                    tb_lines = tb_lines[:12] + ["..."]
                parts.append("\n<b>Stack Trace:</b>\n<pre>")
                parts.append(html.escape("\n".join(tb_lines)))
                parts.append("</pre>")

            parts.append(
                f"\n<b>System:</b> {html.escape(platform.system())} "
                f"{html.escape(platform.release())}"
            )
            parts.append(f"<b>Python:</b> {html.escape(platform.python_version())}")

            return self.send_message("\n".join(parts))

        except Exception as e:
            self.logger.error(f"發送錯誤通知失敗：{self._redact(str(e))}")
            self.logger.debug("錯誤通知失敗詳細追蹤", exc_info=True)
            return False
