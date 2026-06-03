"""Tests for the service factory."""

from pttautosign.utils.config import AppConfig, LogConfig, PTTConfig, TelegramConfig
from pttautosign.utils.factory import ServiceFactory
from pttautosign.utils.ptt import PTTAutoSign
from pttautosign.utils.telegram import TelegramBot


def _app_config() -> AppConfig:
    return AppConfig(
        telegram=TelegramConfig(token="123456789:ABCdef_GHI-jkl", chat_id="42"),
        ptt=PTTConfig(),
        log=LogConfig(),
    )


class TestServiceFactory:
    def test_notification_service_is_telegram_bot(self):
        assert isinstance(
            ServiceFactory(_app_config()).get_notification_service(), TelegramBot
        )

    def test_notification_service_is_cached(self):
        factory = ServiceFactory(_app_config())
        assert factory.get_notification_service() is factory.get_notification_service()

    def test_login_service_is_ptt_autosign(self):
        assert isinstance(
            ServiceFactory(_app_config()).get_login_service(), PTTAutoSign
        )

    def test_login_service_is_cached(self):
        factory = ServiceFactory(_app_config())
        assert factory.get_login_service() is factory.get_login_service()

    def test_notification_service_uses_ptt_timezone(self):
        config = _app_config()
        config.ptt.timezone_hours = 0
        bot = ServiceFactory(config).get_notification_service()
        assert bot.tz is not None
        assert bot.tz.utcoffset(None).total_seconds() == 0
