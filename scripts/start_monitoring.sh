#!/bin/bash

# GALAXY MONITORING - START SCRIPT
# Скрипт запуска системы мониторинга

echo "╔════════════════════════════════════════╗"
echo "║    GALAXY MONITORING SYSTEM            ║"
echo "║    Starting all components...          ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Переходим в директорию проекта
cd /Volumes/Z7S/development/GalaxyDevelopers/DevSystem

# Проверяем, не запущен ли уже сервер
if lsof -Pi :8765 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  WebSocket сервер уже запущен на порту 8765"
    echo "   Используйте ./stop_monitoring.sh для остановки"
    exit 1
fi

if lsof -Pi :8766 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  API сервер уже запущен на порту 8766"
    echo "   Используйте ./stop_monitoring.sh для остановки"
    exit 1
fi

# Создаем необходимые директории
echo "📁 Проверка директорий..."
mkdir -p logs
mkdir -p backups
mkdir -p memory
mkdir -p docs

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден!"
    exit 1
fi

# Проверяем зависимости
echo "📦 Проверка зависимостей..."
python3 -c "import aiohttp" 2>/dev/null || {
    echo "Installing aiohttp..."
    pip3 install aiohttp aiohttp-cors
}

python3 -c "import websockets" 2>/dev/null || {
    echo "Installing websockets..."
    pip3 install websockets
}

python3 -c "import watchdog" 2>/dev/null || {
    echo "Installing watchdog..."
    pip3 install watchdog
}

python3 -c "import prometheus_client" 2>/dev/null || {
    echo "Installing prometheus_client..."
    pip3 install prometheus-client
}

python3 -c "import bandit" 2>/dev/null || {
    echo "Installing bandit..."
    pip3 install bandit
}

python3 -c "import pylint" 2>/dev/null || {
    echo "Installing pylint..."
    pip3 install pylint
}

# Запускаем сервер мониторинга
echo ""
echo "🚀 Запуск сервера мониторинга..."

# Используем nohup для фонового запуска
nohup python3 monitoring_server_fixed.py > logs/monitoring.log 2>&1 &

# Сохраняем PID
echo $! > monitoring.pid

# Ждем запуска
sleep 3

# Проверяем статус
if lsof -Pi :8765 -sTCP:LISTEN -t >/dev/null && lsof -Pi :8766 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Сервер мониторинга успешно запущен!"
    echo ""
    echo "📡 WebSocket: ws://localhost:8765"
    echo "🌐 REST API:  http://localhost:8766"
    echo "📊 Dashboard: file://$PWD/monitoring_dashboard.html"
    echo "🖥️  Interface: file://$PWD/interface/index.html"
    echo ""
    echo "📝 Логи: tail -f logs/monitoring.log"
    echo "🛑 Остановка: ./stop_monitoring.sh"
    echo ""
    
    # Открываем дашборд в браузере
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open monitoring_dashboard.html
    fi
else
    echo "❌ Ошибка запуска сервера!"
    echo "   Проверьте логи: cat logs/monitoring.log"
    exit 1
fi