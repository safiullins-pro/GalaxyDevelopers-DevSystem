#!/bin/bash
# Скрипт для запуска Gemini с промптом из файла в новой панели iTerm2

FILE_PATH="$1"
GEMINI_PATH="/opt/homebrew/bin/gemini"

# Проверяем, что путь к файлу передан
if [ -z "$FILE_PATH" ]; then
    echo "Ошибка: путь к файлу не указан"
    exit 1
fi

# Проверяем существование файла
if [ ! -f "$FILE_PATH" ]; then
    echo "Ошибка: файл $FILE_PATH не найден"
    exit 1
fi

# Открываем новую панель справа и запускаем Gemini с содержимым файла
osascript <<EOF
tell application "iTerm2"
    tell current window
        tell current session
            set newSession to (split vertically with default profile)
            tell newSession
                write text "echo 'Файл: $FILE_PATH' && echo '---' && cat '$FILE_PATH' | $GEMINI_PATH"
            end tell
        end tell
    end tell
end tell
EOF