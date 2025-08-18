#!/bin/bash

# Интеграция памяти Claude CLI с бекендом GalaxyDevelopers
# Автоматическая передача контекста из CLAUDE.md в систему

GALAXY_BASE="/Volumes/Z7S/development/GalaxyDevelopers/DevSystem"
BACKEND_URL="http://127.0.0.1:37777"
MEMORY_DIR="$GALAXY_BASE/MEMORY"
CLAUDE_MD="$GALAXY_BASE/DOCUMENTS/CLAUDE.md"

# Функция для отправки памяти на бекенд
send_memory_to_backend() {
    if [ -f "$CLAUDE_MD" ]; then
        # Читаем содержимое CLAUDE.md
        MEMORY_CONTENT=$(cat "$CLAUDE_MD" | jq -Rs .)
        
        # Отправляем на бекенд через API endpoint
        curl -X POST "$BACKEND_URL/memory/save" \
            -H "Content-Type: application/json" \
            -d "{
                \"type\": \"claude_context\",
                \"content\": $MEMORY_CONTENT,
                \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
                \"source\": \"claude_cli\"
            }" 2>/dev/null
            
        echo "✅ Память отправлена на бекенд"
    else
        echo "⚠️ CLAUDE.md не найден"
    fi
}

# Функция для получения контекста из системы
get_context_from_backend() {
    CONTEXT=$(curl -s "$BACKEND_URL/memory/context?limit=10")
    echo "$CONTEXT"
}

# Функция для синхронизации с локальной базой памяти
sync_with_memory_db() {
    if [ -f "$MEMORY_DIR/unified_memory.db" ]; then
        # Используем существующую систему памяти
        python3 "$MEMORY_DIR/memory_api.py" add_context "$1"
    fi
}

# Хук для автоматической отправки при каждом запуске claude
setup_claude_hook() {
    # Создаем хук для claude CLI
    cat > "$HOME/.claude_hooks/memory_sync.sh" << 'EOF'
#!/bin/bash
# Автоматическая синхронизация памяти при запуске claude

SCRIPT_DIR="/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/SCRIPTS"
if [ -f "$SCRIPT_DIR/claude-memory-integration.sh" ]; then
    source "$SCRIPT_DIR/claude-memory-integration.sh"
    send_memory_to_backend
fi
EOF
    chmod +x "$HOME/.claude_hooks/memory_sync.sh"
}

# Основная логика
case "$1" in
    "send")
        send_memory_to_backend
        ;;
    "get")
        get_context_from_backend
        ;;
    "sync")
        sync_with_memory_db "$2"
        ;;
    "setup")
        setup_claude_hook
        echo "✅ Хук установлен"
        ;;
    *)
        echo "Использование: $0 {send|get|sync|setup}"
        echo "  send  - отправить память на бекенд"
        echo "  get   - получить контекст из системы"
        echo "  sync  - синхронизировать с локальной БД"
        echo "  setup - установить автоматический хук"
        ;;
esac