"""
Клиент для работы с OpenRouter API.
"""

import os
import time
import json
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class OpenRouterError(Exception):
    """Ошибка работы с OpenRouter API."""

    def __init__(self, message: str, status: int = None):
        self.message = message
        self.status = status
        super().__init__(f"OpenRouterError (status={status}): {message}")


class OpenRouterClient:
    """Клиент для взаимодействия с OpenRouter API."""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY не найден в переменных окружения")

    def generate_response(
            self,
            model: str,
            messages: List[Dict[str, str]],
            temperature: float = 0.7,
            max_tokens: int = 400,
            timeout_s: int = 30
    ) -> Dict[str, Any]:
        """
        Генерирует ответ от модели через OpenRouter API.

        Args:
            model: Имя модели (например, "openai/gpt-3.5-turbo")
            messages: Список сообщений в формате [{"role": "user/system", "content": "text"}]
            temperature: Температура генерации (0.0-2.0)
            max_tokens: Максимальное количество токенов в ответе
            timeout_s: Таймаут запроса в секундах

        Returns:
            Словарь с ответом или ошибкой
        """
        try:
            start_time = time.time()

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/yourusername/telegram-ai-bot",
                    "X-Title": "Telegram AI Bot"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=timeout_s
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if response.status_code != 200:
                error_data = response.json().get("error", {})
                error_message = error_data.get("message", response.text)
                raise OpenRouterError(error_message, response.status_code)

            data = response.json()

            if "choices" not in data or not data["choices"]:
                raise OpenRouterError("Пустой ответ от API")

            content = data["choices"][0]["message"]["content"]

            return {
                "text": content,
                "latency_ms": latency_ms,
                "model": model,
                "usage": data.get("usage", {})
            }

        except requests.exceptions.Timeout:
            raise OpenRouterError("Таймаут запроса к OpenRouter API")
        except requests.exceptions.ConnectionError:
            raise OpenRouterError("Ошибка соединения с OpenRouter API")
        except json.JSONDecodeError:
            raise OpenRouterError("Невалидный JSON в ответе от API")
        except Exception as e:
            raise OpenRouterError(f"Неизвестная ошибка: {str(e)}")


def chat_once(
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 400,
        timeout_s: int = 30
) -> tuple[str, int]:
    """
    Упрощенная функция для одного запроса к OpenRouter.

    Args:
        messages: Список сообщений
        model: Имя модели
        temperature: Температура генерации
        max_tokens: Максимальное количество токенов
        timeout_s: Таймаут в секундах

    Returns:
        Кортеж (текст ответа, задержка в мс)
    """
    client = OpenRouterClient()
    response = client.generate_response(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout_s=timeout_s
    )
    return response["text"], response["latency_ms"]