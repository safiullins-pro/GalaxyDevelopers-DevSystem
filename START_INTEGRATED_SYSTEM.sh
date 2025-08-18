#!/bin/bash

# ГЛАВНЫЙ СКРИПТ ЗАПУСКА ИНТЕГРИРОВАННОЙ СИСТЕМЫ
# Main script to start integrated monitoring + experience system

echo "🚀 GALAXY DEVELOPERS - INTEGRATED SYSTEM STARTUP"
echo "================================================"
echo ""

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Базовая директория
BASE_DIR="/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM"
cd "$BASE_DIR"

# 1. Проверка Python и зависимостей
echo -e "${BLUE}[1/5] Проверка зависимостей...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 не найден${NC}"
    exit 1
fi

# Проверяем Flask
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️ Flask не установлен. Устанавливаем...${NC}"
    pip3 install flask flask-cors
fi

echo -e "${GREEN}✅ Зависимости проверены${NC}"

# 2. Останавливаем старые процессы
echo -e "${BLUE}[2/5] Очистка старых процессов...${NC}"
pkill -f "monitoring_server_fixed.py" 2>/dev/null
pkill -f "experience_api.py" 2>/dev/null
pkill -f "pipeline_server.py" 2>/dev/null
sleep 2
echo -e "${GREEN}✅ Старые процессы остановлены${NC}"

# 3. Запуск основного сервера мониторинга
echo -e "${BLUE}[3/5] Запуск сервера мониторинга...${NC}"
python3 DEV_MONITORING/monitoring_server_fixed.py > logs/monitoring.log 2>&1 &
MONITORING_PID=$!
sleep 2

if ps -p $MONITORING_PID > /dev/null; then
    echo -e "${GREEN}✅ Сервер мониторинга запущен (PID: $MONITORING_PID)${NC}"
else
    echo -e "${RED}❌ Ошибка запуска сервера мониторинга${NC}"
    exit 1
fi

# 4. Запуск File Protection System
echo -e "${BLUE}[4/5] Запуск File Protection System...${NC}"
python3 DEV_MONITORING/file_protection_system.py > logs/file_protection.log 2>&1 &
PROTECTION_PID=$!
sleep 2

if ps -p $PROTECTION_PID > /dev/null; then
    echo -e "${GREEN}✅ File Protection System запущен (PID: $PROTECTION_PID)${NC}"
else
    echo -e "${YELLOW}⚠️ File Protection не запустился (необязательный)${NC}"
fi

# 5. Проверка доступности сервисов
echo -e "${BLUE}[5/5] Проверка доступности сервисов...${NC}"

# Проверяем мониторинг
curl -s http://localhost:3005/api/status > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Monitoring API: http://localhost:3005${NC}"
else
    echo -e "${YELLOW}⚠️ Monitoring API недоступен${NC}"
fi

# Проверяем Experience API
curl -s http://localhost:5555/api/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Experience API: http://localhost:5555${NC}"
else
    echo -e "${YELLOW}⚠️ Experience API недоступен${NC}"
fi

# Сохраняем PID'ы
echo "$MONITORING_PID" > /tmp/galaxy_monitoring.pid
echo "$EXPERIENCE_PID" > /tmp/galaxy_experience.pid

# Финальный отчет
echo ""
echo "================================================"
echo -e "${GREEN}🎉 СИСТЕМА УСПЕШНО ЗАПУЩЕНА!${NC}"
echo "================================================"
echo ""
echo "📊 Доступные сервисы:"
echo "  • Мониторинг: http://localhost:3005"
echo "  • Experience API: http://localhost:5555/api/experience"
echo "  • Паттерны: http://localhost:5555/api/patterns"
echo ""
echo "📁 Расположение данных:"
echo "  • Опыт: $BASE_DIR/DOCUMENTS/EXPERIENCE/"
echo "  • Паттерны: $BASE_DIR/DOCUMENTS/PATTERNS/"
echo "  • Логи: $BASE_DIR/logs/"
echo ""
echo "🛑 Для остановки используйте:"
echo "  ./SCRIPTS/stop_all.sh"
echo ""
echo -e "${BLUE}Открыть интерфейс в браузере? (y/n)${NC}"
read -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open http://localhost:3005
fi