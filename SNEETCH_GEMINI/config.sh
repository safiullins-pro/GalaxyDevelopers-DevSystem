#!/bin/bash
# Конфигурация путей для Gemini системы в нашем контуре

# Базовые пути
export GALAXY_BASE="/Volumes/Z7S/development/GalaxyDevelopers/DevSystem"
export GEMINI_SYSTEM="$GALAXY_BASE/GEMINI_SYSTEM"
export GEMINI_LOGS="$GEMINI_SYSTEM/logs"
export GEMINI_OUTPUTS="$GEMINI_SYSTEM/outputs"

# Claude пути
export CLAUDE_LOGS="/Users/safiullins_pro/.claude/projects"
export CLAUDE_CURRENT_LOG="/Users/safiullins_pro/.claude/projects/-Users-safiullins-pro/42545c12-a4cb-4e8c-a90c-c4feccd0360b.jsonl"

# API ключи (загружаем из окружения)
export GEMINI_API_KEY="${GEMINI_API_KEY:-}"

# Создаем необходимые директории
mkdir -p "$GEMINI_LOGS"
mkdir -p "$GEMINI_OUTPUTS"
mkdir -p "$GEMINI_SYSTEM/prompts"
mkdir -p "$GEMINI_SYSTEM/templates"

# Функции для работы из нашего контура
gemini_log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$GEMINI_LOGS/gemini.log"
    echo "$1"
}

check_gemini_api() {
    if [ -z "$GEMINI_API_KEY" ]; then
        gemini_log "❌ GEMINI_API_KEY не установлен"
        return 1
    fi
    return 0
}

# Экспортируем функции
export -f gemini_log
export -f check_gemini_api