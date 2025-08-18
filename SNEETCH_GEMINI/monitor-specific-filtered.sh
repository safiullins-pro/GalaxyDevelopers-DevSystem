#!/bin/bash
# Улучшенный скрипт мониторинга с фильтрацией спама

WATCH_DIRS=(
    "$HOME/Desktop"
    "$HOME/Downloads"
    "$HOME/Documents"
)

FILE_TYPES=(
    "*.pdf"
    "*.png"
    "*.jpg"
    "*.txt"
    "*.md"
    "*.json"
)

# Хранилище последних событий для дедупликации
declare -A LAST_EVENTS
COOLDOWN_SECONDS=2

notify_claude() {
    local file="$1"
    local event="$2"
    local filename=$(basename "$file")
    local dir=$(dirname "$file")
    
    # Пропускаем временные и backup файлы
    if [[ "$filename" =~ \.tmp\.|~$|\.swp$|\.DS_Store|#.*# ]]; then
        return
    fi
    
    # Проверяем cooldown для этого файла
    local file_key="${file}"
    local current_time=$(date +%s)
    local last_time=${LAST_EVENTS[$file_key]:-0}
    local time_diff=$((current_time - last_time))
    
    if [ $time_diff -lt $COOLDOWN_SECONDS ]; then
        # Слишком рано для повторного уведомления
        return
    fi
    
    LAST_EVENTS[$file_key]=$current_time
    
    # Определяем тип файла
    local extension="${filename##*.}"
    
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
    
    # Отправляем в Claude Code (с задержкой для группировки)
    (
        sleep 0.5
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
    ) &
}

echo "🚀 Запускаю улучшенный мониторинг с фильтрацией"
echo "📂 Отслеживаемые директории:"
for dir in "${WATCH_DIRS[@]}"; do
    echo "  - $dir"
done
echo "⏹️  Нажмите Ctrl+C для остановки"
echo ""

# Мониторим каждую директорию
for dir in "${WATCH_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        fswatch -0 -r \
            --event Created \
            --event Updated \
            --exclude ".*\.tmp\..*" \
            --exclude ".*~$" \
            --exclude "\.DS_Store" \
            "$dir" | while read -d "" file
        do
            # Дополнительная проверка паттернов
            for pattern in "${FILE_TYPES[@]}"; do
                if [[ $(basename "$file") == $pattern ]]; then
                    notify_claude "$file" "создан/изменен"
                    break
                fi
            done
        done &
    fi
done

wait