#!/usr/bin/env python3
"""
GalaxyDevelopment Dashboard - Полноценное GUI приложение
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import json
import threading
import time
import subprocess
import os
import webbrowser
from datetime import datetime

class GalaxyDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("🌌 GalaxyDevelopment Control Center")
        self.root.geometry("1200x800")
        self.root.configure(bg='#000000')  # Чёрный фон
        
        # Стили - ЧЁРНАЯ ТЕМА
        style = ttk.Style()
        style.theme_use('clam')
        
        # Тёмная тема с яркими акцентами
        style.configure('Title.TLabel', font=('Arial', 18, 'bold'), foreground='#00ff41', background='#000000')  # Зелёный на чёрном
        style.configure('Status.TLabel', font=('Arial', 11, 'bold'), foreground='#ffffff', background='#000000')  # Белый на чёрном
        style.configure('Success.TLabel', font=('Arial', 11, 'bold'), foreground='#00ff00', background='#000000')  # Ярко-зелёный
        style.configure('Error.TLabel', font=('Arial', 11, 'bold'), foreground='#ff0040', background='#000000')    # Ярко-красный
        style.configure('Warning.TLabel', font=('Arial', 11, 'bold'), foreground='#ffff00', background='#000000')  # Жёлтый
        
        # Переменные состояния
        self.agent_running = False
        self.docker_status = {}
        self.metrics_data = {}
        
        self.setup_ui()
        self.start_monitoring()
    
    def setup_ui(self):
        # Главное меню
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        system_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Система", menu=system_menu)
        system_menu.add_command(label="Открыть Prometheus", command=lambda: webbrowser.open("http://localhost:9090"))
        system_menu.add_command(label="Открыть Grafana", command=lambda: webbrowser.open("http://localhost:3000"))
        system_menu.add_separator()
        system_menu.add_command(label="Выход", command=self.root.quit)
        
        # Заголовок
        title_frame = tk.Frame(self.root, bg='#000000')
        title_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(title_frame, text="🌌 GalaxyDevelopment Control Center", 
                 style='Title.TLabel').pack()
        
        # Основной контейнер
        main_frame = tk.Frame(self.root, bg='#000000')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Левая панель - Статус системы
        left_frame = tk.LabelFrame(main_frame, text="Статус системы", 
                                  bg='#000000', fg='#00ff41', font=('Arial', 14, 'bold'))
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        self.setup_status_panel(left_frame)
        
        # Правая панель - Управление
        right_frame = tk.LabelFrame(main_frame, text="Управление", 
                                   bg='#000000', fg='#00ff41', font=('Arial', 14, 'bold'))
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        self.setup_control_panel(right_frame)
        
        # Нижняя панель - Логи
        log_frame = tk.LabelFrame(self.root, text="Системные логи", 
                                 bg='#000000', fg='#00ff41', font=('Arial', 14, 'bold'))
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.setup_log_panel(log_frame)
    
    def setup_status_panel(self, parent):
        # Docker контейнеры
        docker_frame = tk.LabelFrame(parent, text="Docker Контейнеры", 
                                    bg='#000000', fg='#00ffff', font=('Arial', 12, 'bold'))
        docker_frame.pack(fill='x', padx=5, pady=5)
        
        self.docker_labels = {}
        containers = ['kafka', 'postgres', 'redis', 'prometheus', 'grafana', 'zookeeper']
        
        for i, container in enumerate(containers):
            frame = tk.Frame(docker_frame, bg='#000000')
            frame.pack(fill='x', padx=5, pady=2)
            
            tk.Label(frame, text=f"{container}:", bg='#000000', fg='#ffffff', 
                    font=('Arial', 11, 'bold'), width=12, anchor='w').pack(side='left')
            
            self.docker_labels[container] = ttk.Label(frame, text="Проверка...", 
                                                     style='Status.TLabel')
            self.docker_labels[container].pack(side='left')
        
        # Агенты
        agents_frame = tk.LabelFrame(parent, text="AI Агенты", 
                                    bg='#000000', fg='#00ffff', font=('Arial', 12, 'bold'))
        agents_frame.pack(fill='x', padx=5, pady=5)
        
        self.agent_status = ttk.Label(agents_frame, text="Остановлены", 
                                     style='Error.TLabel')
        self.agent_status.pack(pady=5)
        
        # Метрики
        metrics_frame = tk.LabelFrame(parent, text="Метрики", 
                                     bg='#000000', fg='#00ffff', font=('Arial', 12, 'bold'))
        metrics_frame.pack(fill='x', padx=5, pady=5)
        
        self.metrics_text = scrolledtext.ScrolledText(metrics_frame, height=8, 
                                                     bg='#000000', fg='#00ff00',
                                                     font=('Consolas', 10, 'bold'), 
                                                     insertbackground='#00ff00')
        self.metrics_text.pack(fill='both', expand=True, padx=5, pady=5)
    
    def setup_control_panel(self, parent):
        # Кнопки управления агентами
        agents_frame = tk.LabelFrame(parent, text="Управление агентами", 
                                    bg='#000000', fg='#ff0080', font=('Arial', 12, 'bold'))
        agents_frame.pack(fill='x', padx=5, pady=5)
        
        btn_frame = tk.Frame(agents_frame, bg='#000000')
        btn_frame.pack(pady=10)
        
        self.start_btn = tk.Button(btn_frame, text="🚀 Запустить агенты", 
                                  bg='#00ff00', fg='#000000', font=('Arial', 11, 'bold'),
                                  command=self.start_agents, relief='raised', bd=3)
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = tk.Button(btn_frame, text="⏹️ Остановить агенты", 
                                 bg='#ff0000', fg='#ffffff', font=('Arial', 11, 'bold'),
                                 command=self.stop_agents, state='disabled', relief='raised', bd=3)
        self.stop_btn.pack(side='left', padx=5)
        
        # Кнопки мониторинга
        monitoring_frame = tk.LabelFrame(parent, text="Мониторинг", 
                                        bg='#000000', fg='#ff0080', font=('Arial', 12, 'bold'))
        monitoring_frame.pack(fill='x', padx=5, pady=5)
        
        monitor_buttons = [
            ("📊 Prometheus", "http://localhost:9090"),
            ("📈 Grafana", "http://localhost:3000"),
            ("🔍 Agent Metrics", "http://localhost:8000/metrics")
        ]
        
        for text, url in monitor_buttons:
            btn = tk.Button(monitoring_frame, text=text, 
                           bg='#0080ff', fg='#ffffff', font=('Arial', 10, 'bold'),
                           command=lambda u=url: webbrowser.open(u), relief='raised', bd=2)
            btn.pack(fill='x', padx=5, pady=2)
        
        # Системные действия
        system_frame = tk.LabelFrame(parent, text="Система", 
                                    bg='#000000', fg='#ff0080', font=('Arial', 12, 'bold'))
        system_frame.pack(fill='x', padx=5, pady=5)
        
        system_buttons = [
            ("🔄 Обновить статус", self.refresh_status),
            ("🧹 Очистить логи", self.clear_logs),
            ("📋 Экспорт логов", self.export_logs)
        ]
        
        for text, command in system_buttons:
            btn = tk.Button(system_frame, text=text, 
                           bg='#ffff00', fg='#000000', font=('Arial', 10, 'bold'),
                           command=command, relief='raised', bd=2)
            btn.pack(fill='x', padx=5, pady=2)
    
    def setup_log_panel(self, parent):
        self.log_text = scrolledtext.ScrolledText(parent, height=10, 
                                                 bg='#000000', fg='#00ff00',
                                                 font=('Consolas', 10, 'bold'),
                                                 insertbackground='#00ff00')
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Добавляем начальные логи
        self.log("🌌 GalaxyDevelopment Dashboard запущен")
        self.log("📊 Начинаю мониторинг системы...")
    
    def start_monitoring(self):
        """Запуск фонового мониторинга"""
        def monitor():
            while True:
                try:
                    self.update_docker_status()
                    self.update_agent_status()
                    self.update_metrics()
                    time.sleep(5)
                except Exception as e:
                    self.log(f"❌ Ошибка мониторинга: {e}")
                    time.sleep(10)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def update_docker_status(self):
        """Обновление статуса Docker контейнеров"""
        try:
            result = subprocess.run(['docker-compose', 'ps'], 
                                  capture_output=True, text=True, cwd='/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem')
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Пропускаем заголовок
                
                for container in self.docker_labels:
                    status = "❌ Остановлен"
                    style = 'Error.TLabel'
                    
                    for line in lines:
                        if container in line and 'Up' in line:
                            status = "✅ Работает"
                            style = 'Success.TLabel'
                            break
                    
                    self.docker_labels[container].configure(text=status, style=style)
        except Exception as e:
            for container in self.docker_labels:
                self.docker_labels[container].configure(text="❓ Неизвестно", style='Error.TLabel')
    
    def update_agent_status(self):
        """Обновление статуса агентов"""
        try:
            response = requests.get("http://localhost:8000/metrics", timeout=2)
            if response.status_code == 200:
                self.agent_status.configure(text="✅ Demo Agent работает", style='Success.TLabel')
                self.agent_running = True
                self.start_btn.configure(state='disabled')
                self.stop_btn.configure(state='normal')
            else:
                raise requests.RequestException("Agent not responding")
        except:
            self.agent_status.configure(text="❌ Агенты остановлены", style='Error.TLabel')
            self.agent_running = False
            self.start_btn.configure(state='normal')
            self.stop_btn.configure(state='disabled')
    
    def update_metrics(self):
        """Обновление метрик"""
        try:
            if self.agent_running:
                response = requests.get("http://localhost:8000/metrics", timeout=2)
                if response.status_code == 200:
                    # Парсим метрики демо-агента
                    text = response.text
                    metrics = {}
                    
                    for line in text.split('\n'):
                        if line.startswith('demo_agent_'):
                            parts = line.split(' ')
                            if len(parts) >= 2:
                                key = parts[0]
                                value = parts[1]
                                metrics[key] = value
                    
                    # Обновляем отображение метрик
                    self.metrics_text.delete(1.0, tk.END)
                    self.metrics_text.insert(tk.END, f"📊 Обновлено: {datetime.now().strftime('%H:%M:%S')}\n\n")
                    
                    for key, value in metrics.items():
                        if 'tasks_total' in key:
                            self.metrics_text.insert(tk.END, f"📋 Обработанные задачи: {value}\n")
                        elif 'active_tasks' in key:
                            self.metrics_text.insert(tk.END, f"⚡ Активные задачи: {value}\n")
                        elif 'quality_score' in key:
                            score = float(value)
                            self.metrics_text.insert(tk.END, f"⭐ Качество: {score:.2f}\n")
        except Exception as e:
            pass  # Тихо игнорируем ошибки метрик
    
    def start_agents(self):
        """Запуск агентов"""
        def run_agent():
            try:
                self.log("🚀 Запускаю демо-агент...")
                os.chdir('/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem')
                
                # Останавливаем предыдущий агент
                subprocess.run(['pkill', '-f', 'simple_agent'], capture_output=True)
                
                # Запускаем новый агент
                process = subprocess.Popen(['agent_env/bin/python', 'simple_agent.py'], 
                                         stdout=subprocess.PIPE, 
                                         stderr=subprocess.STDOUT,
                                         text=True)
                
                self.log("✅ Демо-агент запущен успешно!")
                
                # Читаем вывод агента
                for line in iter(process.stdout.readline, ''):
                    if line.strip():
                        self.log(f"🤖 Agent: {line.strip()}")
                
            except Exception as e:
                self.log(f"❌ Ошибка запуска агента: {e}")
        
        thread = threading.Thread(target=run_agent, daemon=True)
        thread.start()
    
    def stop_agents(self):
        """Остановка агентов"""
        try:
            result = subprocess.run(['pkill', '-f', 'simple_agent'], 
                                  capture_output=True, text=True)
            self.log("⏹️ Агенты остановлены")
        except Exception as e:
            self.log(f"❌ Ошибка остановки агентов: {e}")
    
    def refresh_status(self):
        """Принудительное обновление статуса"""
        self.log("🔄 Обновляю статус системы...")
        self.update_docker_status()
        self.update_agent_status()
        self.update_metrics()
    
    def clear_logs(self):
        """Очистка логов"""
        self.log_text.delete(1.0, tk.END)
        self.log("🧹 Логи очищены")
    
    def export_logs(self):
        """Экспорт логов в файл"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"galaxy_logs_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, tk.END))
            
            self.log(f"📋 Логи экспортированы в {filename}")
            messagebox.showinfo("Экспорт", f"Логи сохранены в файл {filename}")
        except Exception as e:
            self.log(f"❌ Ошибка экспорта: {e}")
            messagebox.showerror("Ошибка", f"Не удалось экспортировать логи: {e}")
    
    def log(self, message):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}\n"
        
        def update_log():
            self.log_text.insert(tk.END, log_message)
            self.log_text.see(tk.END)
        
        if threading.current_thread() == threading.main_thread():
            update_log()
        else:
            self.root.after(0, update_log)

if __name__ == "__main__":
    root = tk.Tk()
    app = GalaxyDashboard(root)
    root.mainloop()