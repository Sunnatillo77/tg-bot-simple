import os
import requests
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования для клиент
logger = logging.getLogger(__name__)


class OpenRouterClient:
    def __init__(self):
        # Получаем ключ из переменных окружения
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            error_msg = "OPENROUTER_API_KEY не найден в переменных окружения"
            logger.error(error_msg)
            raise ValueError(error_msg)

        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",  # Ваш сайт
            "X-Title": "Telegram Bot"  # Название приложения
        }
        logger.info("OpenRouterClient инициализирован")

    def generate_response(self, model: str, messages: list, temperature: float = 0.2, max_tokens: int = 400) -> dict:
        """Отправляет запрос к OpenRouter API"""
        if not self.api_key:
            error_msg = "API ключ не установлен"
            logger.error(error_msg)
            return {"error": error_msg}

        if not model:
            error_msg = "Модель не указана"
            logger.error(error_msg)
            return {"error": error_msg}

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            logger.info(f"Отправка запроса к модели: {model}")

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            logger.info(f"Статус ответа от OpenRouter: {response.status_code}")

            # Обработка HTTP ошибок
            if response.status_code == 401:
                error_msg = "Неверный API ключ OpenRouter"
                logger.error(error_msg)
                return {"error": error_msg}
            elif response.status_code == 404:
                error_msg = "Модель не найдена"
                logger.error(error_msg)
                return {"error": error_msg}
            elif response.status_code == 429:
                error_msg = "Превышен лимит запросов. Попробуйте позже."
                logger.warning(error_msg)
                return {"error": error_msg}
            elif response.status_code in [500, 502, 503, 504]:
                error_messages = {
                    500: "Внутренняя ошибка сервера OpenRouter",
                    502: "Плохой шлюз - проблемы с подключением к серверу",
                    503: "Сервис временно недоступен",
                    504: "Таймаут шлюза"
                }
                error_msg = error_messages.get(response.status_code, f"Ошибка сервера ({response.status_code})")
                logger.error(f"{error_msg}. Status code: {response.status_code}")
                return {"error": f"{error_msg}. Попробуйте позже."}
            elif response.status_code != 200:
                error_msg = f"Ошибка API: {response.status_code}"
                logger.error(error_msg)
                return {"error": error_msg}

            data = response.json()

            if "choices" not in data or not data["choices"]:
                error_msg = "Некорректный ответ от API"
                logger.error(error_msg)
                return {"error": error_msg}

            logger.info(f"Успешный ответ от модели {model}, время обработки: {data.get('latency_ms', 0)}мс")

            return {
                "text": data["choices"][0]["message"]["content"],
                "latency_ms": data.get("latency_ms", 0)
            }

        except requests.exceptions.Timeout:
            error_msg = "Таймаут при подключении к OpenRouter"
            logger.error(error_msg)
            return {"error": f"{error_msg}. Попробуйте позже."}
        except requests.exceptions.ConnectionError:
            error_msg = "Ошибка подключения к серверу OpenRouter"
            logger.error(error_msg)
            return {"error": f"{error_msg}. Проверьте интернет-соединение."}
        except requests.exceptions.RequestException as e:
            error_msg = f"Ошибка подключения: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Неизвестная ошибка: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}