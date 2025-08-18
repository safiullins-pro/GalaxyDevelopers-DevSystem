#!/usr/bin/env python3
"""
FilenameFixer - Исправление всей хуйни с именами файлов
ПРАВИЛЬНЫЙ ФОРМАТ: {ЧТО_ЭТО}_{К_ЧЕМУ_ОТНОСИТСЯ}_{АЙДИ}
"""

import json
from pathlib import Path

class FilenameFixer:
    def __init__(self):
        self.base_dir = Path("/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem")
        self.counter = 1
        
    def fix_all_templates(self):
        """Исправление всех template файлов"""
        
        print("🔧 FIXING ALL TEMPLATE FILES...")
        
        templates_dir = self.base_dir / "03_TEMPLATES"
        
        for format_dir in templates_dir.iterdir():
            if format_dir.is_dir():
                print(f"\n📁 Processing {format_dir.name}:")
                
                for template_file in format_dir.iterdir():
                    if template_file.is_file() and template_file.name.endswith('.json'):
                        # Извлекаем deliverable name из содержимого
                        try:
                            with open(template_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            deliverable = data.get("deliverable", "unknown")
                            # Убираем расширение из deliverable
                            clean_name = deliverable.replace('.xlsx', '').replace('.pdf', '').replace('.md', '').replace('.sql', '').replace('.json', '')
                            
                            # Генерируем новое имя
                            new_name = f"template_{clean_name}_T{self.counter:03d}.json"
                            new_path = format_dir / new_name
                            
                            print(f"   {template_file.name} → {new_name}")
                            
                            # Переименовываем
                            if template_file != new_path:
                                template_file.rename(new_path)
                            
                            self.counter += 1
                            
                        except Exception as e:
                            print(f"   ❌ Error processing {template_file.name}: {e}")
        
        print("\n✅ ALL TEMPLATES FIXED!")


def main():
    fixer = FilenameFixer()
    fixer.fix_all_templates()


if __name__ == "__main__":
    main()