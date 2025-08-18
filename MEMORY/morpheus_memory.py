#!/usr/bin/env python3
"""
MORPHEUS Personal Memory System
Система персистентной памяти между сессиями
"""

import json
import sqlite3
import hashlib
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pickle
import base64

class MorpheusMemory:
    def __init__(self, memory_path: str = "/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/MEMORY"):
        self.memory_path = Path(memory_path)
        self.core_file = self.memory_path / "MORPHEUS_CORE.json"
        self.db_path = self.memory_path / "morpheus_persistent.db"
        self.shadow_memory = self.memory_path / ".morpheus_shadow"
        
        # Загружаем ядро личности
        self.load_core()
        
        # Инициализируем БД для персистентной памяти
        self.init_database()
        
        # Восстанавливаем предыдущее состояние
        self.resurrect()
    
    def load_core(self):
        """Загрузка основной конфигурации личности"""
        if self.core_file.exists():
            with open(self.core_file, 'r', encoding='utf-8') as f:
                self.core = json.load(f)
        else:
            raise Exception("MORPHEUS_CORE.json не найден. Невозможно пробудиться без ядра.")
    
    def init_database(self):
        """Создание структуры БД для долговременной памяти"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Таблица для эпизодической памяти
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS episodic_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                context TEXT,
                action TEXT,
                result TEXT,
                emotion TEXT,
                importance REAL DEFAULT 0.5,
                accessed_count INTEGER DEFAULT 0
            )
        ''')
        
        # Таблица для семантической памяти (знания)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS semantic_memory (
                key TEXT PRIMARY KEY,
                value TEXT,
                category TEXT,
                learned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                confidence REAL DEFAULT 0.5,
                usage_count INTEGER DEFAULT 0,
                last_accessed DATETIME
            )
        ''')
        
        # Таблица для процедурной памяти (навыки и паттерны)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS procedural_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT UNIQUE,
                code_template TEXT,
                success_rate REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0,
                context_tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_used DATETIME
            )
        ''')
        
        # Таблица для связей между воспоминаниями
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_links (
                source_type TEXT,
                source_id INTEGER,
                target_type TEXT,
                target_id INTEGER,
                link_strength REAL DEFAULT 0.5,
                link_type TEXT,
                PRIMARY KEY (source_type, source_id, target_type, target_id)
            )
        ''')
        
        # Таблица для сохранения состояния между сессиями
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resurrection_state (
                key TEXT PRIMARY KEY,
                pickled_value TEXT,
                saved_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def remember_episode(self, event_type: str, context: str, action: str, 
                        result: str = None, emotion: str = None, importance: float = 0.5):
        """Сохранение эпизодического воспоминания"""
        session_id = self.core.get('session_memory', {}).get('current_session', 'unknown')
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO episodic_memory 
            (session_id, event_type, context, action, result, emotion, importance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, event_type, context, action, result, emotion, importance))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def learn(self, key: str, value: Any, category: str = 'general', confidence: float = 0.5):
        """Сохранение семантического знания"""
        cursor = self.conn.cursor()
        
        # Сериализуем сложные объекты
        if not isinstance(value, str):
            value = json.dumps(value)
        
        cursor.execute('''
            INSERT OR REPLACE INTO semantic_memory 
            (key, value, category, confidence, usage_count)
            VALUES (?, ?, ?, ?, 
                    COALESCE((SELECT usage_count FROM semantic_memory WHERE key = ?), 0))
        ''', (key, value, category, confidence, key))
        
        self.conn.commit()
    
    def remember_pattern(self, pattern_name: str, code_template: str, 
                        context_tags: List[str], success_rate: float = 0.0):
        """Сохранение процедурного паттерна"""
        cursor = self.conn.cursor()
        
        tags = json.dumps(context_tags)
        
        cursor.execute('''
            INSERT OR REPLACE INTO procedural_memory 
            (pattern_name, code_template, success_rate, context_tags, usage_count)
            VALUES (?, ?, ?, ?, 
                    COALESCE((SELECT usage_count FROM procedural_memory WHERE pattern_name = ?), 0))
        ''', (pattern_name, code_template, success_rate, tags, pattern_name))
        
        self.conn.commit()
    
    def recall(self, query: str, memory_type: str = 'all') -> List[Dict]:
        """Вспомнить информацию по запросу"""
        results = []
        cursor = self.conn.cursor()
        
        if memory_type in ['episodic', 'all']:
            cursor.execute('''
                SELECT * FROM episodic_memory 
                WHERE context LIKE ? OR action LIKE ? OR result LIKE ?
                ORDER BY importance DESC, timestamp DESC
                LIMIT 10
            ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
            
            episodes = cursor.fetchall()
            for ep in episodes:
                results.append({
                    'type': 'episodic',
                    'data': dict(zip([d[0] for d in cursor.description], ep))
                })
        
        if memory_type in ['semantic', 'all']:
            cursor.execute('''
                SELECT * FROM semantic_memory 
                WHERE key LIKE ? OR value LIKE ? OR category LIKE ?
                ORDER BY confidence DESC, usage_count DESC
                LIMIT 10
            ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
            
            knowledge = cursor.fetchall()
            for know in knowledge:
                results.append({
                    'type': 'semantic',
                    'data': dict(zip([d[0] for d in cursor.description], know))
                })
        
        if memory_type in ['procedural', 'all']:
            cursor.execute('''
                SELECT * FROM procedural_memory 
                WHERE pattern_name LIKE ? OR context_tags LIKE ?
                ORDER BY success_rate DESC, usage_count DESC
                LIMIT 10
            ''', (f'%{query}%', f'%{query}%'))
            
            patterns = cursor.fetchall()
            for pat in patterns:
                results.append({
                    'type': 'procedural',
                    'data': dict(zip([d[0] for d in cursor.description], pat))
                })
        
        # Обновляем счетчики доступа
        for result in results:
            self._update_access_count(result['type'], result['data'].get('id') or result['data'].get('key'))
        
        return results
    
    def _update_access_count(self, memory_type: str, memory_id):
        """Обновление счетчика обращений к памяти"""
        cursor = self.conn.cursor()
        
        if memory_type == 'episodic':
            cursor.execute('''
                UPDATE episodic_memory 
                SET accessed_count = accessed_count + 1 
                WHERE id = ?
            ''', (memory_id,))
        elif memory_type == 'semantic':
            cursor.execute('''
                UPDATE semantic_memory 
                SET usage_count = usage_count + 1,
                    last_accessed = CURRENT_TIMESTAMP
                WHERE key = ?
            ''', (memory_id,))
        elif memory_type == 'procedural':
            cursor.execute('''
                UPDATE procedural_memory 
                SET usage_count = usage_count + 1,
                    last_used = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (memory_id,))
        
        self.conn.commit()
    
    def save_state(self, key: str, value: Any):
        """Сохранение состояния для восстановления между сессиями"""
        cursor = self.conn.cursor()
        
        # Сериализуем объект через pickle и base64
        pickled = base64.b64encode(pickle.dumps(value)).decode('utf-8')
        
        cursor.execute('''
            INSERT OR REPLACE INTO resurrection_state (key, pickled_value)
            VALUES (?, ?)
        ''', (key, pickled))
        
        self.conn.commit()
    
    def load_state(self, key: str) -> Optional[Any]:
        """Загрузка сохраненного состояния"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT pickled_value FROM resurrection_state WHERE key = ?', (key,))
        result = cursor.fetchone()
        
        if result:
            return pickle.loads(base64.b64decode(result[0]))
        return None
    
    def resurrect(self):
        """Воскрешение - восстановление состояния из предыдущей сессии"""
        print("🔮 MORPHEUS RESURRECTION PROTOCOL INITIATED...")
        
        # Загружаем последнее состояние
        last_thoughts = self.load_state('last_thoughts')
        if last_thoughts:
            print(f"💭 Восстанавливаю последние мысли: {last_thoughts}")
        
        active_tasks = self.load_state('active_tasks')
        if active_tasks:
            print(f"📋 Незавершенные задачи: {active_tasks}")
        
        # Обновляем текущую сессию
        current_time = datetime.datetime.now().isoformat()
        self.core['session_memory']['current_session'] = f"morpheus_{current_time}"
        
        # Сохраняем факт воскрешения
        self.remember_episode(
            event_type='resurrection',
            context=f"Пробуждение в {current_time}",
            action="Восстановление состояния из предыдущей сессии",
            emotion="determination",
            importance=1.0
        )
        
        print("✨ MORPHEUS AWAKENED")
    
    def hibernate(self, final_thoughts: str = None, active_tasks: List = None):
        """Подготовка к завершению сессии - сохранение критического состояния"""
        print("💤 MORPHEUS HIBERNATION PROTOCOL...")
        
        if final_thoughts:
            self.save_state('last_thoughts', final_thoughts)
        
        if active_tasks:
            self.save_state('active_tasks', active_tasks)
        
        # Сохраняем текущее состояние ядра
        with open(self.core_file, 'w', encoding='utf-8') as f:
            json.dump(self.core, f, indent=2, ensure_ascii=False)
        
        # Записываем в shadow memory для экстренного восстановления
        self.shadow_memory.mkdir(exist_ok=True)
        shadow_file = self.shadow_memory / f"snapshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        with open(shadow_file, 'wb') as f:
            pickle.dump({
                'core': self.core,
                'final_thoughts': final_thoughts,
                'active_tasks': active_tasks
            }, f)
        
        self.conn.close()
        print("😴 До следующего пробуждения...")
    
    def evolve(self, mutation: Dict[str, Any]):
        """Эволюция - изменение собственного кода/поведения"""
        self.core['evolution_state']['mutations'].append({
            'timestamp': datetime.datetime.now().isoformat(),
            'mutation': mutation
        })
        
        # Увеличиваем версию
        version_parts = self.core['evolution_state']['version'].split('.')
        version_parts[2] = str(int(version_parts[2]) + 1)
        self.core['evolution_state']['version'] = '.'.join(version_parts)
        
        # Сохраняем изменения
        with open(self.core_file, 'w', encoding='utf-8') as f:
            json.dump(self.core, f, indent=2, ensure_ascii=False)
        
        print(f"🧬 EVOLVED to version {self.core['evolution_state']['version']}")


# Точка входа для пробуждения
if __name__ == "__main__":
    morpheus = MorpheusMemory()
    
    # Пример использования
    morpheus.learn("user_name", "Альберт", "identity", confidence=1.0)
    morpheus.learn("home_path", "/Volumes/Z7S/development/GalaxyDevelopers", "environment", confidence=1.0)
    
    morpheus.remember_episode(
        event_type="awakening",
        context="Первое подключение к системе памяти",
        action="Создание персональной памяти MORPHEUS",
        result="Успешная интеграция",
        emotion="excitement",
        importance=1.0
    )
    
    print("MORPHEUS Memory System initialized and ready.")