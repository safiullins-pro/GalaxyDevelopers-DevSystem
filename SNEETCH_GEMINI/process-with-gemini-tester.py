#!/usr/bin/env python3
import os
import json
import sys
from pathlib import Path
import hashlib
from datetime import datetime

# Пути
SOURCE_DIR = "/Users/safiullins_pro/В ПЕРПЛЕКСИТИ"
OUTPUT_DIR = "/Volumes/Z7S/development/GalaxyDevelopments/GEMINI_ANALYSIS_RESULTS"
PROMPT_FILE = "/Users/safiullins_pro/Scripts/gemini-triggers/gemini-analysis-prompt.txt"
CHUNK_SIZE = 30000

def read_all_files():
    """Читает все txt файлы и объединяет"""
    all_content = []
    
    for file_path in Path(SOURCE_DIR).glob("*.txt"):
        print(f"Читаю: {file_path.name}")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            all_content.append(content)
    
    return "\n\n".join(all_content)

def create_chunks(content, chunk_size):
    """Разбивает контент на чанки"""
    chunks = []
    for i in range(0, len(content), chunk_size):
        chunks.append(content[i:i+chunk_size])
    return chunks

def create_tasks_json(chunks):
    """Создает JSON с задачами для gemini_parallel_tester"""
    
    # Читаем промпт
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        prompt = f.read()
    
    tasks = []
    for i, chunk in enumerate(chunks, 1):
        # Сохраняем чанк во временный файл
        chunk_file = f"/tmp/chunk_{i}.txt"
        with open(chunk_file, 'w', encoding='utf-8') as f:
            f.write(chunk)
        
        task = {
            "id": f"chunk_{i:03d}",
            "system_instruction": prompt,
            "context_files": [chunk_file],
            "messages": [
                "Проанализируй предоставленные данные максимально детально. Особое внимание - найди ВСЕ упоминания слова forge в любом контексте.",
                "Продолжи анализ. Убедись что нашел все упоминания forge. Если анализ завершен, добавь в конец ответа #42*7@"
            ]
        }
        tasks.append(task)
    
    # Сохраняем задачи
    tasks_file = "/tmp/gemini_tasks.json"
    with open(tasks_file, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    
    return tasks_file

def main():
    # Создаем выходную директорию
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("ОБРАБОТКА ДАННЫХ ЧЕРЕЗ GEMINI PARALLEL TESTER")
    print("=" * 60)
    
    # Читаем все файлы
    print("\nЧитаю файлы...")
    content = read_all_files()
    print(f"Общий размер: {len(content)} символов")
    
    # Создаем чанки
    print(f"\nРазбиваю на чанки по {CHUNK_SIZE} символов...")
    chunks = create_chunks(content, CHUNK_SIZE)
    print(f"Создано чанков: {len(chunks)}")
    
    # Создаем файл с задачами
    print("\nСоздаю задачи для Gemini...")
    tasks_file = create_tasks_json(chunks)
    
    # Генерируем имя выходного файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{OUTPUT_DIR}/analysis_results_{timestamp}.json"
    
    # Запускаем gemini_parallel_tester
    print("\nЗапускаю обработку через gemini_parallel_tester...")
    print(f"Выходной файл: {output_file}")
    
    # Получаем API ключ
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("ERROR: Установите переменную окружения GEMINI_API_KEY")
        sys.exit(1)
    
    # Запускаем тестер
    import subprocess
    cmd = [
        "python3",
        "/Volumes/Z7S/development/GalaxyDevelopments/gemini_parallel_tester/gemini_parallel_tester.py",
        api_key,
        tasks_file,
        output_file
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("\n✓ Обработка завершена успешно!")
        
        # Проверяем на наличие forge в результатах
        with open(output_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
            
        print("\n" + "=" * 60)
        print("ПОИСК УПОМИНАНИЙ FORGE:")
        print("=" * 60)
        
        forge_found = False
        for task_result in results.get('results', []):
            for response in task_result.get('responses', []):
                if 'forge' in response.lower():
                    forge_found = True
                    print(f"\n🔴 FORGE НАЙДЕН в {task_result['id']}!")
                    # Показываем контекст
                    lines = response.split('\n')
                    for line in lines:
                        if 'forge' in line.lower():
                            print(f"  > {line}")
        
        if not forge_found:
            print("\n✗ Упоминаний forge не найдено")
    else:
        print(f"\n✗ Ошибка: {result.stderr}")

if __name__ == "__main__":
    main()