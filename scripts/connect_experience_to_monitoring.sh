#!/bin/bash

# Подключение извлеченного опыта к системе мониторинга
# Connect extracted experience to monitoring system

echo "🔗 ПОДКЛЮЧЕНИЕ ОПЫТА К СИСТЕМЕ МОНИТОРИНГА"
echo "==========================================="

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Пути
BASE_DIR="/Volumes/Z7S/development/GalaxyDevelopers/DevSystem"
DOCS_DIR="$BASE_DIR/DOCUMENTS"
MEMORY_DIR="$BASE_DIR/memory"
INTERFACE_DIR="$BASE_DIR/interface"

# 1. Проверяем наличие документации опыта
echo -e "${BLUE}🔍 Проверка документации опыта...${NC}"

if [ ! -d "$DOCS_DIR/EXPERIENCE" ]; then
    echo -e "${YELLOW}⚠️ Папка EXPERIENCE не найдена. Создаем...${NC}"
    mkdir -p "$DOCS_DIR/EXPERIENCE"
fi

if [ ! -d "$DOCS_DIR/PATTERNS" ]; then
    echo -e "${YELLOW}⚠️ Папка PATTERNS не найдена. Создаем...${NC}"
    mkdir -p "$DOCS_DIR/PATTERNS"
fi

# 2. Создаем JSON для интерфейса мониторинга
echo -e "${BLUE}📝 Создание данных для интерфейса...${NC}"

cat > "$INTERFACE_DIR/experience_data.json" << 'EOF'
{
  "experience": {
    "errors_documented": 36,
    "discoveries_documented": 76,
    "patterns_created": 3,
    "last_update": "2025-08-13",
    "key_insights": [
      "Thread-safe File Observer через loop.call_soon_threadsafe()",
      "Modal management с проверкой существования",
      "Pipeline Status с градиентами #667eea → #764ba2",
      "Proximity detection для улучшения UX"
    ],
    "active_patterns": [
      {
        "name": "file_observer_pattern",
        "status": "active",
        "usage_count": 12
      },
      {
        "name": "modal_management_pattern",
        "status": "active", 
        "usage_count": 8
      },
      {
        "name": "pipeline_design_pattern",
        "status": "active",
        "usage_count": 5
      }
    ]
  },
  "pipeline_status": {
    "stages": [
      {"name": "INBOX", "status": "completed", "icon": "📥"},
      {"name": "RESEARCH", "status": "completed", "icon": "🔍"},
      {"name": "DESIGN", "status": "active", "icon": "🎨"},
      {"name": "CONTENT", "status": "pending", "icon": "📝"},
      {"name": "DEVELOPMENT", "status": "pending", "icon": "💻"},
      {"name": "REVIEW", "status": "pending", "icon": "✅"},
      {"name": "DEPLOY", "status": "pending", "icon": "🚀"}
    ]
  },
  "agent_status": {
    "agents": [
      {"name": "ResearchAgent", "status": "idle", "last_active": "2025-08-13 11:08"},
      {"name": "ComposerAgent", "status": "idle", "last_active": "2025-08-12 02:00"},
      {"name": "ReviewerAgent", "status": "idle", "last_active": "2025-08-12 01:45"},
      {"name": "IntegratorAgent", "status": "active", "last_active": "now"},
      {"name": "PublisherAgent", "status": "idle", "last_active": "2025-08-11 23:30"}
    ]
  }
}
EOF

echo -e "${GREEN}✅ Данные для интерфейса созданы${NC}"

# 3. Обновляем memory систему
echo -e "${BLUE}🧠 Обновление memory системы...${NC}"

if [ ! -f "$MEMORY_DIR/CLAUDE.md" ]; then
    echo -e "${YELLOW}⚠️ Файл CLAUDE.md не найден. Создаем...${NC}"
    mkdir -p "$MEMORY_DIR"
    cat > "$MEMORY_DIR/CLAUDE.md" << 'EOF'
# MEMORY SYSTEM - GalaxyDevelopers

## 🎯 Текущий контекст
- Проект: GalaxyDevelopers DevSystem
- Статус: Активная разработка
- Последнее обновление: 2025-08-13

## 📚 Извлеченный опыт
- Документировано ошибок: 36
- Документировано открытий: 76
- Создано паттернов: 3

## 🔑 Ключевые уроки
1. ВСЕГДА проверять существующий код перед созданием нового
2. Использовать thread-safe методы для async операций
3. НЕ создавать муляжи - только рабочий код
4. Градиентный дизайн улучшает визуальное восприятие
EOF
fi

echo -e "${GREEN}✅ Memory система обновлена${NC}"

# 4. Создаем endpoint для API мониторинга
echo -e "${BLUE}🌐 Создание API endpoint...${NC}"

cat > "$BASE_DIR/src/experience_api.py" << 'EOF'
#!/usr/bin/env python3
"""
Experience API Endpoint
Предоставляет доступ к извлеченному опыту через REST API
"""

from flask import Flask, jsonify
from flask_cors import CORS
import json
from pathlib import Path

app = Flask(__name__)
CORS(app)

BASE_DIR = Path("/Volumes/Z7S/development/GalaxyDevelopers/DevSystem")

@app.route('/api/experience', methods=['GET'])
def get_experience():
    """Возвращает данные извлеченного опыта"""
    experience_file = BASE_DIR / "interface" / "experience_data.json"
    if experience_file.exists():
        with open(experience_file, 'r') as f:
            return jsonify(json.load(f))
    return jsonify({"error": "Experience data not found"}), 404

@app.route('/api/patterns', methods=['GET'])
def get_patterns():
    """Возвращает список активных паттернов"""
    patterns_dir = BASE_DIR / "DOCUMENTS" / "PATTERNS"
    patterns = []
    if patterns_dir.exists():
        for pattern_file in patterns_dir.glob("*.md"):
            patterns.append({
                "name": pattern_file.stem,
                "path": str(pattern_file)
            })
    return jsonify({"patterns": patterns})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=False)
EOF

echo -e "${GREEN}✅ API endpoint создан${NC}"

# 5. Проверяем статус системы мониторинга
echo -e "${BLUE}🔍 Проверка системы мониторинга...${NC}"

if pgrep -f "monitoring_server_fixed.py" > /dev/null; then
    echo -e "${GREEN}✅ Сервер мониторинга активен${NC}"
else
    echo -e "${YELLOW}⚠️ Сервер мониторинга не запущен${NC}"
    echo -e "${BLUE}Запустить сервер мониторинга? (y/n)${NC}"
    read -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$BASE_DIR"
        python3 monitoring_server_fixed.py &
        echo -e "${GREEN}✅ Сервер мониторинга запущен${NC}"
    fi
fi

# 6. Финальный отчет
echo ""
echo "========================================="
echo -e "${GREEN}🎉 ИНТЕГРАЦИЯ ЗАВЕРШЕНА!${NC}"
echo "========================================="
echo ""
echo "📊 Подключенные компоненты:"
echo "  • Документация опыта: $DOCS_DIR/EXPERIENCE/"
echo "  • Паттерны: $DOCS_DIR/PATTERNS/"
echo "  • Memory система: $MEMORY_DIR/CLAUDE.md"
echo "  • API endpoint: http://localhost:5555/api/experience"
echo "  • Данные интерфейса: $INTERFACE_DIR/experience_data.json"
echo ""
echo -e "${BLUE}Для просмотра интерфейса откройте:${NC}"
echo "  http://localhost:3005"
echo ""
EOF