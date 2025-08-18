#!/usr/bin/env python3
"""
Упрощенный агент для демонстрации на M2 Mac
"""

import json
import time
from datetime import datetime
from prometheus_client import Counter, Gauge, start_http_server

# Метрики
TASKS_PROCESSED = Counter('demo_agent_tasks_total', 'Обработанные задачи')
ACTIVE_TASKS = Gauge('demo_agent_active_tasks', 'Активные задачи') 
QUALITY_SCORE = Gauge('demo_agent_quality_score', 'Оценка качества')

def simulate_work():
    """Имитация работы агента"""
    print("🌌 GalaxyDevelopment Demo Agent запущен!")
    print("📊 Метрики доступны на http://localhost:8000/metrics")
    
    # Запуск метрик сервера
    start_http_server(8000)
    
    task_id = 1
    
    while True:
        try:
            # Имитация обработки задачи
            ACTIVE_TASKS.set(1)
            print(f"🔄 Обрабатываю задачу #{task_id}...")
            
            # "Обработка" 3 секунды
            time.sleep(3)
            
            # Завершение задачи
            TASKS_PROCESSED.inc()
            QUALITY_SCORE.set(0.85 + (task_id % 10) * 0.01)  # 0.85-0.94
            ACTIVE_TASKS.set(0)
            
            print(f"✅ Задача #{task_id} завершена! Всего обработано: {int(TASKS_PROCESSED._value.get())}")
            
            task_id += 1
            
            # Пауза между задачами
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\n🛑 Агент остановлен")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(5)

if __name__ == "__main__":
    simulate_work()