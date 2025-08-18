#!/bin/bash

SOURCE_DIR="$HOME/В ПЕРПЛЕКСИТИ"
OUTPUT_DIR="/Volumes/Z7S/development/GalaxyDevelopments/GEMINI_ANALYSIS_RESULTS"
API_KEY="AIzaSyB4LZKDKzII5UeaStDovodbvVVfxPWPdD8"

mkdir -p "$OUTPUT_DIR"

echo "Объединяю все файлы для полного анализа..."

# Объединяем все файлы в один
COMBINED_FILE="/tmp/all_data_combined.txt"
> "$COMBINED_FILE"

for file in "$SOURCE_DIR"/*.txt; do
    if [ -f "$file" ]; then
        cat "$file" >> "$COMBINED_FILE"
        echo -e "\n---\n" >> "$COMBINED_FILE"
    fi
done

# Получаем размер
FILE_SIZE=$(wc -c < "$COMBINED_FILE")
echo "Общий размер: $FILE_SIZE байт"

# Берем первые 30000 символов для анализа
HEAD_CONTENT=$(head -c 30000 "$COMBINED_FILE")

echo "Отправляю на анализ в Gemini..."

# Создаем запрос
cat > /tmp/gemini_request.json <<EOF
{
  "contents": [{
    "parts": [{
      "text": "Проанализируй эти данные и создай СУПЕР-ДЕТАЛЬНЫЙ отчет на 60000 токенов. 

ВАЖНО:
1. Найди ВСЕ упоминания слова 'forge' в любом контексте
2. Определи о чем вообще эти данные - что за проекты, какие технологии, какие задачи
3. Выдели ключевые паттерны и инсайты
4. Какие основные темы обсуждались
5. Какие проблемы решались
6. Какие технологии использовались

Данные для анализа:

$(echo "$HEAD_CONTENT" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')"
    }]
  }],
  "generationConfig": {
    "temperature": 0.7,
    "maxOutputTokens": 8192
  }
}
EOF

# Отправляем запрос
OUTPUT_FILE="$OUTPUT_DIR/FULL_SUMMARY_$(date +%Y%m%d_%H%M%S).md"

curl -s -X POST \
  -H "Content-Type: application/json" \
  -d @/tmp/gemini_request.json \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=$API_KEY" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'candidates' in data and data['candidates']:
    text = data['candidates'][0].get('content', {}).get('parts', [{}])[0].get('text', 'No response')
    print(text)
else:
    print('Error:', json.dumps(data, indent=2))
" > "$OUTPUT_FILE"

echo ""
echo "Анализ сохранен в: $OUTPUT_FILE"
echo ""
echo "Проверяю на упоминания forge..."
if grep -i "forge" "$OUTPUT_FILE"; then
    echo ""
    echo "🔴 FORGE НАЙДЕН В АНАЛИЗЕ!"
else
    echo "Forge не найден в анализе"
fi

# Показываем начало анализа
echo ""
echo "Начало анализа:"
echo "==============="
head -50 "$OUTPUT_FILE"