#!/bin/bash

# GALAXY MONITORING - STATUS SCRIPT
# Скрипт проверки статуса системы мониторинга

echo "╔════════════════════════════════════════╗"
echo "║    GALAXY MONITORING SYSTEM            ║"
echo "║    System Status Check                 ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка WebSocket сервера
echo "🔍 Проверка компонентов:"
echo ""

# WebSocket
if lsof -Pi :8765 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "📡 WebSocket Server: ${GREEN}✅ ONLINE${NC} (port 8765)"
    WS_PID=$(lsof -ti :8765)
    echo "   PID: $WS_PID"
else
    echo -e "📡 WebSocket Server: ${RED}❌ OFFLINE${NC}"
fi

# REST API
if lsof -Pi :8766 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "🌐 REST API Server:  ${GREEN}✅ ONLINE${NC} (port 8766)"
    API_PID=$(lsof -ti :8766)
    echo "   PID: $API_PID"
else
    echo -e "🌐 REST API Server:  ${RED}❌ OFFLINE${NC}"
fi

echo ""
echo "📊 Детальная информация:"
echo ""

# Проверка через API
if lsof -Pi :8766 -sTCP:LISTEN -t >/dev/null ; then
    # Получаем статус через API
    STATUS=$(curl -s http://localhost:8766/api/monitoring/status 2>/dev/null)
    
    if [ ! -z "$STATUS" ]; then
        # Парсим JSON (если установлен jq)
        if command -v jq &> /dev/null; then
            echo "WebSocket клиенты: $(echo $STATUS | jq -r '.websocket_clients')"
            echo "File Observer:     $(echo $STATUS | jq -r '.file_observer_active' | sed 's/true/✅ Активен/;s/false/❌ Неактивен/')"
            echo "Отслеживаемые пути:"
            echo $STATUS | jq -r '.watched_paths[]' | sed 's/^/   - /'
            echo "Последние изменения: $(echo $STATUS | jq -r '.recent_changes')"
        else
            echo "$STATUS" | python3 -m json.tool 2>/dev/null || echo "   Не удалось получить детальную информацию"
        fi
    fi
else
    echo "   API сервер недоступен"
fi

echo ""
echo "📝 Последние логи:"
echo ""

# Показываем последние логи
if [ -f logs/monitoring.log ]; then
    tail -n 10 logs/monitoring.log | sed 's/^/   /'
else
    echo "   Лог файл не найден"
fi

echo ""
echo "🎛️  Управление:"
echo "   Запуск:      ./start_monitoring.sh"
echo "   Остановка:   ./stop_monitoring.sh"
echo "   Перезапуск:  ./restart_monitoring.sh"
echo "   Логи:        tail -f logs/monitoring.log"
echo ""

# Проверка PID файла
if [ -f monitoring.pid ]; then
    PID=$(cat monitoring.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "📌 PID файл: ${GREEN}✅ Валидный${NC} (PID: $PID)"
    else
        echo -e "📌 PID файл: ${YELLOW}⚠️  Устаревший${NC} (процесс не найден)"
    fi
else
    echo "📌 PID файл: Не найден"
fi