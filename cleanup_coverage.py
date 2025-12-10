#!/usr/bin/env python3
"""
Скрипт для очистки файлов coverage перед запуском тестов.
"""

import os
import shutil
import sys


def cleanup_coverage():
    """Удаляет файлы .coverage и каталог htmlcov"""

    files_to_remove = ['.coverage', '.coverage.*']
    dirs_to_remove = ['htmlcov']

    removed_count = 0

    # Удаляем файлы
    for file_pattern in files_to_remove:
        if file_pattern.endswith('.*'):
            # Ищем файлы по шаблону
            import glob
            for file_path in glob.glob(file_pattern):
                try:
                    os.remove(file_path)
                    print(f"✓ Удален файл: {file_path}")
                    removed_count += 1
                except OSError as e:
                    print(f"✗ Ошибка удаления файла {file_path}: {e}")
        else:
            # Обычный файл
            if os.path.exists(file_pattern):
                try:
                    os.remove(file_pattern)
                    print(f"✓ Удален файл: {file_pattern}")
                    removed_count += 1
                except OSError as e:
                    print(f"✗ Ошибка удаления файла {file_pattern}: {e}")

    # Удаляем каталоги
    for dir_path in dirs_to_remove:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            try:
                shutil.rmtree(dir_path)
                print(f"✓ Удален каталог: {dir_path}")
                removed_count += 1
            except OSError as e:
                print(f"✗ Ошибка удаления каталога {dir_path}: {e}")

    if removed_count == 0:
        print("ℹ Нечего удалять, все чисто!")

    return 0


if __name__ == "__main__":
    sys.exit(cleanup_coverage())