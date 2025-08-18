#!/usr/bin/env python3
"""
ИЗВЛЕЧЕНИЕ ВСЕХ ВЕРСИЙ FORGE ДИЗАЙНА ИЗ ЛОГОВ
Находим и сохраняем все HTML версии от легендарного дизайнера
"""

import json
import sys
import re
from pathlib import Path

def extract_html_from_json_line(line):
    """Извлекает HTML из строки JSON лога"""
    try:
        data = json.loads(line)
        
        # Проверяем Write tool
        if data.get('type') == 'assistant':
            content = data.get('message', {}).get('content', [])
            for item in content:
                if isinstance(item, dict):
                    # Write tool input
                    if item.get('name') == 'Write':
                        input_data = item.get('input', {})
                        html_content = input_data.get('content', '')
                        if '<!DOCTYPE html>' in html_content:
                            return html_content, 'write_tool'
                    
                    # Обычный текст ответа
                    if 'text' in item:
                        text = item['text']
                        if '<!DOCTYPE html>' in text:
                            return text, 'text_response'
        
        # Проверяем tool_result 
        if data.get('type') == 'user':
            content = data.get('message', {}).get('content', [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'tool_result':
                        result_content = item.get('content', '')
                        if '<!DOCTYPE html>' in result_content:
                            # Убираем номера строк если есть
                            clean_html = re.sub(r'^\s*\d+→', '', result_content, flags=re.MULTILINE)
                            return clean_html, 'tool_result'
            
            # Старый формат
            if isinstance(content, str) and '<!DOCTYPE html>' in content:
                return content, 'user_content'
    
    except Exception as e:
        pass
    
    return None, None

def extract_features(html):
    """Извлекает ключевые особенности HTML"""
    features = {
        'has_memory_forge': 'MEMORY FORGE' in html,
        'has_emoji': bool(re.search(r'[🧠💬📝📸🔍✨🌌🚀]', html)),
        'has_forge_slider': 'forge-slider' in html,
        'has_mercedes_black': '#100f12' in html,
        'has_neon_purple': '#9f50ff' in html or '#BF00FF' in html,
        'has_proximity': 'proximity' in html.lower(),
        'has_glint': 'glint' in html.lower(),
        'line_count': html.count('\n'),
        'size': len(html)
    }
    
    # Подсчёт эмодзи
    emoji_pattern = re.compile(r'[🧠💬📝📸🔍✨🌌🚀💾🔥🎨⚖️]')
    features['emoji_count'] = len(emoji_pattern.findall(html))
    
    # Находим title
    title_match = re.search(r'<title>(.*?)</title>', html)
    features['title'] = title_match.group(1) if title_match else 'No title'
    
    return features

def main():
    log_file = '/Users/safiullins_pro/.claude/projects/-Users-safiullins-pro/09607727-dbed-4598-b8bf-f2aff761abd0.jsonl'
    output_dir = Path('/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/HR/DEV_AGENTS/FORGE_VERSIONS')
    output_dir.mkdir(exist_ok=True)
    
    print("🔍 СКАНИРУЮ ЛОГИ НА FORGE ВЕРСИИ...")
    print(f"📂 Файл: {log_file}")
    print("=" * 80)
    
    versions_found = []
    
    with open(log_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            html_content, source_type = extract_html_from_json_line(line)
            
            if html_content:
                features = extract_features(html_content)
                
                # Определяем имя версии
                version_name = f"v{line_num:03d}"
                if features['has_memory_forge'] and features['has_emoji']:
                    version_name += "_FULL_EMOJI"
                elif features['has_memory_forge']:
                    version_name += "_MEMORY_FORGE"
                elif features['has_neon_purple']:
                    version_name += "_NEON"
                elif features['has_proximity']:
                    version_name += "_PROXIMITY"
                else:
                    version_name += "_BASIC"
                
                # Сохраняем HTML
                output_file = output_dir / f"FORGE_{version_name}.html"
                output_file.write_text(html_content)
                
                version_info = {
                    'line': line_num,
                    'file': output_file.name,
                    'source': source_type,
                    'features': features
                }
                versions_found.append(version_info)
                
                print(f"\n📄 ВЕРСИЯ {len(versions_found)}:")
                print(f"   Строка: {line_num}")
                print(f"   Источник: {source_type}")
                print(f"   Title: {features['title']}")
                print(f"   Размер: {features['size']:,} байт ({features['line_count']} строк)")
                print(f"   Особенности:")
                if features['has_memory_forge']:
                    print(f"      ✅ MEMORY FORGE")
                if features['has_emoji']:
                    print(f"      ✅ Эмодзи ({features['emoji_count']} шт)")
                if features['has_forge_slider']:
                    print(f"      ✅ forge-slider")
                if features['has_mercedes_black']:
                    print(f"      ✅ Mercedes Black (#100f12)")
                if features['has_neon_purple']:
                    print(f"      ✅ Neon Purple")
                if features['has_proximity']:
                    print(f"      ✅ Proximity язычок")
                if features['has_glint']:
                    print(f"      ✅ Glint анимация")
                print(f"   Сохранено: {output_file.name}")
    
    print("\n" + "=" * 80)
    print(f"🎯 ИТОГО НАЙДЕНО ВЕРСИЙ: {len(versions_found)}")
    
    # Ищем лучшую версию
    if versions_found:
        best_version = max(versions_found, key=lambda v: (
            v['features']['has_memory_forge'],
            v['features']['has_emoji'],
            v['features']['emoji_count'],
            v['features']['has_forge_slider'],
            v['features']['size']
        ))
        
        print(f"\n🏆 ЛУЧШАЯ ВЕРСИЯ:")
        print(f"   Файл: {best_version['file']}")
        print(f"   Строка в логе: {best_version['line']}")
        print(f"   Title: {best_version['features']['title']}")
        if best_version['features']['has_memory_forge']:
            print(f"   ✨ Полная MEMORY FORGE")
        if best_version['features']['emoji_count'] > 0:
            print(f"   ✨ {best_version['features']['emoji_count']} эмодзи")
        
        # Создаём симлинк на лучшую версию
        best_link = output_dir / "BEST_FORGE_VERSION.html"
        if best_link.exists():
            best_link.unlink()
        best_link.symlink_to(output_dir / best_version['file'])
        print(f"\n🔗 Симлинк на лучшую версию: BEST_FORGE_VERSION.html")
    
    # Сохраняем отчёт
    report_file = output_dir / "extraction_report.json"
    report_file.write_text(json.dumps(versions_found, indent=2))
    print(f"\n📊 Отчёт сохранён: extraction_report.json")

if __name__ == "__main__":
    main()