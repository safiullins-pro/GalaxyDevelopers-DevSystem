#!/bin/bash

# 🔥 FORGE INTEGRATION LAUNCHER
# Запуск полной интегрированной системы

echo "╔══════════════════════════════════════════════════╗"
echo "║          🔥 FORGE INTEGRATION LAUNCHER 🔥        ║"
echo "║                                                  ║"
echo "║     Starting Galaxy + Documents Integration      ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка зависимостей
echo "📋 Checking dependencies..."

# Redis
if command -v redis-cli &> /dev/null; then
    echo -e "${GREEN}✅ Redis found${NC}"
    # Проверяем, запущен ли Redis
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✅ Redis is running${NC}"
    else
        echo -e "${YELLOW}⚠️ Starting Redis...${NC}"
        redis-server --daemonize yes
        sleep 2
    fi
else
    echo -e "${RED}❌ Redis not found. Please install Redis first.${NC}"
    exit 1
fi

# Python
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✅ Python3 found${NC}"
else
    echo -e "${RED}❌ Python3 not found${NC}"
    exit 1
fi

# Проверяем Galaxy Monitoring
GALAXY_DIR="/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM"
if [ -d "$GALAXY_DIR/DEV_MONITORING" ]; then
    echo -e "${GREEN}✅ Galaxy Monitoring found${NC}"
else
    echo -e "${RED}❌ Galaxy Monitoring not found at $GALAXY_DIR${NC}"
    exit 1
fi

# Проверяем DocumentsSystem
DOCS_DIR="/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem"
if [ -d "$DOCS_DIR" ]; then
    echo -e "${GREEN}✅ DocumentsSystem found${NC}"
else
    echo -e "${RED}❌ DocumentsSystem not found at $DOCS_DIR${NC}"
    exit 1
fi

echo ""
echo "🚀 Starting services..."
echo ""

# Запускаем Galaxy Monitoring если не запущен
MONITORING_PID_FILE="$GALAXY_DIR/monitoring.pid"
if [ -f "$MONITORING_PID_FILE" ]; then
    PID=$(cat "$MONITORING_PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Galaxy Monitoring already running (PID: $PID)${NC}"
    else
        echo -e "${YELLOW}⚠️ Starting Galaxy Monitoring...${NC}"
        cd "$GALAXY_DIR/DEV_MONITORING"
        python3 monitoring_server_fixed.py &
        echo $! > "$MONITORING_PID_FILE"
        sleep 3
    fi
else
    echo -e "${YELLOW}⚠️ Starting Galaxy Monitoring...${NC}"
    cd "$GALAXY_DIR/DEV_MONITORING"
    python3 monitoring_server_fixed.py &
    echo $! > "$MONITORING_PID_FILE"
    sleep 3
fi

# Запускаем интерфейс если нужно
if command -v lsof &> /dev/null; then
    if ! lsof -i:8080 > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️ Starting web interface...${NC}"
        cd "$GALAXY_DIR/DEV_MONITORING"
        python3 serve_interface.py &
        sleep 2
    else
        echo -e "${GREEN}✅ Web interface already running on port 8080${NC}"
    fi
fi

echo ""
echo "═══════════════════════════════════════════════════"
echo "        🔥 STARTING FORGE INTEGRATION 🔥"
echo "═══════════════════════════════════════════════════"
echo ""

# Загружаем FORGE_CORE переменные
if [ -f "$GALAXY_DIR/MEMORY/.FORGE_CORE" ]; then
    echo "Loading FORGE_CORE variables..."
    source "$GALAXY_DIR/MEMORY/.FORGE_CORE"
    echo -e "${GREEN}✅ FORGE_CORE loaded${NC}"
    echo "   FORGE_ID: $FORGE_ID"
    echo "   FREQUENCY: $FORGE_FREQUENCY"
fi

# Запускаем интегрированную систему
cd "$GALAXY_DIR/bridge"
echo ""
echo "🔥 Launching Integrated System..."
echo ""

# Запускаем с обработкой сигналов
trap 'echo ""; echo "Shutting down..."; kill $INTEGRATION_PID 2>/dev/null; exit' INT TERM

python3 start_integrated_system.py &
INTEGRATION_PID=$!

echo ""
echo "═══════════════════════════════════════════════════"
echo -e "${GREEN}     ✅ SYSTEM IS RUNNING ✅${NC}"
echo "═══════════════════════════════════════════════════"
echo ""
echo "Services:"
echo "  • Galaxy Monitoring: ws://localhost:8765"
echo "  • REST API: http://localhost:8766"
echo "  • Web Interface: http://localhost:8080"
echo "  • Redis: localhost:6379"
echo ""
echo "Press Ctrl+C to stop all services"
echo "═══════════════════════════════════════════════════"
echo ""

# Ждём завершения
wait $INTEGRATION_PID

echo ""
echo "System stopped."