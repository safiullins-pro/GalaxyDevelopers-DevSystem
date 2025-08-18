#!/usr/bin/env python3
import sys
import json
import redis
import subprocess

def main():
    """
    Этот скрипт вызывается pre-commit хуком.
    Он собирает измененные файлы, читает их содержимое и отправляет
    в Redis для анализа AI Code Auditor Agent.
    """
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    # Получаем список измененных файлов
    staged_files = subprocess.check_output(['git', 'diff', '--cached', '--name-only']).decode().splitlines()
    
    if not staged_files:
        print("Нет измененных файлов для анализа.")
        sys.exit(0)

    print(f"Найдено {len(staged_files)} измененных файлов для анализа...")

    for file_path in staged_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            event_data = {
                'file_path': file_path,
                'file_content': content,
                'commit_id': 'local_commit' # В реальной системе здесь был бы ID коммита
            }
            
            # Отправляем событие в Redis
            r.publish('file_changes', json.dumps(event_data))
            print(f"  - Отправлен на анализ файл: {file_path}")

        except Exception as e:
            print(f"Не удалось обработать файл {file_path}: {e}", file=sys.stderr)

    # Здесь можно добавить логику ожидания ответа от аудитора,
    # если требуется блокировать коммит.
    # Например, слушать канал 'analysis_results' или 'blocking_requests'.
    
    print("Все файлы отправлены на асинхронный анализ.")
    sys.exit(0) # Пока не блокируем коммит

if __name__ == "__main__":
    main()
