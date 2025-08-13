#!/bin/bash

# GALAXY MONITORING - STOP SCRIPT
# Скрипт остановки системы мониторинга

echo "╔════════════════════════════════════════╗"
echo "║    GALAXY MONITORING SYSTEM            ║"
echo "║    Stopping all components...          ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Переходим в директорию проекта
cd /Volumes/Z7S/development/GalaxyDevelopers/DevSystem

# Проверяем PID файл
if [ -f monitoring.pid ]; then
    PID=$(cat monitoring.pid)
    echo "🛑 Останавливаем процесс с PID: $PID"
    
    # Пытаемся остановить процесс
    if kill $PID 2>/dev/null; then
        echo "✅ Процесс остановлен"
        rm monitoring.pid
    else
        echo "⚠️  Процесс не найден, очищаем PID файл"
        rm monitoring.pid
    fi
else
    echo "⚠️  PID файл не найден"
fi

# Останавливаем все процессы на портах
echo ""
echo "🔍 Проверка портов..."

# WebSocket порт 8765
if lsof -Pi :8765 -sTCP:LISTEN -t >/dev/null ; then
    echo "   Останавливаем WebSocket сервер (порт 8765)..."
    lsof -ti :8765 | xargs kill -9 2>/dev/null
fi

# API порт 8766
if lsof -Pi :8766 -sTCP:LISTEN -t >/dev/null ; then
    echo "   Останавливаем API сервер (порт 8766)..."
    lsof -ti :8766 | xargs kill -9 2>/dev/null
fi

# Убиваем все процессы monitoring_server
pkill -f "monitoring_server" 2>/dev/null

echo ""
echo "✅ Все компоненты мониторинга остановлены"
echo ""
echo "Для повторного запуска используйте: ./start_monitoring.sh"