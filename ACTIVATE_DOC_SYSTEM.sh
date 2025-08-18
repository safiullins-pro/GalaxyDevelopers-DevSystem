#!/bin/bash

# GalaxyDevelopers DevSystem - Автоматическая система документации
# Главный скрипт активации

set -e

PROJECT_ROOT="/Volumes/Z7S/development/GalaxyDevelopers/DevSystem"
DOC_SYSTEM_DIR="$PROJECT_ROOT/DOC_SYSTEM"

echo "🚀 ЗАПУСК СИСТЕМЫ АВТОМАТИЧЕСКОЙ ДОКУМЕНТАЦИИ GALAXYDEVELOPERS"
echo "============================================================"

# Проверка директории
if [ ! -d "$DOC_SYSTEM_DIR" ]; then
    echo "❌ Директория DOC_SYSTEM не найдена!"
    exit 1
fi

cd "$PROJECT_ROOT"

# Установка зависимостей Python
echo "📦 Установка зависимостей..."
pip3 install -q flask flask-cors flask-socketio pyyaml jinja2 networkx watchdog google-generativeai openai anthropic 2>/dev/null || true

# Создание Git hooks
echo "🔗 Настройка Git hooks..."
cat > "$PROJECT_ROOT/.git/hooks/pre-commit" << 'EOF'
#!/bin/bash
# DOC_SYSTEM Pre-commit hook

PROJECT_ROOT="/Volumes/Z7S/development/GalaxyDevelopers/DevSystem"
python3 "$PROJECT_ROOT/DOC_SYSTEM/hooks/pre_commit.py"

if [ $? -ne 0 ]; then
    echo "❌ Валидация не пройдена. Коммит отменен."
    exit 1
fi
EOF

chmod +x "$PROJECT_ROOT/.git/hooks/pre-commit"

cat > "$PROJECT_ROOT/.git/hooks/post-commit" << 'EOF'
#!/bin/bash
# DOC_SYSTEM Post-commit hook

PROJECT_ROOT="/Volumes/Z7S/development/GalaxyDevelopers/DevSystem"
python3 "$PROJECT_ROOT/DOC_SYSTEM/hooks/post_commit.py" &
EOF

chmod +x "$PROJECT_ROOT/.git/hooks/post-commit"

# Создание hook скриптов
echo "📝 Создание hook обработчиков..."

cat > "$DOC_SYSTEM_DIR/hooks/pre_commit.py" << 'EOF'
#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from validators.validation_agent import ValidationAgent

def main():
    # Получаем список измененных файлов
    result = subprocess.run(['git', 'diff', '--cached', '--name-only'], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        return 0
    
    files = result.stdout.strip().split('\n')
    if not files or files == ['']:
        return 0
    
    # Валидация
    validator = ValidationAgent()
    has_errors = False
    
    for file_path_str in files:
        file_path = Path(file_path_str)
        if file_path.exists():
            results = validator.validate_file(file_path)
            
            for result in results:
                if not result.get('passed', True):
                    if result['level'] in ['error', 'critical']:
                        print(f"❌ {file_path}: {result['message']}")
                        has_errors = True
                    elif result['level'] == 'warning':
                        print(f"⚠️  {file_path}: {result['message']}")
    
    return 1 if has_errors else 0

if __name__ == "__main__":
    sys.exit(main())
EOF

cat > "$DOC_SYSTEM_DIR/hooks/post_commit.py" << 'EOF'
#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.file_monitor import FileMonitor
from generators.doc_generator import DocumentationGenerator

def main():
    try:
        # Обновляем документацию
        monitor = FileMonitor()
        generator = DocumentationGenerator()
        
        # Сканируем проект
        metadata = monitor.scan_directory()
        
        # Генерируем документацию
        project_doc = generator.generate_project_documentation(metadata)
        
        # Сохраняем документацию
        generator.save_documentation(project_doc)
        
        # Обновляем CLAUDE.md
        generator.update_claude_context(project_doc)
        
        print("✅ Документация обновлена")
        
    except Exception as e:
        print(f"⚠️ Ошибка обновления документации: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
EOF

chmod +x "$DOC_SYSTEM_DIR/hooks/pre_commit.py"
chmod +x "$DOC_SYSTEM_DIR/hooks/post_commit.py"

# Запуск первичного сканирования
echo "🔍 Первичное сканирование проекта..."
python3 << 'PYTHON_SCRIPT'
import sys
from pathlib import Path

sys.path.insert(0, "/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/DOC_SYSTEM")

from core.file_monitor import FileMonitor
from analyzers.dependency_analyzer import DependencyAnalyzer
from generators.doc_generator import DocumentationGenerator

try:
    print("Инициализация компонентов...")
    monitor = FileMonitor()
    analyzer = DependencyAnalyzer()
    generator = DocumentationGenerator()
    
    print("Сканирование файлов...")
    metadata = monitor.scan_directory()
    print(f"Найдено {len(metadata)} файлов")
    
    print("Анализ зависимостей...")
    analyzer.build_dependency_graph()
    stats = analyzer.get_statistics()
    
    print(f"Статистика:")
    print(f"  - Всего зависимостей: {stats['total_dependencies']}")
    print(f"  - Orphaned файлов: {stats['orphaned_files']}")
    print(f"  - Циклических зависимостей: {stats['circular_dependencies']}")
    
    print("Генерация документации...")
    project_doc = generator.generate_project_documentation(metadata)
    generator.save_documentation(project_doc)
    generator.update_claude_context(project_doc)
    
    print("✅ Документация сгенерирована успешно")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
PYTHON_SCRIPT

# Запуск API сервера
echo ""
echo "🌐 Запуск API сервера на порту 37777..."
echo "============================================"
echo "API endpoints:"
echo "  GET  http://localhost:37777/api/status       - Статус системы"
echo "  GET  http://localhost:37777/api/files        - Список файлов"
echo "  POST http://localhost:37777/api/analyze      - Анализ проекта"
echo "  POST http://localhost:37777/api/generate-docs - Генерация документации"
echo ""
echo "Нажмите Ctrl+C для остановки"
echo ""

# Запуск API сервера
python3 "$DOC_SYSTEM_DIR/api/server.py"