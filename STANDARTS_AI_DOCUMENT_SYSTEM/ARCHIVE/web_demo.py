#!/usr/bin/env python3
"""
Веб-интерфейс для демонстрации GalaxyDevelopment
"""
from flask import Flask, render_template_string, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import requests
from datetime import datetime

app = Flask(__name__)

# Подключение к базе данных
def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        user='galaxy',
        password='dev2025!',
        database='galaxydevelopment',
        cursor_factory=RealDictCursor
    )

# Главная страница
@app.route('/')
def index():
    return render_template_string("""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌌 GalaxyDevelopment - Система Автоматической Документации</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
            color: #00ff41;
            font-family: 'Courier New', monospace;
            min-height: 100vh;
        }
        
        .header {
            background: rgba(0, 0, 0, 0.9);
            padding: 20px;
            text-align: center;
            border-bottom: 2px solid #00ff41;
        }
        
        .header h1 {
            font-size: 2.5em;
            text-shadow: 0 0 10px #00ff41;
            animation: glow 2s ease-in-out infinite alternate;
        }
        
        @keyframes glow {
            from { text-shadow: 0 0 10px #00ff41, 0 0 20px #00ff41; }
            to { text-shadow: 0 0 20px #00ff41, 0 0 30px #00ff41; }
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .status-card {
            background: rgba(0, 255, 65, 0.1);
            border: 1px solid #00ff41;
            border-radius: 10px;
            padding: 20px;
            transition: all 0.3s ease;
        }
        
        .status-card:hover {
            background: rgba(0, 255, 65, 0.2);
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 255, 65, 0.3);
        }
        
        .status-card h3 {
            color: #ff6b35;
            margin-bottom: 10px;
            font-size: 1.2em;
        }
        
        .status-active {
            color: #00ff41;
            font-weight: bold;
        }
        
        .status-error {
            color: #ff4444;
            font-weight: bold;
        }
        
        .documentation {
            background: rgba(0, 0, 0, 0.8);
            border: 1px solid #00ff41;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .documentation h3 {
            color: #ff6b35;
            margin-bottom: 15px;
        }
        
        .doc-content {
            background: rgba(0, 255, 65, 0.05);
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #00ff41;
            white-space: pre-wrap;
            font-size: 0.9em;
        }
        
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .metric {
            background: rgba(0, 255, 65, 0.1);
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            border: 1px solid #00ff41;
        }
        
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #00ff41;
        }
        
        .metric-label {
            color: #ccc;
            font-size: 0.9em;
        }
        
        .refresh-btn {
            background: linear-gradient(45deg, #00ff41, #ff6b35);
            color: black;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            margin: 10px;
            transition: all 0.3s ease;
        }
        
        .refresh-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(0, 255, 65, 0.4);
        }
        
        .json-data {
            background: #111;
            padding: 15px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 0.8em;
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #333;
        }
        
        .loading {
            text-align: center;
            color: #00ff41;
            font-size: 1.2em;
            animation: pulse 1s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 0.5; }
            50% { opacity: 1; }
            100% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌌 GalaxyDevelopment</h1>
        <p>Система Автоматической Сквозной Документации</p>
        <button class="refresh-btn" onclick="loadData()">🔄 Обновить</button>
    </div>
    
    <div class="container">
        <div class="status-grid">
            <div class="status-card">
                <h3>🔧 Docker Services</h3>
                <div id="docker-status" class="loading">Загрузка...</div>
            </div>
            
            <div class="status-card">
                <h3>🤖 ResearchAgent</h3>
                <div id="agent-status" class="loading">Загрузка...</div>
            </div>
            
            <div class="status-card">
                <h3>📊 Prometheus Metrics</h3>
                <div id="metrics-status" class="loading">Загрузка...</div>
            </div>
            
            <div class="status-card">
                <h3>🗄️ Database</h3>
                <div id="db-status" class="loading">Загрузка...</div>
            </div>
        </div>
        
        <div class="metrics" id="metrics-grid">
            <!-- Метрики будут загружены динамически -->
        </div>
        
        <div class="documentation" id="latest-docs">
            <h3>📝 Последняя сгенерированная документация</h3>
            <div id="doc-content" class="loading">Загрузка...</div>
        </div>
    </div>
    
    <script>
        async function loadData() {
            // Загрузка статуса Docker
            try {
                const dockerResponse = await fetch('/api/docker-status');
                const dockerData = await dockerResponse.json();
                document.getElementById('docker-status').innerHTML = formatDockerStatus(dockerData);
            } catch (e) {
                document.getElementById('docker-status').innerHTML = '<span class="status-error">Ошибка загрузки</span>';
            }
            
            // Загрузка статуса агента
            try {
                const agentResponse = await fetch('/api/agent-status');
                const agentData = await agentResponse.json();
                document.getElementById('agent-status').innerHTML = formatAgentStatus(agentData);
            } catch (e) {
                document.getElementById('agent-status').innerHTML = '<span class="status-error">Ошибка загрузки</span>';
            }
            
            // Загрузка метрик
            try {
                const metricsResponse = await fetch('/api/metrics');
                const metricsData = await metricsResponse.json();
                document.getElementById('metrics-status').innerHTML = '<span class="status-active">✅ Доступны</span>';
                document.getElementById('metrics-grid').innerHTML = formatMetrics(metricsData);
            } catch (e) {
                document.getElementById('metrics-status').innerHTML = '<span class="status-error">❌ Недоступны</span>';
            }
            
            // Загрузка данных БД
            try {
                const dbResponse = await fetch('/api/database');
                const dbData = await dbResponse.json();
                document.getElementById('db-status').innerHTML = formatDbStatus(dbData);
                document.getElementById('doc-content').innerHTML = formatDocumentation(dbData.latest_doc);
            } catch (e) {
                document.getElementById('db-status').innerHTML = '<span class="status-error">Ошибка подключения</span>';
            }
        }
        
        function formatDockerStatus(data) {
            if (!data.services) return '<span class="status-error">Нет данных</span>';
            let html = '';
            data.services.forEach(service => {
                const status = service.status === 'Up' ? 'status-active' : 'status-error';
                html += `<div class="${status}">${service.name}: ${service.status}</div>`;
            });
            return html;
        }
        
        function formatAgentStatus(data) {
            if (data.error) return `<span class="status-error">❌ ${data.error}</span>`;
            return `
                <div class="status-active">✅ Работает на порту ${data.port}</div>
                <div>PID: ${data.pid || 'N/A'}</div>
                <div>Статус: ${data.healthy ? 'Здоров' : 'Проблемы'}</div>
            `;
        }
        
        function formatMetrics(data) {
            if (data.error) return '<div class="status-error">Ошибка загрузки метрик</div>';
            return `
                <div class="metric">
                    <div class="metric-value">${data.tasks_total || 0}</div>
                    <div class="metric-label">Задач обработано</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${data.active_tasks || 0}</div>
                    <div class="metric-label">Активных задач</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${data.errors_total || 0}</div>
                    <div class="metric-label">Ошибок</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${data.processing_time || '0.00'}с</div>
                    <div class="metric-label">Время обработки</div>
                </div>
            `;
        }
        
        function formatDbStatus(data) {
            if (data.error) return `<span class="status-error">❌ ${data.error}</span>`;
            return `
                <div class="status-active">✅ Подключена</div>
                <div>Процессов: ${data.processes_count}</div>
                <div>Документов: ${data.docs_count}</div>
            `;
        }
        
        function formatDocumentation(doc) {
            if (!doc) return 'Нет данных';
            const content = JSON.parse(doc.content);
            return `
                <div><strong>Процесс:</strong> ${doc.process_id}</div>
                <div><strong>Качество:</strong> ${(doc.quality_score * 100).toFixed(1)}%</div>
                <div><strong>Создан:</strong> ${new Date(doc.created_at).toLocaleString()}</div>
                <div><strong>Создатель:</strong> ${doc.created_by}</div>
                <br>
                <div class="json-data">${JSON.stringify(content, null, 2)}</div>
            `;
        }
        
        // Автообновление каждые 10 секунд
        setInterval(loadData, 10000);
        
        // Первоначальная загрузка
        loadData();
    </script>
</body>
</html>
    """)

