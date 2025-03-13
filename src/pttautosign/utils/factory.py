"""
Factory module for creating service instances.
"""

from typing import Dict, Any, Optional
from pttautosign.utils.config import AppConfig, TelegramConfig, PTTConfig
from pttautosign.utils.interfaces import NotificationService, LoginService
from pttautosign.utils.telegram import TelegramBot
from pttautosign.utils.ptt import PTTAutoSign

class ServiceFactory:
    """Factory class for creating service instances."""
    
    def __init__(self, app_config: AppConfig):
        """Initialize the factory with application configuration.
        
        Args:
            app_config: Application configuration
        """
        self.app_config = app_config
        self._services: Dict[str, Any] = {}
    
    def get_notification_service(self) -> NotificationService:
        """Get notification service instance.
        
        Returns:
            NotificationService: Notification service instance
        """
        if "notification" not in self._services:
            self._services["notification"] = TelegramBot(self.app_config.telegram)
        return self._services["notification"]
    
    def get_login_service(self) -> LoginService:
        """Get login service instance.
        
        Returns:
            LoginService: Login service instance
        """
        if "login" not in self._services:
            notification_service = self.get_notification_service()
            self._services["login"] = PTTAutoSign(notification_service, self.app_config.ptt)
        return self._services["login"] 