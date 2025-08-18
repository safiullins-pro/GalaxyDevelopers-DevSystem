#!/bin/bash
# Скрипт для отправки захваченного текста из терминала в Gemini

CAPTURED_TEXT="$1"
CONTEXT="$2"
GEMINI_PATH="/opt/homebrew/bin/gemini"

# Если контекст не указан, используем дефолтный
if [ -z "$CONTEXT" ]; then
    CONTEXT="Проанализируй этот вывод из терминала:"
fi

# Создаем временный файл для сохранения контекста
TEMP_FILE="/tmp/gemini_capture_$(date +%s).txt"
echo "$CONTEXT" > "$TEMP_FILE"
echo "---" >> "$TEMP_FILE"
echo "$CAPTURED_TEXT" >> "$TEMP_FILE"

# Открываем новую панель и отправляем в Gemini
osascript <<EOF
tell application "iTerm2"
    tell current window
        tell current session
            set newSession to (split vertically with default profile)
            tell newSession
                write text "cat '$TEMP_FILE' | $GEMINI_PATH && rm '$TEMP_FILE'"
            end tell
        end tell
    end tell
end tell
EOF