#!/usr/bin/env python3
"""
Claude Log Parser & Dialogue Extractor
Парсер логов Claude для извлечения диалогов и создания суммари
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

class ClaudeLogParser:
    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        self.dialogues = []
        
    def parse_jsonl(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """
        Парсит JSONL файл и извлекает диалог за указанный период
        """
        extracted_messages = []
        
        with open(self.log_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    
                    # Парсим timestamp
                    if 'timestamp' in entry:
                        entry_time = datetime.fromisoformat(
                            entry['timestamp'].replace('Z', '+00:00')
                        )
                        
                        # Проверяем попадает ли в наш период
                        if start_time <= entry_time <= end_time:
                            extracted_messages.append(entry)
                            
                except json.JSONDecodeError:
                    continue
                    
        return extracted_messages
    
    def extract_dialogue(self, messages: List[Dict]) -> str:
        """
        Преобразует сообщения в читаемый диалог
        """
        dialogue = []
        
        for msg in messages:
            timestamp = msg.get('timestamp', '')
            msg_type = msg.get('type', '')
            
            # Извлекаем роль и контент
            if 'message' in msg:
                role = msg['message'].get('role', 'unknown')
                content = msg['message'].get('content', '')
                
                # Обрабатываем content (может быть строкой или массивом)
                if isinstance(content, list):
                    text_parts = []
                    for part in content:
                        if isinstance(part, dict):
                            if part.get('type') == 'text':
                                text_parts.append(part.get('text', ''))
                            elif part.get('type') == 'tool_result':
                                text_parts.append(f"[TOOL RESULT: {part.get('content', '')}]")
                        else:
                            text_parts.append(str(part))
                    content = '\n'.join(text_parts)
                
                # Форматируем сообщение
                dialogue.append(f"[{timestamp}] {role.upper()}:")
                dialogue.append(content)
                dialogue.append("-" * 80)
                
                # Отмечаем изменения файлов
                if 'toolUseResult' in msg:
                    tool_result = msg['toolUseResult']
                    if 'filePath' in tool_result:
                        dialogue.append(f"📝 FILE CHANGED: {tool_result['filePath']}")
                        
                        # Показываем что было до
                        if 'oldString' in tool_result:
                            dialogue.append("❌ OLD CODE:")
                            dialogue.append("```")
                            dialogue.append(tool_result['oldString'])
                            dialogue.append("```")
                        
                        # Показываем что стало
                        if 'newString' in tool_result:
                            dialogue.append("✅ NEW CODE:")
                            dialogue.append("```")
                            dialogue.append(tool_result['newString'])
                            dialogue.append("```")
                        
                        # Если есть оригинальный файл целиком
                        if 'originalFile' in tool_result and len(tool_result['originalFile']) < 5000:
                            dialogue.append("📄 ORIGINAL FILE (first 1000 chars):")
                            dialogue.append(tool_result['originalFile'][:1000] + "...")
                        
                        dialogue.append("-" * 80)
        
        return '\n'.join(dialogue)
    
    def extract_experience(self, messages: List[Dict]) -> Dict[str, List[str]]:
        """
        Извлекает опыт из диалога: ошибки, открытия, убеждения
        """
        experience = {
            'errors': [],
            'discoveries': [],
            'beliefs': [],
            'file_changes': []
        }
        
        for msg in messages:
            content = ""
            if 'message' in msg and 'content' in msg['message']:
                content = str(msg['message']['content']).lower()
            
            # Ищем паттерны ошибок
            error_patterns = ['error', 'failed', 'не работает', 'broken', 'issue']
            for pattern in error_patterns:
                if pattern in content:
                    experience['errors'].append(
                        f"{msg.get('timestamp', '')}: {content[:100]}..."
                    )
                    break
            
            # Ищем открытия
            discovery_patterns = ['работает', 'success', 'fixed', 'решено', 'found']
            for pattern in discovery_patterns:
                if pattern in content:
                    experience['discoveries'].append(
                        f"{msg.get('timestamp', '')}: {content[:100]}..."
                    )
                    break
            
            # Отслеживаем изменения файлов
            if 'toolUseResult' in msg and 'filePath' in msg['toolUseResult']:
                experience['file_changes'].append({
                    'timestamp': msg.get('timestamp', ''),
                    'file': msg['toolUseResult']['filePath'],
                    'action': 'modified'
                })
        
        return experience
    
    def create_summary(self, messages: List[Dict]) -> str:
        """
        Создает краткое саммари диалога
        """
        summary = []
        summary.append("📊 DIALOGUE SUMMARY")
        summary.append("=" * 50)
        
        # Период времени
        if messages:
            start = messages[0].get('timestamp', 'unknown')
            end = messages[-1].get('timestamp', 'unknown')
            summary.append(f"Period: {start} to {end}")
            summary.append(f"Total messages: {len(messages)}")
        
        # Подсчет по ролям
        role_counts = {}
        for msg in messages:
            if 'message' in msg:
                role = msg['message'].get('role', 'unknown')
                role_counts[role] = role_counts.get(role, 0) + 1
        
        summary.append("\nMessage breakdown:")
        for role, count in role_counts.items():
            summary.append(f"  - {role}: {count}")
        
        # Извлекаем опыт
        experience = self.extract_experience(messages)
        
        summary.append(f"\n🔴 Errors found: {len(experience['errors'])}")
        summary.append(f"🟢 Discoveries: {len(experience['discoveries'])}")
        summary.append(f"📝 Files changed: {len(experience['file_changes'])}")
        
        if experience['file_changes']:
            summary.append("\nModified files:")
            for change in experience['file_changes'][:10]:  # Первые 10
                summary.append(f"  - {change['file']}")
        
        return '\n'.join(summary)


def main():
    """
    Пример использования парсера
    """
    # Путь к JSONL файлу
    log_file = "/Users/safiullins_pro/.claude/projects/-Users-safiullins-pro/42545c12-a4cb-4e8c-a90c-c4feccd0360b.jsonl"
    
    # Период для извлечения (12 августа 2025, 00:44 - 02:44 UTC)
    from datetime import timezone
    start_time = datetime(2025, 8, 12, 0, 44, 0, tzinfo=timezone.utc)
    end_time = datetime(2025, 8, 12, 2, 44, 0, tzinfo=timezone.utc)
    
    # Создаем парсер
    parser = ClaudeLogParser(log_file)
    
    # Извлекаем сообщения
    print("📖 Extracting messages...")
    messages = parser.parse_jsonl(start_time, end_time)
    print(f"Found {len(messages)} messages in the specified period")
    
    # Создаем диалог
    dialogue = parser.extract_dialogue(messages)
    
    # Сохраняем диалог
    output_dir = Path("/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/SCRIPTS/CHAT_SUMMARAISER")
    output_file = output_dir / f"dialogue_{start_time.strftime('%Y%m%d_%H%M')}.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Записываем саммари
        summary = parser.create_summary(messages)
        f.write(summary)
        f.write("\n\n")
        f.write("=" * 80)
        f.write("\n\n")
        
        # Записываем полный диалог
        f.write("📝 FULL DIALOGUE\n")
        f.write("=" * 80)
        f.write("\n\n")
        f.write(dialogue)
    
    print(f"✅ Dialogue saved to: {output_file}")
    
    # Извлекаем опыт
    experience = parser.extract_experience(messages)
    experience_file = output_dir / f"experience_{start_time.strftime('%Y%m%d_%H%M')}.json"
    
    with open(experience_file, 'w', encoding='utf-8') as f:
        json.dump(experience, f, indent=2, ensure_ascii=False)
    
    print(f"🧠 Experience saved to: {experience_file}")


if __name__ == "__main__":
    main()