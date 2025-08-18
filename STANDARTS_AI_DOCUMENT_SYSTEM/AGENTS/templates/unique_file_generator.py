#!/usr/bin/env python3
"""
UniqueFileGenerator - ИСПРАВЛЯЕТ ПРОБЛЕМУ ОДИНАКОВЫХ ИМЕН ФАЙЛОВ
ГЕНЕРИРУЕТ УНИКАЛЬНЫЕ ИМЕНА ПО ПРОЦЕССАМ: P1.1, P1.2, P2.1 и т.д.
Автор: GALAXYDEVELOPMENT
Версия: 1.0.0
"""

import json
from pathlib import Path
from typing import Dict, List

class UniqueFileGenerator:
    """Генератор уникальных имен файлов по процессам"""
    
    def __init__(self):
        self.base_dir = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem")
        self.process_counter = {}  # phase_id -> counter
        
    def generate_process_filename(self, process_id: str, process_name: str, deliverable: str, format_type: str) -> str:
        """Генерация уникального имени файла по процессу"""
        
        # Очистка названия процесса
        clean_name = self._clean_name(process_name)
        
        # Определение расширения
        extension = self._get_extension(format_type, deliverable)
        
        # Генерируем имя: P1.1_analysis_current_docs.xlsx
        filename = f"{process_id}_{clean_name}.{extension}"
        
        return filename
    
    def _clean_name(self, name: str) -> str:
        """Очистка названия для имени файла"""
        
        # Переводим на английский основные термины
        translations = {
            "Анализ": "analysis",
            "Техническая": "technical", 
            "Ревизия": "revision",
            "Команда": "team",
            "Оценка": "assessment",
            "Зрелости": "maturity",
            "Процессов": "processes",
            "Требования": "requirements",
            "Планирование": "planning",
            "Дизайн": "design",
            "Архитектура": "architecture",
            "База данных": "database",
            "Интеграция": "integration",
            "Безопасность": "security",
            "Тестирование": "testing",
            "Развертывание": "deployment",
            "Мониторинг": "monitoring",
            "Документация": "documentation",
            "Обучение": "training",
            "Аудит": "audit",
            "Соответствие": "compliance",
            "Производительность": "performance",
            "Масштабирование": "scaling",
            "Релиз": "release"
        }
        
        # Применяем переводы
        result = name
        for ru, en in translations.items():
            result = result.replace(ru, en)
        
        # Очистка от спецсимволов
        result = result.lower()
        result = result.replace(" ", "_")
        result = result.replace("-", "_")
        result = "".join(c for c in result if c.isalnum() or c == "_")
        
        # Удаляем множественные подчеркивания
        while "__" in result:
            result = result.replace("__", "_")
            
        return result.strip("_")
    
    def _get_extension(self, format_type: str, deliverable: str) -> str:
        """Определение расширения файла"""
        
        if format_type:
            return format_type
        
        # Определяем по deliverable
        if ".xlsx" in deliverable:
            return "xlsx"
        elif ".sql" in deliverable:
            return "sql"
        elif ".md" in deliverable:
            return "md"
        elif ".pdf" in deliverable:
            return "pdf"
        elif ".json" in deliverable:
            return "json"
        else:
            return "txt"
    
    def rename_all_templates(self):
        """Переименование всех шаблонов с уникальными именами"""
        
        print("🚀 ПЕРЕИМЕНОВАНИЕ ВСЕХ ШАБЛОНОВ")
        
        # Загружаем конфигурацию проекта
        config_path = self.base_dir / " ToDo" / "9d7e2139-7cfe-4512-99c0-70b4247b038f.jsonl  —  _Users_safiullins_pro_.claude_projects_-Volumes-Z7S-development-GalaxyAnalitics---------AppsScript-AnaliticsSystem.json"
        
        if not config_path.exists():
            print("❌ Project config not found!")
            return
        
        with open(config_path, 'r', encoding='utf-8') as f:
            project_config = json.load(f)
        
        # Обрабатываем каждый процесс
        for phase in project_config.get("phases", []):
            phase_id = phase.get("phase_id")
            
            for process in phase.get("microprocesses", []):
                process_id = process.get("id")
                process_name = process.get("name", "unknown")
                
                # Обрабатываем deliverables
                for deliverable in process.get("deliverables", []):
                    old_name = deliverable  # deliverable это просто строка
                    format_type = self._get_extension("", old_name).replace(".", "")
                    
                    # Генерируем новое имя
                    new_filename = self.generate_process_filename(
                        process_id, process_name, old_name, format_type
                    )
                    
                    print(f"📝 {process_id}: {old_name} → {new_filename}")
                    
                    # Ищем существующий template файл
                    self._rename_template_file(old_name, new_filename, format_type)
        
        print("✅ ПЕРЕИМЕНОВАНИЕ ЗАВЕРШЕНО!")
    
    def _rename_template_file(self, old_name: str, new_filename: str, format_type: str):
        """Переименование конкретного template файла"""
        
        # Определяем папку по формату
        format_folders = {
            "xlsx": "XLSX",
            "sql": "SQL", 
            "md": "MD",
            "pdf": "PDF",
            "json": "JSON"
        }
        
        folder_name = format_folders.get(format_type, "OTHER")
        templates_dir = self.base_dir / "03_TEMPLATES" / folder_name
        
        if not templates_dir.exists():
            return
        
        # Ищем файлы по паттерну
        old_pattern = old_name.replace(".", "_").replace(" ", "_").lower()
        
        for template_file in templates_dir.glob("*template.json"):
            if old_pattern in template_file.stem.lower():
                # Новое имя файла
                new_template_name = f"{new_filename.replace('.' + format_type, '')}_template.json"
                new_path = templates_dir / new_template_name
                
                # Переименовываем
                template_file.rename(new_path)
                print(f"   📁 {template_file.name} → {new_template_name}")
                break
    
    def create_filename_mapping(self):
        """Создание JSON маппинга старых и новых имен файлов"""
        
        mapping = {
            "file_mapping": {},
            "process_files": {},
            "statistics": {
                "total_processes": 0,
                "files_renamed": 0
            }
        }
        
        # Загружаем конфигурацию проекта
        config_path = self.base_dir / " ToDo" / "9d7e2139-7cfe-4512-99c0-70b4247b038f.jsonl  —  _Users_safiullins_pro_.claude_projects_-Volumes-Z7S-development-GalaxyAnalitics---------AppsScript-AnaliticsSystem.json"
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                project_config = json.load(f)
            
            for phase in project_config.get("phases", []):
                for process in phase.get("microprocesses", []):
                    process_id = process.get("id")
                    process_name = process.get("name", "")
                    
                    mapping["process_files"][process_id] = {
                        "process_name": process_name,
                        "files": []
                    }
                    
                    for deliverable in process.get("deliverables", []):
                        old_name = deliverable  # deliverable это просто строка
                        format_type = self._get_extension("", old_name).replace(".", "")
                        
                        new_filename = self.generate_process_filename(
                            process_id, process_name, old_name, format_type
                        )
                        
                        mapping["file_mapping"][old_name] = new_filename
                        mapping["process_files"][process_id]["files"].append({
                            "old_name": old_name,
                            "new_name": new_filename,
                            "format": format_type
                        })
                        
                        mapping["statistics"]["files_renamed"] += 1
                    
                    mapping["statistics"]["total_processes"] += 1
        
        # Сохраняем маппинг
        mapping_file = self.base_dir / "00_PROJECT_MANAGEMENT" / "FILENAME_MAPPING.json"
        mapping_file.parent.mkdir(exist_ok=True)
        
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Filename mapping saved to: {mapping_file}")
        return mapping


def main():
    """Исправление проблемы одинаковых имен файлов"""
    
    print("🔥 FIXING DUPLICATE FILENAMES PROBLEM!")
    
    generator = UniqueFileGenerator()
    
    # Создаем маппинг
    mapping = generator.create_filename_mapping()
    
    print(f"📊 STATISTICS:")
    print(f"   Total processes: {mapping['statistics']['total_processes']}")
    print(f"   Files to rename: {mapping['statistics']['files_renamed']}")
    
    # Показываем примеры новых имен
    print(f"\n💡 EXAMPLES OF NEW FILENAMES:")
    for process_id, info in list(mapping["process_files"].items())[:5]:
        print(f"   {process_id} ({info['process_name']}):")
        for file_info in info["files"]:
            print(f"      - {file_info['old_name']} → {file_info['new_name']}")
    
    # Переименовываем файлы
    print(f"\n🚀 RENAMING FILES...")
    generator.rename_all_templates()
    
    print(f"✅ PROBLEM SOLVED!")


if __name__ == "__main__":
    main()