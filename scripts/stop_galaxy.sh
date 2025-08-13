#!/bin/bash
# 🛑 GALAXY DEVELOPERS SYSTEM STOPPER

echo "🛑 Остановка Galaxy Developers System..."

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Останавливаем процессы по PID
if [ -f /tmp/galaxy_pipeline.pid ]; then
    PID=$(cat /tmp/galaxy_pipeline.pid)
    kill $PID 2>/dev/null && echo -e "${GREEN}✓ Pipeline Server остановлен${NC}"
    rm -f /tmp/galaxy_pipeline.pid
fi

if [ -f /tmp/galaxy_interface.pid ]; then
    PID=$(cat /tmp/galaxy_interface.pid)
    kill $PID 2>/dev/null && echo -e "${GREEN}✓ Интерфейс остановлен${NC}"
    rm -f /tmp/galaxy_interface.pid
fi

if [ -f /tmp/galaxy_monitor.pid ]; then
    PID=$(cat /tmp/galaxy_monitor.pid)
    kill $PID 2>/dev/null && echo -e "${GREEN}✓ File Monitor остановлен${NC}"
    rm -f /tmp/galaxy_monitor.pid
fi

# Останавливаем Docker контейнеры
echo -e "${YELLOW}🐳 Остановка Docker контейнеров...${NC}"
cd /Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem
if [ -f "docker-compose.minimal.yml" ]; then
    docker-compose -f docker-compose.minimal.yml down 2>/dev/null
fi

echo -e "${GREEN}✅ Система полностью остановлена${NC}"