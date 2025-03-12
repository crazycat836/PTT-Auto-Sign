"""
Tests for the Telegram module.
"""

import unittest
from unittest.mock import patch, MagicMock
from config import TelegramConfig
from utils.telegram import TelegramBot

class TestTelegramBot(unittest.TestCase):
    """Test cases for TelegramBot class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = TelegramConfig(token="test_token", chat_id="test_chat_id")
        self.bot = TelegramBot(self.config)
    
    def test_init(self):
        """Test initialization"""
        self.assertEqual(self.bot.config.token, "test_token")
        self.assertEqual(self.bot.config.chat_id, "test_chat_id")
        self.assertEqual(self.bot.api_url, "https://api.telegram.org/bottest_token")
    
    @patch('requests.post')
    def test_send_message_success(self, mock_post):
        """Test successful message sending"""
        # Setup mock
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Call method
        result = self.bot.send_message("Test message")
        
        # Assertions
        self.assertTrue(result)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json']['text'], "Test message")
        self.assertEqual(kwargs['json']['chat_id'], "test_chat_id")
        self.assertEqual(kwargs['json']['parse_mode'], "html")
    
    @patch('requests.post')
    def test_send_message_failure(self, mock_post):
        """Test failed message sending"""
        # Setup mock to raise exception
        mock_post.side_effect = Exception("Test error")
        
        # Call method
        result = self.bot.send_message("Test message")
        
        # Assertions
        self.assertFalse(result)
        mock_post.assert_called_once()

if __name__ == '__main__':
    unittest.main() 