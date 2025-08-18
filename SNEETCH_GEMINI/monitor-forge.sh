#!/bin/bash

# Скрипт для мониторинга папки с результатами анализа и поиска упоминаний forge

OUTPUT_DIR="/Volumes/Z7S/development/GalaxyDevelopments/GEMINI_ANALYSIS_RESULTS"
FORGE_FOUND_FILE="/tmp/forge_alerts.txt"

echo "========================================================"
echo "МОНИТОРИНГ FORGE В РЕЗУЛЬТАТАХ GEMINI"
echo "Папка: $OUTPUT_DIR"
echo "========================================================"
echo ""

# Очищаем файл с алертами
> "$FORGE_FOUND_FILE"

# Функция для проверки файла
check_file() {
    local file="$1"
    local filename=$(basename "$file")
    
    if grep -i "forge" "$file" > /dev/null 2>&1; then
        echo "🔴 FORGE НАЙДЕН: $filename"
        echo "----------------------------------------"
        
        # Сохраняем в файл алертов
        {
            echo "FILE: $filename"
            echo "PATH: $file"
            echo "TIMESTAMP: $(date)"
            echo "CONTEXT:"
            grep -i -n -C 3 "forge" "$file"
            echo "========================================"
            echo ""
        } >> "$FORGE_FOUND_FILE"
        
        # Выводим контекст в консоль
        grep -i -C 2 "forge" "$file" | head -20
        echo "----------------------------------------"
        echo ""
        
        return 0
    fi
    return 1
}

# Проверяем существующие файлы
echo "Проверяю существующие файлы..."
found_count=0
total_count=0

for file in "$OUTPUT_DIR"/*.md; do
    if [ -f "$file" ]; then
        ((total_count++))
        if check_file "$file"; then
            ((found_count++))
        fi
    fi
done

echo ""
echo "========================================================"
echo "РЕЗУЛЬТАТЫ ПОИСКА:"
echo "Проверено файлов: $total_count"
echo "Найдено упоминаний forge: $found_count"
if [ $found_count -gt 0 ]; then
    echo ""
    echo "Детали сохранены в: $FORGE_FOUND_FILE"
fi
echo "========================================================"

# Если найдены упоминания, показываем сводку
if [ $found_count -gt 0 ]; then
    echo ""
    echo "СВОДКА УПОМИНАНИЙ FORGE:"
    echo "------------------------"
    cat "$FORGE_FOUND_FILE"
fi