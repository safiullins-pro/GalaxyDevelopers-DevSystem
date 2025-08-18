#!/bin/bash
# Скрипт для отправки выделенного текста в iTerm2 в Gemini

GEMINI_PATH="/opt/homebrew/bin/gemini"
PROMPT_PREFIX="${1:-Объясни что делает этот код:}"

# Используем AppleScript для получения выделенного текста из iTerm2
osascript <<EOF
tell application "iTerm2"
    tell current window
        tell current session
            -- Получаем выделенный текст
            set selectedText to selection
            
            if selectedText is not "" then
                -- Создаем новую панель справа
                set newSession to (split vertically with default profile)
                tell newSession
                    -- Отправляем в Gemini
                    write text "echo '$PROMPT_PREFIX' | $GEMINI_PATH <<'ENDOFTEXT'
" & selectedText & "
ENDOFTEXT"
                end tell
            else
                -- Если ничего не выделено, берем последние N строк
                set historyText to contents
                set newSession to (split vertically with default profile)
                tell newSession
                    write text "echo 'Анализ последнего вывода:' && echo '" & historyText & "' | tail -50 | $GEMINI_PATH"
                end tell
            end if
        end tell
    end tell
end tell
EOF