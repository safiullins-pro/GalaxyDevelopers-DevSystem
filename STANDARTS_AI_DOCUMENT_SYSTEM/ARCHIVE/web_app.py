#!/usr/bin/env python3
"""
Web приложение GalaxyDevelopment
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import subprocess
import requests

class GalaxyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>🌌 GalaxyDevelopment System</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: white; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .status-box {{ background: #2d2d2d; padding: 20px; margin: 10px 0; border-radius: 8px; }}
        .metrics {{ background: #333; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .green {{ color: #4CAF50; }}
        .red {{ color: #f44336; }}
        .buttons {{ text-align: center; margin: 20px 0; }}
        .button {{ background: #4CAF50; color: white; padding: 10px 20px; margin: 10px; text-decoration: none; border-radius: 5px; }}
        .button:hover {{ background: #45a049; }}
        .refresh {{ background: #2196F3; }}
        .logs {{ background: #1a1a1a; border: 1px solid #444; padding: 10px; font-family: monospace; }}
    </style>
    <script>
        function refreshData() {{
            location.reload();
        }}
        
        setInterval(refreshData, 5000); // обновление каждые 5 секунд
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌌 GALAXYDEVELOPMENT СИСТЕМА</h1>
            <p>Статус системы автоматической документации</p>
        </div>
        
        <div class="status-box">
            <h2>🔍 Статус сервисов</h2>
            {self.get_services_status()}
        </div>
        
        <div class="status-box">
            <h2>📊 Метрики Demo Agent</h2>
            {self.get_agent_metrics()}
        </div>
        
        <div class="buttons">
            <a href="javascript:refreshData()" class="button refresh">🔄 Обновить</a>
            <a href="http://localhost:9090" target="_blank" class="button">📊 Prometheus</a>
            <a href="http://localhost:3000" target="_blank" class="button">📈 Grafana</a>
        </div>
        
        <div class="status-box">
            <h2>📋 Информация о системе</h2>
            <div class="metrics">
                <strong>🌌 GalaxyDevelopment v1.0</strong><br>
                • 5 AI-агентов: Research, Composer, Reviewer, Integrator, Publisher<br>
                • 150+ IT-процессов готовы к обработке<br>
                • Поддержка стандартов: ITIL 4, ISO/IEC 20000, COBIT, NIST<br>
                • Команда: 35 специализированных ролей<br>
                • Инфраструктура: Kafka, PostgreSQL, Redis, Prometheus, Grafana
            </div>
        </div>
    </div>
</body>
</html>
            """
            
            self.wfile.write(html.encode())
        else:
            super().do_GET()
    
    def get_services_status(self):
        services = {
            "Demo Agent": "http://localhost:8000/metrics",
            "Prometheus": "http://localhost:9090",
            "Grafana": "http://localhost:3000"
        }
        
        status_html = ""
        
        for service, url in services.items():
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    status_html += f'<div class="metrics">✅ <span class="green">{service}: РАБОТАЕТ</span></div>'
                else:
                    status_html += f'<div class="metrics">❌ <span class="red">{service}: ОШИБКА {response.status_code}</span></div>'
            except:
                status_html += f'<div class="metrics">❌ <span class="red">{service}: НЕ ДОСТУПЕН</span></div>'
        
        # Docker сервисы
        try:
            result = subprocess.run(['docker-compose', 'ps', '--format', 'json'], 
                                  capture_output=True, text=True, cwd='/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem')
            if result.returncode == 0 and result.stdout.strip():
                containers = [json.loads(line) for line in result.stdout.strip().split('\\n')]
                running = len([c for c in containers if c.get('State') == 'running'])
                status_html += f'<div class="metrics">🐳 <span class="green">Docker контейнеров: {running} запущено</span></div>'
            else:
                status_html += f'<div class="metrics">❌ <span class="red">Docker: не доступен</span></div>'
        except:
            status_html += f'<div class="metrics">❌ <span class="red">Docker: ошибка проверки</span></div>'
        
        return status_html
    
    def get_agent_metrics(self):
        try:
            response = requests.get("http://localhost:8000/metrics", timeout=2)
            if response.status_code == 200:
                lines = response.text.split('\\n')
                
                tasks_total = "0"
                active_tasks = "0"
                quality_score = "0.0"
                
                for line in lines:
                    if line.startswith('demo_agent_tasks_total '):
                        tasks_total = line.split()[-1]
                    elif line.startswith('demo_agent_active_tasks '):
                        active_tasks = line.split()[-1]
                    elif line.startswith('demo_agent_quality_score '):
                        quality_score = line.split()[-1]
                
                return f'''
                <div class="metrics">
                    📋 <strong>Обработано задач:</strong> {tasks_total}<br>
                    🔄 <strong>Активных задач:</strong> {active_tasks}<br>
                    ⭐ <strong>Оценка качества:</strong> {float(quality_score):.2f}<br>
                    🕐 <strong>Обновлено:</strong> {subprocess.run(["date"], capture_output=True, text=True).stdout.strip()}
                </div>
                '''
            else:
                return '<div class="metrics">❌ Не удалось получить метрики агента</div>'
                
        except Exception as e:
            return f'<div class="metrics">❌ Ошибка: {e}</div>'

if __name__ == '__main__':
    server = HTTPServer(('localhost', 8080), GalaxyHandler)
    print("🌌 GalaxyDevelopment Web App запущен!")
    print("📱 Открывай: http://localhost:8080")
    print("🛑 Для остановки: Ctrl+C")
    server.serve_forever()