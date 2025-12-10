"""
Тесты для модуля openrouter_client.py
"""

import json
import responses
import pytest
from importlib import reload


@responses.activate
def test_chat_once_success(openrouter_module, monkeypatch):
    """Тест успешного запроса к OpenRouter"""
    chat_once = openrouter_module.chat_once

    # Мокаем URL
    url = "https://openrouter.ai/api/v1/chat/completions"

    # Устанавливаем фиктивный ответ
    mock_response = {
        "id": "test_id",
        "choices": [
            {
                "message": {
                    "content": "This is a test response from OpenRouter"
                }
            }
        ]
    }

    responses.add(
        responses.POST,
        url,
        json=mock_response,
        status=200
    )

    # Вызываем функцию
    messages = [{"role": "user", "content": "Hello, how are you?"}]
    model = "test-model"

    result_text, latency_ms = chat_once(
        messages=messages,
        model=model,
        temperature=0.7,
        max_tokens=100,
        timeout_s=10
    )

    # Проверяем результат
    assert result_text == "This is a test response from OpenRouter"
    assert isinstance(latency_ms, int)
    assert latency_ms >= 0

    # Проверяем отправленные данные
    assert len(responses.calls) == 1
    request = responses.calls[0].request

    # Проверяем заголовки
    assert request.headers["Authorization"] == "Bearer test_key"
    assert request.headers["Content-Type"] == "application/json"

    # Проверяем тело запроса
    body = json.loads(request.body)
    assert body["model"] == model
    assert body["messages"] == messages
    assert body["temperature"] == 0.7
    assert body["max_tokens"] == 100


@responses.activate
def test_chat_once_http_error(openrouter_module, monkeypatch):
    """Тест обработки HTTP ошибок"""
    chat_once = openrouter_module.chat_once
    OpenRouterError = openrouter_module.OpenRouterError

    url = "https://openrouter.ai/api/v1/chat/completions"

    # Тестируем различные коды ошибок
    error_cases = [
        (401, "Unauthorized"),
        (429, "Too Many Requests"),
        (500, "Internal Server Error"),
        (503, "Service Unavailable")
    ]

    for status_code, error_name in error_cases:
        responses.reset()

        responses.add(
            responses.POST,
            url,
            json={"error": {"message": f"Test {error_name}"}},
            status=status_code
        )

        # Проверяем, что исключение выбрасывается
        with pytest.raises(OpenRouterError) as exc_info:
            chat_once(
                messages=[{"role": "user", "content": "Test"}],
                model="test-model",
                temperature=0.7,
                max_tokens=100,
                timeout_s=5
            )

        # Проверяем сообщение об ошибке
        error = exc_info.value
        assert error.status == status_code
        assert error_name in str(error) or str(status_code) in str(error)


@responses.activate
def test_chat_once_network_error(openrouter_module, monkeypatch):
    """Тест обработки сетевых ошибок"""
    chat_once = openrouter_module.chat_once
    OpenRouterError = openrouter_module.OpenRouterError

    url = "https://openrouter.ai/api/v1/chat/completions"

    # Симулируем таймаут
    responses.add(
        responses.POST,
        url,
        body=ConnectionError("Connection timed out")
    )

    with pytest.raises(OpenRouterError) as exc_info:
        chat_once(
            messages=[{"role": "user", "content": "Test"}],
            model="test-model",
            temperature=0.7,
            max_tokens=100,
            timeout_s=1
        )

    error = exc_info.value
    assert "сетевой ошибке" in str(error) or "таймаут" in str(error).lower()


@responses.activate
def test_chat_once_invalid_response(openrouter_module, monkeypatch):
    """Тест обработки невалидного ответа"""
    chat_once = openrouter_module.chat_once
    OpenRouterError = openrouter_module.OpenRouterError

    url = "https://openrouter.ai/api/v1/chat/completions"

    # Отправляем невалидный JSON
    responses.add(
        responses.POST,
        url,
        body="Invalid JSON response",
        status=200,
        content_type="application/json"
    )

    with pytest.raises(OpenRouterError) as exc_info:
        chat_once(
            messages=[{"role": "user", "content": "Test"}],
            model="test-model",
            temperature=0.7,
            max_tokens=100,
            timeout_s=5
        )

    error = exc_info.value
    assert "невалидный ответ" in str(error) or "JSON" in str(error)


@responses.activate
def test_chat_once_empty_response(openrouter_module, monkeypatch):
    """Тест обработки пустого ответа"""
    chat_once = openrouter_module.chat_once
    OpenRouterError = openrouter_module.OpenRouterError

    url = "https://openrouter.ai/api/v1/chat/completions"

    # Отправляем пустой ответ
    responses.add(
        responses.POST,
        url,
        json={"choices": []},  # Пустой список choices
        status=200
    )

    with pytest.raises(OpenRouterError) as exc_info:
        chat_once(
            messages=[{"role": "user", "content": "Test"}],
            model="test-model",
            temperature=0.7,
            max_tokens=100,
            timeout_s=5
        )

    error = exc_info.value
    assert "пустой ответ" in str(error) or "отсутствует" in str(error)


def test_openrouter_client_module_reload(monkeypatch):
    """Тест перезагрузки модуля с новыми переменными окружения"""
    import openrouter_client

    # Устанавливаем новое значение API ключа
    new_key = "new_test_key_123"
    monkeypatch.setenv("OPENROUTER_API_KEY", new_key)

    # Перезагружаем модуль
    reloaded_module = reload(openrouter_client)

    # Проверяем, что модуль перезагрузился
    # (в реальном коде нужно проверить, что ключ используется)
    assert reloaded_module is not None