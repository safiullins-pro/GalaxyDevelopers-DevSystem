#!/usr/bin/env python3
"""
🌐 HTTP сервер для интерфейса мониторинга
Запускает веб-сервер для корректной работы fetch и CORS
"""

import http.server
import socketserver
import os
from pathlib import Path

# Настройки
PORT = 8080
INTERFACE_DIR = "/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/INTERFACE"

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP обработчик с поддержкой CORS"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=INTERFACE_DIR, **kwargs)
    
    def end_headers(self):
        """Добавляем CORS заголовки"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Обработка preflight запросов"""
        self.send_response(200)
        self.end_headers()

def main():
    """Запуск сервера"""
    os.chdir(INTERFACE_DIR)
    
    with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
        print(f"""
╔════════════════════════════════════════╗
║   GALAXY INTERFACE SERVER              ║
║   Serving monitoring dashboard         ║
╚════════════════════════════════════════╝

🌐 Interface доступен по адресу:
   http://localhost:{PORT}/index.html

📊 Monitoring API: http://localhost:8766
📡 WebSocket: ws://localhost:8765

Для остановки нажмите Ctrl+C
        """)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Сервер остановлен")

if __name__ == "__main__":
    main()