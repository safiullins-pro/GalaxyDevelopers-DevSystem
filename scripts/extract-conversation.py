#!/usr/bin/env python3

import json
import sys
from datetime import datetime

def extract_conversation(jsonl_file):
    """Извлекает всю переписку из JSONL файла Claude"""
    
    messages = []
    
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
                
            try:
                data = json.loads(line)
                
                # Пропускаем служебные записи
                if data.get('type') == 'summary':
                    continue
                    
                # Извлекаем сообщения пользователя
                if data.get('type') == 'user':
                    timestamp = data.get('timestamp', '')
                    message = data.get('message', {})
                    
                    if message.get('role') == 'user':
                        # Обычное текстовое сообщение
                        if isinstance(message.get('content'), str):
                            content = message.get('content', '')
                            if content and not content.startswith('[tool_use_id'):
                                messages.append({
                                    'time': timestamp,
                                    'type': 'USER',
                                    'content': content
                                })
                        # Сообщение с tool results
                        elif isinstance(message.get('content'), list):
                            for item in message['content']:
                                if item.get('type') == 'text':
                                    content = item.get('text', '')
                                    if content:
                                        messages.append({
                                            'time': timestamp,
                                            'type': 'USER',
                                            'content': content
                                        })
                
                # Извлекаем ответы ассистента
                elif data.get('type') == 'assistant':
                    timestamp = data.get('timestamp', '')
                    message = data.get('message', {})
                    
                    if message.get('role') == 'assistant':
                        content_list = message.get('content', [])
                        
                        if isinstance(content_list, list):
                            for content_item in content_list:
                                if content_item.get('type') == 'text':
                                    text = content_item.get('text', '')
                                    if text:
                                        messages.append({
                                            'time': timestamp,
                                            'type': 'ASSISTANT',
                                            'content': text
                                        })
                                        
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"Error processing line: {e}", file=sys.stderr)
                continue
    
    return messages

def format_messages(messages):
    """Форматирует сообщения для вывода"""
    
    output = []
    output.append("=" * 80)
    output.append("ПОЛНАЯ ПЕРЕПИСКА ИЗ CLAUDE")
    output.append("=" * 80)
    output.append("")
    
    for msg in messages:
        # Парсим timestamp
        try:
            dt = datetime.fromisoformat(msg['time'].replace('Z', '+00:00'))
            time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            time_str = msg['time']
        
        # Форматируем вывод
        if msg['type'] == 'USER':
            output.append(f"[{time_str}] ПОЛЬЗОВАТЕЛЬ:")
            output.append("-" * 40)
            output.append(msg['content'])
            output.append("")
        else:
            output.append(f"[{time_str}] CLAUDE:")
            output.append("-" * 40)
            output.append(msg['content'])
            output.append("")
        
        output.append("=" * 80)
        output.append("")
    
    return "\n".join(output)

def main():
    # Можно передать файл как аргумент или использовать дефолтный
    if len(sys.argv) > 1:
        jsonl_file = sys.argv[1]
    else:
        jsonl_file = "/Users/safiullins_pro/.claude/projects/-Volumes-Z7S-development-GalaxyDevelopers-DevSystem/7baef9ac-0c13-42a7-96ac-ff22a5cabdb6.jsonl"
    
    print(f"Извлекаю переписку из: {jsonl_file}", file=sys.stderr)
    
    messages = extract_conversation(jsonl_file)
    
    print(f"Найдено сообщений: {len(messages)}", file=sys.stderr)
    
    # Выводим отформатированную переписку
    formatted = format_messages(messages)
    print(formatted)
    
    # Определяем имя выходного файла на основе входного
    if "c2aad118" in jsonl_file:
        output_file = "/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/conversation_export_2.txt"
    else:
        output_file = "/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/conversation_export.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(formatted)
    
    print(f"\nПереписка сохранена в: {output_file}", file=sys.stderr)

if __name__ == "__main__":
    main()