#!/usr/bin/env python3
import os
import json
import time
import hashlib
from pathlib import Path
import subprocess
from datetime import datetime

# Конфигурация
SOURCE_DIR = "/Users/safiullins_pro/В ПЕРПЛЕКСИТИ"
OUTPUT_DIR = "/Volumes/Z7S/development/GalaxyDevelopments/GEMINI_ANALYSIS_RESULTS"
GEMINI_TESTER = "/Volumes/Z7S/development/GalaxyDevelopments/gemini_parallel_tester"
PROMPT_FILE = "/Users/safiullins_pro/Scripts/gemini-triggers/gemini-analysis-prompt.txt"

# Параметры чанков и rate limiting
CHUNK_SIZE = 30000  # символов в чанке
REQUESTS_PER_MINUTE = 25
DELAY_BETWEEN_REQUESTS = 60 / REQUESTS_PER_MINUTE  # 2.4 секунды

def read_jsonl_files():
    """Читает все JSONL файлы из папки"""
    all_content = []
    jsonl_files = list(Path(SOURCE_DIR).glob("*.jsonl"))
    
    print(f"Найдено {len(jsonl_files)} JSONL файлов")
    
    for file_path in jsonl_files:
        print(f"Обрабатываю: {file_path.name}")
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    all_content.append(json.dumps(data, ensure_ascii=False))
                except:
                    continue
    
    return all_content

def create_chunks(content_list, chunk_size):
    """Разбивает контент на чанки"""
    chunks = []
    current_chunk = []
    current_size = 0
    
    for item in content_list:
        item_size = len(item)
        if current_size + item_size > chunk_size and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [item]
            current_size = item_size
        else:
            current_chunk.append(item)
            current_size += item_size
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks

def generate_filename(chunk_content, index):
    """Генерирует уникальное имя файла для чанка"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    content_hash = hashlib.md5(chunk_content.encode()).hexdigest()[:8]
    return f"analysis_chunk_{index:03d}_{timestamp}_{content_hash}.md"

def process_chunk_with_gemini(chunk, index):
    """Обрабатывает чанк через Gemini API"""
    # Читаем промпт
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        prompt = f.read()
    
    # Создаем временный файл с контентом
    temp_file = f"/tmp/chunk_{index}.txt"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(f"{prompt}\n\n---\nДАННЫЕ ДЛЯ АНАЛИЗА:\n---\n{chunk}")
    
    # Генерируем имя выходного файла
    output_filename = generate_filename(chunk, index)
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # Запускаем gemini_parallel_tester
    cmd = [
        "python3",
        f"{GEMINI_TESTER}/gemini_tester.py",
        "--input", temp_file,
        "--output", output_path,
        "--max-tokens", "60000"
    ]
    
    print(f"Обрабатываю чанк {index}: {output_filename}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(f"✓ Успешно обработан чанк {index}")
            # Удаляем временный файл
            os.remove(temp_file)
            return output_path
        else:
            print(f"✗ Ошибка обработки чанка {index}: {result.stderr}")
            return None
    except subprocess.TimeoutExpired:
        print(f"✗ Таймаут при обработке чанка {index}")
        return None
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return None

def main():
    # Создаем выходную директорию
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("ЗАПУСК АНАЛИЗА JSONL ФАЙЛОВ ЧЕРЕЗ GEMINI")
    print("=" * 60)
    
    # Читаем все JSONL файлы
    content = read_jsonl_files()
    print(f"\nВсего прочитано {len(content)} записей")
    
    # Создаем чанки
    chunks = create_chunks(content, CHUNK_SIZE)
    print(f"Создано {len(chunks)} чанков по ~{CHUNK_SIZE} символов")
    
    # Обрабатываем чанки с учетом rate limiting
    processed_files = []
    for i, chunk in enumerate(chunks, 1):
        result = process_chunk_with_gemini(chunk, i)
        if result:
            processed_files.append(result)
        
        # Rate limiting
        if i < len(chunks):
            print(f"Ожидание {DELAY_BETWEEN_REQUESTS:.1f} сек (rate limit)...")
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    print("\n" + "=" * 60)
    print(f"ОБРАБОТКА ЗАВЕРШЕНА")
    print(f"Успешно обработано: {len(processed_files)} из {len(chunks)} чанков")
    print(f"Результаты сохранены в: {OUTPUT_DIR}")
    print("=" * 60)
    
    # Выводим список созданных файлов
    if processed_files:
        print("\nСозданные файлы:")
        for f in processed_files:
            print(f"  - {os.path.basename(f)}")

if __name__ == "__main__":
    main()