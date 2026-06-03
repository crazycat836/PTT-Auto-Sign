"""Tests for the PTT auto sign-in service."""

from unittest.mock import MagicMock, patch

import pytest
from PyPtt import exceptions as PTT_exceptions

from pttautosign.utils.config import PTTConfig
from pttautosign.utils.ptt import PTTAutoSign


def _exc(cls, message="error"):
    """Build a PyPtt exception instance without running its i18n-dependent
    __init__ (which is unavailable outside a live PTT session).

    The real exceptions set ``self.message`` in __init__; we set it here so that
    ``str(exc)`` works (the production code calls it via ``dict.get`` defaults)."""
    exc = cls.__new__(cls)
    exc.message = message
    return exc


@pytest.fixture
def notifier():
    n = MagicMock()
    n.send_message.return_value = True
    return n


class TestFormatSuccessMessage:
    def test_no_new_mails_translated(self, notifier):
        msg = PTTAutoSign(notifier)._format_success_message(
            "alice", {"login_count": 100, "mail": "No new mails"}
        )
        assert "最近無新信件" in msg
        assert "alice" in msg

    def test_new_mail_count_extracted(self, notifier):
        msg = PTTAutoSign(notifier)._format_success_message(
            "bob", {"login_count": 5, "mail": "You have 3 new mails"}
        )
        assert "您有 3 封新信件" in msg

    def test_malformed_mail_does_not_crash(self, notifier):
        # H4 regression: 'new mails' present but no count must not raise IndexError.
        msg = PTTAutoSign(notifier)._format_success_message(
            "eve", {"login_count": 1, "mail": "New mails"}
        )
        assert "登入成功" in msg

    def test_missing_mail_key_does_not_crash(self, notifier):
        msg = PTTAutoSign(notifier)._format_success_message("x", {"login_count": 1})
        assert "登入成功" in msg


class TestFormatErrorMessage:
    def test_known_error_uses_mapped_message(self, notifier):
        signer = PTTAutoSign(notifier)
        msg = signer._format_error_message("u", _exc(PTT_exceptions.WrongPassword))
        assert "密碼錯誤" in msg

    def test_unregistered_user_prefixes_id(self, notifier):
        signer = PTTAutoSign(notifier)
        msg = signer._format_error_message("alice", _exc(PTT_exceptions.UnregisteredUser))
        assert msg.startswith("❌ alice")


class TestLogin:
    def _signer(self, notifier, **cfg):
        config = PTTConfig(max_retries=2, retry_delay=0, **cfg)
        return PTTAutoSign(notifier, config)

    @patch("pttautosign.utils.ptt.PTT")
    def test_successful_login_sends_notification(self, mock_ptt, notifier):
        api = mock_ptt.API.return_value
        api.get_user.return_value = {"login_count": 1, "mail": "No new mails"}
        signer = self._signer(notifier)
        assert signer.login("alice", "pw") is True
        notifier.send_message.assert_called_once()
        api.logout.assert_called_once()

    @patch("pttautosign.utils.ptt.PTT")
    def test_wrong_password_returns_false_without_retry(self, mock_ptt, notifier):
        api = mock_ptt.API.return_value
        api.login.side_effect = _exc(PTT_exceptions.WrongPassword)
        signer = self._signer(notifier)
        assert signer.login("alice", "bad") is False
        assert api.login.call_count == 1

    @patch("pttautosign.utils.ptt.time.sleep")
    @patch("pttautosign.utils.ptt.PTT")
    def test_login_too_often_retries_then_fails(self, mock_ptt, _sleep, notifier):
        api = mock_ptt.API.return_value
        api.login.side_effect = _exc(PTT_exceptions.LoginTooOften)
        signer = self._signer(notifier)  # max_retries=2 -> 3 attempts total
        assert signer.login("alice", "pw") is False
        assert api.login.call_count == 3

    @patch("pttautosign.utils.ptt.PTT")
    def test_disable_notifications_suppresses_send(self, mock_ptt, notifier):
        api = mock_ptt.API.return_value
        api.get_user.return_value = {"login_count": 1, "mail": "No new mails"}
        signer = PTTAutoSign(notifier, PTTConfig(), disable_notifications=True)
        assert signer.login("alice", "pw") is True
        notifier.send_message.assert_not_called()

    @patch("pttautosign.utils.ptt.PTT")
    def test_send_notification_false_skips_send(self, mock_ptt, notifier):
        api = mock_ptt.API.return_value
        api.get_user.return_value = {"login_count": 1, "mail": "No new mails"}
        signer = PTTAutoSign(notifier, PTTConfig())
        assert signer.login("alice", "pw", send_notification=False) is True
        notifier.send_message.assert_not_called()


class TestBatchLogin:
    def test_empty_accounts_returns_empty(self, notifier):
        assert PTTAutoSign(notifier).batch_login([]) == {}

    @patch.object(PTTAutoSign, "login", return_value=True)
    def test_aggregates_results(self, _mock_login, notifier):
        results = PTTAutoSign(notifier).batch_login([("a", "1"), ("b", "2")])
        assert results == {"a": True, "b": True}

    @patch.object(PTTAutoSign, "login")
    def test_mixed_results(self, mock_login, notifier):
        mock_login.side_effect = lambda u, p: u == "good"
        results = PTTAutoSign(notifier).batch_login([("good", "1"), ("bad", "2")])
        assert results == {"good": True, "bad": False}
