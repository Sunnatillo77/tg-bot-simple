"""
Фикстуры для тестов.
"""

import pytest
import sqlite3
import tempfile
import os
from importlib import reload
import sys

from db import Database
import openrouter_client
from metrics import MetricsRegistry


@pytest.fixture
def db_module(monkeypatch):
    """
    Создаёт временную БД в памяти для тестов.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp_path = tmp.name
    tmp.close()

    # Monkey-patch the Database class to use our temp file
    original_init = Database.__init__

    def patched_init(self, db_path=tmp_path):
        self.db_path = db_path
        self.init_database()

    monkeypatch.setattr(Database, "__init__", patched_init)

    if "db" in sys.modules:
        reload(sys.modules["db"])
    import db

    db_obj = db.Database(tmp_path)

    yield db_obj

    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def main_module(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")

    if "main" in sys.modules:
        reload(sys.modules["main"])
    import main

    yield main


@pytest.fixture
def openrouter_module(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")

    if "openrouter_client" in sys.modules:
        reload(sys.modules["openrouter_client"])
    import openrouter_client

    yield openrouter_client


@pytest.fixture
def metrics_registry():
    registry = MetricsRegistry()
    return registry


@pytest.fixture
def temp_log_dir(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    monkeypatch.setenv("LOG_DIR", str(log_dir))
    monkeypatch.setenv("LOG_FILE", "test.log")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    import logging
    logging.root.handlers.clear()

    yield log_dir

    logging.root.handlers.clear()


@pytest.fixture
def mock_update():
    from unittest.mock import AsyncMock

    mock_update = AsyncMock()
    mock_update.effective_user = AsyncMock()
    mock_update.effective_user.id = 12345
    mock_update.effective_user.first_name = "TestUser"

    mock_update.message = AsyncMock()
    mock_update.message.reply_text = AsyncMock()
    mock_update.message.reply_chat_action = AsyncMock()

    return mock_update


@pytest.fixture
def mock_context():
    from unittest.mock import AsyncMock

    mock_context = AsyncMock()
    mock_context.args = []

    return mock_context