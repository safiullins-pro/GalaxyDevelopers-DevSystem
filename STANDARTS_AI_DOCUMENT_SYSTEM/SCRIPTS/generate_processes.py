#!/usr/bin/env python3
"""
Скрипт генерации задач для создания документации по всем процессам
"""

import csv
import json
import uuid
from datetime import datetime
from kafka import KafkaProducer
import time

def load_processes(csv_file):
    """Загрузка процессов из CSV файла"""
    processes = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            processes.append(row)
    return processes

def create_research_task(process):
    """Создание задачи для ResearchAgent"""
    
    # Определение стандартов на основе категории процесса
    standards = ['ITIL_4']
    
    if process['iso_compliance'] == 'true':
        standards.append('ISO_IEC_20000')
    
    if process['cobit_alignment'] and process['cobit_alignment'] != '':
        standards.append('COBIT')
    
    # Безопасность
    if 'Security' in process['domain'] or 'security' in process['name'].lower():
        standards.extend(['NIST', 'ISO_27001'])
    
    # Управление
    if 'Governance' in process['domain']:
        standards.append('COBIT')
    
    task = {
        'task_id': str(uuid.uuid4()),
        'process_id': process['process_id'],
        'process_name': process['name'],
        'domain': process['domain'],
        'owner': process['owner'],
        'standards': list(set(standards)),  # убираем дубликаты
        'priority': int(process['priority']) if process['priority'] else 5,
        'itil_category': process['itil_category'],
        'cobit_alignment': process['cobit_alignment'],
        'created_at': datetime.now().isoformat()
    }
    
    return task

def send_tasks_to_kafka(tasks, kafka_servers='localhost:9092'):
    """Отправка задач в Kafka"""
    
    producer = KafkaProducer(
        bootstrap_servers=kafka_servers,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
        key_serializer=str.encode
    )
    
    topic = 'research_tasks'
    sent_count = 0
    
    print(f"📨 Отправка {len(tasks)} задач в топик '{topic}'...")
    
    for task in tasks:
        try:
            # Отправляем с ключом process_id для партиционирования
            producer.send(
                topic, 
                key=task['process_id'],
                value=task
            )
            sent_count += 1
            
            if sent_count % 10 == 0:
                print(f"  ✅ Отправлено {sent_count}/{len(tasks)} задач")
                time.sleep(0.5)  # небольшая пауза чтобы не перегружать
            
        except Exception as e:
            print(f"  ❌ Ошибка отправки задачи {task['process_id']}: {e}")
    
    # Ждем отправки всех сообщений
    producer.flush()
    producer.close()
    
    print(f"🎉 Успешно отправлено {sent_count} задач в Kafka")
    return sent_count

def main():
    print("🌌 Генерация задач для системы GalaxyDevelopment")
    print("=" * 50)
    
    # Загрузка процессов
    print("📖 Загрузка каталога процессов...")
    processes = load_processes('process_catalog.csv')
    print(f"  📊 Загружено {len(processes)} процессов")
    
    # Создание задач
    print("🏭 Создание задач для ResearchAgent...")
    tasks = []
    
    for process in processes:
        task = create_research_task(process)
        tasks.append(task)
    
    print(f"  🎯 Создано {len(tasks)} задач")
    
    # Статистика по доменам
    domains = {}
    for task in tasks:
        domain = task['domain']
        domains[domain] = domains.get(domain, 0) + 1
    
    print("📈 Статистика по доменам:")
    for domain, count in sorted(domains.items()):
        print(f"  • {domain}: {count} процессов")
    
    # Статистика по стандартам
    standards_count = {}
    for task in tasks:
        for standard in task['standards']:
            standards_count[standard] = standards_count.get(standard, 0) + 1
    
    print("🏅 Статистика по стандартам:")
    for standard, count in sorted(standards_count.items()):
        print(f"  • {standard}: {count} процессов")
    
    # Отправка в Kafka
    answer = input("\n❓ Отправить задачи в Kafka? (y/N): ")
    if answer.lower() == 'y':
        sent_count = send_tasks_to_kafka(tasks)
        
        print(f"""
🎊 ЗАДАЧИ ОТПРАВЛЕНЫ В СИСТЕМУ!

📊 Статистика:
  • Всего процессов: {len(processes)}
  • Отправлено задач: {sent_count}
  • Уникальных доменов: {len(domains)}
  • Поддерживаемых стандартов: {len(standards_count)}

🤖 Агенты начнут обработку автоматически:
  1. ResearchAgent проанализирует стандарты
  2. ComposerAgent создаст документацию
  3. ReviewerAgent проверит качество
  4. IntegratorAgent интегрирует с Git/Confluence
  5. PublisherAgent опубликует результаты

⏱️ Ожидаемое время обработки: 5-15 минут на процесс
📈 Следите за прогрессом в Grafana: http://localhost:3000
        """)
    else:
        print("❌ Отправка отменена")
        
        # Сохранение в файл для ручной обработки
        with open('generated_tasks.json', 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
        print("💾 Задачи сохранены в файл 'generated_tasks.json'")

if __name__ == "__main__":
    main()