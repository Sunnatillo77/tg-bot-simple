import logging
import os
import random
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes
from db import Database
from openrouter_client import OpenRouterClient
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация компонентов
try:
    db = Database()
    openrouter_client = OpenRouterClient()
    logger.info("Все компоненты успешно инициализированы")
except Exception as e:
    logger.error(f"Ошибка инициализации: {e}")
    print(f"❌ Критическая ошибка: {e}")
    print("Проверьте файл .env и наличие API ключей")
    exit(1)

# Константы
MAX_QUESTION_LENGTH = 2000
MAX_RESPONSE_LENGTH = 4000

# Список команд для меню бота
COMMANDS = [
    ("start", "Запустить бота"),
    ("help", "Показать справку"),
    ("models", "Показать список моделей"),
    ("setmodel", "Выбрать активную модель"),
    ("ask", "Задать вопрос активной модели"),
    ("ask_model", "Задать вопрос конкретной модели (ID)"),
    ("characters", "Показать список персонажей"),
    ("setcharacter", "Выбрать персонажа"),
    ("current", "Текущая активная модель и персонаж"),
    ("ask_random", "Задать вопрос случайному персонажу")
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"🤖 *Добро пожаловать, {user.first_name}!*\n\n"
        "Я - AI бот с поддержкой различных языковых моделей через OpenRouter.\n\n"
        "*📋 Основные возможности:*\n"
        "• Общение с разными AI-моделями\n"
        "• Выбор персонажей для диалога\n"
        "• Работа с бесплатными и платными моделями\n\n"
        "*🚀 Быстрый старт:*\n"
        "1. Посмотреть модели: /models\n"
        "2. Выбрать модель: /setmodel 1\n"
        "3. Выбрать персонажа: /characters\n"
        "4. Задать вопрос: /ask Привет! Как дела?\n\n"
        "*❓ Помощь:* /help\n"
        "*📊 Текущие настройки:* /current"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def show_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список всех моделей"""
    try:
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
            free = "🆓 БЕСПЛАТНО" if model['is_free'] == 1 else "💳 ПЛАТНАЯ"
            tokens = f"{model['max_tokens']:,}".replace(",", " ")
            text += f"{status} {free} *{model['name']}*\n"
            text += f"   ├ Провайдер: {model['provider']}\n"
            text += f"   ├ Описание: {model['description']}\n"
            text += f"   ├ Макс. токенов: {tokens}\n"
            text += f"   └ ID для выбора: `{model['id']}`\n\n"

        text += "\n*💡 Примеры использования:*\n"
        text += "• `/setmodel 1` - выбрать модель с ID 1\n"
        text += "• `/ask_model 5 Как работает ИИ?` - задать вопрос модели с ID 5\n"
        text += "• `/models` - обновить список"

        await update.message.reply_text(text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка в show_models: {e}")
        await update.message.reply_text("❌ Произошла ошибка при получении списка моделей")


async def set_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор активной модели"""
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите ID модели.\n"
            "*Пример:* `/setmodel 1`\n"
            "*Просмотреть список:* /models",
            parse_mode='Markdown'
        )
        return

    try:
        model_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ ID модели должен быть числом.\n"
            "*Пример:* `/setmodel 3`"
        )
        return

    try:
        models = db.get_all_models()
        model_ids = [model['id'] for model in models]

        if model_id not in model_ids:
            await update.message.reply_text(
                f"❌ Модель с ID `{model_id}` не найдена\n\n"
                f"*Доступные ID:* {', '.join(map(str, model_ids))}\n"
                f"*Просмотреть все:* /models",
                parse_mode='Markdown'
            )
            return

        success = db.set_active_model(model_id)

        if success:
            active_model = db.get_active_model()
            free_status = "🆓 БЕСПЛАТНАЯ" if active_model['is_free'] == 1 else "💳 ПЛАТНАЯ"
            await update.message.reply_text(
                f"✅ *Модель успешно изменена!*\n\n"
                f"*Название:* {active_model['name']}\n"
                f"*Статус:* {free_status}\n"
                f"*Описание:* {active_model['description']}\n"
                f"*Макс. токенов:* {active_model['max_tokens']}\n\n"
                f"*Теперь можете задать вопрос:*\n"
                f"`/ask Ваш вопрос здесь`",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Ошибка при изменении модели")

    except Exception as e:
        logger.error(f"Ошибка в set_model: {e}")
        await update.message.reply_text("❌ Произошла ошибка при изменении модели")


async def ask_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задать вопрос активной модели"""
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите ваш вопрос.\n"
            "*Пример:* `/ask Как работает искусственный интеллект?`\n"
            "*Текущая модель:* /current",
            parse_mode='Markdown'
        )
        return

    question = " ".join(context.args)

    # Проверка длины вопроса
    if len(question) > MAX_QUESTION_LENGTH:
        await update.message.reply_text(
            f"❌ Вопрос слишком длинный. Максимум {MAX_QUESTION_LENGTH} символов.\n"
            f"Сейчас: {len(question)} символов."
        )
        return

    try:
        active_model = db.get_active_model()

        if not active_model:
            await update.message.reply_text(
                "❌ Активная модель не выбрана.\n"
                "Используйте команду `/setmodel <ID>`\n"
                "Просмотреть список моделей: /models",
                parse_mode='Markdown'
            )
            return

        await update.message.reply_chat_action("typing")

        user_id = update.effective_user.id
        character_prompt = db.get_character_prompt(user_id)

        messages = [
            {"role": "system", "content": character_prompt},
            {"role": "user", "content": question}
        ]

        # Отправляем запрос к OpenRouter
        response = openrouter_client.generate_response(
            model=active_model['name'],
            messages=messages,
            max_tokens=active_model.get('max_tokens', 400)
        )

        if "error" in response:
            await update.message.reply_text(
                f"❌ *Ошибка запроса:*\n{response['error']}\n\n"
                f"*Попробуйте:*\n"
                f"• Другую модель: /setmodel\n"
                f"• Повторить позже",
                parse_mode='Markdown'
            )
        else:
            answer = response['text']
            latency = response.get('latency_ms', 0)

            # Обрезаем ответ если слишком длинный для Telegram
            if len(answer) > MAX_RESPONSE_LENGTH:
                answer = answer[:MAX_RESPONSE_LENGTH] + "\n\n... (сообщение обрезано)"

            free_status = "🆓" if active_model['is_free'] == 1 else "💳"
            reply_text = (
                f"{free_status} *{active_model['name']}*\n"
                f"⏱ *Время ответа:* {latency}мс\n\n"
                f"{answer}\n\n"
                f"---\n"
                f"*Используйте:*\n"
                f"• `/ask` - еще вопрос\n"
                f"• `/current` - текущие настройки"
            )

            await update.message.reply_text(reply_text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка в ask_model: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке запроса")


async def ask_model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задать вопрос конкретной модели по ID"""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Укажите ID модели и вопрос.\n"
            "*Пример:* `/ask_model 5 Как работает ИИ?`\n\n"
            "*Список моделей:* /models",
            parse_mode='Markdown'
        )
        return

    try:
        model_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ ID модели должен быть числом.\n"
            "*Пример:* `/ask_model 7 Привет!`"
        )
        return

    # Вопрос - все аргументы после ID
    question = " ".join(context.args[1:])

    # Проверка длины вопроса
    if len(question) > MAX_QUESTION_LENGTH:
        await update.message.reply_text(
            f"❌ Вопрос слишком длинный. Максимум {MAX_QUESTION_LENGTH} символов.\n"
            f"Сейчас: {len(question)} символов."
        )
        return

    try:
        # Получаем модель по ID
        model = db.get_model_by_id(model_id)

        if not model:
            models = db.get_all_models()
            model_ids = [m['id'] for m in models]
            await update.message.reply_text(
                f"❌ Модель с ID `{model_id}` не найдена\n\n"
                f"*Доступные ID:* {', '.join(map(str, model_ids))}\n"
                f"*Просмотреть все:* /models",
                parse_mode='Markdown'
            )
            return

        await update.message.reply_chat_action("typing")

        user_id = update.effective_user.id
        character_prompt = db.get_character_prompt(user_id)

        messages = [
            {"role": "system", "content": character_prompt},
            {"role": "user", "content": question}
        ]

        # Отправляем запрос к OpenRouter
        response = openrouter_client.generate_response(
            model=model['name'],
            messages=messages,
            max_tokens=model.get('max_tokens', 400)
        )

        if "error" in response:
            await update.message.reply_text(
                f"❌ *Ошибка при запросе к модели {model['name']}:*\n"
                f"{response['error']}\n\n"
                f"*Попробуйте:*\n"
                f"• Другую модель\n"
                f"• Повторить позже",
                parse_mode='Markdown'
            )
        else:
            answer = response['text']
            latency = response.get('latency_ms', 0)

            # Обрезаем ответ если слишком длинный для Telegram
            if len(answer) > MAX_RESPONSE_LENGTH:
                answer = answer[:MAX_RESPONSE_LENGTH] + "\n\n... (сообщение обрезано)"

            free_status = "🆓" if model['is_free'] == 1 else "💳"
            reply_text = (
                f"{free_status} *{model['name']} (ID: {model_id})*\n"
                f"⏱ *Время ответа:* {latency}мс\n\n"
                f"{answer}\n\n"
                f"---\n"
                f"*Примечание:* Активная модель не изменена.\n"
                f"*Использовать как активную:* `/setmodel {model_id}`"
            )

            await update.message.reply_text(reply_text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка в ask_model_command: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке запроса")


async def show_characters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список всех персонажей"""
    try:
        characters = db.get_all_characters()

        if not characters:
            await update.message.reply_text("❌ Персонажи не найдены в базе данных")
            return

        user_id = update.effective_user.id
        user_character = db.get_user_character(user_id)
        active_character_name = user_character['name'] if user_character else "Не выбран"

        text = f"🎭 *Список доступных персонажей*\n\n"
        text += f"*Текущий активный персонаж:* {active_character_name}\n\n"

        for character in characters:
            status = "✅ ВАШ" if user_character and user_character['id'] == character['id'] else "⚪"
            prompt_preview = character['prompt'][:80] + "..." if len(character['prompt']) > 80 else character['prompt']
            text += f"{status} *{character['name']}*\n"
            text += f"   ├ ID для выбора: `{character['id']}`\n"
            text += f"   └ Промпт: {prompt_preview}\n\n"

        text += "\n*💡 Использование:*\n"
        text += "• `/setcharacter 1` - выбрать персонажа с ID 1\n"
        text += "• `/characters` - обновить список\n"
        text += "• `/current` - текущий персонаж"

        await update.message.reply_text(text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка в show_characters: {e}")
        await update.message.reply_text("❌ Произошла ошибка при получении списка персонажей")


async def set_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор персонажа для пользователя"""
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите ID персонажа.\n"
            "*Пример:* `/setcharacter 1`\n"
            "*Список персонажей:* /characters",
            parse_mode='Markdown'
        )
        return

    try:
        character_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ ID персонажа должен быть числом.\n"
            "*Пример:* `/setcharacter 2`"
        )
        return

    try:
        characters = db.get_all_characters()
        character_ids = [character['id'] for character in characters]

        if character_id not in character_ids:
            await update.message.reply_text(
                f"❌ Персонаж с ID `{character_id}` не найден\n\n"
                f"*Доступные ID:* {', '.join(map(str, character_ids))}\n"
                f"*Просмотреть все:* /characters",
                parse_mode='Markdown'
            )
            return

        user_id = update.effective_user.id
        success = db.set_user_character(user_id, character_id)

        if success:
            character = db.get_character_by_id(character_id)
            prompt_preview = character['prompt'][:150] + "..." if len(character['prompt']) > 150 else character[
                'prompt']
            await update.message.reply_text(
                f"✅ *Персонаж успешно изменен!*\n\n"
                f"*Имя:* {character['name']}\n"
                f"*ID:* {character['id']}\n"
                f"*Промпт:* {prompt_preview}\n\n"
                f"*Теперь все ваши запросы будут в стиле этого персонажа.*",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Ошибка при изменении персонажа")

    except Exception as e:
        logger.error(f"Ошибка в set_character: {e}")
        await update.message.reply_text("❌ Произошла ошибка при изменении персонажа")


async def current_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать текущую активную модель и персонаж"""
    try:
        active_model = db.get_active_model()
        user_id = update.effective_user.id
        user_character = db.get_user_character(user_id)

        if not active_model:
            await update.message.reply_text(
                "❌ Активная модель не выбрана.\n"
                "Используйте команду `/setmodel <ID>`\n"
                "Просмотреть список моделей: /models",
                parse_mode='Markdown'
            )
            return

        character_name = user_character['name'] if user_character else "Не выбран"
        character_prompt = user_character['prompt'][:200] + "..." if user_character else "Стандартный AI-ассистент"

        free_status = "🆓 БЕСПЛАТНАЯ" if active_model['is_free'] == 1 else "💳 ПЛАТНАЯ"
        tokens = f"{active_model['max_tokens']:,}".replace(",", " ")

        text = (
            f"📊 *Текущие настройки*\n\n"
            f"*🤖 Модель:*\n"
            f"• *Название:* {active_model['name']}\n"
            f"• *Статус:* {free_status}\n"
            f"• *Провайдер:* {active_model['provider']}\n"
            f"• *Описание:* {active_model['description']}\n"
            f"• *Макс. токенов:* {tokens}\n"
            f"• *ID модели:* `{active_model['id']}`\n\n"
            f"*🎭 Персонаж:*\n"
            f"• *Имя:* {character_name}\n"
            f"• *Промпт:* {character_prompt}\n\n"
            f"*🔧 Команды управления:*\n"
            f"• `/setmodel` - изменить модель\n"
            f"• `/setcharacter` - изменить персонажа\n"
            f"• `/models` - список моделей\n"
            f"• `/characters` - список персонажей\n"
            f"• `/ask` - задать вопрос\n"
            f"• `/ask_random` - случайный персонаж"
        )

        await update.message.reply_text(text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка в current_model: {e}")
        await update.message.reply_text("❌ Произошла ошибка при получении настроек")


async def ask_random_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задать вопрос случайному персонажу"""
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите ваш вопрос.\n"
            "*Пример:* `/ask_random Как дела?`",
            parse_mode='Markdown'
        )
        return

    question = " ".join(context.args)

    # Проверка длины вопроса
    if len(question) > MAX_QUESTION_LENGTH:
        await update.message.reply_text(
            f"❌ Вопрос слишком длинный. Максимум {MAX_QUESTION_LENGTH} символов.\n"
            f"Сейчас: {len(question)} символов."
        )
        return

    try:
        active_model = db.get_active_model()

        if not active_model:
            await update.message.reply_text(
                "❌ Активная модель не выбрана.\n"
                "Используйте команду `/setmodel <ID>`",
                parse_mode='Markdown'
            )
            return

        # Получаем случайного персонажа
        characters = db.get_all_characters()
        if not characters:
            await update.message.reply_text("❌ Персонажи не найдены")
            return

        random_character = random.choice(characters)

        await update.message.reply_chat_action("typing")

        # Формируем сообщения для модели
        messages = [
            {"role": "system", "content": random_character['prompt']},
            {"role": "user", "content": question}
        ]

        # Отправляем запрос к OpenRouter
        response = openrouter_client.generate_response(
            model=active_model['name'],
            messages=messages,
            max_tokens=active_model.get('max_tokens', 400)
        )

        if "error" in response:
            await update.message.reply_text(
                f"❌ *Ошибка:* {response['error']}\n\n"
                f"*Попробуйте:*\n"
                f"• Позже\n"
                f"• Другую модель: /setmodel",
                parse_mode='Markdown'
            )
        else:
            answer = response['text']
            latency = response.get('latency_ms', 0)

            # Обрезаем ответ если слишком длинный для Telegram
            if len(answer) > MAX_RESPONSE_LENGTH:
                answer = answer[:MAX_RESPONSE_LENGTH] + "\n\n... (сообщение обрезано)"

            reply_text = (
                f"🎭 *Случайный персонаж:* {random_character['name']}\n"
                f"🤖 *Модель:* {active_model['name']}\n"
                f"⏱ *Время ответа:* {latency}мс\n\n"
                f"{answer}\n\n"
                f"---\n"
                f"*Хотите использовать этого персонажа?*\n"
                f"`/setcharacter {random_character['id']}`"
            )

            await update.message.reply_text(reply_text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка в ask_random_character: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке запроса")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать справку"""
    help_text = (
        "📖 *Справка по командам*\n\n"
        "*Основные команды:*\n"
        "`/start` - Запустить бота\n"
        "`/help` - Показать эту справку\n"
        "`/current` - Текущие настройки\n\n"

        "*Управление моделями:*\n"
        "`/models` - Список всех моделей\n"
        "`/setmodel <ID>` - Выбрать активную модель\n"
        "`/ask <вопрос>` - Задать вопрос активной модели\n"
        "`/ask_model <ID> <вопрос>` - Задать вопрос конкретной модели\n\n"

        "*Управление персонажами:*\n"
        "`/characters` - Список всех персонажей\n"
        "`/setcharacter <ID>` - Выбрать персонажа\n"
        "`/ask_random <вопрос>` - Задать вопрос случайному персонажу\n\n"

        "*Примеры использования:*\n"
        "• `/setmodel 3` - выбрать модель с ID 3\n"
        "• `/ask Что такое ИИ?` - задать вопрос\n"
        "• `/ask_model 7 Погода в Москве` - вопрос к модели ID=7\n"
        "• `/setcharacter 2` - выбрать персонажа с ID 2\n\n"

        "*💡 Важно:*\n"
        "• Бесплатные модели (🆓) имеют ограничения\n"
        "• Макс. длина вопроса: 2000 символов\n"
        "• Токены - единицы измерения текста\n\n"

        "*❓ Проблемы?*\n"
        "• Проверьте активную модель: /current\n"
        "• Обновите список: /models\n"
        "• Попробуйте другую модель"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}", exc_info=True)

    if update and update.message:
        try:
            await update.message.reply_text(
                "❌ Произошла непредвиденная ошибка.\n\n"
                "*Что можно сделать:*\n"
                "• Проверить активную модель: /current\n"
                "• Попробовать другую модель: /setmodel\n"
                "• Повторить запрос позже",
                parse_mode='Markdown'
            )
        except:
            pass


async def post_init(application: Application):
    commands = [BotCommand(cmd[0], cmd[1]) for cmd in COMMANDS]
    await application.bot.set_my_commands(commands)
    logger.info("Команды меню установлены")


def main():
    """Основная функция запуска бота"""
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    if not TELEGRAM_TOKEN:
        print("❌ Ошибка: TELEGRAM_BOT_TOKEN не найден")
        print("Создайте файл .env с содержимым:")
        print("TELEGRAM_BOT_TOKEN=ваш_токен_бота")
        print("OPENROUTER_API_KEY=ваш_ключ_openrouter")
        return

    # Создаем приложение
    try:
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
        application.add_handler(CommandHandler("ask_model", ask_model_command))
        application.add_handler(CommandHandler("characters", show_characters))
        application.add_handler(CommandHandler("setcharacter", set_character))
        application.add_handler(CommandHandler("current", current_model))
        application.add_handler(CommandHandler("ask_random", ask_random_character))

        # Обработчик ошибок
        application.add_error_handler(error_handler)


        print("🤖 Бот запускается...")
        print("📊 Команды:", [cmd[0] for cmd in COMMANDS])
        print("✅ Бот готов к работе!")

        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        print(f"❌ Ошибка запуска: {e}")


if __name__ == "__main__":
    main()