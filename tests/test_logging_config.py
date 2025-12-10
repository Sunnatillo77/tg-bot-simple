"""
Тесты для модуля logging_config.py
"""

import pytest
import os
import logging
from logging_config import setup_logging, DotTimeFormatter


def test_dot_time_formatter():
    formatter = DotTimeFormatter()

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )

    import time as time_module
    record.created = time_module.time()
    record.msecs = 123.456

    formatted_time = formatter.formatTime(record)

    assert len(formatted_time) > 0
    assert formatted_time.count(":") == 2
    assert "." in formatted_time

    parts = formatted_time.split(".")
    assert len(parts) == 2
    assert len(parts[1]) == 3


def test_setup_logging_with_custom_env(temp_log_dir, monkeypatch):
    monkeypatch.setenv("LOG_ENCODING", "utf-8")
    monkeypatch.setenv("LOG_MAX_BYTES", "1000000")
    monkeypatch.setenv("LOG_BACKUP_COUNT", "3")

    original_handlers = logging.root.handlers.copy()
    original_level = logging.root.level

    try:
        setup_logging()

        assert temp_log_dir.exists()
        assert temp_log_dir.is_dir()

        root_logger = logging.getLogger()
        assert len(root_logger.handlers) >= 1
        assert root_logger.level == logging.DEBUG

        file_handlers = [
            h for h in root_logger.handlers
            if isinstance(h, logging.handlers.RotatingFileHandler)
        ]

        assert len(file_handlers) == 1

        file_handler = file_handlers[0]
        assert file_handler.maxBytes == 1000000
        assert file_handler.backupCount == 3
        assert file_handler.encoding == "utf-8"

        formatter = file_handler.formatter
        assert isinstance(formatter, DotTimeFormatter)

    finally:
        logging.root.handlers = original_handlers
        logging.root.setLevel(original_level)