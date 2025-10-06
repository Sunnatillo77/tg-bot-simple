import os
import logging
from dotenv import load_dotenv
import telebot
from telebot import types
import requests
import time
import sys

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("В .env файле нет TOKEN")

# Создание объекта бота
bot = telebot.TeleBot(TOKEN)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

print("🤖 Инициализация бота...")

# Остальной код остается БЕЗ ИЗМЕНЕНИЙ (как в предыдущем ответе)
# Словарь для погоды
WMO_DESC = {
    0: "ясно", 1: "в осн. ясно", 2: "переменная облачность", 3: "пасмурно",
    45: "туман", 48: "изморозь", 51: "морось", 53: "морось", 55: "сильная морось",
    61: "дождь", 63: "дождь", 65: "сильный дождь", 71: "снег",
    80: "ливни", 95: "гроза"
}

# Кэш для погоды
weather_cache = {}
CACHE_DURATION = 600


def parse_ints_from_text(text: str) -> list[int]:
    text = text.replace(",", " ")
    tokens = [t for t in text.split() if not t.startswith("/")]
    result = []
    for t in tokens:
        cleaned_token = t.strip().lstrip("-")
        if cleaned_token.isdigit():
            result.append(int(t))
    return result


def make_main_keyboard() -> types.ReplyKeyboardMarkup:
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("📊 Сумма", "📈 Максимум")
    keyboard.row("ℹ️ О боте", "🌤 Погода (Москва)")
    keyboard.row("/help", "/confirm", "/hide")
    return keyboard


def fetch_weather_moscow() -> str:
    current_time = time.time()
    if 'data' in weather_cache and current_time - weather_cache.get('timestamp', 0) < CACHE_DURATION:
        return weather_cache['data']

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 55.7558,
        "longitude": 37.6173,
        "current": "temperature_2m,weather_code",
        "timezone": "Europe/Moscow"
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        current_data = response.json()["current"]
        temperature = round(current_data["temperature_2m"])
        weather_code = int(current_data.get("weather_code", 0))

        if temperature < 0:
            emoji = "❄️"
        elif temperature > 20:
            emoji = "☀️"
        else:
            emoji = "⛅"

        weather_text = f"{emoji} Москва: сейчас {temperature}°C, {WMO_DESC.get(weather_code, 'по данным модели')}"

        weather_cache['data'] = weather_text
        weather_cache['timestamp'] = current_time

        return weather_text
    except Exception as e:
        logging.error(f"Ошибка получения погоды: {e}")
        return "❌ Не удалось получить данные о погоде"


# Обработчики команд (остаются без изменений)
@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = """🤖 Привет! Я учебный бот.

Доступные команды:
/start, /help - показать справку
/about - информация о боте
/sum - сумма чисел
/max - максимум чисел
/confirm - подтверждение действия
/hide - скрыть клавиатуру
/show - показать клавиатуру

Используйте кнопки ниже для быстрого доступа к функциям!"""

    bot.reply_to(message, welcome_text, reply_markup=make_main_keyboard())
    logging.info(f"Пользователь {message.from_user.first_name} начал работу с ботом")


@bot.message_handler(commands=['help'])
def help_cmd(message):
    help_text = """📋 Доступные команды:

🔹 Основные команды:
/start - начать работу
/help - эта справка
/about - информация о боте

🔹 Математические операции:
/sum 2 3 5 - сумма чисел
/max 2 3 5 - максимум чисел

🔹 Интерфейс:
/confirm - подтверждение действия
/hide - скрыть клавиатуру
/show - показать клавиатуру

💡 Используйте кнопки меню для удобства!"""
    bot.reply_to(message, help_text)
    logging.info(f"Команда /help от {message.from_user.first_name}")


@bot.message_handler(commands=['about'])
def about(message):
    about_text = """ℹ️ О боте:

Я учебный бот, созданный для демонстрации возможностей Telegram Bot API.

📊 Функциональность:
• Сумма и максимум чисел
• Погода в Москве
• Inline-кнопки для подтверждения
• Reply-клавиатура для навигации

🛠 Технологии:
• Python 3.11
• pyTelegramBotAPI
• Open-Meteo API"""
    bot.reply_to(message, about_text)
    logging.info(f"Команда /about от {message.from_user.first_name}")


@bot.message_handler(commands=['sum'])
def sum_command(message):
    logging.info(f"/sum от {message.from_user.first_name}: {message.text}")
    numbers = parse_ints_from_text(message.text)
    logging.info(f"Распознаны числа: {numbers}")

    if numbers:
        total = sum(numbers)
        logging.info(f"Результат суммы: {total}")
        bot.reply_to(message, f"📊 Сумма: {total}")
    else:
        bot.reply_to(message, "❌ Не вижу чисел. Пример: /sum 2 3 10 или 2, 3, -5")


@bot.message_handler(commands=['max'])
def max_command(message):
    logging.info(f"/max от {message.from_user.first_name}: {message.text}")
    numbers = parse_ints_from_text(message.text)
    logging.info(f"Распознаны числа: {numbers}")

    if numbers:
        maximum = max(numbers)
        logging.info(f"Результат максимума: {maximum}")
        bot.reply_to(message, f"📈 Максимум: {maximum}")
    else:
        bot.reply_to(message, "❌ Не вижу чисел. Пример: /max 2 3 10 или 2, 3, -5")


