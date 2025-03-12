"""
Tests for the application context.
"""

import unittest
from unittest.mock import patch, MagicMock
from config import AppConfig, ConfigValidationError
from utils.app_context import AppContext
from utils.interfaces import NotificationService, LoginService

class TestAppContext(unittest.TestCase):
    """Test cases for AppContext class"""
    
    @patch('utils.app_context.AppConfig')
    @patch('utils.app_context.setup_logging')
    @patch('utils.app_context.ServiceFactory')
    def test_initialize(self, mock_factory, mock_setup_logging, mock_app_config):
        """Test initialization"""
        # Setup mocks
        mock_app_config.from_env.return_value = MagicMock()
        mock_factory.return_value = MagicMock()
        
        # Call method
        app_context = AppContext()
        app_context.initialize()
        
        # Assertions
        self.assertIsNotNone(app_context.app_config)
        self.assertIsNotNone(app_context.service_factory)
        mock_app_config.from_env.assert_called_once()
        mock_setup_logging.assert_called_once()
        mock_factory.assert_called_once()
    
    @patch('utils.app_context.AppConfig')
    @patch('utils.app_context.setup_logging')
    @patch('utils.app_context.ServiceFactory')
    def test_get_notification_service(self, mock_factory, mock_setup_logging, mock_app_config):
        """Test get_notification_service"""
        # Setup mocks
        mock_app_config.from_env.return_value = MagicMock()
        mock_factory_instance = MagicMock()
        mock_factory.return_value = mock_factory_instance
        mock_notification_service = MagicMock()
        mock_factory_instance.get_notification_service.return_value = mock_notification_service
        
        # Call method
        app_context = AppContext()
        app_context.initialize()
        service = app_context.get_notification_service()
        
        # Assertions
        self.assertEqual(service, mock_notification_service)
        mock_factory_instance.get_notification_service.assert_called_once()
    
    @patch('utils.app_context.AppConfig')
    @patch('utils.app_context.setup_logging')
    @patch('utils.app_context.ServiceFactory')
    def test_get_login_service(self, mock_factory, mock_setup_logging, mock_app_config):
        """Test get_login_service"""
        # Setup mocks
        mock_app_config.from_env.return_value = MagicMock()
        mock_factory_instance = MagicMock()
        mock_factory.return_value = mock_factory_instance
        mock_login_service = MagicMock()
        mock_factory_instance.get_login_service.return_value = mock_login_service
        
        # Call method
        app_context = AppContext()
        app_context.initialize()
        service = app_context.get_login_service()
        
        # Assertions
        self.assertEqual(service, mock_login_service)
        mock_factory_instance.get_login_service.assert_called_once()
    
    @patch('utils.app_context.AppConfig')
    @patch('utils.app_context.setup_logging')
    @patch('utils.app_context.ServiceFactory')
    @patch('utils.app_context.get_ptt_accounts')
    def test_run(self, mock_get_accounts, mock_factory, mock_setup_logging, mock_app_config):
        """Test run"""
        # Setup mocks
        mock_app_config_instance = MagicMock()
        mock_app_config.from_env.return_value = mock_app_config_instance
        mock_app_config_instance.telegram.token = "test_token"
        mock_app_config_instance.telegram.chat_id = "test_chat_id"
        
        mock_factory_instance = MagicMock()
        mock_factory.return_value = mock_factory_instance
        
        mock_notification_service = MagicMock()
        mock_factory_instance.get_notification_service.return_value = mock_notification_service
        
        mock_login_service = MagicMock()
        mock_factory_instance.get_login_service.return_value = mock_login_service
        
        mock_get_accounts.return_value = [("user1", "pass1"), ("user2", "pass2")]
        mock_login_service.batch_login.return_value = {"user1": True, "user2": False}
        
        # Call method
        app_context = AppContext()
        app_context.initialize()
        app_context.run()
        
        # Assertions
        mock_login_service.batch_login.assert_called_once()
        mock_notification_service.send_message.assert_called_once()
    
    @patch('utils.app_context.AppConfig')
    @patch('utils.app_context.setup_logging')
    @patch('utils.app_context.ServiceFactory')
    @patch('utils.app_context.get_ptt_accounts')
    def test_run_with_exception(self, mock_get_accounts, mock_factory, mock_setup_logging, mock_app_config):
        """Test run with exception"""
        # Setup mocks
        mock_app_config_instance = MagicMock()
        mock_app_config.from_env.return_value = mock_app_config_instance
        
        mock_factory_instance = MagicMock()
        mock_factory.return_value = mock_factory_instance
        
        mock_notification_service = MagicMock()
        mock_factory_instance.get_notification_service.return_value = mock_notification_service
        
        mock_login_service = MagicMock()
        mock_factory_instance.get_login_service.return_value = mock_login_service
        
        mock_get_accounts.return_value = [("user1", "pass1")]
        mock_login_service.batch_login.side_effect = Exception("Test error")
        
        # Call method
        app_context = AppContext()
        app_context.initialize()
        
        # Assertions
        with self.assertRaises(Exception):
            app_context.run()
        
        mock_notification_service.send_error_notification.assert_called_once()

if __name__ == '__main__':
    unittest.main() 