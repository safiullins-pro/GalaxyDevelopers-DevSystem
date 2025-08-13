#!/bin/bash
# 🌌 GALAXY DEVELOPERS SYSTEM LAUNCHER
# Запуск всей экосистемы

echo "🌌 ===================================="
echo "   GALAXY DEVELOPERS SYSTEM v2.0     "
echo "==================================== 🌌"
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Пути
INTERFACE_PATH="/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/interface"
DOCUMENTS_PATH="/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem"
BACKEND_PATH="$INTERFACE_PATH/backend"

# Функция проверки порта
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Функция остановки процесса на порту
kill_port() {
    if check_port $1; then
        echo -e "${YELLOW}⚠️  Освобождаем порт $1...${NC}"
        lsof -ti:$1 | xargs kill -9 2>/dev/null
        sleep 1
    fi
}

echo -e "${CYAN}🔧 Подготовка окружения...${NC}"

# Проверяем и освобождаем порты
kill_port 8765  # WebSocket
kill_port 8080  # HTTP API
kill_port 8000  # Interface

# Проверяем Docker
echo -e "${BLUE}🐳 Проверка Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker не запущен! Запустите Docker Desktop${NC}"
    exit 1
fi

# Запускаем инфраструктуру DocumentsSystem
echo -e "${PURPLE}📦 Запуск DocumentsSystem инфраструктуры...${NC}"
cd "$DOCUMENTS_PATH"

# Проверяем docker-compose.minimal.yml
if [ -f "docker-compose.minimal.yml" ]; then
    echo -e "${GREEN}✓ Найден docker-compose.minimal.yml${NC}"
    docker-compose -f docker-compose.minimal.yml up -d postgres redis 2>/dev/null
    
    # Ждем запуска
    echo -e "${YELLOW}⏳ Ожидание запуска БД и Redis...${NC}"
    sleep 5
else
    echo -e "${YELLOW}⚠️  docker-compose.minimal.yml не найден, работаем без Docker${NC}"
fi

# Запускаем Pipeline Server
echo -e "${CYAN}🚀 Запуск Pipeline Server...${NC}"
cd "$BACKEND_PATH"

# Устанавливаем зависимости если нужно
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Создание виртуального окружения...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install websockets aiohttp aiohttp-cors redis psycopg2-binary > /dev/null 2>&1
else
    source venv/bin/activate
fi

# Запускаем сервер в фоне
nohup python3 pipeline_server.py > pipeline.log 2>&1 &
PIPELINE_PID=$!
echo -e "${GREEN}✓ Pipeline Server запущен (PID: $PIPELINE_PID)${NC}"

# Запускаем веб-интерфейс
echo -e "${BLUE}🌐 Запуск веб-интерфейса...${NC}"
cd "$INTERFACE_PATH"

# Простой HTTP сервер для интерфейса
python3 -m http.server 8000 > /dev/null 2>&1 &
INTERFACE_PID=$!
echo -e "${GREEN}✓ Интерфейс запущен (PID: $INTERFACE_PID)${NC}"

# Запускаем мониторинг файлов (опционально)
if [ -f "$DOCUMENTS_PATH/file_monitor.py" ]; then
    echo -e "${PURPLE}👁️  Запуск File Monitor...${NC}"
    cd "$DOCUMENTS_PATH"
    nohup python3 file_monitor.py > monitor.log 2>&1 &
    MONITOR_PID=$!
    echo -e "${GREEN}✓ File Monitor запущен (PID: $MONITOR_PID)${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}✨ СИСТЕМА УСПЕШНО ЗАПУЩЕНА! ✨${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}📍 Доступные сервисы:${NC}"
echo -e "   ${BLUE}• Интерфейс:${NC} http://localhost:8000"
echo -e "   ${BLUE}• Pipeline API:${NC} http://localhost:8080"
echo -e "   ${BLUE}• WebSocket:${NC} ws://localhost:8765"
echo ""
echo -e "${YELLOW}💡 Команды управления:${NC}"
echo -e "   • Остановить: ${CYAN}./stop_galaxy.sh${NC}"
echo -e "   • Логи: ${CYAN}tail -f $BACKEND_PATH/pipeline.log${NC}"
echo -e "   • Статус: ${CYAN}ps aux | grep -E 'pipeline_server|http.server'${NC}"
echo ""
echo -e "${PURPLE}🚀 Откройте браузер: ${NC}${GREEN}http://localhost:8000${NC}"
echo ""

# Сохраняем PID'ы для остановки
echo "$PIPELINE_PID" > /tmp/galaxy_pipeline.pid
echo "$INTERFACE_PID" > /tmp/galaxy_interface.pid
[ ! -z "$MONITOR_PID" ] && echo "$MONITOR_PID" > /tmp/galaxy_monitor.pid

# Функция для graceful shutdown
trap cleanup EXIT

cleanup() {
    echo -e "\n${YELLOW}🛑 Остановка системы...${NC}"
    [ -f /tmp/galaxy_pipeline.pid ] && kill $(cat /tmp/galaxy_pipeline.pid) 2>/dev/null
    [ -f /tmp/galaxy_interface.pid ] && kill $(cat /tmp/galaxy_interface.pid) 2>/dev/null
    [ -f /tmp/galaxy_monitor.pid ] && kill $(cat /tmp/galaxy_monitor.pid) 2>/dev/null
    rm -f /tmp/galaxy_*.pid
    echo -e "${GREEN}✓ Система остановлена${NC}"
}

# Ждем Ctrl+C
echo -e "${CYAN}Нажмите Ctrl+C для остановки системы${NC}"
wait