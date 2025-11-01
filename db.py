import sqlite3
import logging
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "bot.db")
logger = logging.getLogger(__name__)

def _connect():
    """Создание подключения к базе данных с оптимизацией"""
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn

def init_db():
    """Инициализация базы данных"""
    schema = """
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        text TEXT NOT NULL CHECK(length(text) BETWEEN 1 AND 200),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, text) ON CONFLICT IGNORE
    )
    """
    try:
        with _connect() as conn:
            conn.executescript(schema)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

def add_note(user_id: int, text: str) -> int:
    """Добавление новой заметки"""
    try:
        with _connect() as conn:
            cur = conn.execute(
                "INSERT INTO notes (user_id, text) VALUES (?, ?)",
                (user_id, text)
            )
            conn.commit()
            logger.info(f"Note added for user {user_id}: {text[:20]}...")
            return cur.lastrowid
    except sqlite3.IntegrityError as e:
        logger.warning(f"Duplicate note attempt by user {user_id}: {text[:20]}...")
        raise e

def list_notes(user_id: int, limit: int = 10):
    """Получение списка заметок пользователя"""
    with _connect() as conn:
        cur = conn.execute(
            """SELECT id, text, created_at 
            FROM notes 
            WHERE user_id = ? 
            ORDER BY id DESC 
            LIMIT ?""",
            (user_id, limit)
        )
        return cur.fetchall()

def find_notes(user_id: int, query: str, limit: int = 10):
    """Поиск заметок по тексту"""
    with _connect() as conn:
        cur = conn.execute(
            """SELECT id, text 
            FROM notes 
            WHERE user_id = ? 
            AND text LIKE '%' || ? || '%' 
            ORDER BY id DESC 
            LIMIT ?""",
            (user_id, query, limit)
        )
        return cur.fetchall()

def update_note(user_id: int, note_id: int, text: str) -> bool:
    """Обновление заметки"""
    with _connect() as conn:
        cur = conn.execute(
            """UPDATE notes 
            SET text = ? 
            WHERE user_id = ? AND id = ?""",
            (text, user_id, note_id)
        )
        conn.commit()
        logger.info(f"Note {note_id} updated by user {user_id}")
        return cur.rowcount > 0

def delete_note(user_id: int, note_id: int) -> bool:
    """Удаление заметки"""
    with _connect() as conn:
        cur = conn.execute(
            "DELETE FROM notes WHERE user_id = ? AND id = ?",
            (user_id, note_id)
        )
        conn.commit()
        logger.info(f"Note {note_id} deleted by user {user_id}")
        return cur.rowcount > 0

def count_notes(user_id: int) -> int:
    """Подсчет количества заметок пользователя"""
    with _connect() as conn:
        cur = conn.execute(
            "SELECT COUNT(*) as count FROM notes WHERE user_id = ?",
            (user_id,)
        )
        result = cur.fetchone()
        return result['count'] if result else 0

def get_notes_statistics(user_id: int, days: int = 7):
    """Статистика заметок за последние дни"""
    with _connect() as conn:
        cur = conn.execute(
            """SELECT date(created_at) AS date, COUNT(*) AS count
            FROM notes 
            WHERE user_id = ? 
            AND date(created_at) >= date('now', '-' || ? || ' days')
            GROUP BY date(created_at) 
            ORDER BY date DESC""",
            (user_id, days)
        )
        return cur.fetchall()

def export_notes(user_id: int):
    """Экспорт всех заметок пользователя"""
    notes = list_notes(user_id, limit=1000)
    return notes