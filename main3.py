import telebot
from telebot import types
import logging
import os
from dotenv import load_dotenv
import db

load_dotenv()

TOKEN = os.getenv("TOKEN")
DB_PATH = os.getenv("DB_PATH", "bot.db")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TOKEN)


def setup_bot_commands():
    """Настройка меню команд бота"""
    commands = [
        types.BotCommand("start", "Запустить бота"),
        types.BotCommand("note_add", "Добавить заметку"),
        types.BotCommand("note_list", "Список заметок"),
        types.BotCommand("note_find", "Поиск заметок"),
        types.BotCommand("note_edit", "Редактировать заметку"),
        types.BotCommand("note_del", "Удалить заметку"),
        types.BotCommand("note_count", "Статистика заметок"),
        types.BotCommand("note_export", "Экспорт заметок"),
    ]
    bot.set_my_commands(commands)

#yyyyy
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Приветственное сообщение"""
    welcome_text = """
🤖 **Бот для заметок с базой данных**
     

Доступные команды:
/note_add - Добавить заметку
/note_list - Показать последние заметки  
/note_find - Найти заметки
/note_edit - Редактировать заметку
/note_del - Удалить заметку
/note_count - Статистика
/note_export - Экспорт всех заметок

Просто используйте команды из меню!
    """
    bot.reply_to(message, welcome_text, parse_mode='Markdown')


@bot.message_handler(commands=['note_add'])
def add_note_handler(message):
    """Добавление новой заметки"""
    try:
        text = message.text.replace('/note_add', '').strip()
        if not text:
            bot.reply_to(message, "❌ Использование: /note_add <текст заметки>")
            return

        if len(text) > 200:
            bot.reply_to(message, "❌ Заметка слишком длинная (макс. 200 символов)")
            return

        note_id = db.add_note(message.from_user.id, text)
        bot.reply_to(message, f"✅ Заметка #{note_id} добавлена!")

    except Exception as e:
        error_msg = "❌ Ошибка при добавлении заметки"
        if "UNIQUE" in str(e):
            error_msg = "❌ Такая заметка уже существует"
        bot.reply_to(message, error_msg)
        logger.error(f"Error adding note: {e}")


@bot.message_handler(commands=['note_list'])
def list_notes_handler(message):
    """Показать список заметок"""
    try:
        notes = db.list_notes(message.from_user.id, limit=10)
        if not notes:
            bot.reply_to(message, "📝 У вас пока нет заметок")
            return

        response = "📋 **Ваши последние заметки:**\n\n"
        for note in notes:
            response += f"#{note['id']} - {note['text']}\n"
            response += f"<i>{note['created_at']}</i>\n\n"

        bot.reply_to(message, response, parse_mode='HTML')

    except Exception as e:
        bot.reply_to(message, "❌ Ошибка при получении заметок")
        logger.error(f"Error listing notes: {e}")


@bot.message_handler(commands=['note_find'])
def find_notes_handler(message):
    """Поиск заметок"""
    try:
        query = message.text.replace('/note_find', '').strip()
        if not query:
            bot.reply_to(message, "❌ Использование: /note_find <запрос>")
            return

        notes = db.find_notes(message.from_user.id, query)
        if not notes:
            bot.reply_to(message, f"🔍 По запросу '{query}' ничего не найдено")
            return

        response = f"🔍 **Результаты поиска '{query}':**\n\n"
        for note in notes:
            response += f"#{note['id']} - {note['text']}\n\n"

        bot.reply_to(message, response, parse_mode='HTML')

    except Exception as e:
        bot.reply_to(message, "❌ Ошибка при поиске заметок")
        logger.error(f"Error finding notes: {e}")


@bot.message_handler(commands=['note_edit'])
def edit_note_handler(message):
    """Редактирование заметки"""
    try:
        parts = message.text.split(' ', 2)
        if len(parts) < 3:
            bot.reply_to(message, "❌ Использование: /note_edit <id> <новый текст>")
            return

        note_id = parts[1]
        new_text = parts[2]

        if not note_id.isdigit():
            bot.reply_to(message, "❌ ID заметки должен быть числом")
            return

        if len(new_text) > 200:
            bot.reply_to(message, "❌ Заметка слишком длинная (макс. 200 символов)")
            return

        success = db.update_note(message.from_user.id, int(note_id), new_text)
        if success:
            bot.reply_to(message, f"✅ Заметка #{note_id} обновлена!")
        else:
            bot.reply_to(message, f"❌ Заметка #{note_id} не найдена")

    except Exception as e:
        bot.reply_to(message, "❌ Ошибка при редактировании заметки")
        logger.error(f"Error editing note: {e}")


@bot.message_handler(commands=['note_del'])
def delete_note_handler(message):
    """Удаление заметки"""
    try:
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            bot.reply_to(message, "❌ Использование: /note_del <id>")
            return

        note_id = parts[1]
        if not note_id.isdigit():
            bot.reply_to(message, "❌ ID заметки должен быть числом")
            return

        success = db.delete_note(message.from_user.id, int(note_id))
        if success:
            bot.reply_to(message, f"✅ Заметка #{note_id} удалена!")
        else:
            bot.reply_to(message, f"❌ Заметка #{note_id} не найдена")

    except Exception as e:
        bot.reply_to(message, "❌ Ошибка при удалении заметки")
        logger.error(f"Error deleting note: {e}")


@bot.message_handler(commands=['note_count'])
def count_notes_handler(message):
    """Статистика заметок"""
    try:
        count = db.count_notes(message.from_user.id)
        stats = db.get_notes_statistics(message.from_user.id, days=7)

        response = f"📊 **Статистика заметок:**\n\n"
        response += f"Всего заметок: **{count}**\n\n"

        if stats:
            response += "Активность за неделю:\n"
            for stat in stats:
                response += f"{stat['date']}: {stat['count']} заметок\n"
        else:
            response += "За последнюю неделю заметок нет\n"

        bot.reply_to(message, response, parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, "❌ Ошибка при получении статистики")
        logger.error(f"Error counting notes: {e}")


@bot.message_handler(commands=['note_export'])
def export_notes_handler(message):
    """Экспорт заметок в файл"""
    try:
        notes = db.export_notes(message.from_user.id)
        if not notes:
            bot.reply_to(message, "📝 У вас пока нет заметок для экспорта")
            return

        # Создание текстового файла
        filename = f"notes_{message.from_user.id}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Экспорт заметок пользователя {message.from_user.first_name}\n")
            f.write(f"Всего заметок: {len(notes)}\n")
            f.write("=" * 50 + "\n\n")

            for note in notes:
                f.write(f"#{note['id']} - {note['text']}\n")
                f.write(f"Создано: {note['created_at']}\n")
                f.write("-" * 30 + "\n")

        # Отправка файла
        with open(filename, 'rb') as f:
            bot.send_document(message.chat.id, f, caption="📁 Ваши заметки")

        logger.info(f"Notes exported for user {message.from_user.id}")

    except Exception as e:
        bot.reply_to(message, "❌ Ошибка при экспорте заметок")
        logger.error(f"Error exporting notes: {e}")


@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    """Обработка прочих сообщений"""
    bot.reply_to(message, "🤖 Используйте команды из меню для работы с заметками")


if __name__ == "__main__":
    # Инициализация базы данных
    db.init_db()
    setup_bot_commands()

    logger.info("Bot started successfully")
    print("Бот запущен...")

    bot.infinity_polling(skip_pending=True)