# API endpoints
@app.route('/api/docker-status')
def docker_status():
    try:
        import subprocess
        result = subprocess.run(['docker-compose', 'ps', '--format', 'json'], 
                               capture_output=True, text=True, cwd='/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem')
        if result.returncode == 0:
            services = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    service = json.loads(line)
                    services.append({
                        'name': service.get('Service', 'unknown'),
                        'status': service.get('State', 'unknown')
                    })
            return jsonify({'services': services})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/agent-status')
def agent_status():
    try:
        response = requests.get('http://localhost:8001/metrics', timeout=5)
        if response.status_code == 200:
            return jsonify({
                'port': 8001,
                'healthy': True,
                'pid': 'running'
            })
    except Exception as e:
        return jsonify({'error': 'Agent недоступен'})

@app.route('/api/metrics')
def metrics():
    try:
        response = requests.get('http://localhost:8001/metrics', timeout=5)
        if response.status_code == 200:
            metrics_text = response.text
            # Парсинг простых метрик
            data = {}
            for line in metrics_text.split('\n'):
                if 'research_agent_tasks_total' in line and not line.startswith('#'):
                    data['tasks_total'] = float(line.split()[-1])
                elif 'research_agent_active_tasks' in line and not line.startswith('#'):
                    data['active_tasks'] = float(line.split()[-1])
                elif 'research_agent_errors_total{error_type="health_check"}' in line:
                    data['errors_total'] = float(line.split()[-1])
                elif 'research_agent_processing_seconds_sum' in line and not line.startswith('#'):
                    data['processing_time'] = float(line.split()[-1])
            return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/database')
def database():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Подсчет процессов
        cur.execute("SELECT COUNT(*) FROM processes")
        processes_count = cur.fetchone()['count']
        
        # Подсчет документации
        cur.execute("SELECT COUNT(*) FROM documentation")
        docs_count = cur.fetchone()['count']
        
        # Последняя документация
        cur.execute("""
            SELECT process_id, content, quality_score, created_at, created_by 
            FROM documentation 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        latest_doc = cur.fetchone()
        
        conn.close()
        
        return jsonify({
            'processes_count': processes_count,
            'docs_count': docs_count,
            'latest_doc': dict(latest_doc) if latest_doc else None
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999, debug=True)