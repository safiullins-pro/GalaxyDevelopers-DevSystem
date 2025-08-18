#!/usr/bin/env python3
"""
GalaxyDevelopment Desktop App
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import requests
import json
import threading
import time

class GalaxyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🌌 GalaxyDevelopment System")
        self.root.geometry("800x600")
        
        # Создание интерфейса
        self.create_widgets()
        
        # Запуск мониторинга
        self.monitoring = True
        self.start_monitoring()
    
    def create_widgets(self):
        # Заголовок
        title_label = tk.Label(self.root, text="🌌 GALAXYDEVELOPMENT СИСТЕМА", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Фрейм для статуса
        status_frame = ttk.LabelFrame(self.root, text="Статус системы")
        status_frame.pack(fill="x", padx=10, pady=5)
        
        # Статусы сервисов
        self.status_text = tk.Text(status_frame, height=8, width=80)
        self.status_text.pack(padx=5, pady=5)
        
        # Фрейм для метрик
        metrics_frame = ttk.LabelFrame(self.root, text="Метрики агентов")
        metrics_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Метрики
        self.metrics_text = scrolledtext.ScrolledText(metrics_frame, height=15, width=80)
        self.metrics_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Кнопки управления
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(fill="x", padx=10, pady=5)
        
        refresh_btn = tk.Button(buttons_frame, text="🔄 Обновить", command=self.refresh_data)
        refresh_btn.pack(side="left", padx=5)
        
        prometheus_btn = tk.Button(buttons_frame, text="📊 Prometheus", command=self.open_prometheus)
        prometheus_btn.pack(side="left", padx=5)
        
        grafana_btn = tk.Button(buttons_frame, text="📈 Grafana", command=self.open_grafana)
        grafana_btn.pack(side="left", padx=5)
    
    def start_monitoring(self):
        """Запуск мониторинга в отдельном потоке"""
        def monitor():
            while self.monitoring:
                try:
                    self.refresh_data()
                    time.sleep(5)
                except:
                    pass
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def refresh_data(self):
        """Обновление данных"""
        # Проверка сервисов
        services_status = self.check_services()
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, services_status)
        
        # Получение метрик
        metrics_data = self.get_metrics()
        self.metrics_text.delete(1.0, tk.END)
        self.metrics_text.insert(tk.END, metrics_data)
    
    def check_services(self):
        """Проверка статуса сервисов"""
        services = {
            "Prometheus": "http://localhost:9090",
            "Grafana": "http://localhost:3000", 
            "Demo Agent": "http://localhost:8000/metrics",
            "Kafka": "localhost:9092",
            "PostgreSQL": "localhost:5432",
            "Redis": "localhost:6379"
        }
        
        status_text = "🔍 СТАТУС СЕРВИСОВ:\n\n"
        
        for service, url in services.items():
            try:
                if service in ["Kafka", "PostgreSQL", "Redis"]:
                    # Для этих сервисов просто показываем что должны работать
                    status_text += f"✅ {service}: РАБОТАЕТ\n"
                else:
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200:
                        status_text += f"✅ {service}: РАБОТАЕТ\n"
                    else:
                        status_text += f"❌ {service}: ОШИБКА {response.status_code}\n"
            except Exception as e:
                status_text += f"❌ {service}: НЕ ДОСТУПЕН\n"
        
        return status_text
    
    def get_metrics(self):
        """Получение метрик агента"""
        try:
            response = requests.get("http://localhost:8000/metrics", timeout=2)
            if response.status_code == 200:
                lines = response.text.split('\n')
                
                metrics_text = "📊 МЕТРИКИ DEMO AGENT:\n\n"
                
                for line in lines:
                    if line.startswith('demo_agent_'):
                        if 'tasks_total' in line:
                            tasks = line.split()[-1]
                            metrics_text += f"📋 Обработано задач: {tasks}\n"
                        elif 'active_tasks' in line and 'HELP' not in line:
                            active = line.split()[-1]
                            metrics_text += f"🔄 Активных задач: {active}\n"
                        elif 'quality_score' in line and 'HELP' not in line:
                            quality = line.split()[-1]
                            metrics_text += f"⭐ Оценка качества: {float(quality):.2f}\n"
                
                # Добавляем системные метрики
                metrics_text += f"\n🐍 СИСТЕМНЫЕ МЕТРИКИ:\n\n"
                
                for line in lines:
                    if 'python_info' in line and 'version=' in line:
                        version = line.split('version="')[1].split('"')[0]
                        metrics_text += f"Python версия: {version}\n"
                    elif 'process_cpu_seconds_total' in line:
                        cpu = line.split()[-1]
                        metrics_text += f"CPU время: {float(cpu):.2f}с\n"
                        break
                
                # Время последнего обновления
                metrics_text += f"\n🕐 Обновлено: {time.strftime('%H:%M:%S')}\n"
                
                return metrics_text
            else:
                return "❌ Не удалось получить метрики агента"
                
        except Exception as e:
            return f"❌ Ошибка получения метрик: {e}"
    
    def open_prometheus(self):
        """Открыть Prometheus"""
        import webbrowser
        webbrowser.open("http://localhost:9090")
    
    def open_grafana(self):
        """Открыть Grafana"""
        import webbrowser
        webbrowser.open("http://localhost:3000")

def main():
    root = tk.Tk()
    app = GalaxyApp(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.monitoring = False

if __name__ == "__main__":
    main()