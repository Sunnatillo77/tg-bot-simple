"""
Тесты для функций работы с сообщениями.
"""

import pytest
from unittest.mock import patch


def test_build_messages_for_character():
    character_prompt = "Ты опытный программист. Отвечай на технические вопросы подробно и с примерами кода."
    question = "Как написать функцию на Python?"

    def mock_build_messages(character_prompt, question):
        return [
            {"role": "system", "content": character_prompt},
            {"role": "user", "content": question}
        ]

    result = mock_build_messages(character_prompt, question)

    assert len(result) == 2
    assert result[0]["role"] == "system"
    assert result[0]["content"] == character_prompt
    assert result[1]["role"] == "user"
    assert result[1]["content"] == question


def test_messages_with_empty_question():
    character_prompt = "Ты полезный AI-ассистент."

    def mock_build_messages(character_prompt, question):
        if not question or question.strip() == "":
            return []
        return [
            {"role": "system", "content": character_prompt},
            {"role": "user", "content": question}
        ]

    result_empty = mock_build_messages(character_prompt, "")
    assert result_empty == []

    result_spaces = mock_build_messages(character_prompt, "   ")
    assert result_spaces == []

    result_normal = mock_build_messages(character_prompt, "Привет!")
    assert len(result_normal) == 2


def test_build_messages_integration(main_module):
    """Интеграционный тест для реальной функции из main.py"""
    character_prompt = "Ты опытный программист."
    question = "Как написать функцию?"

    result = main_module._build_messages(character_prompt, question)

    assert len(result) == 2
    assert result[0]["role"] == "system"
    assert result[0]["content"] == character_prompt
    assert result[1]["role"] == "user"
    assert result[1]["content"] == question


def test_build_messages_for_character_integration(main_module):
    """Интеграционный тест для реальной функции из main.py"""
    character_prompt = "Ты опытный программист."
    question = "Как написать функцию?"

    result = main_module._build_messages_for_character(character_prompt, question)

    assert len(result) == 2
    assert result[0]["role"] == "system"
    assert result[0]["content"] == character_prompt
    assert result[1]["role"] == "user"
    assert result[1]["content"] == question

    # Тест с пустым вопросом
    result_empty = main_module._build_messages_for_character(character_prompt, "")
    assert result_empty == []

    result_spaces = main_module._build_messages_for_character(character_prompt, "   ")
    assert result_spaces == []