"""
Тесты для команд бота.
"""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_start_command(main_module, mock_update, mock_context):
    from main import start

    await start(mock_update, mock_context)

    assert mock_update.message.reply_text.called

    call_args = mock_update.message.reply_text.call_args
    response_text = call_args[0][0]

    assert "Добро пожаловать" in response_text
    assert "TestUser" in response_text
    assert "Основные возможности" in response_text
    assert "Markdown" in call_args[1]['parse_mode']


@pytest.mark.asyncio
async def test_help_command(main_module, mock_update, mock_context):
    from main import help_command

    await help_command(mock_update, mock_context)

    assert mock_update.message.reply_text.called

    call_args = mock_update.message.reply_text.call_args
    response_text = call_args[0][0]

    assert "Справка по командам" in response_text
    assert "/start" in response_text
    assert "/help" in response_text


@pytest.mark.asyncio
async def test_set_model_no_args(main_module, mock_update, mock_context):
    from main import set_model

    await set_model(mock_update, mock_context)

    assert mock_update.message.reply_text.called

    call_args = mock_update.message.reply_text.call_args
    response_text = call_args[0][0]

    assert "Укажите ID модели" in response_text
    assert "/setmodel 1" in response_text


@pytest.mark.asyncio
async def test_set_model_invalid_id(main_module, mock_update, mock_context):
    from main import set_model

    mock_context.args = ["invalid_id"]

    await set_model(mock_update, mock_context)

    assert mock_update.message.reply_text.called

    call_args = mock_update.message.reply_text.call_args
    response_text = call_args[0][0]

    assert "ID модели должен быть числом" in response_text


@pytest.mark.asyncio
async def test_ask_no_question(main_module, mock_update, mock_context):
    from main import ask_model

    await ask_model(mock_update, mock_context)

    assert mock_update.message.reply_text.called

    call_args = mock_update.message.reply_text.call_args
    response_text = call_args[0][0]

    assert "Укажите ваш вопрос" in response_text
    assert "/ask" in response_text