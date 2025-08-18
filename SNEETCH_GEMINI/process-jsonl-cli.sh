#!/bin/bash

# Конфигурация
SOURCE_DIR="$HOME/В ПЕРПЛЕКСИТИ"
OUTPUT_DIR="/Volumes/Z7S/development/GalaxyDevelopments/GEMINI_ANALYSIS_RESULTS"
PROMPT_FILE="$HOME/Scripts/gemini-triggers/gemini-analysis-prompt.txt"
CHUNK_SIZE=30000
REQUESTS_PER_MINUTE=25

# Создаем выходную директорию
mkdir -p "$OUTPUT_DIR"

echo "========================================================"
echo "АНАЛИЗ JSONL ФАЙЛОВ ЧЕРЕЗ GEMINI CLI"
echo "========================================================"
echo ""

# Читаем промпт
PROMPT=$(<"$PROMPT_FILE")

# Собираем все JSONL в один файл
TEMP_ALL="/tmp/all_jsonl_data.txt"
> "$TEMP_ALL"

echo "Собираю JSONL файлы..."
for file in "$SOURCE_DIR"/*.txt; do
    if [ -f "$file" ]; then
        echo "  - $(basename "$file")"
        cat "$file" >> "$TEMP_ALL"
        echo "" >> "$TEMP_ALL"
    fi
done

# Получаем размер файла
FILE_SIZE=$(wc -c < "$TEMP_ALL")
echo ""
echo "Общий размер данных: $FILE_SIZE байт"

# Функция для генерации уникального имени
generate_filename() {
    local index=$1
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local hash=$(echo "$2" | md5 | cut -c1-8)
    echo "analysis_${index}_${timestamp}_${hash}.md"
}

# Разбиваем на чанки и обрабатываем
chunk_index=1
current_pos=0

echo ""
echo "Начинаю обработку чанками по $CHUNK_SIZE символов..."
echo "Rate limit: $REQUESTS_PER_MINUTE запросов в минуту"
echo ""

# Создаем временный файл для текущего чанка
TEMP_CHUNK="/tmp/current_chunk.txt"

while [ $current_pos -lt $FILE_SIZE ]; do
    # Извлекаем чанк
    dd if="$TEMP_ALL" of="$TEMP_CHUNK" bs=1 skip=$current_pos count=$CHUNK_SIZE 2>/dev/null
    
    # Генерируем имя выходного файла
    output_file=$(generate_filename $chunk_index "$(cat "$TEMP_CHUNK" | head -c 100)")
    output_path="$OUTPUT_DIR/$output_file"
    
    echo "[$chunk_index] Обрабатываю чанк: $output_file"
    
    # Формируем полный промпт с данными
    {
        echo "$PROMPT"
        echo ""
        echo "---"
        echo "ДАННЫЕ ДЛЯ АНАЛИЗА:"
        echo "---"
        cat "$TEMP_CHUNK"
    } | gemini -m "gemini-2.0-flash-thinking-exp-1219" -p "Проанализируй предоставленные данные и найди все упоминания forge" > "$output_path"
    
    if [ $? -eq 0 ]; then
        echo "    ✓ Успешно сохранено в: $output_file"
    else
        echo "    ✗ Ошибка обработки чанка $chunk_index"
    fi
    
    # Обновляем позицию
    current_pos=$((current_pos + CHUNK_SIZE))
    chunk_index=$((chunk_index + 1))
    
    # Rate limiting (если не последний чанк)
    if [ $current_pos -lt $FILE_SIZE ]; then
        sleep_time=$(echo "scale=1; 60 / $REQUESTS_PER_MINUTE" | bc)
        echo "    Ожидание $sleep_time сек (rate limit)..."
        sleep $sleep_time
    fi
    
    echo ""
done

# Очистка временных файлов
rm -f "$TEMP_ALL" "$TEMP_CHUNK"

echo "========================================================"
echo "ОБРАБОТКА ЗАВЕРШЕНА"
echo "Обработано чанков: $((chunk_index - 1))"
echo "Результаты сохранены в: $OUTPUT_DIR"
echo "========================================================"
echo ""
echo "Созданные файлы:"
ls -1t "$OUTPUT_DIR"/*.md 2>/dev/null | head -20 | while read f; do
    echo "  - $(basename "$f")"
done