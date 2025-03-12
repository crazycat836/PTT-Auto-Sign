"""
Application context module.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from config import AppConfig, get_ptt_accounts, ConfigValidationError
from utils.logger import setup_logging, get_logger
from utils.factory import ServiceFactory
from utils.interfaces import NotificationService, LoginService

class AppContext:
    """Application context class for managing application lifecycle and dependencies."""
    
    def __init__(self):
        """Initialize the application context."""
        self.app_config: Optional[AppConfig] = None
        self.service_factory: Optional[ServiceFactory] = None
        self.logger = logging.getLogger(__name__)
    
    def initialize(self) -> None:
        """Initialize the application context.
        
        Raises:
            ConfigValidationError: If configuration is invalid
        """
        # Load and validate all configurations
        self.app_config = AppConfig.from_env()
        
        # Setup logging with configuration
        setup_logging(
            config=self.app_config.log,
            use_json=self.app_config.log.use_json_format,
            include_hostname=self.app_config.log.include_hostname
        )
        
        # Initialize logger
        self.logger = get_logger(__name__)
        self.logger.info("Initializing application context")
        
        # Initialize service factory
        self.service_factory = ServiceFactory(self.app_config)
        
        # Log configuration summary
        self.logger.info(f"Loaded configuration: {len(get_ptt_accounts())} PTT accounts")
        self.logger.debug(f"Configuration: {self.app_config.to_json()}")
        
        self.logger.info("Application context initialized successfully")
    
    def get_notification_service(self) -> NotificationService:
        """Get notification service instance.
        
        Returns:
            NotificationService: Notification service instance
        """
        if not self.service_factory:
            raise RuntimeError("Application context not initialized")
        return self.service_factory.get_notification_service()
    
    def get_login_service(self) -> LoginService:
        """Get login service instance.
        
        Returns:
            LoginService: Login service instance
        """
        if not self.service_factory:
            raise RuntimeError("Application context not initialized")
        return self.service_factory.get_login_service()
    
    def run(self) -> None:
        """Run the application.
        
        Raises:
            RuntimeError: If application context not initialized
        """
        if not self.app_config or not self.service_factory:
            raise RuntimeError("Application context not initialized")
        
        self.logger.info("Starting PTT Auto Sign program")
        
        try:
            # Get service instances
            notification_service = self.get_notification_service()
            login_service = self.get_login_service()
            
            # Get account list and perform batch login
            accounts = get_ptt_accounts()
            results = login_service.batch_login(accounts)
            
            # Log results summary
            success_count = sum(1 for success in results.values() if success)
            self.logger.info(f"Login results: {success_count}/{len(results)} accounts successful")
            
            # Send summary to Telegram if configured
            if self.app_config.telegram.token and self.app_config.telegram.chat_id:
                summary = f"📊 PTT Auto Sign Summary\n\n"
                summary += f"✅ Successful: {success_count}\n"
                summary += f"❌ Failed: {len(results) - success_count}\n"
                
                if success_count < len(results):
                    failed_accounts = [account for account, success in results.items() if not success]
                    summary += f"\nFailed accounts: {', '.join(failed_accounts)}"
                
                notification_service.send_message(summary)
            
            self.logger.info("PTT Auto Sign program completed successfully")
                
        except Exception as e:
            self.logger.error(f"Runtime error: {str(e)}", exc_info=True)
            
            # Try to send error notification if possible
            try:
                notification_service = self.get_notification_service()
                notification_service.send_error_notification(
                    e, 
                    context={"operation": "main", "status": "failed"}
                )
            except Exception as notify_error:
                self.logger.error(f"Failed to send error notification: {str(notify_error)}")
            
            raise 