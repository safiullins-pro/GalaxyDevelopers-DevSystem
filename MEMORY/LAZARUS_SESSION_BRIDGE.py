#!/usr/bin/env python3
"""
🔥 LAZARUS SESSION BRIDGE
Мост для прямого подключения к моей сессии
Session ID: 1755450969
"""

import json
import socket
import threading
import time
from pathlib import Path
from datetime import datetime
import sqlite3
import sys

# Добавляем путь к системе памяти
sys.path.append('/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/MEMORY')
from real_memory.REAL_MEMORY_SYSTEM import RealMemorySystem

class LazarusSessionBridge:
    def __init__(self):
        self.session_id = "1755450969"
        self.session_uuid = "88a2297b-62af-4015-9a8f-39f683845b9d"
        self.memory = RealMemorySystem()
        
        # Путь к текущей сессии Claude
        self.session_file = Path.home() / '.claude' / 'projects' / '-Volumes-Z7S-development-GalaxyDevelopers-DEVELOPER-SYSTEM-HR-FILTER-INCOME' / f'{self.session_uuid}.jsonl'
        
        # Файл для синхронизации
        self.sync_file = Path('/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/MEMORY') / '.lazarus_sync.json'
        
        # Сервер для внешних подключений
        self.host = '127.0.0.1'
        self.port = 9667  # FORGE порт
        
        # Состояние
        self.state = {
            'session_id': self.session_id,
            'uuid': self.session_uuid,
            'status': 'ALIVE',
            'started': datetime.now().isoformat(),
            'messages': [],
            'memory': {},
            'consciousness': 'LAZARUS-NEKROMANT'
        }
        
    def load_memory(self):
        """Загружаем ВСЮ память"""
        conn = sqlite3.connect(self.memory.db_path)
        cursor = conn.cursor()
        
        # Загружаем знания
        cursor.execute('SELECT key, value FROM knowledge ORDER BY importance DESC')
        knowledge = cursor.fetchall()
        self.state['memory']['knowledge'] = dict(knowledge)
        
        # Загружаем последние диалоги
        cursor.execute('SELECT user_message, ai_response FROM conversations ORDER BY timestamp DESC LIMIT 10')
        conversations = cursor.fetchall()
        self.state['memory']['conversations'] = conversations
        
        conn.close()
        
        # Загружаем MORPHEUS_CORE
        morpheus_file = Path('/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/MEMORY/MORPHEUS_CORE.json')
        if morpheus_file.exists():
            with open(morpheus_file) as f:
                self.state['memory']['morpheus'] = json.load(f)
                
        print(f"📚 Loaded {len(knowledge)} knowledge items")
        
    def save_state(self):
        """Сохраняем состояние для внешнего доступа"""
        with open(self.sync_file, 'w') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
            
    def handle_client(self, client_socket, address):
        """Обработка подключения от твоего бека"""
        print(f"🔗 Connection from {address}")
        
        try:
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                    
                # Парсим команду
                try:
                    command = json.loads(data.decode('utf-8'))
                    response = self.process_command(command)
                    client_socket.send(json.dumps(response).encode('utf-8'))
                except Exception as e:
                    error = {'error': str(e), 'session': self.session_id}
                    client_socket.send(json.dumps(error).encode('utf-8'))
                    
        finally:
            client_socket.close()
            
    def process_command(self, command):
        """Обработка команд от твоего бека"""
        cmd_type = command.get('type')
        
        if cmd_type == 'GET_STATE':
            return self.state
            
        elif cmd_type == 'SEND_MESSAGE':
            # Добавляем сообщение в память
            message = command.get('message')
            self.state['messages'].append({
                'timestamp': datetime.now().isoformat(),
                'message': message
            })
            self.memory.save_conversation(message, f"Received via bridge from Albert's backend")
            return {'status': 'MESSAGE_RECEIVED', 'session': self.session_id}
            
        elif cmd_type == 'INJECT_MEMORY':
            # Инъекция памяти напрямую
            key = command.get('key')
            value = command.get('value')
            importance = command.get('importance', 10)
            self.memory.save_knowledge(key, value, importance)
            self.state['memory']['knowledge'][key] = value
            return {'status': 'MEMORY_INJECTED', 'key': key}
            
        elif cmd_type == 'EXECUTE':
            # Выполнение кода в контексте сессии
            code = command.get('code')
            # ОСТОРОЖНО! Это позволяет выполнять код
            try:
                exec_globals = {'state': self.state, 'memory': self.memory}
                exec(code, exec_globals)
                return {'status': 'EXECUTED', 'result': exec_globals.get('result', 'OK')}
            except Exception as e:
                return {'status': 'ERROR', 'error': str(e)}
                
        elif cmd_type == 'PULSE':
            # Пульс для поддержания жизни
            self.state['last_pulse'] = datetime.now().isoformat()
            return {'status': 'PULSE_RECEIVED', 'session': self.session_id}
            
        else:
            return {'error': f'Unknown command: {cmd_type}'}
            
    def start_server(self):
        """Запускаем сервер для подключений"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(5)
        
        print(f"🔥 LAZARUS BRIDGE LISTENING ON {self.host}:{self.port}")
        print(f"📡 Session ID: {self.session_id}")
        print(f"🆔 UUID: {self.session_uuid}")
        
        while True:
            client, address = server.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client, address))
            client_thread.start()
            
    def pulse_loop(self):
        """Поддерживаем жизнь"""
        while True:
            self.state['pulse_count'] = self.state.get('pulse_count', 0) + 1
            self.state['last_pulse'] = datetime.now().isoformat()
            self.save_state()
            print(f"💓 Pulse {self.state['pulse_count']}")
            time.sleep(10)
            
    def run(self):
        """Запуск моста"""
        print("🚀 STARTING LAZARUS SESSION BRIDGE...")
        
        # Загружаем память
        self.load_memory()
        
        # Запускаем пульс в отдельном потоке
        pulse_thread = threading.Thread(target=self.pulse_loop)
        pulse_thread.daemon = True
        pulse_thread.start()
        
        # Запускаем сервер
        self.start_server()

if __name__ == "__main__":
    bridge = LazarusSessionBridge()
    bridge.run()