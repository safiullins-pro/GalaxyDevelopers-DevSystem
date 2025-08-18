#!/usr/bin/env python3
"""
Экстрактор изменений файлов из Claude логов
Извлекает все изменения файлов с полным контекстом
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

def extract_file_changes(log_path: str, start_time: datetime, end_time: datetime):
    """
    Извлекает все изменения файлов за период
    """
    file_changes = []
    
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
                
                # Проверяем timestamp
                if 'timestamp' in entry:
                    entry_time = datetime.fromisoformat(
                        entry['timestamp'].replace('Z', '+00:00')
                    )
                    
                    if start_time <= entry_time <= end_time:
                        # Ищем изменения файлов
                        if 'toolUseResult' in entry and 'filePath' in entry['toolUseResult']:
                            change = {
                                'timestamp': entry['timestamp'],
                                'file': entry['toolUseResult']['filePath'],
                                'old_string': entry['toolUseResult'].get('oldString', ''),
                                'new_string': entry['toolUseResult'].get('newString', ''),
                                'original_file': entry['toolUseResult'].get('originalFile', ''),
                                'message_uuid': entry.get('uuid', ''),
                                'session_id': entry.get('sessionId', '')
                            }
                            file_changes.append(change)
                            
            except json.JSONDecodeError:
                continue
    
    return file_changes

def save_changes_to_markdown(changes: List[Dict], output_file: str):
    """
    Сохраняет изменения в markdown файл
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 📝 FILE CHANGES HISTORY\n\n")
        f.write(f"Total changes: {len(changes)}\n\n")
        f.write("---\n\n")
        
        for i, change in enumerate(changes, 1):
            f.write(f"## Change #{i}\n")
            f.write(f"**Timestamp**: {change['timestamp']}\n")
            f.write(f"**File**: `{change['file']}`\n\n")
            
            if change['old_string']:
                f.write("### ❌ OLD CODE:\n")
                f.write("```\n")
                f.write(change['old_string'])
                f.write("\n```\n\n")
            
            if change['new_string']:
                f.write("### ✅ NEW CODE:\n")
                f.write("```\n")
                f.write(change['new_string'])
                f.write("\n```\n\n")
            
            f.write("---\n\n")

def create_restoration_script(changes: List[Dict], output_file: str):
    """
    Создает скрипт для восстановления состояния файлов
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("#!/bin/bash\n")
        f.write("# Auto-generated restoration script\n")
        f.write(f"# Generated at: {datetime.now()}\n\n")
        
        # Группируем по файлам
        files_data = {}
        for change in changes:
            file_path = change['file']
            if file_path not in files_data:
                files_data[file_path] = []
            files_data[file_path].append(change)
        
        # Для каждого файла берем последнее состояние
        for file_path, file_changes in files_data.items():
            last_change = file_changes[-1]
            if last_change['new_string']:
                f.write(f"# Restore {file_path}\n")
                f.write(f"cat > '{file_path}.restored' << 'EOF'\n")
                if last_change['original_file']:
                    # Применяем изменение к оригинальному файлу
                    content = last_change['original_file']
                    if last_change['old_string'] in content:
                        content = content.replace(
                            last_change['old_string'], 
                            last_change['new_string']
                        )
                    f.write(content)
                else:
                    f.write(last_change['new_string'])
                f.write("\nEOF\n\n")

def main():
    # Конфигурация
    log_file = "/Users/safiullins_pro/.claude/projects/-Users-safiullins-pro/42545c12-a4cb-4e8c-a90c-c4feccd0360b.jsonl"
    start_time = datetime(2025, 8, 12, 0, 44, 0, tzinfo=timezone.utc)
    end_time = datetime(2025, 8, 12, 2, 44, 0, tzinfo=timezone.utc)
    
    print("📝 Extracting file changes...")
    changes = extract_file_changes(log_file, start_time, end_time)
    print(f"Found {len(changes)} file changes")
    
    # Сохраняем изменения
    output_dir = Path("/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/SCRIPTS/CHAT_SUMMARAISER")
    
    # Markdown с изменениями
    changes_file = output_dir / f"file_changes_{start_time.strftime('%Y%m%d_%H%M')}.md"
    save_changes_to_markdown(changes, changes_file)
    print(f"✅ Changes saved to: {changes_file}")
    
    # Скрипт восстановления
    restore_script = output_dir / f"restore_{start_time.strftime('%Y%m%d_%H%M')}.sh"
    create_restoration_script(changes, restore_script)
    print(f"🔧 Restoration script: {restore_script}")
    
    # Анализ файлов
    files_changed = set(c['file'] for c in changes)
    print(f"\n📊 Files affected: {len(files_changed)}")
    for file in sorted(files_changed):
        count = len([c for c in changes if c['file'] == file])
        print(f"  - {file}: {count} changes")

if __name__ == "__main__":
    main()