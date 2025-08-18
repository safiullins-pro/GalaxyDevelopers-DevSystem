#!/usr/bin/env python3
"""
Отправка тестовой задачи в ResearchAgent
"""
import json
import uuid
from datetime import datetime
from kafka import KafkaProducer

def send_test_task():
    # Kafka Producer
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
        key_serializer=str.encode
    )
    
    # Тестовая задача
    task = {
        'task_id': str(uuid.uuid4()),
        'process_id': 'PROC_TEST_001',
        'process_name': 'Test Process Management',
        'domain': 'TESTING',
        'owner': 'Test Manager',
        'standards': ['ITIL_4', 'ISO_IEC_20000', 'COBIT'],
        'priority': 1,
        'created_at': datetime.now().isoformat()
    }
    
    print(f"Отправляем задачу: {task['task_id']}")
    print(f"Процесс: {task['process_name']}")
    
    # Отправка в Kafka
    producer.send('research_tasks', key=task['process_id'], value=task)
    producer.flush()
    
    print("✅ Задача отправлена в research_tasks")
    print(f"Ожидайте обработку ResearchAgent...")

if __name__ == "__main__":
    send_test_task()