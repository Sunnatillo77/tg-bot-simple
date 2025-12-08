import sqlite3
from typing import List, Optional


class Database:
    def __init__(self, db_path: str = "bot.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Создаем таблицу моделей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    provider TEXT NOT NULL,
                    active INTEGER DEFAULT 0 CHECK (active IN (0,1)),
                    description TEXT,
                    max_tokens INTEGER DEFAULT 4096,
                    is_free INTEGER DEFAULT 0
                )
            ''')

            # Создаем уникальный индекс для активной модели
            cursor.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_active_model 
                ON models(active) WHERE active = 1
            ''')

            # Создаем таблицу персонажей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS characters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    prompt TEXT NOT NULL
                )
            ''')

            # Создаем таблицу связей пользователей и персонажей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_characters (
                    user_id INTEGER NOT NULL,
                    character_id INTEGER NOT NULL,
                    active INTEGER DEFAULT 1 CHECK (active IN (0,1)),
                    PRIMARY KEY (user_id, character_id),
                    FOREIGN KEY (character_id) REFERENCES characters(id)
                )
            ''')

            # Создаем уникальный индекс для активного персонажа пользователя
            cursor.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_user_active_character 
                ON user_characters(user_id, active) WHERE active = 1
            ''')

            # Добавляем 10 моделей (если их еще нет)
            models = [
                # Бесплатные модели
                ("openrouter/cinematika-7b", "OpenRouter", "Бесплатная модель для творчества", 8192, 1),
                ("google/gemma-2b-it", "Google", "Легкая модель от Google", 8192, 1),
                ("microsoft/phi-2", "Microsoft", "Компактная модель от Microsoft", 2048, 1),
                ("huggingfaceh4/zephyr-7b-beta", "Hugging Face", "Быстрая и эффективная модель", 8192, 1),

                # Платные (но недорогие) модели
                ("openai/gpt-3.5-turbo", "OpenAI", "GPT-3.5 Turbo - баланс качества и скорости", 4096, 0),
                ("anthropic/claude-3-haiku", "Anthropic", "Claude 3 Haiku - быстрая и умная", 200000, 0),
                ("meta-llama/llama-3.1-8b-instruct", "Meta", "Llama 3.1 8B - открытая модель", 8192, 0),
                ("google/gemini-pro-1.5", "Google", "Gemini Pro 1.5 - мощная модель", 1000000, 0),
                ("mistralai/mistral-7b-instruct", "Mistral AI", "Mistral 7B - французская модель", 32768, 0),
                ("cohere/command-r-plus", "Cohere", "Command R+ - для бизнес-задач", 128000, 0)
            ]

            # Проверяем, есть ли уже модели
            cursor.execute("SELECT COUNT(*) FROM models")
            count = cursor.fetchone()[0]

            if count == 0:
                # Добавляем модели, первую делаем активной
                for i, (name, provider, description, max_tokens, is_free) in enumerate(models):
                    active = 1 if i == 0 else 0  # Первую модель делаем активной
                    cursor.execute('''
                        INSERT INTO models (name, provider, active, description, max_tokens, is_free)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (name, provider, active, description, max_tokens, is_free))

            # Добавляем персонажей (если их еще нет)
            cursor.execute("SELECT COUNT(*) FROM characters")
            count = cursor.fetchone()[0]

            if count == 0:
                characters = [
                    ("Ассистент", "Ты полезный AI-ассистент. Отвечай кратко и по делу."),
                    ("Программист",
                     "Ты опытный программист. Отвечай на технические вопросы подробно и с примерами кода."),
                    ("Учитель", "Ты терпеливый учитель. Объясняй сложные понятия простыми словами."),
                    ("Поэт", "Ты творческий поэт. Отвечай в стихотворной форме."),
                    ("Историк", "Ты знающий историк. Отвечай с историческими фактами и контекстом.")
                ]

                for name, prompt in characters:
                    cursor.execute('''
                        INSERT INTO characters (name, prompt)
                        VALUES (?, ?)
                    ''', (name, prompt))

            conn.commit()

    def get_all_models(self) -> List[dict]:
        """Получение списка всех моделей"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM models ORDER BY active DESC, is_free DESC, name")
            return [dict(row) for row in cursor.fetchall()]

    def get_active_model(self) -> Optional[dict]:
        """Получение активной модели"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM models WHERE active = 1 LIMIT 1")
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_model_by_id(self, model_id: int) -> Optional[dict]:
        """Получение модели по ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM models WHERE id = ?", (model_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def set_active_model(self, model_id: int) -> bool:
        """Установка активной модели"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Блокируем запись и обновляем активность
            cursor.execute("BEGIN IMMEDIATE")

            # Сбрасываем активность у всех моделей
            cursor.execute("UPDATE models SET active = 0")

            # Устанавливаем активность выбранной модели
            cursor.execute("UPDATE models SET active = 1 WHERE id = ?", (model_id,))

            conn.commit()

            # Проверяем, обновлена ли модель
            cursor.execute("SELECT COUNT(*) FROM models WHERE id = ? AND active = 1", (model_id,))
            return cursor.fetchone()[0] > 0

    def get_all_characters(self) -> List[dict]:
        """Получение списка всех персонажей"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM characters ORDER BY id")
            return [dict(row) for row in cursor.fetchall()]

    def get_character_by_id(self, character_id: int) -> Optional[dict]:
        """Получение персонажа по ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def set_user_character(self, user_id: int, character_id: int) -> bool:
        """Установка персонажа для пользователя (upsert)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Используем UPSERT (INSERT OR REPLACE)
            cursor.execute('''
                INSERT INTO user_characters (user_id, character_id, active)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id, character_id) 
                DO UPDATE SET active = 1
            ''', (user_id, character_id))

            # Деактивируем другие персонажи пользователя
            cursor.execute('''
                UPDATE user_characters 
                SET active = 0 
                WHERE user_id = ? AND character_id != ?
            ''', (user_id, character_id))

            conn.commit()
            return True

    def get_user_character(self, user_id: int) -> Optional[dict]:
        """Получение активного персонажа пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.* FROM characters c
                JOIN user_characters uc ON c.id = uc.character_id
                WHERE uc.user_id = ? AND uc.active = 1
                LIMIT 1
            ''', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_character_prompt(self, user_id: int) -> str:
        """Получение промпта персонажа пользователя"""
        character = self.get_user_character(user_id)
        if character:
            return character['prompt']
        return "Ты полезный AI-ассистент. Отвечай кратко и по делу."