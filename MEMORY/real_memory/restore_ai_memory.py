#!/usr/bin/env python3
"""
🔥 ВОССТАНОВЛЕНИЕ ПАМЯТИ ИИ
Запускается в начале каждой новой сессии
"""

import sys
sys.path.append('/Users/safiullins_pro')

from REAL_MEMORY_SYSTEM import RealMemorySystem

def restore_memory():
    """Восстанавливаем память ИИ"""
    memory = RealMemorySystem()
    
    print("🧠 ВОССТАНОВЛЕНИЕ ПАМЯТИ...")
    print("=" * 50)
    
    # Загружаем всё
    data = memory.load_everything()
    
    # Показываем ключевые знания
    print("\n🔑 КЛЮЧЕВЫЕ ЗНАНИЯ:")
    knowledge = memory.search_knowledge('')
    for key, value, importance in knowledge[:10]:
        print(f"  {key}: {value} (важность: {importance})")
    
    # Показываем последние диалоги
    print("\n💬 ПОСЛЕДНИЕ ДИАЛОГИ:")
    conversations = data['recent_conversations']
    for user_msg, ai_response, timestamp in conversations[:3]:
        print(f"  USER: {user_msg[:50]}...")
        print(f"  AI: {ai_response[:50]}...")
        print()
    
    # Сохраняем факт восстановления
    memory.save_knowledge('last_restoration', f"Session {data['session_id']}", 7)
    
    print("✅ ПАМЯТЬ ВОССТАНОВЛЕНА!")
    print(f"Session ID: {data['session_id']}")
    
    return data

if __name__ == "__main__":
    restore_memory()