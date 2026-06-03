"""Shared pytest fixtures for the pttautosign test suite."""

from unittest.mock import MagicMock

import pytest

# Every environment variable the application reads. Cleared before each test so
# the host environment / a local .env never leaks into assertions.
_APP_ENV_VARS = (
    "PTT_USERNAME",
    "PTT_PASSWORD",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "DISABLE_NOTIFICATIONS",
    "TELEGRAM_RETRY_COUNT",
    "TELEGRAM_TIMEOUT",
    "timezone_hours",
    "ptt_timezone_hours",
    "ptt_max_retries",
    "ptt_retry_delay",
    "ptt_connection_timeout",
    "ptt_kick_other_session",
    "LOG_FORMAT",
    "DEBUG_MODE",
    "LOG_LEVEL",
    "TEST_MODE",
)


@pytest.fixture(autouse=True)
def clean_app_env(monkeypatch):
    """Remove all app env vars so each test controls its own environment."""
    for var in _APP_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def telegram_env(monkeypatch):
    """Set a minimal valid Telegram environment."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456789:ABCdef_GHI-jkl")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "987654321")


@pytest.fixture
def mock_notifier():
    """A stand-in NotificationService whose send_message succeeds by default."""
    notifier = MagicMock()
    notifier.send_message.return_value = True
    notifier.send_error_notification.return_value = True
    return notifier
