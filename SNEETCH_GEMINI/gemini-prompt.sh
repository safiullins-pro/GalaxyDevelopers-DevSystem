#!/bin/bash
# Скрипт для запуска Gemini с промптом в новой панели iTerm2

PROMPT="$1"
GEMINI_PATH="/opt/homebrew/bin/gemini"

# Проверяем, что промпт передан
if [ -z "$PROMPT" ]; then
    echo "Ошибка: промпт не указан"
    exit 1
fi

# Открываем новую панель справа и запускаем Gemini
osascript <<EOF
tell application "iTerm2"
    tell current window
        tell current session
            set newSession to (split vertically with default profile)
            tell newSession
                write text "echo 'Промпт: $PROMPT' && echo '---' && echo '$PROMPT' | $GEMINI_PATH"
            end tell
        end tell
    end tell
end tell
EOF