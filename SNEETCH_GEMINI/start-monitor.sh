#!/bin/bash
# Скрипт для запуска мониторинга в фоне

MONITOR_SCRIPT="$HOME/Scripts/gemini-triggers/monitor-specific.sh"
PID_FILE="$HOME/.file-monitor.pid"

# Функция для остановки существующего мониторинга
stop_monitor() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "⏹️  Останавливаю существующий мониторинг (PID: $PID)"
            kill $PID
            pkill -P $PID  # Убиваем дочерние процессы
        fi
        rm "$PID_FILE"
    fi
}

# Функция для запуска мониторинга
start_monitor() {
    echo "🚀 Запускаю файловый мониторинг для Claude Code..."
    nohup "$MONITOR_SCRIPT" > /dev/null 2>&1 &
    echo $! > "$PID_FILE"
    echo "✅ Мониторинг запущен (PID: $(cat "$PID_FILE"))"
    echo "📝 Для остановки используйте: $0 stop"
}

# Обработка параметров
case "$1" in
    start)
        stop_monitor
        start_monitor
        ;;
    stop)
        stop_monitor
        echo "✅ Мониторинг остановлен"
        ;;
    restart)
        stop_monitor
        start_monitor
        ;;
    status)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                echo "✅ Мониторинг активен (PID: $PID)"
            else
                echo "❌ Мониторинг не активен (процесс не найден)"
            fi
        else
            echo "❌ Мониторинг не запущен"
        fi
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status}"
        echo ""
        echo "  start   - Запустить мониторинг"
        echo "  stop    - Остановить мониторинг"
        echo "  restart - Перезапустить мониторинг"
        echo "  status  - Проверить статус"
        exit 1
        ;;
esac