"""
Tests for the config module.
"""

import unittest
from unittest.mock import patch
from config import TelegramConfig, PTTConfig, get_ptt_accounts
from PyPtt import exceptions as PTT_exceptions

class TestTelegramConfig(unittest.TestCase):
    """Test cases for TelegramConfig class"""
    
    def test_init(self):
        """Test initialization"""
        config = TelegramConfig(token="test_token", chat_id="test_chat_id")
        self.assertEqual(config.token, "test_token")
        self.assertEqual(config.chat_id, "test_chat_id")
    
    @patch('os.getenv')
    def test_from_env_success(self, mock_getenv):
        """Test successful loading from environment"""
        # Setup mock
        mock_getenv.side_effect = lambda key: {
            "bot_token": "env_token",
            "chat_id": "env_chat_id"
        }.get(key)
        
        # Call method
        config = TelegramConfig.from_env()
        
        # Assertions
        self.assertEqual(config.token, "env_token")
        self.assertEqual(config.chat_id, "env_chat_id")
    
    @patch('os.getenv')
    def test_from_env_missing_values(self, mock_getenv):
        """Test loading with missing environment values"""
        # Setup mock
        mock_getenv.return_value = None
        
        # Call method and check exception
        with self.assertRaises(ValueError):
            TelegramConfig.from_env()

class TestPTTConfig(unittest.TestCase):
    """Test cases for PTTConfig class"""
    
    def test_init(self):
        """Test initialization"""
        config = PTTConfig()
        self.assertEqual(config.timezone_hours, 8)
        self.assertIsNotNone(config.error_messages)
        
        # Check error messages
        self.assertIn(PTT_exceptions.WrongPassword, config.error_messages)
        self.assertIn(PTT_exceptions.WrongIDorPassword, config.error_messages)
        self.assertIn(PTT_exceptions.LoginTooOften, config.error_messages)

class TestGetPTTAccounts(unittest.TestCase):
    """Test cases for get_ptt_accounts function"""
    
    @patch('os.getenv')
    def test_get_accounts_success(self, mock_getenv):
        """Test successful account retrieval"""
        # Setup mock
        mock_getenv.side_effect = lambda key: {
            "ptt_id_1": "user1,pass1",
            "ptt_id_2": "user2,pass2",
            "ptt_id_3": "none,none",
            "ptt_id_4": None
        }.get(key)
        
        # Call function
        accounts = get_ptt_accounts()
        
        # Assertions
        self.assertEqual(len(accounts), 2)
        self.assertEqual(accounts[0], ("user1", "pass1"))
        self.assertEqual(accounts[1], ("user2", "pass2"))
    
    @patch('os.getenv')
    def test_get_accounts_missing_main(self, mock_getenv):
        """Test with missing main account"""
        # Setup mock
        mock_getenv.return_value = None
        
        # Call function and check exception
        with self.assertRaises(ValueError):
            get_ptt_accounts()

if __name__ == '__main__':
    unittest.main() 