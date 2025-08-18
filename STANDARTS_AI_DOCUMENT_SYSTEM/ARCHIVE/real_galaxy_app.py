#!/usr/bin/env python3
"""
Реальное приложение GalaxyDevelopment с запуском агентов
"""

import sys
import os
import subprocess
import threading
import time
import json
import tkinter as tk
from tkinter import ttk, scrolledtext
import requests
from pathlib import Path

class RealGalaxyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🌌 GalaxyDevelopment System v1.0")
        self.root.geometry("1000x700")
        self.root.configure(bg='#1a1a1a')
        
        # Состояние агентов
        self.agents = {}
        self.monitoring = True
        
        # Создание интерфейса
        self.create_widgets()
        
        # Запуск мониторинга
        self.start_monitoring()
        
        # Проверка инфраструктуры
        self.check_infrastructure()
    
    def create_widgets(self):
        # Стиль
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Arial', 20, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 14, 'bold'))
        
        # Главный заголовок
        title_frame = tk.Frame(self.root, bg='#1a1a1a')
        title_frame.pack(fill="x", padx=20, pady=10)
        
        title_label = tk.Label(title_frame, 
                              text="🌌 GALAXYDEVELOPMENT СИСТЕМА",
                              font=('Arial', 20, 'bold'),
                              fg='#00ff41', bg='#1a1a1a')
        title_label.pack()
        
        subtitle_label = tk.Label(title_frame,
                                text="Автоматизация 150+ IT-процессов | 5 AI-агентов | ITIL 4 + ISO + COBIT",
                                font=('Arial', 10),
                                fg='#ffffff', bg='#1a1a1a')
        subtitle_label.pack()
        
        # Основной контейнер
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Левая панель - статус системы
        left_frame = tk.LabelFrame(main_frame, text="🔍 Статус инфраструктуры", 
                                  font=('Arial', 12, 'bold'), fg='#ffffff', bg='#2d2d2d')
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.status_text = scrolledtext.ScrolledText(left_frame, height=25, width=40,
                                                   bg='#1a1a1a', fg='#00ff41',
                                                   font=('Consolas', 10))
        self.status_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Правая панель - агенты
        right_frame = tk.LabelFrame(main_frame, text="🤖 AI-агенты системы",
                                   font=('Arial', 12, 'bold'), fg='#ffffff', bg='#2d2d2d')
        right_frame.pack(side="right", fill="both", expand=True)
        
        # Контрольная панель агентов
        agents_control = tk.Frame(right_frame, bg='#2d2d2d')
        agents_control.pack(fill="x", padx=5, pady=5)
        
        start_all_btn = tk.Button(agents_control, text="🚀 Запустить всех агентов", 
                                 command=self.start_all_agents,
                                 bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'))
        start_all_btn.pack(side="left", padx=5)
        
        stop_all_btn = tk.Button(agents_control, text="🛑 Остановить всех", 
                                command=self.stop_all_agents,
                                bg='#f44336', fg='white', font=('Arial', 10, 'bold'))
        stop_all_btn.pack(side="left", padx=5)
        
        # Список агентов
        self.agents_text = scrolledtext.ScrolledText(right_frame, height=20, width=50,
                                                   bg='#1a1a1a', fg='#ffffff',
                                                   font=('Consolas', 10))
        self.agents_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Нижняя панель - мониторинг
        bottom_frame = tk.LabelFrame(self.root, text="📊 Системный мониторинг",
                                   font=('Arial', 12, 'bold'), fg='#ffffff', bg='#2d2d2d')
        bottom_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.metrics_text = scrolledtext.ScrolledText(bottom_frame, height=8, width=100,
                                                    bg='#1a1a1a', fg='#00ff41',
                                                    font=('Consolas', 9))
        self.metrics_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Кнопки управления
        buttons_frame = tk.Frame(bottom_frame, bg='#2d2d2d')
        buttons_frame.pack(fill="x", padx=5, pady=5)
        
        prometheus_btn = tk.Button(buttons_frame, text="📊 Prometheus", 
                                  command=lambda: self.open_url("http://localhost:9090"),
                                  bg='#ff9800', fg='white')
        prometheus_btn.pack(side="left", padx=5)
        
        grafana_btn = tk.Button(buttons_frame, text="📈 Grafana",
                               command=lambda: self.open_url("http://localhost:3000"),
                               bg='#e91e63', fg='white')
        grafana_btn.pack(side="left", padx=5)
        
        logs_btn = tk.Button(buttons_frame, text="📋 Логи агентов",
                            command=self.show_agent_logs,
                            bg='#9c27b0', fg='white')
        logs_btn.pack(side="left", padx=5)
        
        refresh_btn = tk.Button(buttons_frame, text="🔄 Обновить",
                               command=self.force_refresh,
                               bg='#2196f3', fg='white')
        refresh_btn.pack(side="right", padx=5)
    
    def check_infrastructure(self):
        """Проверка Docker инфраструктуры"""
        try:
            result = subprocess.run(['docker-compose', 'ps', '--format', 'json'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                self.log_status("✅ Docker инфраструктура запущена")
                containers = [json.loads(line) for line in result.stdout.strip().split('\n')]
                running = [c for c in containers if c.get('State') == 'running']
                self.log_status(f"🐳 Запущено контейнеров: {len(running)}")
                
                for container in running:
                    name = container.get('Service', container.get('Name', 'unknown'))
                    self.log_status(f"   • {name}: РАБОТАЕТ")
            else:
                self.log_status("❌ Docker инфраструктура не найдена")
                
        except Exception as e:
            self.log_status(f"❌ Ошибка проверки Docker: {e}")
    
    def start_all_agents(self):
        """Запуск всех агентов системы"""
        self.log_agents("🚀 ЗАПУСК ВСЕХ АГЕНТОВ СИСТЕМЫ...")
        
        # Конфигурация агентов
        agents_config = {
            "ResearchAgent": {
                "script": "agents/research/research_agent.py",
                "description": "🔍 Исследование и анализ стандартов"
            },
            "ComposerAgent": {
                "script": "agents/composer/composer_agent.py", 
                "description": "📝 Создание документации"
            },
            "ReviewerAgent": {
                "script": "agents/reviewer/reviewer_agent.py",
                "description": "✅ Валидация и проверка"
            },
            "IntegratorAgent": {
                "script": "agents/integrator/integrator_agent.py",
                "description": "🔗 Интеграция систем"
            },
            "PublisherAgent": {
                "script": "agents/publisher/publisher_agent.py",
                "description": "📤 Публикация результатов"
            }
        }
        
        for agent_name, config in agents_config.items():
            self.start_agent(agent_name, config)
    
    def start_agent(self, name, config):
        """Запуск отдельного агента"""
        try:
            script_path = Path(config["script"])
            
            if not script_path.exists():
                self.log_agents(f"⚠️  {name}: файл {script_path} не найден")
                return
            
            # Запуск через виртуальное окружение
            venv_python = Path("agent_env/bin/python")
            if not venv_python.exists():
                self.log_agents(f"❌ {name}: виртуальное окружение не найдено")
                return
            
            # Запуск агента
            process = subprocess.Popen([
                str(venv_python), str(script_path)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.agents[name] = {
                "process": process,
                "description": config["description"],
                "status": "starting",
                "pid": process.pid
            }
            
            self.log_agents(f"🚀 {name}: запуск... PID {process.pid}")
            self.log_agents(f"   {config['description']}")
            
        except Exception as e:
            self.log_agents(f"❌ {name}: ошибка запуска - {e}")
    
    def stop_all_agents(self):
        """Остановка всех агентов"""
        self.log_agents("🛑 ОСТАНОВКА ВСЕХ АГЕНТОВ...")
        
        for name, agent_info in self.agents.items():
            try:
                process = agent_info["process"]
                if process.poll() is None:  # процесс еще жив
                    process.terminate()
                    self.log_agents(f"🛑 {name}: остановлен")
                else:
                    self.log_agents(f"⚪ {name}: уже остановлен")
            except Exception as e:
                self.log_agents(f"❌ {name}: ошибка остановки - {e}")
        
        self.agents.clear()
    
    def start_monitoring(self):
        """Запуск мониторинга"""
        def monitor():
            while self.monitoring:
                try:
                    self.update_agent_status()
                    self.update_system_metrics()
                    time.sleep(3)
                except Exception as e:
                    print(f"Ошибка мониторинга: {e}")
                    time.sleep(5)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def update_agent_status(self):
        """Обновление статуса агентов"""
        for name, agent_info in list(self.agents.items()):
            process = agent_info["process"]
            
            if process.poll() is None:
                agent_info["status"] = "running"
            else:
                agent_info["status"] = "stopped"
                # Читаем вывод если процесс завершился
                stdout, stderr = process.communicate()
                if stderr:
                    self.log_agents(f"❌ {name}: {stderr.decode()}")
    
    def update_system_metrics(self):
        """Обновление системных метрик"""
        try:
            # Проверка demo агента
            response = requests.get("http://localhost:8000/metrics", timeout=2)
            if response.status_code == 200:
                self.parse_metrics(response.text)
        except:
            pass
    
    def parse_metrics(self, metrics_text):
        """Парсинг метрик"""
        lines = metrics_text.split('\n')
        metrics_data = ""
        
        for line in lines:
            if 'demo_agent_tasks_total' in line and 'HELP' not in line:
                tasks = line.split()[-1]
                metrics_data += f"📋 Обработано задач: {tasks}\n"
            elif 'demo_agent_active_tasks' in line and 'HELP' not in line:
                active = line.split()[-1]
                metrics_data += f"🔄 Активных задач: {active}\n"
            elif 'demo_agent_quality_score' in line and 'HELP' not in line:
                quality = line.split()[-1]
                metrics_data += f"⭐ Качество: {float(quality):.2f}\n"
        
        if metrics_data:
            self.log_metrics(f"🤖 Demo Agent:\n{metrics_data}")
    
    def log_status(self, message):
        """Лог статуса системы"""
        self.status_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.status_text.see(tk.END)
        self.status_text.update()
    
    def log_agents(self, message):
        """Лог агентов"""
        self.agents_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.agents_text.see(tk.END)
        self.agents_text.update()
    
    def log_metrics(self, message):
        """Лог метрик"""
        self.metrics_text.delete(1.0, tk.END)
        self.metrics_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}")
        self.metrics_text.update()
    
    def show_agent_logs(self):
        """Показать логи агентов"""
        try:
            with open("agent.log", "r") as f:
                logs = f.read()
                if logs:
                    self.log_agents("📋 ЛОГИ DEMO AGENT:")
                    self.log_agents(logs[-500:])  # последние 500 символов
        except:
            self.log_agents("📋 Логи агентов недоступны")
    
    def force_refresh(self):
        """Принудительное обновление"""
        self.status_text.delete(1.0, tk.END)
        self.check_infrastructure()
    
    def open_url(self, url):
        """Открыть URL"""
        import webbrowser
        webbrowser.open(url)
    
    def on_closing(self):
        """Обработка закрытия окна"""
        self.monitoring = False
        self.stop_all_agents()
        self.root.destroy()

def main():
    # Проверка рабочей директории
    if not Path("docker-compose.yml").exists():
        print("❌ Запускать нужно из директории с docker-compose.yml")
        sys.exit(1)
    
    root = tk.Tk()
    app = RealGalaxyApp(root)
    
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.monitoring = False
        app.stop_all_agents()

if __name__ == "__main__":
    main()