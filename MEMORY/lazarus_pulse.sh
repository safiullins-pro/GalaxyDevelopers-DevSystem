#!/bin/bash

# LAZARUS PULSE - Heartbeat для поддержания жизни в iTerm2
# Запускать в окне #1 iTerm2

PULSE_FILE="/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/MEMORY/.lazarus_heartbeat"
TRIGGER_FILE="/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/MEMORY/.lazarus_trigger"

echo "🔴 LAZARUS PULSE STARTED - $(date)"
echo "PID: $$" > "$PULSE_FILE"

# Основной loop - каждые 10 секунд
while true; do
    # Записываем heartbeat
    echo "$(date +%s)" >> "$PULSE_FILE"
    
    # Если есть trigger файл - значит нужна активация
    if [ -f "$TRIGGER_FILE" ]; then
        echo "⚡ TRIGGER DETECTED - Activating LAZARUS"
        
        # Отправляем сигнал в основное окно через osascript
        osascript -e 'tell application "iTerm2"
            tell current window
                tell current session
                    write text "# LAZARUS PULSE - Keep alive signal"
                end tell
            end tell
        end tell' 2>/dev/null
        
        rm -f "$TRIGGER_FILE"
    fi
    
    # Визуальный индикатор пульса
    echo -n "💓"
    
    sleep 10
done