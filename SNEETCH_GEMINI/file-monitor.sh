#!/bin/bash
# Скрипт для мониторинга файлов и отправки уведомлений в Claude Code

# Параметры
WATCH_DIR="${1:-$HOME}"  # Директория для мониторинга (по умолчанию HOME)
FILE_PATTERN="${2:-*.txt}"  # Паттерн файлов (по умолчанию все .txt)
CLAUDE_TRIGGER="${3:-[FILE-ALERT]}"  # Триггер для Claude

# Функция для отправки уведомления в активный терминал с Claude Code
send_to_claude() {
    local file_path="$1"
    local file_name=$(basename "$file_path")
    local action="$2"
    
    # Формируем сообщение для Claude
    local message="$CLAUDE_TRIGGER: Файл '$file_name' был $action в директории $(dirname "$file_path")"
    
    # Отправляем в активную сессию iTerm2
    osascript <<EOF
tell application "iTerm2"
    tell current window
        tell current session
            -- Отправляем сообщение прямо в терминал
            write text "$message"
            write text "Посмотри файл: $file_path"
        end tell
    end tell
end tell
EOF
}

# Запускаем мониторинг
echo "🔍 Начинаю мониторинг директории: $WATCH_DIR"
echo "📁 Отслеживаю файлы: $FILE_PATTERN"
echo "🤖 Буду отправлять уведомления в Claude Code"
echo "Нажмите Ctrl+C для остановки"
echo "---"

# Мониторим изменения
fswatch -0 -r --event Created --event Updated --event Renamed "$WATCH_DIR" | while read -d "" event
do
    # Проверяем, соответствует ли файл паттерну
    if [[ $(basename "$event") == $FILE_PATTERN ]]; then
        echo "📌 Обнаружено изменение: $event"
        send_to_claude "$event" "изменен"
    fi
done