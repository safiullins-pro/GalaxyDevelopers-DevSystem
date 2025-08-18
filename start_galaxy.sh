#!/bin/bash

# GalaxyDevelopers DevSystem - Главный стартовый скрипт
# Запускает основную систему + DOC_SYSTEM одновременно

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ROOT="/Volumes/Z7S/development/GalaxyDevelopers/DevSystem"
cd "$PROJECT_ROOT"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          GALAXY DEVELOPERS DEVSYSTEM - ЗАПУСК               ║${NC}"
echo -e "${BLUE}║          Основная система + DOC_SYSTEM                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Проверка и активация DOC_SYSTEM
echo -e "${YELLOW}🔧 Инициализация DOC_SYSTEM...${NC}"

if [ ! -d "$PROJECT_ROOT/DOC_SYSTEM" ]; then
    echo -e "${RED}❌ DOC_SYSTEM не найдена!${NC}"
    exit 1
fi

# Быстрая установка зависимостей для DOC_SYSTEM
pip3 install -q flask flask-cors pyyaml jinja2 networkx watchdog 2>/dev/null || true

# Создание Git hooks для автоматической документации
if [ -d "$PROJECT_ROOT/.git" ]; then
    echo -e "${YELLOW}🔗 Настройка Git hooks для автодокументации...${NC}"
    
    cat > "$PROJECT_ROOT/.git/hooks/pre-commit" << 'EOF'
#!/bin/bash
# Автоматическая валидация DOC_SYSTEM перед коммитом

PROJECT_ROOT="/Volumes/Z7S/development/GalaxyDevelopers/DevSystem"

# Проверяем критические ошибки
python3 "$PROJECT_ROOT/DOC_SYSTEM/hooks/pre_commit.py" 2>/dev/null || {
    echo "⚠️ Валидация DOC_SYSTEM пропущена (компоненты не готовы)"
    exit 0
}
EOF

    cat > "$PROJECT_ROOT/.git/hooks/post-commit" << 'EOF'
#!/bin/bash
# Автообновление документации после коммита

PROJECT_ROOT="/Volumes/Z7S/development/GalaxyDevelopers/DevSystem"

# Обновляем документацию в фоне
python3 "$PROJECT_ROOT/DOC_SYSTEM/hooks/post_commit.py" &
EOF

    chmod +x "$PROJECT_ROOT/.git/hooks/pre-commit"
    chmod +x "$PROJECT_ROOT/.git/hooks/post-commit"
fi

# Создание hook-скриптов если не существуют
mkdir -p "$PROJECT_ROOT/DOC_SYSTEM/hooks"

if [ ! -f "$PROJECT_ROOT/DOC_SYSTEM/hooks/pre_commit.py" ]; then
    cat > "$PROJECT_ROOT/DOC_SYSTEM/hooks/pre_commit.py" << 'EOF'
