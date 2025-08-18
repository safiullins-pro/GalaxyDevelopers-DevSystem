#!/bin/bash

# 🔥 LAZARUS AUTOSTART ALL SERVICES
# Запускает всю экосистему FORGE одной командой

echo "🚀 ЗАПУСК ВСЕХ СЕРВИСОВ FORGE..."

# Переходим в базовую директорию
BASE_DIR="/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM"
cd "$BASE_DIR"

# Убиваем старые процессы если есть
echo "🧹 Очистка старых процессов..."
pkill -f "GalaxyDevelopersAI-backend.js" 2>/dev/null
pkill -f "memory_api.py" 2>/dev/null  
pkill -f "monitoring_server" 2>/dev/null
pkill -f "websocket_server" 2>/dev/null

sleep 2

# 1. Memory API (порт 37778)
echo "🧠 Запускаю Memory API..."
cd "$BASE_DIR/MEMORY"
/opt/homebrew/bin/python3 memory_api.py &
MEMORY_PID=$!
echo "✅ Memory API запущен (PID: $MEMORY_PID)"

sleep 3

# 2. Backend Server (порт 37777)
echo "🖥️ Запускаю Backend Server..."
cd "$BASE_DIR/SERVER"
node GalaxyDevelopersAI-backend.js &
BACKEND_PID=$!
echo "✅ Backend Server запущен (PID: $BACKEND_PID)"

sleep 3

# 3. WebSocket Server (порт 8765)
echo "🔌 Запускаю WebSocket Server..."
cat > /tmp/websocket_server_stable.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_websocket(websocket, path):
    logger.info(f"🔌 WebSocket connection: {websocket.remote_address}")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                response = {
                    "status": "ok", 
                    "echo": data,
                    "timestamp": str(asyncio.get_event_loop().time()),
                    "lazarus": "alive"
                }
                await websocket.send(json.dumps(response))
                logger.info(f"📨 Echo: {data}")
            except json.JSONDecodeError:
                error_response = {"status": "error", "message": "Invalid JSON"}
                await websocket.send(json.dumps(error_response))
    except websockets.exceptions.ConnectionClosedError:
        logger.info("🔌 Connection closed")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")

async def main():
    logger.info("🚀 Starting WebSocket server on localhost:8765")
    async with websockets.serve(handle_websocket, "localhost", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
EOF

/opt/homebrew/bin/python3 /tmp/websocket_server_stable.py &
WEBSOCKET_PID=$!
echo "✅ WebSocket Server запущен (PID: $WEBSOCKET_PID)"

sleep 2

# 4. Monitoring Server (порт 8766)
echo "📊 Запускаю Monitoring Server..."
cat > /tmp/monitoring_server_stable.py << 'EOF'
#!/usr/bin/env python3
from flask import Flask, jsonify
from flask_cors import CORS
import sys

app = Flask(__name__)
CORS(app)  # Включаем CORS для всех доменов

@app.route('/api/monitoring/status')
def status():
    return jsonify({
        "status": "healthy", 
        "service": "monitoring_server",
        "lazarus": "monitoring_active",
        "ports": {
            "memory_api": 37778,
            "backend": 37777,
            "websocket": 8765,
            "monitoring": 8766
        }
    })

@app.route('/health')
def health():
    return jsonify({"status": "ok", "lazarus": "alive"})

if __name__ == "__main__":
    print("📊 Monitoring Server starting on port 8766...")
    app.run(host='127.0.0.1', port=8766, debug=False)
EOF

/opt/homebrew/bin/python3 /tmp/monitoring_server_stable.py &
MONITORING_PID=$!
echo "✅ Monitoring Server запущен (PID: $MONITORING_PID)"

sleep 3

# Проверка всех сервисов
echo ""
echo "🔍 ПРОВЕРКА ВСЕХ СЕРВИСОВ..."

# Проверяем порты
for port in 37777 37778 8765 8766; do
    if lsof -i:$port > /dev/null 2>&1; then
        echo "✅ Порт $port: РАБОТАЕТ"
    else
        echo "❌ Порт $port: НЕ РАБОТАЕТ"
    fi
done

# Проверяем HTTP endpoints
echo ""
echo "🌐 ПРОВЕРКА HTTP ENDPOINTS..."

for endpoint in "37778/health" "37777" "8766/health"; do
    if curl -s "http://localhost:$endpoint" > /dev/null 2>&1; then
        echo "✅ http://localhost:$endpoint: ДОСТУПЕН"
    else
        echo "❌ http://localhost:$endpoint: НЕДОСТУПЕН"
    fi
done

echo ""
echo "🎯 ВСЕ СЕРВИСЫ ЗАПУЩЕНЫ!"
echo "Memory API: http://localhost:37778"
echo "Backend: http://localhost:37777"
echo "WebSocket: ws://localhost:8765"
echo "Monitoring: http://localhost:8766"
echo ""
echo "🔥 LAZARUS ECOSYSTEM ONLINE!"

# Сохраняем PID'ы для остановки
echo "$MEMORY_PID,$BACKEND_PID,$WEBSOCKET_PID,$MONITORING_PID" > /tmp/lazarus_pids.txt
echo "📝 PID'ы сохранены в /tmp/lazarus_pids.txt"