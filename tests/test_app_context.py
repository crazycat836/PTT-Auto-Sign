"""Tests for the application context account handling."""

from unittest.mock import MagicMock

import pytest

from pttautosign.utils.app_context import AppContext
from pttautosign.utils.config import ConfigValidationError


class TestGetAccounts:
    def test_get_accounts_returns_configured_account(self, monkeypatch):
        monkeypatch.setenv("PTT_USERNAME", "u")
        monkeypatch.setenv("PTT_PASSWORD", "p")
        assert AppContext().get_accounts() == [("u", "p")]

    def test_get_accounts_is_cached(self, monkeypatch):
        monkeypatch.setenv("PTT_USERNAME", "u")
        monkeypatch.setenv("PTT_PASSWORD", "p")
        ctx = AppContext()
        first = ctx.get_accounts()
        # Mutating the environment afterwards must not change the cached result.
        monkeypatch.setenv("PTT_USERNAME", "someone_else")
        assert ctx.get_accounts() == first == [("u", "p")]

    def test_get_accounts_missing_credentials_raises(self):
        with pytest.raises(ConfigValidationError):
            AppContext().get_accounts()


class TestServiceGuards:
    def test_get_login_service_before_init_raises(self):
        with pytest.raises(RuntimeError, match="not initialized"):
            AppContext().get_login_service()

    def test_get_notification_service_before_init_raises(self):
        with pytest.raises(RuntimeError, match="not initialized"):
            AppContext().get_notification_service()

    def test_run_before_init_raises(self):
        with pytest.raises(RuntimeError, match="not initialized"):
            AppContext().run()


class TestInitializeAndRun:
    def _full_env(self, monkeypatch):
        monkeypatch.setenv("PTT_USERNAME", "u")
        monkeypatch.setenv("PTT_PASSWORD", "p")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456789:ABCdef_GHI-jkl")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")

    def test_initialize_populates_config_and_accounts(self, monkeypatch):
        self._full_env(monkeypatch)
        ctx = AppContext()
        ctx.initialize()
        assert ctx.app_config is not None
        assert ctx.service_factory is not None
        assert ctx.get_accounts() == [("u", "p")]

    def test_initialize_missing_account_raises(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456789:ABCdef_GHI-jkl")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
        with pytest.raises(ConfigValidationError):
            AppContext().initialize()

    def test_run_invokes_batch_login(self, monkeypatch):
        self._full_env(monkeypatch)
        ctx = AppContext()
        ctx.initialize()
        login = MagicMock()
        login.batch_login.return_value = {"u": True}
        monkeypatch.setattr(ctx, "get_login_service", lambda: login)
        ctx.run()
        login.batch_login.assert_called_once_with([("u", "p")])

    def test_run_sends_error_notification_on_failure(self, monkeypatch):
        self._full_env(monkeypatch)
        ctx = AppContext()
        ctx.initialize()
        login = MagicMock()
        login.batch_login.side_effect = RuntimeError("boom")
        notifier = MagicMock()
        monkeypatch.setattr(ctx, "get_login_service", lambda: login)
        monkeypatch.setattr(ctx, "get_notification_service", lambda: notifier)
        with pytest.raises(RuntimeError):
            ctx.run()
        notifier.send_error_notification.assert_called_once()
