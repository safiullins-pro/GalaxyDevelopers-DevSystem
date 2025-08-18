#!/usr/bin/env python3
"""
Быстрое обновление MD5 сумм в документации
Запускать когда файлы изменены легально
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

BASE_PATH = "/Volumes/Z7S/development/GalaxyDevelopers/DevSystem"
FILES_STRUCTURE_PATH = f"{BASE_PATH}/DOCUMENTS/FILES_STRUCTURE"

def calculate_md5(file_path):
    """Считаем MD5 сумму файла"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def update_all_md5():
    """Обновляем MD5 для всех файлов"""
    updated = 0
    
    print("Обновляю MD5 суммы в документации...")
    
    for json_file in Path(FILES_STRUCTURE_PATH).glob("*.json"):
        modified = False
        
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        dir_name = data.get('directory', '')
        dir_path = data.get('path', f"{BASE_PATH}/{dir_name}")
        
        # Обновляем MD5 для каждого файла
        for file_name, file_info in data.get('files', {}).items():
            file_path = f"{dir_path}/{file_name}"
            
            if os.path.exists(file_path):
                new_md5 = calculate_md5(file_path)
                old_md5 = file_info.get('md5')
                
                if new_md5 != old_md5:
                    file_info['md5'] = new_md5
                    file_info['last_checked'] = datetime.now().isoformat()
                    file_info['status'] = '✅ verified'
                    modified = True
                    updated += 1
                    print(f"  ✅ {dir_name}/{file_name} - MD5 обновлен")
        
        # Сохраняем если были изменения
        if modified:
            data['last_update'] = datetime.now().isoformat()
            with open(json_file, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Обновлено {updated} файлов")
    return updated

if __name__ == "__main__":
    update_all_md5()