#!/bin/bash

# Автоматическая очистка macOS метаданных (._* файлов)
# Запускается в фоне и следит за появлением новых метаданных

PROJECT_DIR="/Volumes/Z7S/development/GalaxyDevelopers/DevSystem"

echo "Starting cleanup watcher for macOS metadata files..."

# Используем fswatch для мониторинга файловой системы
# Если fswatch не установлен, используем простой цикл
if command -v fswatch &> /dev/null; then
    echo "Using fswatch for monitoring..."
    fswatch -r "$PROJECT_DIR" | while read path; do
        # Удаляем все ._ файлы при любом изменении
        find "$PROJECT_DIR" -name "._*" -delete 2>/dev/null
    done
else
    echo "fswatch not found, using polling mode..."
    echo "Install fswatch for better performance: brew install fswatch"
    
    # Fallback - проверяем каждые 5 секунд
    while true; do
        # Удаляем все ._ файлы
        find "$PROJECT_DIR" -name "._*" -delete 2>/dev/null
        sleep 5
    done
fi