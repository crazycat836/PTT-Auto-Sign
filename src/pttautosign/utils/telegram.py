"""
Telegram bot module for sending notifications.
"""

import logging
import traceback
import platform
import socket
import requests
from datetime import datetime
from typing import Optional, Dict, Any, Union
from pttautosign.utils.config import TelegramConfig
from pttautosign.utils.interfaces import NotificationService

class TelegramBot(NotificationService):
    """Telegram Bot handler class for sending notifications"""
    
    def __init__(self, config: TelegramConfig):
        """Initialize the Telegram bot with configuration
        
        Args:
            config: Telegram configuration containing token and chat_id
        """
        self.config = config
        self.api_url = f"https://api.telegram.org/bot{config.token}"
        self.logger = logging.getLogger(__name__)
        self.hostname = socket.gethostname()
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def send_message(self, text: str, parse_mode: str = "html") -> bool:
        """Send message to Telegram
        
        Args:
            text: Message content to send
            parse_mode: Message parse mode (html, markdown, etc.)
            
        Returns:
            bool: Whether the message was sent successfully
        """
        try:
            # Mask sensitive information in logs
            masked_text = text[:100] + "..." if len(text) > 100 else text
            self.logger.info(f"正在發送 Telegram 訊息：{masked_text}")
            
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.config.chat_id,
                    "text": text,
                    "parse_mode": parse_mode
                },
                timeout=10  # Add timeout for better error handling
            )
            response.raise_for_status()
            self.logger.info("Telegram 訊息發送成功")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Telegram 訊息發送失敗：{str(e)}", exc_info=True)
            return False
        except Exception as e:
            self.logger.error(f"發送 Telegram 訊息時發生未預期的錯誤：{str(e)}", exc_info=True)
            return False
    
    def send_error_notification(self, error: Exception, context: Optional[Dict[str, Any]] = None, 
                               retry: bool = True) -> bool:
        """Send error notification to Telegram
        
        Args:
            error: Exception that occurred
            context: Additional context information
            retry: Whether to retry sending the message if it fails
            
        Returns:
            bool: Whether the message was sent successfully
        """
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            error_type = type(error).__name__
            error_message = str(error)
            
            # Format error message
            message = f"❌ <b>Error Notification</b>\n\n"
            message += f"<b>Time:</b> {now}\n"
            message += f"<b>Host:</b> {self.hostname}\n"
            message += f"<b>Error Type:</b> {error_type}\n"
            message += f"<b>Error Message:</b> {error_message}\n"
            
            # Add context if provided
            if context:
                message += "\n<b>Context:</b>\n"
                for key, value in context.items():
                    message += f"• <b>{key}:</b> {value}\n"
            
            # Add stack trace (limited to 10 lines)
            tb = traceback.format_exc()
            if tb and tb != "NoneType: None\n":
                tb_lines = tb.split("\n")
                if len(tb_lines) > 12:
                    tb_lines = tb_lines[:12] + ["..."]
                message += "\n<b>Stack Trace:</b>\n<pre>"
                message += "\n".join(tb_lines)
                message += "</pre>"
            
            # Add system info
            message += f"\n<b>System:</b> {platform.system()} {platform.release()}"
            message += f"\n<b>Python:</b> {platform.python_version()}"
            
            # Send message
            return self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"發送錯誤通知失敗：{str(e)}", exc_info=True)
            return False
    
    def send_with_retry(self, text: str, max_retries: Optional[int] = None, 
                       retry_delay: Optional[int] = None) -> bool:
        """Send message with retry
        
        Args:
            text: Message content to send
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
            
        Returns:
            bool: Whether the message was sent successfully
        """
        import time
        
        max_retries = max_retries or self.max_retries
        retry_delay = retry_delay or self.retry_delay
        
        for attempt in range(max_retries):
            if attempt > 0:
                self.logger.info(f"正在重試發送訊息（第 {attempt+1}/{max_retries} 次嘗試）")
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                
            if self.send_message(text):
                return True
        
        self.logger.error(f"訊息發送失敗，已重試 {max_retries} 次")
        return False 