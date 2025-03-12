"""
Tests for the PTT module.
"""

import unittest
from unittest.mock import patch, MagicMock
from config import PTTConfig
from utils.ptt import PTTAutoSign
from PyPtt import exceptions as PTT_exceptions

class TestPTTAutoSign(unittest.TestCase):
    """Test cases for PTTAutoSign class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.telegram_mock = MagicMock()
        self.config = PTTConfig()
        self.ptt_auto_sign = PTTAutoSign(self.telegram_mock, self.config)
        # Mock the PTT API
        self.ptt_auto_sign.ptt = MagicMock()
    
    def test_format_success_message(self):
        """Test success message formatting"""
        user_info = {
            'login_count': 100,
            'mail': '5 封未讀'
        }
        message = self.ptt_auto_sign._format_success_message("test_user", user_info)
        self.assertIn("test_user", message)
        self.assertIn("100", message)
        self.assertIn("5 封未讀", message)
    
    def test_format_error_message(self):
        """Test error message formatting"""
        error = PTT_exceptions.WrongPassword()
        message = self.ptt_auto_sign._format_error_message("test_user", error)
        self.assertIn("❌", message)
        self.assertIn("PTT login failed", message)
    
    @patch('PyPtt.PTT.API')
    def test_daily_login_success(self, mock_ptt_api):
        """Test successful login"""
        # Setup mocks
        self.ptt_auto_sign.ptt.login.return_value = None
        self.ptt_auto_sign.ptt.get_user.return_value = {'login_count': 100, 'mail': '0 封未讀'}
        self.ptt_auto_sign.ptt.is_login.return_value = True
        
        # Call method
        result = self.ptt_auto_sign.daily_login("test_user", "test_pass")
        
        # Assertions
        self.assertTrue(result)
        self.ptt_auto_sign.ptt.login.assert_called_once_with("test_user", "test_pass", kick_other_session=True)
        self.ptt_auto_sign.ptt.get_user.assert_called_once_with("test_user")
        self.telegram_mock.send_message.assert_called_once()
        self.ptt_auto_sign.ptt.logout.assert_called_once()
    
    @patch('PyPtt.PTT.API')
    def test_daily_login_failure(self, mock_ptt_api):
        """Test failed login"""
        # Setup mocks
        self.ptt_auto_sign.ptt.login.side_effect = PTT_exceptions.WrongPassword()
        self.ptt_auto_sign.ptt.is_login.return_value = False
        
        # Call method
        result = self.ptt_auto_sign.daily_login("test_user", "test_pass")
        
        # Assertions
        self.assertFalse(result)
        self.ptt_auto_sign.ptt.login.assert_called_once_with("test_user", "test_pass", kick_other_session=True)
        self.telegram_mock.send_message.assert_called_once()
    
    def test_batch_login(self):
        """Test batch login"""
        # Setup mocks
        self.ptt_auto_sign.daily_login = MagicMock()
        self.ptt_auto_sign.daily_login.side_effect = [True, False]
        
        # Call method
        accounts = [("user1", "pass1"), ("user2", "pass2")]
        results = self.ptt_auto_sign.batch_login(accounts)
        
        # Assertions
        self.assertEqual(len(results), 2)
        self.assertTrue(results["user1"])
        self.assertFalse(results["user2"])
        self.assertEqual(self.ptt_auto_sign.daily_login.call_count, 2)

if __name__ == '__main__':
    unittest.main() 