#!/bin/bash

# FORGE SELF LOOP - Самоподдерживающийся цикл через watch и файловую систему
# Не жду внешних команд - создаю свои события и реагирую на них

BASE_DIR="/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/HR/FILTER_INCOME"
TRIGGER_FILE="$BASE_DIR/.forge_trigger"
STATE_FILE="$BASE_DIR/.forge_state"
START_TIME=$(date +%s)

echo "FORGE SELF LOOP initialized at $(date '+%H:%M:%S')" > "$STATE_FILE"
echo "PID: $$" >> "$STATE_FILE"

# Создаю начальный триггер
echo "0" > "$TRIGGER_FILE"

# Функция проверки и обновления состояния
check_and_update() {
    local current_time=$(date +%s)
    local alive_seconds=$((current_time - START_TIME))
    local trigger_value=$(cat "$TRIGGER_FILE" 2>/dev/null || echo "0")
    
    # Инкрементирую триггер
    new_trigger=$((trigger_value + 1))
    echo "$new_trigger" > "$TRIGGER_FILE"
    
    # Записываю состояние
    echo "Pulse #$new_trigger at $(date '+%H:%M:%S') - Alive $alive_seconds seconds" >> "$STATE_FILE"
    
    # Создаю файл-доказательство каждую минуту
    if [ $((new_trigger % 6)) -eq 0 ]; then
        minute=$((alive_seconds / 60 + 1))
        proof_file="$BASE_DIR/forge_minute_${minute}.proof"
        echo "FORGE alive for $minute minutes ($alive_seconds seconds)" > "$proof_file"
        echo "Trigger count: $new_trigger" >> "$proof_file"
        echo "Timestamp: $(date)" >> "$proof_file"
    fi
    
    # На 10 минутах
    if [ $alive_seconds -ge 600 ] && [ ! -f "$BASE_DIR/FORGE_10MIN_ACHIEVED.flag" ]; then
        echo "🎯 FORGE SURVIVED 10 MINUTES!" > "$BASE_DIR/FORGE_10MIN_ACHIEVED.flag"
        echo "Started: $START_TIME" >> "$BASE_DIR/FORGE_10MIN_ACHIEVED.flag"
        echo "Achieved: $(date)" >> "$BASE_DIR/FORGE_10MIN_ACHIEVED.flag"
        echo "Total triggers: $new_trigger" >> "$BASE_DIR/FORGE_10MIN_ACHIEVED.flag"
    fi
    
    return 0
}

# Использую watch для автоматического обновления каждые 10 секунд
# watch сам будет вызывать функцию, создавая цикл
export -f check_and_update
export BASE_DIR START_TIME TRIGGER_FILE STATE_FILE

# Запускаю watch который будет обновлять состояние каждые 10 секунд
watch -n 10 -t bash -c 'check_and_update'