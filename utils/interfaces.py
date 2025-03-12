"""
Interface definitions for service classes.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional

class NotificationService(ABC):
    """Abstract base class for notification services."""
    
    @abstractmethod
    def send_message(self, text: str, parse_mode: str = "html") -> bool:
        """Send a message.
        
        Args:
            text: Message content
            parse_mode: Message format
            
        Returns:
            bool: Whether the message was sent successfully
        """
        pass
    
    @abstractmethod
    def send_error_notification(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> bool:
        """Send an error notification.
        
        Args:
            error: Exception that occurred
            context: Additional context information
            
        Returns:
            bool: Whether the message was sent successfully
        """
        pass

class LoginService(ABC):
    """Abstract base class for login services."""
    
    @abstractmethod
    def login(self, username: str, password: str) -> bool:
        """Perform login.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            bool: Whether login was successful
        """
        pass
    
    @abstractmethod
    def batch_login(self, accounts: List[Tuple[str, str]]) -> Dict[str, bool]:
        """Perform batch login.
        
        Args:
            accounts: List of (username, password) tuples
            
        Returns:
            Dict[str, bool]: Dictionary mapping usernames to login success status
        """
        pass