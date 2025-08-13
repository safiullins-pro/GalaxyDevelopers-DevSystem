#!/usr/bin/env python3
"""
Memory API Server для интеграции с GalaxyDevelopersAI backend
Работает на порту 37778 параллельно с основным сервером
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sqlite3
import time
from pathlib import Path
from datetime import datetime
import sys
import os

# Добавляем путь к модулям памяти
sys.path.append(str(Path(__file__).parent))

app = Flask(__name__)
CORS(app)

class MemoryAPI:
    def __init__(self):
        self.memory_dir = Path(__file__).parent
        self.db_path = self.memory_dir / 'unified_memory.db'
        self.real_memory_db = self.memory_dir / 'real_memory' / 'memory.db'
        self.init_database()
        
    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица для диалогов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp REAL,
                user_message TEXT,
                ai_response TEXT,
                context_data TEXT,
                model TEXT
            )
        ''')
        
        # Таблица для знаний
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                value TEXT,
                importance INTEGER DEFAULT 5,
                last_updated REAL,
                source TEXT
            )
        ''')
        
        # Таблица для промптов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                content TEXT,
                category TEXT,
                usage_count INTEGER DEFAULT 0,
                created_at REAL,
                last_used REAL,
                effectiveness_score REAL DEFAULT 5.0
            )
        ''')
        
        # Таблица для слепков контекста
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS context_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id TEXT UNIQUE,
                context_data TEXT,
                metadata TEXT,
                created_at REAL,
                tags TEXT,
                importance INTEGER DEFAULT 5
            )
        ''')
        
        # Таблица для векторных эмбеддингов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vector_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_hash TEXT UNIQUE,
                original_text TEXT,
                embedding BLOB,
                metadata TEXT,
                created_at REAL,
                search_count INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def save_conversation(self, user_message, ai_response, context=None, model='gemini'):
        """Сохранение диалога в память"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        session_id = f"session_{int(time.time())}"
        timestamp = time.time()
        context_json = json.dumps(context) if context else '{}'
        
        cursor.execute('''
            INSERT INTO conversations (session_id, timestamp, user_message, ai_response, context_data, model)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, timestamp, user_message, ai_response, context_json, model))
        
        conn.commit()
        conn.close()
        
        return session_id
        
    def get_context(self, limit=10):
        """Получение контекста из последних диалогов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_message, ai_response, timestamp, model
            FROM conversations
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Форматируем контекст
        context = []
        for row in reversed(rows):  # Возвращаем в хронологическом порядке
            user_msg, ai_resp, ts, model = row
            dt = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            context.append({
                'timestamp': dt,
                'user': user_msg,
                'assistant': ai_resp,
                'model': model
            })
            
        return context
        
    def save_knowledge(self, key, value, importance=5, source='user'):
        """Сохранение знания/факта"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = time.time()
        
        cursor.execute('''
            INSERT OR REPLACE INTO knowledge (key, value, importance, last_updated, source)
            VALUES (?, ?, ?, ?, ?)
        ''', (key, value, importance, timestamp, source))
        
        conn.commit()
        conn.close()
        
    def get_knowledge(self, key=None):
        """Получение знаний"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if key:
            cursor.execute('SELECT value FROM knowledge WHERE key = ?', (key,))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
        else:
            cursor.execute('SELECT key, value, importance FROM knowledge ORDER BY importance DESC')
            rows = cursor.fetchall()
            conn.close()
            return [{'key': r[0], 'value': r[1], 'importance': r[2]} for r in rows]
    
    def save_prompt(self, name, content, category='general'):
        """Сохранение промпта"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = time.time()
        cursor.execute('''
            INSERT OR REPLACE INTO prompts (name, content, category, created_at, last_used)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, content, category, timestamp, timestamp))
        
        conn.commit()
        conn.close()
        
    def get_prompts(self, category=None):
        """Получение промптов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if category:
            cursor.execute('SELECT name, content, category, effectiveness_score FROM prompts WHERE category = ? ORDER BY effectiveness_score DESC', (category,))
        else:
            cursor.execute('SELECT name, content, category, effectiveness_score FROM prompts ORDER BY effectiveness_score DESC')
        
        rows = cursor.fetchall()
        conn.close()
        return [{'name': r[0], 'content': r[1], 'category': r[2], 'score': r[3]} for r in rows]
    
    def save_context_snapshot(self, context_data, tags=None, metadata=None):
        """Сохранение слепка контекста"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        import hashlib
        snapshot_id = hashlib.md5(str(time.time()).encode()).hexdigest()
        timestamp = time.time()
        tags_str = json.dumps(tags) if tags else '[]'
        metadata_str = json.dumps(metadata) if metadata else '{}'
        
        cursor.execute('''
            INSERT INTO context_snapshots (snapshot_id, context_data, metadata, created_at, tags)
            VALUES (?, ?, ?, ?, ?)
        ''', (snapshot_id, context_data, metadata_str, timestamp, tags_str))
        
        conn.commit()
        conn.close()
        return snapshot_id
    
    def get_context_snapshots(self, limit=10):
        """Получение слепков контекста"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT snapshot_id, context_data, metadata, created_at, tags, importance
            FROM context_snapshots
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': r[0],
            'context': r[1],
            'metadata': json.loads(r[2]),
            'created_at': datetime.fromtimestamp(r[3]).strftime('%Y-%m-%d %H:%M:%S'),
            'tags': json.loads(r[4]),
            'importance': r[5]
        } for r in rows]
    
    def save_vector_embedding(self, text, embedding=None):
        """Сохранение векторного эмбеддинга"""
        import hashlib
        import numpy as np
        
        content_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Заглушка для эмбеддинга - в реальности нужен векторизатор
        if embedding is None:
            embedding = np.random.rand(768).tobytes()  # Симуляция 768-мерного вектора
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO vector_embeddings (content_hash, original_text, embedding, created_at)
            VALUES (?, ?, ?, ?)
        ''', (content_hash, text, embedding, time.time()))
        
        conn.commit()
        conn.close()
        return content_hash
    
    def vector_search(self, query_text, limit=5):
        """Векторный поиск (заглушка)"""
        # В реальности здесь должен быть косинусный поиск по векторам
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Пока простой текстовый поиск
        cursor.execute('''
            SELECT original_text, content_hash
            FROM vector_embeddings
            WHERE original_text LIKE ?
            ORDER BY search_count DESC
            LIMIT ?
        ''', (f'%{query_text}%', limit))
        
        rows = cursor.fetchall()
        
        # Увеличиваем счетчик поиска
        for row in rows:
            cursor.execute('UPDATE vector_embeddings SET search_count = search_count + 1 WHERE content_hash = ?', (row[1],))
        
        conn.commit()
        conn.close()
        
        return [{'text': r[0], 'hash': r[1]} for r in rows]

# Создаем экземпляр API
memory_api = MemoryAPI()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'memory_api'})

@app.route('/save_conversation', methods=['POST'])
def save_conversation():
    """Сохранение диалога"""
    data = request.json
    session_id = memory_api.save_conversation(
        user_message=data.get('user_message'),
        ai_response=data.get('ai_response'),
        context=data.get('context'),
        model=data.get('model', 'gemini')
    )
    return jsonify({'success': True, 'session_id': session_id})

@app.route('/get_context', methods=['GET'])
def get_context():
    """Получение контекста"""
    limit = request.args.get('limit', 10, type=int)
    context = memory_api.get_context(limit)
    return jsonify({'context': context})

@app.route('/save_knowledge', methods=['POST'])
def save_knowledge():
    """Сохранение знания"""
    data = request.json
    memory_api.save_knowledge(
        key=data.get('key'),
        value=data.get('value'),
        importance=data.get('importance', 5),
        source=data.get('source', 'user')
    )
    return jsonify({'success': True})

@app.route('/get_knowledge', methods=['GET'])
def get_knowledge():
    """Получение знаний"""
    key = request.args.get('key')
    knowledge = memory_api.get_knowledge(key)
    return jsonify({'knowledge': knowledge})

@app.route('/save_prompt', methods=['POST'])
def save_prompt():
    """Сохранение промпта"""
    data = request.json
    memory_api.save_prompt(
        name=data.get('name'),
        content=data.get('content'),
        category=data.get('category', 'general')
    )
    return jsonify({'success': True})

@app.route('/get_prompts', methods=['GET'])
def get_prompts():
    """Получение промптов"""
    category = request.args.get('category')
    prompts = memory_api.get_prompts(category)
    return jsonify({'prompts': prompts})

@app.route('/save_snapshot', methods=['POST'])
def save_snapshot():
    """Сохранение слепка контекста"""
    data = request.json
    snapshot_id = memory_api.save_context_snapshot(
        context_data=data.get('context'),
        tags=data.get('tags'),
        metadata=data.get('metadata')
    )
    return jsonify({'success': True, 'snapshot_id': snapshot_id})

@app.route('/get_snapshots', methods=['GET'])
def get_snapshots():
    """Получение слепков контекста"""
    limit = request.args.get('limit', 10, type=int)
    snapshots = memory_api.get_context_snapshots(limit)
    return jsonify({'snapshots': snapshots})

@app.route('/save_embedding', methods=['POST'])
def save_embedding():
    """Сохранение векторного эмбеддинга"""
    data = request.json
    content_hash = memory_api.save_vector_embedding(
        text=data.get('text'),
        embedding=data.get('embedding')
    )
    return jsonify({'success': True, 'hash': content_hash})

@app.route('/vector_search', methods=['POST'])
def vector_search():
    """Векторный поиск"""
    query = request.json.get('query', '')
    limit = request.json.get('limit', 5)
    results = memory_api.vector_search(query, limit)
    return jsonify({'results': results})

@app.route('/search_memory', methods=['POST'])
def search_memory():
    """Поиск в памяти"""
    query = request.json.get('query', '')
    
    conn = sqlite3.connect(memory_api.db_path)
    cursor = conn.cursor()
    
    # Ищем в диалогах
    cursor.execute('''
        SELECT user_message, ai_response, timestamp
        FROM conversations
        WHERE user_message LIKE ? OR ai_response LIKE ?
        ORDER BY timestamp DESC
        LIMIT 20
    ''', (f'%{query}%', f'%{query}%'))
    
    conversations = cursor.fetchall()
    
    # Ищем в знаниях
    cursor.execute('''
        SELECT key, value, importance
        FROM knowledge
        WHERE key LIKE ? OR value LIKE ?
        ORDER BY importance DESC
    ''', (f'%{query}%', f'%{query}%'))
    
    knowledge = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'conversations': [
            {
                'user': c[0],
                'assistant': c[1],
                'timestamp': datetime.fromtimestamp(c[2]).strftime('%Y-%m-%d %H:%M:%S')
            } for c in conversations
        ],
        'knowledge': [
            {'key': k[0], 'value': k[1], 'importance': k[2]} for k in knowledge
        ]
    })

if __name__ == '__main__':
    print("🧠 Memory API starting on port 37778...")
    app.run(host='127.0.0.1', port=37778, debug=False)