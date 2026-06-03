"""Tests for the Telegram notification service."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from pttautosign.utils.config import TelegramConfig
from pttautosign.utils.telegram import TelegramBot, _redact_context

TOKEN = "123456789:ABCdef_GHI-jkl"


def make_bot(**overrides) -> TelegramBot:
    params = dict(token=TOKEN, chat_id="42", retry_count=3, timeout=10)
    params.update(overrides)
    return TelegramBot(TelegramConfig(**params))


def _ok_response() -> MagicMock:
    return MagicMock(raise_for_status=lambda: None)


class TestTokenGuard:
    def test_invalid_token_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid Telegram bot token"):
            TelegramBot(TelegramConfig(token="bad-token", chat_id="42"))

    def test_valid_token_constructs(self):
        assert make_bot().api_url.endswith(f"/bot{TOKEN}")


class TestSendMessage:
    @patch("pttautosign.utils.telegram.requests.post")
    def test_success_single_attempt(self, mock_post):
        mock_post.return_value = _ok_response()
        assert make_bot().send_message("hi") is True
        assert mock_post.call_count == 1

    @patch("pttautosign.utils.telegram.time.sleep")
    @patch("pttautosign.utils.telegram.requests.post")
    def test_retries_then_succeeds(self, mock_post, _sleep):
        failing = MagicMock(
            raise_for_status=MagicMock(
                side_effect=requests.exceptions.ConnectionError("boom")
            )
        )
        mock_post.side_effect = [failing, _ok_response()]
        assert make_bot(retry_count=3).send_message("hi") is True
        assert mock_post.call_count == 2

    @patch("pttautosign.utils.telegram.time.sleep")
    @patch("pttautosign.utils.telegram.requests.post")
    def test_all_attempts_fail_returns_false(self, mock_post, _sleep):
        mock_post.side_effect = requests.exceptions.ConnectionError("boom")
        assert make_bot(retry_count=3).send_message("hi") is False
        assert mock_post.call_count == 3

    @patch("pttautosign.utils.telegram.time.sleep")
    @patch("pttautosign.utils.telegram.requests.post")
    def test_retry_count_below_one_still_attempts_once(self, mock_post, _sleep):
        mock_post.return_value = _ok_response()
        assert make_bot(retry_count=0).send_message("hi") is True
        assert mock_post.call_count == 1


class TestTokenRedactionInLogs:
    @patch("pttautosign.utils.telegram.time.sleep")
    @patch("pttautosign.utils.telegram.requests.post")
    def test_token_not_leaked_in_failure_log(self, mock_post, _sleep, caplog):
        # HTTPError messages embed the full request URL, including the token.
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        err = requests.exceptions.HTTPError(f"400 Client Error for url: {url}")
        mock_post.return_value = MagicMock(
            raise_for_status=MagicMock(side_effect=err)
        )
        with caplog.at_level("WARNING"):
            assert make_bot(retry_count=1).send_message("hi") is False
        logged = " ".join(r.getMessage() for r in caplog.records)
        assert "ABCdef_GHI-jkl" not in logged
        assert "123456789:***" in logged


class TestRedactContext:
    def test_none_returns_empty_dict(self):
        assert _redact_context(None) == {}

    def test_sensitive_keys_masked_others_preserved(self):
        result = _redact_context(
            {"password": "secret", "api_key": "k", "operation": "main"}
        )
        assert result["password"] == "***"
        assert result["api_key"] == "***"
        assert result["operation"] == "main"


class TestErrorNotification:
    @patch.object(TelegramBot, "send_message", return_value=True)
    def test_escapes_html_in_error_message(self, mock_send):
        ok = make_bot().send_error_notification(
            ValueError("<script>&bad"), {"operation": "x"}
        )
        assert ok is True
        body = mock_send.call_args[0][0]
        assert "&lt;script&gt;" in body
        assert "<script>" not in body
