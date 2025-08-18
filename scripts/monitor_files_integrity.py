#!/usr/bin/env python3
"""
Мониторинг целостности файлов через MD5
Проверяет каждые 5 минут, что файлы не изменены без обновления документации
"""

import hashlib
import json
import time
import os
from datetime import datetime
from pathlib import Path

BASE_PATH = "/Volumes/Z7S/development/GalaxyDevelopers/DevSystem"
FILES_STRUCTURE_PATH = f"{BASE_PATH}/DOCUMENTS/FILES_STRUCTURE"
CHECK_INTERVAL = 300  # 5 минут

def calculate_md5(file_path):
    """Считаем MD5 сумму файла"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def update_md5_in_json(json_file, file_name, new_md5):
    """Обновляем MD5 в JSON документации"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    if file_name in data.get('files', {}):
        data['files'][file_name]['md5'] = new_md5
        data['files'][file_name]['last_checked'] = datetime.now().isoformat()
        
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    return False

def check_integrity():
    """Основная проверка целостности"""
    errors = []
    warnings = []
    checked = 0
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Проверяю целостность файлов...")
    
    # Проходим по всем JSON структурам
    for json_file in Path(FILES_STRUCTURE_PATH).glob("*.json"):
        with open(json_file, 'r') as f:
            structure = json.load(f)
        
        dir_name = structure.get('directory', '')
        dir_path = structure.get('path', f"{BASE_PATH}/{dir_name}")
        
        # Проверяем файлы
        for file_name, file_info in structure.get('files', {}).items():
            checked += 1
            file_path = f"{dir_path}/{file_name}"
            
            if not os.path.exists(file_path):
                warnings.append(f"⚠️  {dir_name}/{file_name} - файл не существует")
                continue
            
            current_md5 = calculate_md5(file_path)
            saved_md5 = file_info.get('md5')
            
            if not saved_md5:
                # Первый раз - сохраняем MD5
                update_md5_in_json(json_file, file_name, current_md5)
                print(f"   ✅ {file_name} - MD5 сохранен")
            elif current_md5 != saved_md5:
                # MD5 не совпадает!
                errors.append(f"❌ {dir_name}/{file_name} - ИЗМЕНЕН БЕЗ ОБНОВЛЕНИЯ ДОКУМЕНТАЦИИ!")
    
    # Результаты
    print(f"Проверено файлов: {checked}")
    
    if errors:
        print("\n🚨 КРИТИЧЕСКИЕ ОШИБКИ - ФАЙЛЫ ИЗМЕНЕНЫ:")
        for error in errors:
            print(f"   {error}")
        
        # Записываем в лог
        with open(f"{BASE_PATH}/DOCUMENTS/integrity_errors.log", 'a') as f:
            f.write(f"\n[{datetime.now().isoformat()}] ОШИБКИ ЦЕЛОСТНОСТИ:\n")
            for error in errors:
                f.write(f"  {error}\n")
        
        return False
    
    if warnings:
        print("\n⚠️  Предупреждения:")
        for warning in warnings:
            print(f"   {warning}")
    
    print("✅ Все файлы соответствуют документации")
    return True

def monitor_loop():
    """Бесконечный цикл мониторинга"""
    print("=" * 60)
    print("МОНИТОРИНГ ЦЕЛОСТНОСТИ ФАЙЛОВ")
    print(f"Проверка каждые {CHECK_INTERVAL/60} минут")
    print("=" * 60)
    
    while True:
        try:
            is_ok = check_integrity()
            
            if not is_ok:
                # Отправляем алерт (можно добавить уведомление)
                print("\n🔴 ТРЕБУЕТСЯ ОБНОВЛЕНИЕ ДОКУМЕНТАЦИИ!")
                print("Запустите: python3 SCRIPTS/update_documentation.py")
            
            # Ждем до следующей проверки
            print(f"\nСледующая проверка через {CHECK_INTERVAL/60} минут...")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n👋 Мониторинг остановлен")
            break
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            time.sleep(60)  # При ошибке ждем минуту

if __name__ == "__main__":
    # Быстрая проверка или мониторинг
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Одна проверка и выход
        check_integrity()
    else:
        # Бесконечный мониторинг
        monitor_loop()