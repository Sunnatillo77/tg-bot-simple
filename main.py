import logging
import os
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from db import Database
from openrouter_client import OpenRouterClient
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

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
    logger.info(f"Пользователь {update.effective_user.id} запустил бота")


async def show_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список всех моделей"""
    models = db.get_all_models()

    if not models:
        await update.message.reply_text("❌ Модели не найдены в базе данных")
        logger.warning("Модели не найдены в базе данных")
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
    logger.info(f"Пользователь {update.effective_user.id} запросил список моделей")


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
        logger.warning(f"Пользователь {update.effective_user.id} ввел некорректный ID модели: {context.args[0]}")
        return

    models = db.get_all_models()
    model_ids = [model['id'] for model in models]

    if model_id not in model_ids:
        await update.message.reply_text(
            f"❌ Модель с ID {model_id} не найдена\n"
            f"Доступные ID: {', '.join(map(str, model_ids))}"
        )
        logger.warning(f"Пользователь {update.effective_user.id} запросил несуществующую модель ID: {model_id}")
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
        logger.info(f"Пользователь {update.effective_user.id} выбрал модель: {active_model['name']} (ID: {model_id})")
    else:
        await update.message.reply_text("❌ Ошибка при изменении модели")
        logger.error(f"Ошибка при изменении модели на ID: {model_id} для пользователя {update.effective_user.id}")


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
        logger.warning(f"Пользователь {update.effective_user.id} пытается задать вопрос без выбранной модели")
        return

    await update.message.reply_chat_action("typing")
    logger.info(
        f"Пользователь {update.effective_user.id} задал вопрос модели {active_model['name']}: {question[:50]}...")

    messages = [
        {"role": "system", "content": "Ты полезный AI-ассистент. Отвечай кратко и по делу."},
        {"role": "user", "content": question}
    ]

    response = openrouter_client.generate_response(
        model=active_model['name'],
        messages=messages
    )

    if "error" in response:
        await update.message.reply_text(
            f"❌ Ошибка: {response['error']}\n"
            f"Попробуйте другую модель или повторите позже."
        )
        logger.error(f"Ошибка от OpenRouter для пользователя {update.effective_user.id}: {response['error']}")
    else:
        answer = response['text']
        latency = response.get('latency_ms', 0)

        # Обрезаем ответ если слишком длинный для Telegram
        if len(answer) > 4000:
            answer = answer[:4000] + "..."
            logger.warning(f"Ответ от модели обрезан с {len(response['text'])} до 4000 символов")

        reply_text = (
            f"🤖 *Ответ от {active_model['name']}*\n"
            f"Время ответа: {latency}мс\n\n"
            f"{answer}"
        )

        await update.message.reply_text(reply_text, parse_mode='Markdown')
        logger.info(
            f"Успешный ответ пользователю {update.effective_user.id} от модели {active_model['name']}, время: {latency}мс")


async def current_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать текущую активную модель"""
    active_model = db.get_active_model()

    if not active_model:
        await update.message.reply_text("❌ Активная модель не выбрана")
        logger.info(f"Пользователь {update.effective_user.id} запросил текущую модель, но она не выбрана")
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
    logger.info(f"Пользователь {update.effective_user.id} запросил информацию о текущей модели: {active_model['name']}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    logger.info(f"Пользователь {update.effective_user.id} запросил справку")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка в боте: {context.error}", exc_info=context.error)

    if update and update.message:
        await update.message.reply_text(
            "❌ Произошла ошибка. Попробуйте позже или выберите другую модель.\n"
            "Если ошибка повторяется, свяжитесь с администратором."
        )


async def post_init(application: Application):
    """Функция для настройки команд меню после инициализации"""
    commands = [BotCommand(cmd[0], cmd[1]) for cmd in COMMANDS]
    await application.bot.set_my_commands(commands)
    logger.info("Команды бота установлены")


def main():
    """Основная функция запуска бота"""
    # Проверяем наличие .env файла
    if not os.path.exists('.env'):
        logger.error("Файл .env не найден")
        print("❌ Ошибка: Создайте файл .env с переменными TELEGRAM_BOT_TOKEN и OPENROUTER_API_KEY")
        print("   Пример содержимого .env:")
        print("   TELEGRAM_BOT_TOKEN=ваш_токен_бота")
        print("   OPENROUTER_API_KEY=ваш_ключ_openrouter")
        print("\n   Создайте бота через @BotFather и получите ключ OpenRouter на https://openrouter.ai/keys")
        return

    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        print("❌ Ошибка: TELEGRAM_BOT_TOKEN не найден в .env файле")
        return

    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY не найден в переменных окружения")
        print("⚠️  Предупреждение: OPENROUTER_API_KEY не найден в .env файле")
        print("   Бот запустится, но запросы к моделям не будут работать")

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
    print("=" * 50)
    print("🤖 Бот запускается...")
    print(f"📁 База данных: bot.db")
    print(f"📝 Логи: bot.log")
    print("=" * 50)

    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        print(f"❌ Критическая ошибка: {e}")


if __name__ == "__main__":
    main()