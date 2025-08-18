#!/bin/bash
# Скрипт для мониторинга специфических файлов и отправки в Claude Code

# Настройки по умолчанию
WATCH_DIRS=(
    "$HOME/Desktop"
    "$HOME/Downloads"
    "$HOME/Documents"
)

# Типы файлов для мониторинга
FILE_TYPES=(
    "*.pdf"
    "*.png"
    "*.jpg"
    "*.txt"
    "*.md"
    "*.json"
)

# Функция для уведомления Claude
notify_claude() {
    local file="$1"
    local event="$2"
    local filename=$(basename "$file")
    local dir=$(dirname "$file")
    
    # Определяем тип файла
    local extension="${filename##*.}"
    
    # Формируем сообщение в зависимости от типа
    case "$extension" in
        pdf)
            msg="📄 Новый PDF документ: $filename"
            ;;
        png|jpg|jpeg)
            msg="🖼️ Новое изображение: $filename"
            ;;
        txt|md)
            msg="📝 Новый текстовый файл: $filename"
            ;;
        json)
            msg="🔧 Новый JSON файл: $filename"
            ;;
        *)
            msg="📎 Новый файл: $filename"
            ;;
    esac
    
    # Отправляем в Claude Code
    osascript <<EOF
tell application "iTerm2"
    tell current window
        tell current session
            write text ""
            write text "=== ФАЙЛОВОЕ УВЕДОМЛЕНИЕ ==="
            write text "$msg"
            write text "Путь: $file"
            write text "Событие: $event"
            write text "Время: $(date '+%H:%M:%S')"
            write text "---"
            write text "Проверь этот файл: $file"
            write text ""
        end tell
    end tell
end tell
EOF
}

# Запуск мониторинга
echo "🚀 Запускаю мониторинг файловой системы для Claude Code"
echo "📂 Отслеживаемые директории:"
for dir in "${WATCH_DIRS[@]}"; do
    echo "  - $dir"
done
echo "📋 Типы файлов: ${FILE_TYPES[*]}"
echo "⏹️  Нажмите Ctrl+C для остановки"
echo "=" 
echo ""

# Мониторим каждую директорию
for dir in "${WATCH_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        fswatch -0 -r \
            --event Created \
            --event Updated \
            --event Renamed \
            --event MovedTo \
            "$dir" | while read -d "" file
        do
            # Проверяем соответствие паттернам
            for pattern in "${FILE_TYPES[@]}"; do
                if [[ $(basename "$file") == $pattern ]]; then
                    notify_claude "$file" "создан/изменен"
                    break
                fi
            done
        done &
    fi
done

# Ждем завершения
wait