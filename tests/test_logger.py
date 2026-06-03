"""Tests for the logging setup and color formatter."""

import logging

from pttautosign.utils.config import LogConfig
from pttautosign.utils.logger import setup_logging


def _color_formatter():
    setup_logging(LogConfig(log_level=logging.DEBUG))
    return logging.getLogger().handlers[0].formatter


def test_record_name_and_levelname_restored_after_format():
    formatter = _color_formatter()
    record = logging.LogRecord(
        "a.b.c.d", logging.INFO, "path", 1, "msg", None, None
    )

    formatted = formatter.format(record)

    # M3 regression: the shared LogRecord must be left untouched so other
    # handlers see the original values, even though the output is shortened.
    assert record.name == "a.b.c.d"
    assert record.levelname == "INFO"
    # The rendered line shortens the name to the last two segments.
    assert "c.d" in formatted


def test_short_name_unchanged_for_shallow_loggers():
    formatter = _color_formatter()
    record = logging.LogRecord("a.b", logging.INFO, "path", 1, "msg", None, None)

    formatter.format(record)

    assert record.name == "a.b"
