import os
import logging
from dotenv import load_dotenv
import telebot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Получение токена бота
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("В .env файле нет TOKEN")

# Создание объекта бота
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    bot.reply_to(message, "Привет! Я твой первый бот! Напиши /help")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    logger.info(f"Пользователь {message.from_user.id} запросил помощь")
    help_text = """
Доступные команды:

/start - начать работу с ботом
/help - получить справку по командам
/about - информация о боте
/ping - проверить работоспособность бота
"""
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['about'])
def about(message):
    logger.info(f"Пользователь {message.from_user.id} запросил информацию о боте")
    about_text = """
🤖 **Обо мне:**

**Автор:** [Суннатилло]
**Версия:** 1.0
**Назначение:** Учебный проект для освоения создания Telegram ботов
"""
    bot.reply_to(message, about_text)

@bot.message_handler(commands=['ping'])
def ping(message):
    logger.info(f"Пользователь {message.from_user.id} проверил работоспособность бота")
    bot.reply_to(message, "🏓 pong! Бот работает исправно!")

# Обработка любого текстового сообщения
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    logger.info(f"Пользователь {message.from_user.id} отправил сообщение: {message.text}")
    bot.reply_to(message, "Я пока понимаю только команды. Напиши /help для списка команд")

if __name__ == "__main__":
    logger.info("Бот запускается...")
    print("🤖 Бот запущен! Для остановки нажмите Ctrl+C")
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
        print(f"Произошла ошибка: {e}")