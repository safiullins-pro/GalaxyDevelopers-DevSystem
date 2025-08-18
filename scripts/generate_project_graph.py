#!/usr/bin/env python3
"""
Генератор графа проекта из JSON структуры файлов
Анализирует зависимости, находит мусор, создает актуальный контекст
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

class ProjectAnalyzer:
    def __init__(self, base_path="/Volumes/Z7S/development/GalaxyDevelopers/DevSystem"):
        self.base_path = base_path
        self.files_structure_path = f"{base_path}/DOCUMENTS/FILES_STRUCTURE"
        self.project_data = {}
        self.dependencies = {}
        self.orphaned = []
        self.deprecated = []
        self.duplicates = []
        
    def load_all_json_structures(self):
        """Загружаем все JSON файлы структуры"""
        for json_file in Path(self.files_structure_path).glob("*.json"):
            with open(json_file, 'r') as f:
                data = json.load(f)
                self.project_data[data.get('directory', json_file.stem)] = data
    
    def analyze_dependencies(self):
        """Анализируем зависимости между файлами"""
        for dir_name, dir_data in self.project_data.items():
            files = dir_data.get('files', {})
            for file_name, file_info in files.items():
                file_path = f"{dir_name}/{file_name}"
                
                # Собираем импорты/экспорты
                connections = file_info.get('connections', [])
                imports = file_info.get('functionality', {}).get('dependencies', [])
                
                self.dependencies[file_path] = {
                    'imports': connections + imports,
                    'imported_by': [],
                    'tags': file_info.get('tags', [])
                }
        
        # Обратные связи
        for file_path, deps in self.dependencies.items():
            for imported_file in deps['imports']:
                if imported_file in self.dependencies:
                    self.dependencies[imported_file]['imported_by'].append(file_path)
    
    def detect_garbage(self):
        """Находим мусор по критериям"""
        
        for file_path, deps in self.dependencies.items():
            # 1. Orphaned - файлы без связей
            if not deps['imports'] and not deps['imported_by']:
                if 'test' not in file_path.lower() and 'backup' not in file_path.lower():
                    self.orphaned.append({
                        'file': file_path,
                        'reason': 'Нет импортов и не импортируется',
                        'severity': 'high'
                    })
            
            # 2. Deprecated - устаревшие файлы
            if 'deprecated' in deps.get('tags', []):
                self.deprecated.append({
                    'file': file_path,
                    'reason': 'Помечен как deprecated',
                    'severity': 'medium'
                })
            
            # 3. Test/Backup файлы старше 30 дней
            if 'test' in file_path.lower() or 'backup' in file_path.lower():
                file_full_path = f"{self.base_path}/{file_path}"
                if os.path.exists(file_full_path):
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_full_path))
                    if datetime.now() - mtime > timedelta(days=30):
                        self.deprecated.append({
                            'file': file_path,
                            'reason': f'Тестовый/backup файл старше 30 дней',
                            'severity': 'low'
                        })
    
    def find_duplicates(self):
        """Ищем дублирующийся функционал"""
        functionality_hashes = {}
        
        for dir_name, dir_data in self.project_data.items():
            files = dir_data.get('files', {})
            for file_name, file_info in files.items():
                # Создаем хеш из функционала
                functionality = json.dumps(file_info.get('functionality', {}), sort_keys=True)
                func_hash = hashlib.md5(functionality.encode()).hexdigest()[:8]
                
                if func_hash in functionality_hashes:
                    self.duplicates.append({
                        'files': [functionality_hashes[func_hash], f"{dir_name}/{file_name}"],
                        'reason': 'Похожий функционал',
                        'severity': 'medium'
                    })
                else:
                    functionality_hashes[func_hash] = f"{dir_name}/{file_name}"
    
    def generate_graph(self):
        """Генерируем граф проекта"""
        output = []
        output.append("=" * 60)
        output.append("СТРУКТУРА ПРОЕКТА GalaxyDevelopers")
        output.append(f"Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 60)
        output.append("")
        
        # Основная структура
        for dir_name, dir_data in sorted(self.project_data.items()):
            tags = ', '.join(dir_data.get('tags', []))
            output.append(f"📁 {dir_name}/ [{tags}]")
            output.append(f"   {dir_data.get('description', '')}")
            
            # Файлы
            files = dir_data.get('files', {})
            for file_name, file_info in sorted(files.items()):
                file_tags = ', '.join(file_info.get('tags', []))
                output.append(f"   📄 {file_name} [{file_tags}]")
                output.append(f"      {file_info.get('description', '')}")
                
                # Связи
                connections = file_info.get('connections', [])
                if connections:
                    output.append(f"      → Связи: {', '.join(connections)}")
            
            output.append("")
        
        # Анализ мусора
        output.append("=" * 60)
        output.append("АНАЛИЗ КАЧЕСТВА КОДА")
        output.append("=" * 60)
        output.append("")
        
        if self.orphaned:
            output.append("🔴 ORPHANED FILES (файлы без связей):")
            for item in self.orphaned:
                output.append(f"   - {item['file']}: {item['reason']}")
            output.append("")
        
        if self.deprecated:
            output.append("🟡 DEPRECATED/OLD FILES:")
            for item in self.deprecated:
                output.append(f"   - {item['file']}: {item['reason']}")
            output.append("")
        
        if self.duplicates:
            output.append("🟠 ВОЗМОЖНЫЕ ДУБЛИКАТЫ:")
            for item in self.duplicates:
                output.append(f"   - {', '.join(item['files'])}: {item['reason']}")
            output.append("")
        
        # Статистика
        output.append("=" * 60)
        output.append("СТАТИСТИКА")
        output.append("=" * 60)
        total_files = sum(len(d.get('files', {})) for d in self.project_data.values())
        output.append(f"Всего директорий: {len(self.project_data)}")
        output.append(f"Всего файлов: {total_files}")
        output.append(f"Файлов без связей: {len(self.orphaned)}")
        output.append(f"Устаревших файлов: {len(self.deprecated)}")
        output.append(f"Возможных дубликатов: {len(self.duplicates)}")
        
        # Рекомендации
        garbage_count = len(self.orphaned) + len(self.deprecated)
        if garbage_count > 0:
            output.append("")
            output.append("⚠️  РЕКОМЕНДАЦИИ:")
            output.append(f"   Можно удалить {garbage_count} файлов для очистки проекта")
            if self.orphaned:
                output.append(f"   Проверить {len(self.orphaned)} файлов без связей")
        
        return "\n".join(output)
    
    def generate_context_for_ai(self):
        """Генерируем компактный контекст для AI"""
        context = {
            "project": "GalaxyDevelopers DevSystem",
            "structure": {},
            "critical_files": [],
            "api_endpoints": [],
            "ports": {"backend": 37777, "memory": 37778},
            "issues": []
        }
        
        for dir_name, dir_data in self.project_data.items():
            context["structure"][dir_name] = {
                "purpose": dir_data.get("description", ""),
                "files_count": len(dir_data.get("files", {})),
                "key_files": list(dir_data.get("files", {}).keys())[:3]
            }
            
            # Собираем критические файлы
            for file_name, file_info in dir_data.get("files", {}).items():
                if "critical" in file_info.get("tags", []):
                    context["critical_files"].append(f"{dir_name}/{file_name}")
                
                # API endpoints
                if "api_endpoints" in file_info.get("functionality", {}):
                    context["api_endpoints"].extend(
                        file_info["functionality"]["api_endpoints"]
                    )
        
        # Проблемы
        if self.orphaned:
            context["issues"].append(f"{len(self.orphaned)} orphaned files")
        if self.deprecated:
            context["issues"].append(f"{len(self.deprecated)} deprecated files")
        
        return json.dumps(context, indent=2, ensure_ascii=False)
    
    def run(self):
        """Запуск полного анализа"""
        print("🔍 Загружаем структуру проекта...")
        self.load_all_json_structures()
        
        print("🔗 Анализируем зависимости...")
        self.analyze_dependencies()
        
        print("🗑️  Ищем мусор...")
        self.detect_garbage()
        self.find_duplicates()
        
        print("📊 Генерируем граф...")
        graph = self.generate_graph()
        
        # Сохраняем результаты
        output_path = f"{self.base_path}/DOCUMENTS/project_graph.txt"
        with open(output_path, 'w') as f:
            f.write(graph)
        print(f"✅ Граф сохранен в {output_path}")
        
        # Контекст для AI
        context_path = f"{self.base_path}/DOCUMENTS/ai_context.json"
        with open(context_path, 'w') as f:
            f.write(self.generate_context_for_ai())
        print(f"✅ AI контекст сохранен в {context_path}")
        
        # Выводим результат
        print("\n" + graph)
        
        return {
            "orphaned": len(self.orphaned),
            "deprecated": len(self.deprecated),
            "duplicates": len(self.duplicates),
            "total_garbage": len(self.orphaned) + len(self.deprecated)
        }

if __name__ == "__main__":
    analyzer = ProjectAnalyzer()
    results = analyzer.run()
    
    if results["total_garbage"] > 0:
        print(f"\n🚨 Найдено {results['total_garbage']} файлов для очистки!")
        print("Запустите 'python3 clean_garbage.py' для удаления")