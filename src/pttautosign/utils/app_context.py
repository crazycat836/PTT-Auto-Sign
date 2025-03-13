"""
Application context module.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from pttautosign.utils.config import AppConfig, get_ptt_accounts, ConfigValidationError
from pttautosign.utils.logger import setup_logging, get_logger
from pttautosign.utils.factory import ServiceFactory
from pttautosign.utils.interfaces import NotificationService, LoginService

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
        # Load configuration first
        self._load_configuration()
        
        # Setup logging with configuration
        self.logger = setup_logging(self.app_config.log)
        
        # Log initialization
        self.logger.debug("應用程式上下文已建立")
        self.logger.debug("正在初始化應用程式上下文")
        self.logger.debug(f"已載入設定：{len(get_ptt_accounts())} 個 PTT 帳號")
        
        # Initialize services
        self._initialize_services()
        
        self.logger.debug("應用程式上下文初始化完成")
    
    def _load_configuration(self) -> None:
        """Load application configuration."""
        # Load and validate all configurations
        self.app_config = AppConfig.from_env()
    
    def _initialize_services(self) -> None:
        """Initialize service factory and services."""
        # Initialize service factory
        self.service_factory = ServiceFactory(self.app_config)
    
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
        
        self.logger.info("PTT 自動簽到程式開始執行")
        
        try:
            # Get service instances
            notification_service = self.get_notification_service()
            login_service = self.get_login_service()
            
            # Get account list and perform batch login
            accounts = get_ptt_accounts()
            self.logger.debug(f"正在處理 {len(accounts)} 個 PTT 帳號")
            
            results = login_service.batch_login(accounts)
            
            # Log results summary
            success_count = sum(1 for success in results.values() if success)
            self.logger.debug(f"登入結果：{success_count}/{len(results)} 個帳號成功")
            
            # Log failed accounts if any
            if success_count < len(results):
                failed_accounts = [account for account, success in results.items() if not success]
                self.logger.warning(f"失敗帳號：{', '.join(failed_accounts)}")
            else:
                self.logger.debug("所有帳號處理完成")
            
            self.logger.info("PTT 自動簽到程式執行完成")
                
        except Exception as e:
            self.logger.error(f"執行時錯誤：{str(e)}", exc_info=True)
            
            # Try to send error notification if possible
            try:
                notification_service = self.get_notification_service()
                notification_service.send_error_notification(
                    e, 
                    context={"operation": "main", "status": "failed"}
                )
            except Exception as notify_error:
                self.logger.error(f"發送錯誤通知失敗：{str(notify_error)}")
            
            raise 