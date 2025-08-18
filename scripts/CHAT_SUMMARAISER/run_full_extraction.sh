#!/bin/bash

# Полный цикл извлечения и интеграции опыта из логов Claude
# Full cycle of experience extraction and integration from Claude logs

echo "🚀 ЗАПУСК ПОЛНОГО ЦИКЛА ИЗВЛЕЧЕНИЯ ОПЫТА"
echo "========================================="

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Директории
SCRIPT_DIR="/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/SCRIPTS/CHAT_SUMMARAISER"
DOCS_DIR="/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/DOCUMENTS"

# 1. Парсинг логов и извлечение диалога
echo -e "${BLUE}📖 Шаг 1: Парсинг логов Claude...${NC}"
cd "$SCRIPT_DIR"
python3 claude_log_parser.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Диалог извлечен успешно${NC}"
else
    echo -e "${YELLOW}⚠️ Ошибка при парсинге логов${NC}"
    exit 1
fi

# 2. Интеграция с документооборотом
echo -e "${BLUE}🔄 Шаг 2: Интеграция с документооборотом...${NC}"
python3 doc_integrator.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Интеграция завершена${NC}"
else
    echo -e "${YELLOW}⚠️ Ошибка при интеграции${NC}"
    exit 1
fi

# 3. Показываем результаты
echo -e "${BLUE}📊 Результаты:${NC}"
echo "----------------------------------------"

# Проверяем созданные файлы
if [ -f "$DOCS_DIR/EXPERIENCE/errors_$(date +%Y%m%d).md" ]; then
    echo -e "${GREEN}✓${NC} Документация ошибок создана"
fi

if [ -f "$DOCS_DIR/EXPERIENCE/discoveries_$(date +%Y%m%d).md" ]; then
    echo -e "${GREEN}✓${NC} Документация открытий создана"
fi

if [ -d "$DOCS_DIR/PATTERNS" ] && [ "$(ls -A $DOCS_DIR/PATTERNS)" ]; then
    echo -e "${GREEN}✓${NC} Паттерны извлечены:"
    ls -1 "$DOCS_DIR/PATTERNS" | sed 's/^/    - /'
fi

if [ -f "$DOCS_DIR/integration_report.md" ]; then
    echo -e "${GREEN}✓${NC} Отчет об интеграции: $DOCS_DIR/integration_report.md"
fi

echo "----------------------------------------"
echo -e "${GREEN}🎉 Все операции завершены успешно!${NC}"

# 4. Предлагаем открыть отчет
echo ""
echo -e "${BLUE}Открыть отчет об интеграции? (y/n)${NC}"
read -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open "$DOCS_DIR/integration_report.md"
fi