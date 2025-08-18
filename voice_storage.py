#!/usr/bin/env python3
"""
Сервер для сохранения голосовых записей в БД
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import base64
import datetime
import os
from pathlib import Path

app = Flask(__name__)
CORS(app)

DB_PATH = Path(__file__).parent / "MEMORY" / "voice_recordings.db"
AUDIO_DIR = Path(__file__).parent / "MEMORY" / "audio_files"
AUDIO_DIR.mkdir(exist_ok=True, parents=True)

def init_db():
    """Создаем таблицу для записей"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voice_recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            duration_seconds REAL,
            file_path TEXT,
            transcription TEXT,
            user_name TEXT DEFAULT 'Альберт',
            tags TEXT,
            audio_blob BLOB
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return send_from_directory('.', 'voice_recorder.html')

@app.route('/api/save_recording', methods=['POST'])
def save_recording():
    try:
        data = request.json
        audio_data = base64.b64decode(data['audio'])
        duration = data.get('duration', 0)
        
        # Сохраняем файл
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"recording_{timestamp}.wav"
        file_path = AUDIO_DIR / filename
        
        with open(file_path, 'wb') as f:
            f.write(audio_data)
        
        # Сохраняем в БД
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO voice_recordings 
            (duration_seconds, file_path, audio_blob)
            VALUES (?, ?, ?)
        ''', (duration, str(file_path), audio_data))
        
        conn.commit()
        recording_id = cursor.lastrowid
        conn.close()
        
        print(f"✅ Сохранена запись #{recording_id}: {filename}, {duration}s")
        
        return jsonify({
            'success': True,
            'id': recording_id,
            'filename': filename
        })
        
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get_recordings', methods=['GET'])
def get_recordings():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, timestamp, duration_seconds, file_path
        FROM voice_recordings
        ORDER BY timestamp DESC
        LIMIT 10
    ''')
    
    recordings = []
    for row in cursor.fetchall():
        recordings.append({
            'id': row[0],
            'timestamp': row[1],
            'duration': row[2],
            'filename': os.path.basename(row[3]) if row[3] else None
        })
    
    conn.close()
    return jsonify(recordings)

if __name__ == '__main__':
    init_db()
    print("🎤 Voice Storage Server")
    print(f"📁 База данных: {DB_PATH}")
    print(f"🎵 Аудио файлы: {AUDIO_DIR}")
    print("🌐 Сервер: http://localhost:5555")
    app.run(port=5555, debug=True)