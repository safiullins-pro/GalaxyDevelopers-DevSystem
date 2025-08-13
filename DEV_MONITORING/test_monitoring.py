#!/usr/bin/env python3
"""
Тестирование системы мониторинга
"""

import asyncio
import aiohttp
import websockets
import json
import time
from pathlib import Path

async def test_websocket():
    """Тест WebSocket соединения"""
    print("🧪 Тестирование WebSocket...")
    
    try:
        async with websockets.connect('ws://localhost:8765/monitoring') as websocket:
            # Получаем приветственное сообщение
            message = await websocket.recv()
            data = json.loads(message)
            print(f"✅ WebSocket подключен: {data['message']}")
            
            # Отправляем ping
            await websocket.send(json.dumps({'type': 'ping'}))
            response = await websocket.recv()
            pong = json.loads(response)
            print(f"✅ Ping-Pong: {pong['type']}")
            
            # Запрашиваем статус
            await websocket.send(json.dumps({'type': 'get_status'}))
            status = await websocket.recv()
            status_data = json.loads(status)
            print(f"✅ Статус системы: {status_data['type']}")
            
            return True
    except Exception as e:
        print(f"❌ WebSocket ошибка: {e}")
        return False

async def test_rest_api():
    """Тест REST API endpoints"""
    print("\n🧪 Тестирование REST API...")
    
    endpoints = [
        ('GET', '/api/monitoring/file-changes', None),
        ('GET', '/api/monitoring/syntax-check', None),
        ('GET', '/api/monitoring/security-scan', None),
        ('GET', '/api/monitoring/compliance/ISO27001', None),
        ('GET', '/api/monitoring/compliance/ITIL4', None),
        ('GET', '/api/monitoring/compliance/COBIT', None),
        ('GET', '/api/monitoring/integration-test', None),
        ('GET', '/api/monitoring/status', None),
        ('GET', '/api/monitoring/metrics', None),
    ]
    
    async with aiohttp.ClientSession() as session:
        for method, endpoint, data in endpoints:
            url = f'http://localhost:8766{endpoint}'
            try:
                if method == 'GET':
                    async with session.get(url) as response:
                        if response.status == 200:
                            if endpoint != '/api/monitoring/metrics':
                                result = await response.json()
                                print(f"✅ {endpoint}: OK")
                            else:
                                result = await response.text()
                                print(f"✅ {endpoint}: Metrics available")
                        else:
                            print(f"❌ {endpoint}: Status {response.status}")
                elif method == 'POST':
                    async with session.post(url, json=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            print(f"✅ {endpoint}: OK")
                        else:
                            print(f"❌ {endpoint}: Status {response.status}")
            except Exception as e:
                print(f"❌ {endpoint}: {e}")

async def test_file_watcher():
    """Тест файлового мониторинга"""
    print("\n🧪 Тестирование File Watcher...")
    
    # Создаем тестовый файл
    test_file = Path('/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/test_monitoring_file.txt')
    
    async with aiohttp.ClientSession() as session:
        # Очищаем старые изменения
        await session.get('http://localhost:8766/api/monitoring/file-changes')
        
        # Создаем файл
        test_file.write_text('Test content')
        print(f"✅ Создан файл: {test_file}")
        
        # Ждем обработки
        await asyncio.sleep(2)
        
        # Проверяем изменения
        async with session.get('http://localhost:8766/api/monitoring/file-changes') as response:
            changes = await response.json()
            if changes:
                print(f"✅ Обнаружено {len(changes)} изменений")
                for change in changes[:3]:
                    print(f"   - {change['type']}: {Path(change['path']).name}")
            else:
                print("⚠️ Изменения не обнаружены (возможно, файл в игнор-листе)")
        
        # Удаляем тестовый файл
        if test_file.exists():
            test_file.unlink()
            print(f"✅ Удален тестовый файл")

async def test_agent_integration():
    """Тест интеграции с агентами"""
    print("\n🧪 Тестирование интеграции с агентами...")
    
    async with aiohttp.ClientSession() as session:
        # Тест валидации
        validation_data = {
            'agents': ['ResearchAgent', 'ReviewerAgent'],
            'context': {'test': True}
        }
        
        async with session.post('http://localhost:8766/api/agents/validate', 
                               json=validation_data) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Валидация агентов: Score {result['score']}%")
            else:
                print(f"❌ Валидация агентов: Status {response.status}")
        
        # Тест обработки задачи
        process_data = {
            'agent': 'ComposerAgent',
            'file': '/test/file.md',
            'action': 'created'
        }
        
        async with session.post('http://localhost:8766/api/agents/process', 
                               json=process_data) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Задача агента: {result['taskId']} ({result['status']})")
            else:
                print(f"❌ Задача агента: Status {response.status}")

async def test_compliance():
    """Тест проверки соответствия стандартам"""
    print("\n🧪 Тестирование Compliance Checker...")
    
    standards = ['ISO27001', 'ITIL4', 'COBIT']
    
    async with aiohttp.ClientSession() as session:
        for standard in standards:
            url = f'http://localhost:8766/api/monitoring/compliance/{standard}'
            async with session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    status = "✅" if result['compliant'] else "⚠️"
                    print(f"{status} {standard}: Score {result['score']:.1f}%")
                    
                    # Показываем детали проверок
                    if 'checks' in result:
                        for check, passed in result['checks'].items():
                            check_status = "✓" if passed else "✗"
                            print(f"    {check_status} {check}")
                else:
                    print(f"❌ {standard}: Status {response.status}")

async def test_security_scan():
    """Тест сканирования безопасности"""
    print("\n🧪 Тестирование Security Scanner...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8766/api/monitoring/security-scan') as response:
            if response.status == 200:
                result = await response.json()
                if result['vulnerabilities']:
                    print(f"⚠️ Найдено {result['total']} уязвимостей:")
                    for vuln in result['vulnerabilities'][:5]:
                        print(f"   - {vuln.get('severity', 'UNKNOWN')}: {vuln['message']}")
                        print(f"     Файл: {Path(vuln['file']).name}:{vuln.get('line', '?')}")
                else:
                    print("✅ Уязвимости не найдены")
            else:
                print(f"❌ Security scan: Status {response.status}")

async def test_syntax_check():
    """Тест проверки синтаксиса"""
    print("\n🧪 Тестирование Syntax Checker...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8766/api/monitoring/syntax-check') as response:
            if response.status == 200:
                result = await response.json()
                if result['errors']:
                    print(f"⚠️ Найдено {result['total']} синтаксических ошибок:")
                    for error in result['errors'][:5]:
                        print(f"   - {Path(error['file']).name}:{error.get('line', '?')}")
                        print(f"     {error['message']}")
                else:
                    print("✅ Синтаксические ошибки не найдены")
            else:
                print(f"❌ Syntax check: Status {response.status}")

async def test_metrics():
    """Тест Prometheus метрик"""
    print("\n🧪 Тестирование Prometheus метрик...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8766/api/monitoring/metrics') as response:
            if response.status == 200:
                metrics = await response.text()
                
                # Проверяем наличие ключевых метрик
                key_metrics = [
                    'galaxy_file_changes_total',
                    'galaxy_syntax_errors',
                    'galaxy_security_issues',
                    'galaxy_compliance_score',
                    'galaxy_websocket_connections',
                    'galaxy_api_requests_total',
                    'galaxy_check_duration_seconds'
                ]
                
                for metric in key_metrics:
                    if metric in metrics:
                        print(f"✅ {metric}: Доступна")
                    else:
                        print(f"❌ {metric}: Не найдена")
            else:
                print(f"❌ Metrics: Status {response.status}")

async def main():
    """Главная функция тестирования"""
    print("""
    ╔════════════════════════════════════════╗
    ║    GALAXY MONITORING SYSTEM TEST       ║
    ║    Полное тестирование компонентов     ║
    ╚════════════════════════════════════════╝
    """)
    
    # Даем серверу время на запуск
    print("⏳ Ожидание запуска сервера...")
    await asyncio.sleep(2)
    
    # Запускаем тесты
    await test_websocket()
    await test_rest_api()
    await test_file_watcher()
    await test_agent_integration()
    await test_compliance()
    await test_security_scan()
    await test_syntax_check()
    await test_metrics()
    
    print("\n✅ Тестирование завершено!")
    
    # Итоговая статистика
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8766/api/monitoring/status') as response:
            if response.status == 200:
                status = await response.json()
                print("\n📊 Статус системы:")
                print(f"   WebSocket клиенты: {status['websocket_clients']}")
                print(f"   File Observer: {'Активен' if status['file_observer_active'] else 'Неактивен'}")
                print(f"   Отслеживаемые пути: {len(status['watched_paths'])}")
                print(f"   Последние изменения: {status['recent_changes']}")

if __name__ == '__main__':
    asyncio.run(main())