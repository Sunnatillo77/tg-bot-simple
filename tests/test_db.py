"""
Тесты для модуля db.py
"""

import pytest
import sqlite3
from db import Database


def test_get_all_models(db_module):
    models = db_module.get_all_models()
    assert len(models) > 0
    assert isinstance(models, list)

    for model in models:
        assert 'id' in model
        assert 'name' in model
        assert 'provider' in model
        assert 'active' in model
        assert 'description' in model
        assert 'max_tokens' in model
        assert 'is_free' in model


def test_get_active_model(db_module):
    active_model = db_module.get_active_model()
    assert active_model is not None
    assert active_model['active'] == 1

    with sqlite3.connect(db_module.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM models WHERE active = 1")
        count = cursor.fetchone()[0]
        assert count == 1


def test_set_active_model(db_module):
    models = db_module.get_all_models()
    inactive_models = [m for m in models if m['active'] == 0]
    assert len(inactive_models) > 0

    target_model = inactive_models[0]
    success = db_module.set_active_model(target_model['id'])
    assert success is True

    new_active = db_module.get_active_model()
    assert new_active['id'] == target_model['id']

    with sqlite3.connect(db_module.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM models WHERE active = 1")
        count = cursor.fetchone()[0]
        assert count == 1


def test_set_active_model_invalid_id(db_module):
    """Тест установки несуществующей модели"""
    with pytest.raises(Exception):
        db_module.set_active_model(99999)


def test_get_all_characters(db_module):
    characters = db_module.get_all_characters()
    assert len(characters) > 0
    assert isinstance(characters, list)

    for character in characters:
        assert 'id' in character
        assert 'name' in character
        assert 'prompt' in character


def test_set_user_character(db_module):
    characters = db_module.get_all_characters()
    assert len(characters) >= 2

    user_id = 1001

    success1 = db_module.set_user_character(user_id, characters[0]['id'])
    assert success1 is True

    user_character = db_module.get_user_character(user_id)
    assert user_character is not None
    assert user_character['id'] == characters[0]['id']

    success2 = db_module.set_user_character(user_id, characters[1]['id'])
    assert success2 is True

    user_character = db_module.get_user_character(user_id)
    assert user_character['id'] == characters[1]['id']

    with sqlite3.connect(db_module.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM user_characters WHERE user_id = ? AND active = 1",
            (user_id,)
        )
        count = cursor.fetchone()[0]
        assert count == 1


def test_get_character_prompt_default(db_module):
    user_id = 99999
    prompt = db_module.get_character_prompt(user_id)

    assert prompt is not None
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "AI-ассистент" in prompt or "помощный" in prompt


def test_get_character_prompt_with_character(db_module):
    user_id = 1002
    characters = db_module.get_all_characters()
    assert len(characters) > 0

    db_module.set_user_character(user_id, characters[0]['id'])
    prompt = db_module.get_character_prompt(user_id)
    assert prompt == characters[0]['prompt']


def test_get_model_by_id(db_module):
    models = db_module.get_all_models()
    assert len(models) > 0

    test_model = models[0]
    model_by_id = db_module.get_model_by_id(test_model['id'])
    assert model_by_id is not None
    assert model_by_id['id'] == test_model['id']
    assert model_by_id['name'] == test_model['name']


def test_get_character_by_id(db_module):
    characters = db_module.get_all_characters()
    assert len(characters) > 0

    test_character = characters[0]
    character_by_id = db_module.get_character_by_id(test_character['id'])
    assert character_by_id is not None
    assert character_by_id['id'] == test_character['id']
    assert character_by_id['name'] == test_character['name']


def test_get_user_character_default(db_module):
    """Тест получения персонажа по умолчанию, когда у пользователя нет выбора"""
    user_id = 999999  # Несуществующий пользователь
    character = db_module.get_user_character(user_id)

    # Должен вернуться None или базовый персонаж
    if character is None:
        # Проверяем, что get_character_prompt возвращает дефолтный промпт
        prompt = db_module.get_character_prompt(user_id)
        assert "AI-ассистент" in prompt
    else:
        # Или возвращается какой-то существующий персонаж
        assert 'id' in character
        assert 'name' in character
        assert 'prompt' in character