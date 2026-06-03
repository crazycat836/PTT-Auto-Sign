"""Tests for configuration loading, validation, and secret redaction."""

import logging

import pytest

from pttautosign.utils.config import (
    AppConfig,
    ConfigValidationError,
    LogConfig,
    PTTConfig,
    TelegramConfig,
    get_ptt_accounts,
)


class TestTelegramConfig:
    def _valid(self, **overrides) -> TelegramConfig:
        params = dict(token="123456789:ABCdef_GHI-jkl", chat_id="42")
        params.update(overrides)
        return TelegramConfig(**params)

    def test_valid_config_passes_validation(self):
        self._valid().validate()  # must not raise

    def test_missing_token_raises(self):
        with pytest.raises(ConfigValidationError, match="token is required"):
            TelegramConfig(token="", chat_id="42").validate()

    def test_malformed_token_raises(self):
        with pytest.raises(ConfigValidationError, match="Invalid Telegram bot token"):
            TelegramConfig(token="not-a-token", chat_id="42").validate()

    def test_missing_chat_id_raises(self):
        with pytest.raises(ConfigValidationError, match="chat ID is required"):
            TelegramConfig(token="123:ABCdef", chat_id="").validate()

    def test_negative_retry_count_raises(self):
        with pytest.raises(ConfigValidationError, match="Retry count"):
            self._valid(retry_count=-1).validate()

    def test_non_positive_timeout_raises(self):
        with pytest.raises(ConfigValidationError, match="Timeout"):
            self._valid(timeout=0).validate()

    def test_to_dict_masks_secret_but_keeps_bot_id(self):
        result = self._valid(token="123456789:SUPERsecretVALUE").to_dict()
        assert result["token"] == "123456789:***"

    def test_to_dict_masks_token_without_colon(self):
        cfg = TelegramConfig(token="weirdtokennocolon", chat_id="42")
        assert cfg.to_dict()["token"] == "***"

    def test_from_env_reads_values(self, telegram_env):
        cfg = TelegramConfig.from_env()
        assert cfg.token == "123456789:ABCdef_GHI-jkl"
        assert cfg.chat_id == "987654321"

    def test_from_env_missing_raises(self):
        with pytest.raises(ConfigValidationError):
            TelegramConfig.from_env()

    def test_from_env_non_integer_retry_raises(self, telegram_env, monkeypatch):
        monkeypatch.setenv("TELEGRAM_RETRY_COUNT", "abc")
        with pytest.raises(ConfigValidationError, match="TELEGRAM_RETRY_COUNT"):
            TelegramConfig.from_env()


class TestPTTConfig:
    def test_defaults_are_valid(self):
        PTTConfig().validate()

    def test_error_messages_populated(self):
        assert len(PTTConfig().error_messages) == 6

    @pytest.mark.parametrize("hours", [-13, 15])
    def test_timezone_out_of_range_raises(self, hours):
        with pytest.raises(ConfigValidationError, match="Timezone"):
            PTTConfig(timezone_hours=hours).validate()

    def test_negative_max_retries_raises(self):
        with pytest.raises(ConfigValidationError, match="Max retries"):
            PTTConfig(max_retries=-1).validate()

    def test_from_env_prefers_ptt_prefixed_timezone(self, monkeypatch):
        monkeypatch.setenv("ptt_timezone_hours", "0")
        monkeypatch.setenv("timezone_hours", "5")
        assert PTTConfig.from_env().timezone_hours == 0

    def test_from_env_falls_back_to_legacy_timezone(self, monkeypatch):
        monkeypatch.setenv("timezone_hours", "3")
        assert PTTConfig.from_env().timezone_hours == 3

    def test_from_env_non_integer_raises(self, monkeypatch):
        monkeypatch.setenv("ptt_max_retries", "lots")
        with pytest.raises(ConfigValidationError, match="ptt_max_retries"):
            PTTConfig.from_env()

    def test_to_dict_drops_unserializable_error_messages(self):
        assert "error_messages" not in PTTConfig().to_dict()


class TestLogConfig:
    def test_debug_mode_sets_debug_level(self, monkeypatch):
        monkeypatch.setenv("DEBUG_MODE", "true")
        assert LogConfig.from_env().log_level == logging.DEBUG

    def test_invalid_log_level_falls_back_to_info(self, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "NOT_A_LEVEL")
        assert LogConfig.from_env().log_level == logging.INFO

    def test_to_dict_stringifies_level(self):
        assert LogConfig(log_level=logging.WARNING).to_dict()["log_level"] == "WARNING"


class TestAppConfig:
    def test_to_dict_has_no_test_mode(self, telegram_env):
        config = AppConfig.from_env()
        result = config.to_dict()
        assert "test_mode" not in result
        assert set(result) == {"telegram", "ptt", "log"}


class TestGetPttAccounts:
    def test_returns_single_account(self, monkeypatch):
        monkeypatch.setenv("PTT_USERNAME", "user1")
        monkeypatch.setenv("PTT_PASSWORD", "pass1")
        assert get_ptt_accounts() == [("user1", "pass1")]

    def test_missing_credentials_raises(self):
        with pytest.raises(ConfigValidationError, match="No PTT account"):
            get_ptt_accounts()
