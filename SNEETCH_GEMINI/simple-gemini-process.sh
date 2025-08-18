#!/bin/bash

# Простой скрипт для обработки через gemini CLI

SOURCE_DIR="$HOME/В ПЕРПЛЕКСИТИ"
OUTPUT_DIR="/Volumes/Z7S/development/GalaxyDevelopments/GEMINI_ANALYSIS_RESULTS"
API_KEY="AIzaSyB4LZKDKzII5UeaStDovodbvVVfxPWPdD8"

mkdir -p "$OUTPUT_DIR"

echo "Обрабатываю файлы через Gemini..."

# Обрабатываем каждый файл
for file in "$SOURCE_DIR"/*.txt; do
    if [ -f "$file" ]; then
        filename=$(basename "$file" .txt)
        output_file="$OUTPUT_DIR/${filename}_analysis.md"
        
        echo "Обрабатываю: $filename"
        
        # Отправляем в Gemini
        cat "$file" | head -c 30000 | curl -s \
            -H "Content-Type: application/json" \
            -d "{
                \"contents\": [{
                    \"parts\": [{
                        \"text\": \"Найди ВСЕ упоминания слова forge в этом тексте. Покажи контекст каждого упоминания:\n\n$(cat "$file" | head -c 30000 | sed 's/"/\\"/g' | tr '\n' ' ')\"
                    }]
                }]
            }" \
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=$API_KEY" \
            | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No response'))" \
            > "$output_file"
        
        # Проверяем на forge
        if grep -i "forge" "$output_file" > /dev/null 2>&1; then
            echo "🔴 FORGE НАЙДЕН в $filename!"
            grep -i "forge" "$output_file"
        fi
        
        sleep 2.5  # Rate limit
    fi
done

echo "Готово! Проверяю все файлы на forge..."
grep -i "forge" "$OUTPUT_DIR"/*.md 2>/dev/null || echo "Forge не найден"