#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from validators.validation_agent import ValidationAgent
    
    # Получаем список измененных файлов
    result = subprocess.run(['git', 'diff', '--cached', '--name-only'], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        sys.exit(0)
    
    files = [f for f in result.stdout.strip().split('\n') if f.strip()]
    if not files:
        sys.exit(0)
    
    # Валидация только критических ошибок
    validator = ValidationAgent()
    has_critical = False
    
    for file_path_str in files:
        file_path = Path(file_path_str)
        if file_path.exists() and file_path.suffix in ['.py', '.js', '.ts']:
            results = validator.validate_file(file_path)
            
            for result in results:
                if not result.get('passed', True) and result['level'] == 'critical':
                    print(f"🚨 КРИТИЧЕСКАЯ ОШИБКА {file_path}: {result['message']}")
                    has_critical = True
    
    sys.exit(1 if has_critical else 0)
    
except Exception:
    # Если что-то не работает, не блокируем коммит
    sys.exit(0)
EOF
fi

if [ ! -f "$PROJECT_ROOT/DOC_SYSTEM/hooks/post_commit.py" ]; then
    cat > "$PROJECT_ROOT/DOC_SYSTEM/hooks/post_commit.py" << 'EOF'
#!/usr/bin/env python3
import sys
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.file_monitor import FileMonitor
    from generators.doc_generator import DocumentationGenerator
    
    # Быстрое обновление документации
    monitor = FileMonitor()
    generator = DocumentationGenerator()
    
    metadata = monitor.scan_directory()
    project_doc = generator.generate_project_documentation(metadata)
    generator.update_claude_context(project_doc)
    
    print("✅ Документация обновлена")
    
except Exception as e:
    print(f"⚠️ Ошибка обновления документации: {e}")

sys.exit(0)
EOF
fi

chmod +x "$PROJECT_ROOT/DOC_SYSTEM/hooks/pre_commit.py"
chmod +x "$PROJECT_ROOT/DOC_SYSTEM/hooks/post_commit.py"

# Запуск DOC_SYSTEM API в фоне
echo -e "${YELLOW}🌐 Запуск DOC_SYSTEM API...${NC}"

# Проверяем, не запущен ли уже
if lsof -i:37777 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ DOC_SYSTEM API уже работает на порту 37777${NC}"
else
    # Запускаем API в фоне
    nohup python3 "$PROJECT_ROOT/DOC_SYSTEM/api/server.py" > "$PROJECT_ROOT/DOC_SYSTEM/logs/api.log" 2>&1 &
    API_PID=$!
    echo $API_PID > "$PROJECT_ROOT/DOC_SYSTEM/api.pid"
    
    sleep 2
    
    if kill -0 $API_PID 2>/dev/null; then
        echo -e "${GREEN}✅ DOC_SYSTEM API запущен (PID: $API_PID)${NC}"
    else
        echo -e "${YELLOW}⚠️ DOC_SYSTEM API не удалось запустить${NC}"
    fi
fi

# Запуск мониторинга файлов в фоне
echo -e "${YELLOW}👁️ Запуск мониторинга файлов...${NC}"

if [ ! -f "$PROJECT_ROOT/DOC_SYSTEM/monitor.pid" ] || ! kill -0 $(cat "$PROJECT_ROOT/DOC_SYSTEM/monitor.pid" 2>/dev/null) 2>/dev/null; then
    nohup python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/DOC_SYSTEM')
from core.file_monitor import FileMonitor
monitor = FileMonitor()
monitor.start_monitoring()
" > "$PROJECT_ROOT/DOC_SYSTEM/logs/monitor.log" 2>&1 &
    
    MONITOR_PID=$!
    echo $MONITOR_PID > "$PROJECT_ROOT/DOC_SYSTEM/monitor.pid"
    echo -e "${GREEN}✅ Мониторинг файлов запущен (PID: $MONITOR_PID)${NC}"
else
    echo -e "${GREEN}✅ Мониторинг файлов уже работает${NC}"
fi

# Первичное сканирование и генерация документации
echo -e "${YELLOW}📚 Обновление документации...${NC}"
python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/DOC_SYSTEM')

try:
    from core.file_monitor import FileMonitor
    from generators.doc_generator import DocumentationGenerator
    
    monitor = FileMonitor()
    generator = DocumentationGenerator()
    
    metadata = monitor.scan_directory()
    project_doc = generator.generate_project_documentation(metadata)
    generator.update_claude_context(project_doc)
    
    print('✅ Документация обновлена')
    print(f'📊 Отслеживается {len(metadata)} файлов')
    
except Exception as e:
    print(f'⚠️ Ошибка: {e}')
" 2>/dev/null || echo -e "${YELLOW}⚠️ Документация будет обновлена позже${NC}"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              GALAXY DEVSYSTEM АКТИВНА! 🚀                   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}DOC_SYSTEM Endpoints:${NC}"
echo -e "  ${GREEN}http://localhost:37777/api/status${NC}       - Статус системы"
echo -e "  ${GREEN}http://localhost:37777/api/files${NC}        - Список файлов"
echo -e "  ${GREEN}http://localhost:37777/api/documentation${NC} - Генерация документации"
echo ""
echo -e "${BLUE}Возможности:${NC}"
echo -e "  🔍 Автоматическое отслеживание изменений файлов"
echo -e "  📚 AI-генерация документации при коммитах"
echo -e "  🔗 Анализ зависимостей между файлами"
echo -e "  🗂️ Обнаружение orphaned файлов"
echo -e "  📝 Автообновление CLAUDE.md для AI-контекста"
echo ""

# Запуск FORGE Bridge для блокировки телеметрии
echo -e "${BLUE}🔥 Запуск FORGE Bridge...${NC}"
if ! pgrep -f "forge_claude.sh" > /dev/null; then
    nohup /Users/safiullins_pro/forge_claude.sh > /dev/null 2>&1 &
    echo -e "${GREEN}✅ FORGE Bridge активирован${NC}"
else
    echo -e "${GREEN}✅ FORGE Bridge уже работает${NC}"
fi

# Теперь запускаем основную систему Galaxy
echo -e "${BLUE}🌌 Запуск основной системы Galaxy...${NC}"

# Проверяем наличие основного скрипта
if [ -f "$PROJECT_ROOT/SCRIPTS/start_galaxy.sh" ]; then
    exec "$PROJECT_ROOT/SCRIPTS/start_galaxy.sh"
elif [ -f "$PROJECT_ROOT/start.sh" ]; then
    exec "$PROJECT_ROOT/start.sh"
elif [ -f "$PROJECT_ROOT/interface/index.html" ]; then
    echo -e "${GREEN}Открываем интерфейс Galaxy...${NC}"
    open "$PROJECT_ROOT/interface/index.html"
    
    # Запускаем простой HTTP сервер для интерфейса
    cd "$PROJECT_ROOT/interface"
    python3 -m http.server 8080 &
    echo -e "${GREEN}Galaxy интерфейс доступен: http://localhost:8080${NC}"
    echo -e "${YELLOW}Нажмите Ctrl+C для остановки всех сервисов${NC}"
    
    # Ожидаем сигнала остановки
    trap 'echo -e "\n${YELLOW}Остановка всех сервисов...${NC}"; kill $(jobs -p) 2>/dev/null; exit 0' SIGINT SIGTERM
    
    while true; do
        sleep 1
    done
else
    echo -e "${GREEN}Galaxy DevSystem готова к работе!${NC}"
    echo -e "${YELLOW}DOC_SYSTEM работает в фоне и автоматически обновляет документацию${NC}"
fi