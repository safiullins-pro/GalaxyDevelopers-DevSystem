#!/bin/bash

# Скрипт остановки всех компонентов системы
# Stop all system components

echo "🛑 ОСТАНОВКА СИСТЕМЫ GALAXY DEVELOPERS"
echo "======================================"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Останавливаем процессы
echo "Останавливаем процессы..."

# Monitoring server
if pgrep -f "monitoring_server_fixed.py" > /dev/null; then
    pkill -f "monitoring_server_fixed.py"
    echo -e "${GREEN}✓${NC} Monitoring server остановлен"
else
    echo "  Monitoring server не запущен"
fi

# Experience API
if pgrep -f "experience_api.py" > /dev/null; then
    pkill -f "experience_api.py"
    echo -e "${GREEN}✓${NC} Experience API остановлен"
else
    echo "  Experience API не запущен"
fi

# Pipeline server
if pgrep -f "pipeline_server.py" > /dev/null; then
    pkill -f "pipeline_server.py"
    echo -e "${GREEN}✓${NC} Pipeline server остановлен"
else
    echo "  Pipeline server не запущен"
fi

# Очищаем PID файлы
rm -f /tmp/galaxy_monitoring.pid 2>/dev/null
rm -f /tmp/galaxy_experience.pid 2>/dev/null

echo ""
echo -e "${GREEN}✅ Все компоненты остановлены${NC}"
echo ""