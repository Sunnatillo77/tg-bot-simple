import logging
import asyncio
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from db import Database
from openrouter_client import OpenRouterClient
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)
logger = logging.getLogger(__name__)

# Инициализация базы данных и клиента OpenRouter
db = Database()
openrouter_client = OpenRouterClient()

# Список команд для меню бота
COMMANDS = [
    ("start", "Запустить бота"),
    ("help", "Показать справку"),
    ("models", "Показать список моделей"),
    ("setmodel", "Выбрать активную модель"),
    ("ask", "Задать вопрос модели"),
    ("current", "Текущая активная модель")
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = (
        "🤖 *Добро пожаловать в AI бота!*\n\n"
        "Я использую различные языковые модели через OpenRouter.\n\n"
        "*Доступные команды:*\n"
        "/models - Показать все модели\n"
        "/setmodel - Выбрать активную модель\n"
        "/ask - Задать вопрос AI\n"
        "/current - Текущая активная модель\n"
        "/help - Справка\n\n"
        "Для начала выберите модель командой /setmodel"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def show_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список всех моделей"""
    models = db.get_all_models()

    if not models:
        await update.message.reply_text("❌ Модели не найдены в базе данных")
        return

    active_model = db.get_active_model()
    active_model_name = active_model['name'] if active_model else "Не выбрана"

    text = f"📋 *Список доступных моделей*\n\n"
    text += f"*Текущая активная модель:* {active_model_name}\n\n"

    for model in models:
        status = "✅ АКТИВНА" if model['active'] == 1 else "⚪"
        free = "🆓 БЕСПЛАТНО" if model['is_free'] == 1 else "💳"
        text += f"{status} {free} *{model['name']}*\n"
        text += f"   └ {model['description']}\n"
        text += f"   └ Макс. токенов: {model['max_tokens']}\n"
        text += f"   └ ID для выбора: {model['id']}\n\n"

    text += "\nЧтобы выбрать модель, используйте команду:\n`/setmodel <ID_модели>`"

    await update.message.reply_text(text, parse_mode='Markdown')


async def set_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор активной модели"""
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите ID модели. Пример: `/setmodel 1`\n"
            "Список моделей: /models",
            parse_mode='Markdown'
        )
        return

    try:
        model_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID модели должен быть числом")
        return

    models = db.get_all_models()
    model_ids = [model['id'] for model in models]

    if model_id not in model_ids:
        await update.message.reply_text(
            f"❌ Модель с ID {model_id} не найдена\n"
            f"Доступные ID: {', '.join(map(str, model_ids))}"
        )
        return

    success = db.set_active_model(model_id)

    if success:
        active_model = db.get_active_model()
        await update.message.reply_text(
            f"✅ Модель изменена!\n"
            f"Теперь активна: *{active_model['name']}*\n"
            f"Описание: {active_model['description']}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Ошибка при изменении модели")


async def ask_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задать вопрос модели"""
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите ваш вопрос. Пример:\n"
            "`/ask Как работает искусственный интеллект?`",
            parse_mode='Markdown'
        )
        return

    question = " ".join(context.args)
    active_model = db.get_active_model()

    if not active_model:
        await update.message.reply_text(
            "❌ Активная модель не выбрана. Используйте /setmodel"
        )
        return

    await update.message.reply_chat_action("typing")

    # Формируем сообщения для модели
    messages = [
        {"role": "system", "content": "Ты полезный AI-ассистент. Отвечай кратко и по делу."},
        {"role": "user", "content": question}
    ]

    # Отправляем запрос к OpenRouter
    response = openrouter_client.generate_response(
        model=active_model['name'],
        messages=messages
    )

    if "error" in response:
        await update.message.reply_text(
            f"❌ Ошибка: {response['error']}\n"
            f"Попробуйте другую модель или повторите позже."
        )
    else:
        answer = response['text']
        latency = response.get('latency_ms', 0)

        # Обрезаем ответ если слишком длинный для Telegram
        if len(answer) > 4000:
            answer = answer[:4000] + "..."

        reply_text = (
            f"🤖 *Ответ от {active_model['name']}*\n"
            f"Время ответа: {latency}мс\n\n"
            f"{answer}"
        )

        await update.message.reply_text(reply_text, parse_mode='Markdown')


async def current_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать текущую активную модель"""
    active_model = db.get_active_model()

    if not active_model:
        await update.message.reply_text("❌ Активная модель не выбрана")
        return

    text = (
        f"✅ *Текущая активная модель*\n\n"
        f"*Название:* {active_model['name']}\n"
        f"*Провайдер:* {active_model['provider']}\n"
        f"*Описание:* {active_model['description']}\n"
        f"*Макс. токенов:* {active_model['max_tokens']}\n"
        f"*Бесплатная:* {'Да' if active_model['is_free'] == 1 else 'Нет'}\n\n"
        f"Изменить модель: /setmodel\n"
        f"Список всех моделей: /models"
    )

    await update.message.reply_text(text, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать справку"""
    help_text = (
        "📖 *Справка по командам*\n\n"
        "*/start* - Запустить бота\n"
        "*/models* - Показать список всех моделей\n"
        "*/setmodel <ID>* - Выбрать активную модель\n"
        "*/ask <вопрос>* - Задать вопрос AI\n"
        "*/current* - Текущая активная модель\n"
        "*/help* - Эта справка\n\n"
        "*Примеры:*\n"
        "`/setmodel 3` - выбрать модель с ID 3\n"
        "`/ask Что такое ИИ?` - задать вопрос\n\n"
        "Бесплатные модели могут иметь ограничения по количеству запросов."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")

    if update and update.message:
        await update.message.reply_text(
            "❌ Произошла ошибка. Попробуйте позже или выберите другую модель."
        )


async def post_init(application: Application):
    """Функция для настройки команд меню после инициализации"""
    commands = [BotCommand(cmd[0], cmd[1]) for cmd in COMMANDS]
    await application.bot.set_my_commands(commands)


def main():
    """Основная функция запуска бота"""
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        print("Ошибка: TELEGRAM_BOT_TOKEN не найден в .env файле")
        return

    # Создаем приложение с post_init функцией
    application = Application.builder() \
        .token(TELEGRAM_TOKEN) \
        .post_init(post_init) \
        .build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("models", show_models))
    application.add_handler(CommandHandler("setmodel", set_model))
    application.add_handler(CommandHandler("ask", ask_model))
    application.add_handler(CommandHandler("current", current_model))

    # Обработчик ошибок
    application.add_error_handler(error_handler)

    # Запуск бота
    print("🤖 Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()