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