@bot.message_handler(commands=['show'])
def show_keyboard(message):
    bot.reply_to(message, "⌨️ Клавиатура активирована!", reply_markup=make_main_keyboard())
    logging.info(f"Пользователь {message.from_user.first_name} запросил показ клавиатуры")


@bot.message_handler(commands=['hide'])
def hide_keyboard(message):
    remove_keyboard = types.ReplyKeyboardRemove()
    bot.reply_to(message, "👋 Клавиатура скрыта!", reply_markup=remove_keyboard)
    logging.info(f"Пользователь {message.from_user.first_name} скрыл клавиатуру")


@bot.message_handler(commands=['confirm'])
def confirm_command(message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("✅ Да", callback_data="confirm:yes"),
        types.InlineKeyboardButton("❌ Нет", callback_data="confirm:no"),
        types.InlineKeyboardButton("😂 Позже", callback_data="confirm:later")
    )
    bot.send_message(message.chat.id, "❓ Сохранить изменения?", reply_markup=keyboard)
    logging.info(f"Команда /confirm от {message.from_user.first_name}")


# Обработчики кнопок
@bot.message_handler(func=lambda message: message.text == "ℹ️ О боте")
def about_button(message):
    bot.reply_to(message,
                 "🤖 Я умный бот с функциями:\n• Сумма чисел\n• Поиск максимума\n• Погода в Москве\n• Подтверждение действий")
    logging.info(f"Кнопка 'О боте' от {message.from_user.first_name}")


@bot.message_handler(func=lambda message: message.text == "📊 Сумма")
def sum_button(message):
    bot.send_message(message.chat.id, "💭 Введите числа через пробел или запятую:")
    bot.register_next_step_handler(message, process_sum_input)
    logging.info(f"Кнопка 'Сумма' от {message.from_user.first_name}")


@bot.message_handler(func=lambda message: message.text == "📈 Максимум")
def max_button(message):
    bot.send_message(message.chat.id, "💭 Введите числа через пробел или запятую:")
    bot.register_next_step_handler(message, process_max_input)
    logging.info(f"Кнопка 'Максимум' от {message.from_user.first_name}")


@bot.message_handler(func=lambda message: message.text == "🌤 Погода (Москва)")
def weather_button(message):
    bot.send_message(message.chat.id, "⏳ Запрашиваю данные о погоде...")
    weather_info = fetch_weather_moscow()
    bot.reply_to(message, weather_info)
    logging.info(f"Кнопка 'Погода' от {message.from_user.first_name}")


# Обработчики ввода
def process_sum_input(message):
    numbers = parse_ints_from_text(message.text)
    if numbers:
        total = sum(numbers)
        bot.reply_to(message, f"📊 Сумма: {total}")
        logging.info(f"Сумма чисел {numbers} = {total}")
    else:
        bot.reply_to(message, "❌ Не вижу чисел. Пример: 2 3 10 или 2, 3, -5")


def process_max_input(message):
    numbers = parse_ints_from_text(message.text)
    if numbers:
        maximum = max(numbers)
        bot.reply_to(message, f"📈 Максимум: {maximum}")
        logging.info(f"Максимум чисел {numbers} = {maximum}")
    else:
        bot.reply_to(message, "❌ Не вижу чисел. Пример: 2 3 10 или 2, 3, -5")


# Inline кнопки
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm:"))
def handle_confirmation(call):
    choice = call.data.split(":")[1]
    bot.answer_callback_query(call.id, "Выбор принят!")
    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=None
    )

    if choice == "yes":
        response = "✅ Изменения сохранены!"
    elif choice == "no":
        response = "❌ Изменения отменены."
    else:
        response = "⏳ Отложено на потом 😊"

    bot.send_message(call.message.chat.id, response)
    logging.info(f"Пользователь {call.from_user.first_name} выбрал: {choice}")


@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    if message.text.startswith('/'):
        bot.reply_to(message, "❌ Неизвестная команда. Напишите /help для списка команд.")
    else:
        bot.reply_to(message, "💡 Используйте команды или кнопки меню для взаимодействия с ботом.")


if __name__ == "__main__":
    print("🤖 Бот запускается...")
    logging.info("Бот запущен")

    try:
        # Останавливаем любые предыдущие вебхуки
        bot.remove_webhook()
        time.sleep(1)

        print("✅ Запуск polling...")
        bot.infinity_polling(skip_pending=True, timeout=60)

    except telebot.apihelper.ApiException as e:
        if "Conflict" in str(e):
            print("❌ ОШИБКА: Уже запущен другой экземпляр бота!")
            print("💡 Решение: Закройте все другие окна терминала и перезапустите бота")
        else:
            print(f"❌ Ошибка API: {e}")
    except KeyboardInterrupt:
        print("⏹ Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
    finally:
        print("👋 Работа бота завершена")