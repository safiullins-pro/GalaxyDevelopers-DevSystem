#!/usr/bin/env python3
"""
💀 CLEANUP AND ORGANIZE
Наводим порядок в проекте!
by FORGE & ALBERT 🔥
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def cleanup_project():
    """Чистим и организуем проект"""
    
    project_root = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem")
    
    print("💀 НАВОДИМ ПОРЯДОК В ПРОЕКТЕ!")
    print("="*50)
    
    # 1. Удаляем все ._* файлы (мусор от macOS)
    print("\n🗑️ УДАЛЯЕМ МУСОРНЫЕ ФАЙЛЫ...")
    trash_count = 0
    for root, dirs, files in os.walk(project_root):
        for file in files:
            if file.startswith("._"):
                file_path = Path(root) / file
                try:
                    file_path.unlink()
                    trash_count += 1
                except:
                    pass
    print(f"   ✅ Удалено мусорных файлов: {trash_count}")
    
    # 2. Создаём правильную структуру папок
    print("\n📁 СОЗДАЁМ ПРАВИЛЬНУЮ СТРУКТУРУ...")
    
    folders = {
        "00_DOCUMENTATION": ["README", "ARCHITECTURE", "GUIDES"],
        "11_SCRIPTS": ["executors", "validators", "generators"],
        "12_CONFIGS": ["env", "docker", "kubernetes"],
        "13_ARCHIVE": ["old", "deprecated", "temp"]
    }
    
    for main_folder, subfolders in folders.items():
        main_path = project_root / main_folder
        main_path.mkdir(exist_ok=True)
        for sub in subfolders:
            (main_path / sub).mkdir(exist_ok=True)
    
    # 3. Перемещаем файлы в правильные папки
    print("\n📦 ОРГАНИЗУЕМ ФАЙЛЫ...")
    moved = 0
    
    # Перемещаем документацию
    for file in project_root.glob("*.md"):
        if file.name not in ["README.md"]:  # README остается в корне
            target = project_root / "00_DOCUMENTATION" / "GUIDES" / file.name
            try:
                shutil.move(str(file), str(target))
                moved += 1
                print(f"   📄 {file.name} -> 00_DOCUMENTATION/GUIDES/")
            except:
                pass
    
    # Перемещаем скрипты
    for file in project_root.glob("*.py"):
        if "executor" in file.name.lower() or "P1" in file.name:
            target = project_root / "11_SCRIPTS" / "executors" / file.name
            try:
                shutil.move(str(file), str(target))
                moved += 1
                print(f"   🐍 {file.name} -> 11_SCRIPTS/executors/")
            except:
                pass
    
    # Перемещаем старые логи
    for file in project_root.glob("*.log"):
        target = project_root / "13_ARCHIVE" / "old" / file.name
        try:
            shutil.move(str(file), str(target))
            moved += 1
        except:
            pass
    
    print(f"\n✅ Перемещено файлов: {moved}")
    
    # 4. Создаём индексный файл
    print("\n📝 СОЗДАЁМ ИНДЕКС ПРОЕКТА...")
    
    index_content = f"""# PROJECT STRUCTURE INDEX
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 📁 MAIN DIRECTORIES

### ACTIVE WORK
- `00_PROJECT_MANAGEMENT/` - Управление проектом
- `01_AGENTS/` - AI агенты системы
- `02_DATA/` - Данные и кэш
- `03_TEMPLATES/` - Шаблоны документов
- `04_STANDARDS/` - Стандарты и методологии
- `05_ROLES/` - Профили ролей (35 ролей)
- `06_PROCESSES/` - Описания процессов (P1-P7)
- `07_DELIVERABLES/` - Результаты работы
- `08_LOGS/` - Логи выполнения
- `09_JOURNALS/` - Журналы операций
- `10_REPORTS/` - Отчеты

### SUPPORT
- `00_DOCUMENTATION/` - Вся документация проекта
- `11_SCRIPTS/` - Исполняемые скрипты
- `12_CONFIGS/` - Конфигурации
- `13_ARCHIVE/` - Архив старых файлов

## 📊 STATISTICS
- Total Processes: 25 (from 7 phases)
- Total Roles: 38
- Total Templates: 81
- Total Standards: 5 (need more!)

## 🚀 QUICK START
1. Run executors from `11_SCRIPTS/executors/`
2. Check results in `07_DELIVERABLES/`
3. View reports in `10_REPORTS/`

---
💀 FORGE & ALBERT PROJECT 🔥
"""
    
    index_path = project_root / "PROJECT_INDEX.md"
    index_path.write_text(index_content)
    print(f"   ✅ PROJECT_INDEX.md создан")
    
    # 5. Финальная статистика
    print("\n📊 ФИНАЛЬНАЯ ПРОВЕРКА...")
    
    # Считаем что осталось в корне
    root_files = list(project_root.glob("*.*"))
    root_files = [f for f in root_files if not f.name.startswith("._")]
    
    print(f"   Файлов в корне: {len(root_files)}")
    print(f"   Папок структуры: {len(list(project_root.glob('*/')))} ")
    
    if len(root_files) <= 5:  # README, .env, .gitignore и пара конфигов - это ОК
        print("\n✅ ПОРЯДОК НАВЕДЁН!")
    else:
        print(f"\n⚠️ В корне всё ещё {len(root_files)} файлов")
        for f in root_files[:10]:
            print(f"     - {f.name}")
    
    return trash_count, moved

if __name__ == "__main__":
    trash, moved = cleanup_project()
    
    print("\n" + "="*50)
    print(f"💀 УБОРКА ЗАВЕРШЕНА! 🔥")
    print(f"🗑️ Удалено мусора: {trash}")
    print(f"📦 Организовано файлов: {moved}")
    print("="*50)