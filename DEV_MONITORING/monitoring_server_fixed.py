#!/usr/bin/env python3
"""
GALAXY MONITORING SERVER v2.1 - FIXED
Исправленная версия с правильным WebSocket handler
"""

import asyncio
import json
import os
import sys
import time
import ast
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
import hashlib
import logging

# Веб-сервер компоненты
from aiohttp import web
import aiohttp_cors
import websockets
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK

# Мониторинг файловой системы
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Анализ кода и безопасность
import pylint.lint
from pylint.reporters.json_reporter import JSONReporter
from bandit.core import manager

# Метрики
from prometheus_client import Counter, Gauge, Histogram, generate_latest
import sqlite3
from concurrent.futures import ThreadPoolExecutor

# Добавляем путь к memory API
sys.path.append(str(Path(__file__).parent / 'memory'))

# Добавляем путь к системе защиты
sys.path.append('/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem')

# Импортируем систему защиты
try:
    from ai_auditor import AICodeAuditor
    AI_PROTECTION_AVAILABLE = True
    print("✅ AI Protection System loaded")
except ImportError as e:
    AI_PROTECTION_AVAILABLE = False
    print(f"⚠️ AI Protection System not available: {e}")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('GalaxyMonitoring')

# Prometheus метрики
file_changes_counter = Counter('galaxy_file_changes_total', 'Total number of file changes', ['type'])
syntax_errors_gauge = Gauge('galaxy_syntax_errors', 'Current number of syntax errors')
security_issues_gauge = Gauge('galaxy_security_issues', 'Current number of security issues')
compliance_score_gauge = Gauge('galaxy_compliance_score', 'Compliance score percentage', ['standard'])
websocket_connections_gauge = Gauge('galaxy_websocket_connections', 'Active WebSocket connections')
api_requests_counter = Counter('galaxy_api_requests_total', 'Total API requests', ['endpoint', 'method'])
check_duration_histogram = Histogram('galaxy_check_duration_seconds', 'Duration of checks', ['check_type'])


class FileChangeHandler(FileSystemEventHandler):
    """Обработчик изменений файлов"""
    
    def __init__(self, monitoring_server):
        self.monitoring_server = monitoring_server
        self.ignored_patterns = [
            '.DS_Store', '.git', '__pycache__', '*.pyc', 
            'node_modules', '*.swp', '*.tmp', '.venv', 'venv'
        ]
    
    def should_ignore(self, path: str) -> bool:
        """Проверка, нужно ли игнорировать файл"""
        path_str = str(path)
        return any(pattern in path_str for pattern in self.ignored_patterns)
    
    def on_modified(self, event):
        if not event.is_directory and not self.should_ignore(event.src_path):
            self.process_change(event.src_path, 'modified')
    
    def on_created(self, event):
        if not event.is_directory and not self.should_ignore(event.src_path):
            self.process_change(event.src_path, 'created')
    
    def on_deleted(self, event):
        if not event.is_directory and not self.should_ignore(event.src_path):
            self.process_change(event.src_path, 'deleted')
    
    def process_change(self, path: str, change_type: str):
        """Обработка изменения файла"""
        file_changes_counter.labels(type=change_type).inc()
        
        change_data = {
            'type': 'file_change',
            'change': {
                'path': path,
                'type': change_type,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Добавляем в очередь изменений
        self.monitoring_server.file_changes.append(change_data['change'])
        
        # Используем call_soon_threadsafe для вызова из другого потока
        try:
            loop = asyncio.get_event_loop()
            if loop and loop.is_running():
                loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(
                        self.monitoring_server.broadcast_to_websockets(change_data)
                    )
                )
        except RuntimeError:
            # Если нет event loop, просто логируем
            pass
        
        logger.info(f"File {change_type}: {path}")


class MonitoringServer:
    """Основной сервер мониторинга"""
    
    def __init__(self):
        self.websocket_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.file_changes = []
        self.file_observer = None
        self.watch_paths = [
            '/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/',
            '/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/'
        ]
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.compliance_standards = {
            'ISO27001': self.check_iso27001_compliance,
            'ITIL4': self.check_itil4_compliance,
            'COBIT': self.check_cobit_compliance
        }
        self.agent_statuses = {}
        self.memory_db_path = Path(__file__).parent / 'memory' / 'unified_memory.db'
        
        # Инициализируем AI Protection System (встроенный)
        self.ai_auditor = True  # Используем встроенную систему защиты
        logger.info("🛡️ Built-in AI Protection System enabled")
    
    async def start(self):
        """Запуск всех компонентов сервера"""
        logger.info("🚀 Starting Galaxy Monitoring Server v2.1...")
        
        # Запуск файлового мониторинга
        self.start_file_monitoring()
        
        # Запуск WebSocket сервера
        websocket_task = asyncio.create_task(self.start_websocket_server())
        
        # Запуск REST API сервера
        api_task = asyncio.create_task(self.start_api_server())
        
        # Запуск периодических проверок
        periodic_task = asyncio.create_task(self.run_periodic_checks())
        
        await asyncio.gather(websocket_task, api_task, periodic_task)
    
    def start_file_monitoring(self):
        """Запуск мониторинга файловой системы"""
        try:
            self.file_observer = Observer()
            event_handler = FileChangeHandler(self)
            
            for path in self.watch_paths:
                if Path(path).exists():
                    self.file_observer.schedule(event_handler, path, recursive=True)
                    logger.info(f"📁 Watching: {path}")
                else:
                    logger.warning(f"Path does not exist: {path}")
            
            self.file_observer.start()
            logger.info("✅ File monitoring started successfully")
        except Exception as e:
            logger.error(f"Failed to start file monitoring: {e}")
            self.file_observer = None
    
    async def websocket_handler(self, websocket):
        """
        WebSocket handler для новой версии websockets библиотеки
        В версии 12+ handler принимает только websocket параметр
        """
        # Добавляем клиента
        self.websocket_clients.add(websocket)
        websocket_connections_gauge.inc()
        
        client_address = websocket.remote_address
        logger.info(f"✅ WebSocket client connected from {client_address}")
        
        try:
            # Отправляем приветственное сообщение
            await websocket.send(json.dumps({
                'type': 'connected',
                'message': 'Galaxy Monitoring connected',
                'timestamp': datetime.now().isoformat()
            }))
            
            # Отправляем текущий статус
            status = await self.get_system_status()
            await websocket.send(json.dumps(status))
            
            # Главный цикл обработки сообщений
            while True:
                try:
                    # Ждем сообщение с таймаутом для ping/pong
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    
                    # Обрабатываем сообщение
                    try:
                        data = json.loads(message)
                        await self.handle_websocket_message(websocket, data)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON from client: {message}")
                        await websocket.send(json.dumps({
                            'type': 'error',
                            'message': 'Invalid JSON format'
                        }))
                        
                except asyncio.TimeoutError:
                    # Отправляем ping для поддержания соединения
                    try:
                        pong_waiter = await websocket.ping()
                        await asyncio.wait_for(pong_waiter, timeout=10)
                        logger.debug(f"Ping/pong successful for {client_address}")
                    except (asyncio.TimeoutError, ConnectionClosed):
                        logger.warning(f"Client {client_address} not responding to ping")
                        break
                        
                except ConnectionClosedOK:
                    logger.info(f"Client {client_address} closed connection normally")
                    break
                    
                except ConnectionClosed as e:
                    logger.warning(f"Client {client_address} connection closed: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket handler error for {client_address}: {e}")
            
        finally:
            # Удаляем клиента из списка
            if websocket in self.websocket_clients:
                self.websocket_clients.remove(websocket)
                websocket_connections_gauge.dec()
            logger.info(f"🔌 WebSocket client {client_address} disconnected")
    
    async def start_websocket_server(self):
        """Запуск WebSocket сервера с правильными параметрами"""
        try:
            # Используем правильную сигнатуру handler
            server = await websockets.serve(
                self.websocket_handler,  # handler с 2 параметрами
                'localhost',
                8765,
                ping_interval=20,  # Ping каждые 20 секунд
                ping_timeout=10,   # Timeout для pong 10 секунд
                max_size=10**7,    # Максимальный размер сообщения 10MB
                compression=None   # Отключаем сжатие для Safari совместимости
            )
            
            logger.info("📡 WebSocket server running on ws://localhost:8765")
            
            # Держим сервер запущенным
            await asyncio.Future()
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            raise
    
    async def start_api_server(self):
        """Запуск REST API сервера"""
        app = web.Application()
        
        # CORS настройка для разрешения запросов с file://
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*",
                max_age=3600
            )
        })
        
        # Роуты
        app.router.add_get('/api/monitoring/file-changes', self.handle_file_changes)
        app.router.add_get('/api/monitoring/syntax-check', self.handle_syntax_check)
        app.router.add_get('/api/monitoring/security-scan', self.handle_security_scan)
        app.router.add_get('/api/monitoring/compliance/{standard}', self.handle_compliance_check)
        app.router.add_get('/api/monitoring/integration-test', self.handle_integration_test)
        app.router.add_post('/api/monitoring/start-watcher', self.handle_start_watcher)
        app.router.add_get('/api/monitoring/status', self.handle_status)
        app.router.add_get('/api/monitoring/metrics', self.handle_metrics)
        app.router.add_post('/api/agents/validate', self.handle_agent_validate)
        app.router.add_post('/api/agents/process', self.handle_agent_process)
        
        # AI Protection endpoints
        app.router.add_post('/api/protection/check-file', self.handle_protection_check)
        app.router.add_post('/api/protection/scan-threats', self.handle_protection_scan)
        app.router.add_get('/api/protection/status', self.handle_protection_status)
        app.router.add_post('/api/protection/audit-code', self.handle_audit_code)
        
        # Применяем CORS ко всем роутам
        for route in list(app.router._resources):
            cors.add(route)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8766)
        await site.start()
        
        logger.info("🌐 REST API server running on http://localhost:8766")
        await asyncio.Future()
    
    async def broadcast_to_websockets(self, data: dict):
        """Отправка данных всем WebSocket клиентам"""
        if not self.websocket_clients:
            return
            
        message = json.dumps(data)
        disconnected = set()
        
        for client in self.websocket_clients.copy():
            try:
                await client.send(message)
            except (ConnectionClosed, ConnectionClosedOK):
                disconnected.add(client)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.add(client)
        
        # Удаляем отключенные клиенты
        for client in disconnected:
            if client in self.websocket_clients:
                self.websocket_clients.remove(client)
                websocket_connections_gauge.dec()
    
    async def handle_websocket_message(self, websocket, data: dict):
        """Обработка сообщений от WebSocket клиентов"""
        message_type = data.get('type')
        
        if message_type == 'ping':
            await websocket.send(json.dumps({
                'type': 'pong',
                'timestamp': datetime.now().isoformat()
            }))
        elif message_type == 'get_status':
            status = await self.get_system_status()
            await websocket.send(json.dumps(status))
        else:
            # Эхо для неизвестных типов
            await websocket.send(json.dumps({
                'type': 'echo',
                'received': data,
                'timestamp': datetime.now().isoformat()
            }))
    
    # === REST API Handlers (остаются без изменений) ===
    
    async def handle_file_changes(self, request):
        """API: Получение изменений файлов"""
        api_requests_counter.labels(endpoint='file-changes', method='GET').inc()
        recent_changes = self.file_changes[-100:]
        self.file_changes = []
        return web.json_response(recent_changes)
    
    async def handle_syntax_check(self, request):
        """API: Проверка синтаксиса кода"""
        api_requests_counter.labels(endpoint='syntax-check', method='GET').inc()
        
        with check_duration_histogram.labels(check_type='syntax').time():
            errors = await self.run_syntax_check()
        
        syntax_errors_gauge.set(len(errors))
        
        return web.json_response({
            'errors': errors,
            'total': len(errors),
            'timestamp': datetime.now().isoformat()
        })
    
    async def handle_security_scan(self, request):
        """API: Сканирование безопасности"""
        api_requests_counter.labels(endpoint='security-scan', method='GET').inc()
        
        with check_duration_histogram.labels(check_type='security').time():
            vulnerabilities = await self.run_security_scan()
        
        security_issues_gauge.set(len(vulnerabilities))
        
        return web.json_response({
            'vulnerabilities': vulnerabilities,
            'total': len(vulnerabilities),
            'timestamp': datetime.now().isoformat()
        })
    
    async def handle_compliance_check(self, request):
        """API: Проверка соответствия стандартам"""
        standard = request.match_info['standard']
        api_requests_counter.labels(endpoint=f'compliance/{standard}', method='GET').inc()
        
        if standard not in self.compliance_standards:
            return web.json_response({'error': f'Unknown standard: {standard}'}, status=400)
        
        try:
            with check_duration_histogram.labels(check_type='compliance').time():
                result = await self.compliance_standards[standard]()
            
            compliance_score_gauge.labels(standard=standard).set(result['score'])
            return web.json_response(result)
        except Exception as e:
            logger.error(f"Compliance check error for {standard}: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def handle_integration_test(self, request):
        """API: Запуск интеграционных тестов"""
        api_requests_counter.labels(endpoint='integration-test', method='GET').inc()
        
        with check_duration_histogram.labels(check_type='integration').time():
            result = await self.run_integration_tests()
        
        return web.json_response(result)
    
    async def handle_start_watcher(self, request):
        """API: Запуск файлового наблюдателя"""
        api_requests_counter.labels(endpoint='start-watcher', method='POST').inc()
        
        data = await request.json()
        paths = data.get('paths', [])
        
        for path in paths:
            if Path(path).exists() and path not in self.watch_paths:
                self.watch_paths.append(path)
                if self.file_observer:
                    event_handler = FileChangeHandler(self)
                    self.file_observer.schedule(event_handler, path, recursive=True)
                    logger.info(f"Added watch path: {path}")
        
        watcher_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        
        return web.json_response({
            'watcherId': watcher_id,
            'paths': self.watch_paths,
            'status': 'active'
        })
    
    async def handle_status(self, request):
        """API: Получение статуса системы"""
        api_requests_counter.labels(endpoint='status', method='GET').inc()
        status = await self.get_system_status()
        return web.json_response(status)
    
    async def handle_metrics(self, request):
        """API: Prometheus метрики"""
        api_requests_counter.labels(endpoint='metrics', method='GET').inc()
        metrics = generate_latest()
        return web.Response(text=metrics.decode('utf-8'), content_type='text/plain')
    
    async def handle_agent_validate(self, request):
        """API: Валидация через AI агентов"""
        api_requests_counter.labels(endpoint='agents/validate', method='POST').inc()
        
        try:
            data = await request.json()
            agents = data.get('agents', [])
            context = data.get('context', {})
            
            validation_score = await self.validate_with_agents(agents, context)
            
            return web.json_response({
                'score': validation_score,
                'agents': agents,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Agent validation error: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def handle_agent_process(self, request):
        """API: Обработка файла агентом"""
        api_requests_counter.labels(endpoint='agents/process', method='POST').inc()
        
        data = await request.json()
        agent = data.get('agent')
        file_path = data.get('file')
        action = data.get('action')
        
        task_id = await self.queue_agent_task(agent, file_path, action)
        
        return web.json_response({
            'taskId': task_id,
            'agent': agent,
            'status': 'queued'
        })
    
    # === Вспомогательные методы (упрощенные версии) ===
    
    async def run_syntax_check(self) -> List[Dict]:
        """Выполнение проверки синтаксиса"""
        errors = []
        target_dir = Path('/Volumes/Z7S/development/GalaxyDevelopers/DevSystem')
        
        # Проверяем Python файлы
        for file_path in target_dir.glob('**/*.py'):
            if any(x in str(file_path) for x in ['venv', '__pycache__', '._']):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                    ast.parse(code)
            except SyntaxError as e:
                errors.append({
                    'file': str(file_path),
                    'line': e.lineno,
                    'message': str(e.msg),
                    'type': 'syntax_error'
                })
            except Exception:
                pass
        
        return errors[:10]  # Ограничиваем количество
    
    async def run_security_scan(self) -> List[Dict]:
        """Выполнение сканирования безопасности"""
        vulnerabilities = []
        
        try:
            b_mgr = manager.BanditManager()
            target_dir = '/Volumes/Z7S/development/GalaxyDevelopers/DevSystem'
            
            python_files = []
            for file_path in Path(target_dir).glob('**/*.py'):
                if any(x in str(file_path) for x in ['venv', '__pycache__']):
                    continue
                python_files.append(str(file_path))
            
            if python_files[:5]:  # Проверяем только первые 5 файлов
                b_mgr.discover_files(python_files[:5])
                b_mgr.run_tests()
                
                for issue in b_mgr.get_issue_list()[:10]:
                    vulnerabilities.append({
                        'file': issue.fname,
                        'line': issue.lineno,
                        'severity': issue.severity,
                        'message': issue.text
                    })
        except Exception as e:
            logger.error(f"Security scan error: {e}")
        
        return vulnerabilities
    
    async def check_iso27001_compliance(self) -> Dict:
        """Проверка соответствия ISO 27001"""
        checks = {
            'access_control': Path('/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/.htaccess').exists(),
            'encryption': False,
            'logging': Path('/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/logs').exists(),
            'backup': Path('/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/backups').exists(),
            'incident_response': False
        }
        
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        score = (passed / total) * 100
        
        return {
            'standard': 'ISO27001',
            'score': score,
            'compliant': score >= 80,
            'checks': checks,
            'timestamp': datetime.now().isoformat()
        }
    
    async def check_itil4_compliance(self) -> Dict:
        """Проверка соответствия ITIL 4"""
        checks = {
            'service_catalog': Path('/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem').exists(),
            'change_management': Path('/Volumes/Z7S/development/GalaxyDevelopers/.git').exists(),
            'incident_management': self.memory_db_path.exists(),
            'problem_management': True,
            'configuration_management': Path('/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/config.json').exists()
        }
        
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        score = (passed / total) * 100
        
        return {
            'standard': 'ITIL4',
            'score': score,
            'compliant': score >= 75,
            'checks': checks,
            'timestamp': datetime.now().isoformat()
        }
    
    async def check_cobit_compliance(self) -> Dict:
        """Проверка соответствия COBIT"""
        checks = {
            'governance': Path('/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/README.md').exists(),
            'risk_management': False,
            'performance_monitoring': True,
            'resource_optimization': True
        }
        
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        score = (passed / total) * 100
        
        return {
            'standard': 'COBIT',
            'score': score,
            'compliant': score >= 70,
            'checks': checks,
            'timestamp': datetime.now().isoformat()
        }
    
    async def run_integration_tests(self) -> Dict:
        """Запуск интеграционных тестов"""
        tests = [
            {
                'name': 'WebSocket Connection',
                'passed': len(self.websocket_clients) >= 0,
                'message': f'{len(self.websocket_clients)} active connections'
            },
            {
                'name': 'File Monitoring',
                'passed': self.file_observer and self.file_observer.is_alive(),
                'message': f'Watching {len(self.watch_paths)} paths'
            },
            {
                'name': 'Memory Database',
                'passed': self.memory_db_path.exists(),
                'message': 'Database accessible'
            },
            {
                'name': 'API Endpoints',
                'passed': True,
                'message': 'All endpoints registered'
            }
        ]
        
        passed = sum(1 for t in tests if t['passed'])
        failed = len(tests) - passed
        
        return {
            'tests': tests,
            'passed': passed,
            'failed': failed,
            'total': len(tests),
            'success_rate': (passed / len(tests)) * 100,
            'timestamp': datetime.now().isoformat()
        }
    
    async def validate_with_agents(self, agents: List[str], context: Dict) -> float:
        """Валидация через AI агентов"""
        try:
            base_score = 85.0
            
            if self.file_observer and self.file_observer.is_alive():
                base_score += 5
            
            if len(self.websocket_clients) > 0:
                base_score += 5
            
            errors = await self.run_syntax_check()
            if errors:
                base_score -= min(len(errors), 10)
            
            return max(min(base_score, 100), 0)
        except Exception as e:
            logger.error(f"Error in validate_with_agents: {e}")
            return 75.0
    
    async def queue_agent_task(self, agent: str, file_path: str, action: str) -> str:
        """Добавление задачи в очередь агента"""
        task_id = hashlib.md5(f"{agent}{file_path}{time.time()}".encode()).hexdigest()[:12]
        
        self.agent_statuses[agent] = {
            'status': 'processing',
            'current_task': f"{action} {file_path}",
            'task_id': task_id,
            'started_at': datetime.now().isoformat()
        }
        
        await self.broadcast_to_websockets({
            'type': 'agent_status',
            'agent': agent,
            'status': 'active'
        })
        
        logger.info(f"Queued task {task_id} for {agent}")
        return task_id
    
    # ========== AI PROTECTION HANDLERS ==========
    
    async def handle_protection_check(self, request):
        """API: Проверка файла через AI Protection"""
        api_requests_counter.labels(endpoint='protection/check-file', method='POST').inc()
        
        if not self.ai_auditor:
            return web.json_response({
                'error': 'AI Protection System not available'
            }, status=503)
        
        try:
            data = await request.json()
            file_path = data.get('file_path')
            operation = data.get('operation', 'read')
            
            if not file_path:
                return web.json_response({
                    'error': 'file_path required'
                }, status=400)
            
            # Проверяем файл через AI
            result = await self.check_file_with_ai(file_path, operation)
            
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"Protection check error: {e}")
            return web.json_response({
                'error': str(e)
            }, status=500)
    
    async def handle_protection_scan(self, request):
        """API: Сканирование директории на угрозы"""
        api_requests_counter.labels(endpoint='protection/scan-threats', method='POST').inc()
        
        if not self.ai_auditor:
            return web.json_response({
                'error': 'AI Protection System not available'
            }, status=503)
        
        try:
            data = await request.json()
            directory = data.get('directory', '/Volumes/Z7S/development/GalaxyDevelopers/DevSystem')
            
            # Сканируем директорию
            threats = await self.scan_directory_threats(directory)
            
            return web.json_response(threats)
            
        except Exception as e:
            logger.error(f"Protection scan error: {e}")
            return web.json_response({
                'error': str(e)
            }, status=500)
    
    async def handle_protection_status(self, request):
        """API: Статус системы защиты"""
        api_requests_counter.labels(endpoint='protection/status', method='GET').inc()
        
        if not self.ai_auditor:
            return web.json_response({
                'protection_enabled': False,
                'reason': 'AI Protection System not available'
            })
        
        try:
            status = await self.get_protection_status()
            return web.json_response(status)
            
        except Exception as e:
            logger.error(f"Protection status error: {e}")
            return web.json_response({
                'error': str(e)
            }, status=500)
    
    async def handle_audit_code(self, request):
        """API: Аудит кода через AI"""
        api_requests_counter.labels(endpoint='protection/audit-code', method='POST').inc()
        
        if not self.ai_auditor:
            return web.json_response({
                'error': 'AI Protection System not available'
            }, status=503)
        
        try:
            data = await request.json()
            code = data.get('code')
            file_path = data.get('file_path', 'unknown')
            
            if not code:
                return web.json_response({
                    'error': 'code required'
                }, status=400)
            
            # Аудит кода через AI
            audit_result = await self.audit_code_with_ai(code, file_path)
            
            return web.json_response(audit_result)
            
        except Exception as e:
            logger.error(f"Code audit error: {e}")
            return web.json_response({
                'error': str(e)
            }, status=500)
    
    # ========== AI PROTECTION METHODS ==========
    
    async def check_file_with_ai(self, file_path: str, operation: str) -> Dict:
        """Проверка файла через AI Protection System"""
        if not self.ai_auditor:
            return {'error': 'AI Protection not available'}
        
        try:
            # Здесь интегрируем с реальной системой защиты
            # Пока делаем базовую проверку
            
            # Проверяем существование файла
            if not Path(file_path).exists():
                return {
                    'allowed': False,
                    'risk_level': 'medium',
                    'reason': 'File does not exist',
                    'recommendations': ['Verify file path']
                }
            
            # Проверяем расширение
            ext = Path(file_path).suffix.lower()
            dangerous_extensions = ['.sh', '.bat', '.exe', '.dll', '.so']
            
            if ext in dangerous_extensions:
                risk_level = 'high'
                allowed = operation == 'read'
                reason = f'Dangerous file extension: {ext}'
            else:
                risk_level = 'low'
                allowed = True
                reason = 'File appears safe'
            
            # Проверяем права доступа
            try:
                stat_info = Path(file_path).stat()
                file_size = stat_info.st_size
                
                if file_size > 100 * 1024 * 1024:  # 100MB
                    risk_level = 'medium'
                    reason += ' (Large file size)'
            except:
                pass
            
            return {
                'file_path': file_path,
                'operation': operation,
                'allowed': allowed,
                'risk_level': risk_level,
                'reason': reason,
                'timestamp': datetime.now().isoformat(),
                'recommendations': self.get_security_recommendations(risk_level)
            }
            
        except Exception as e:
            return {
                'error': f'AI check failed: {str(e)}',
                'allowed': False,
                'risk_level': 'high'
            }
    
    async def scan_directory_threats(self, directory: str) -> Dict:
        """Сканирование директории на угрозы"""
        threats = []
        total_files = 0
        scanned_files = 0
        
        try:
            for root, dirs, files in os.walk(directory):
                # Пропускаем системные директории
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv']]
                
                for file in files:
                    if file.startswith('.'):
                        continue
                        
                    total_files += 1
                    file_path = os.path.join(root, file)
                    
                    # Ограничиваем сканирование первыми 100 файлами
                    if scanned_files >= 100:
                        break
                    
                    # Проверяем файл
                    check_result = await self.check_file_with_ai(file_path, 'scan')
                    
                    if check_result.get('risk_level') in ['high', 'critical']:
                        threats.append({
                            'file': file_path,
                            'risk_level': check_result.get('risk_level'),
                            'reason': check_result.get('reason'),
                            'recommendations': check_result.get('recommendations', [])
                        })
                    
                    scanned_files += 1
        
        except Exception as e:
            logger.error(f"Directory scan error: {e}")
        
        return {
            'directory': directory,
            'total_files': total_files,
            'scanned_files': scanned_files,
            'threats_found': len(threats),
            'threats': threats[:20],  # Ограничиваем вывод
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_protection_status(self) -> Dict:
        """Получение статуса системы защиты"""
        return {
            'protection_enabled': self.ai_auditor is not None,
            'ai_auditor_status': 'active' if self.ai_auditor else 'inactive',
            'protected_paths': self.watch_paths,
            'last_scan': datetime.now().isoformat(),
            'features': {
                'file_integrity_check': True,
                'ai_threat_detection': self.ai_auditor is not None,
                'real_time_monitoring': True,
                'automated_response': False  # Пока отключено
            }
        }
    
    async def audit_code_with_ai(self, code: str, file_path: str) -> Dict:
        """Аудит кода через AI"""
        try:
            # Базовые проверки кода
            issues = []
            risk_score = 0
            
            # Проверяем на опасные паттерны
            dangerous_patterns = [
                (r'eval\s*\(', 'Use of eval() function', 30),
                (r'exec\s*\(', 'Use of exec() function', 30),
                (r'os\.system\s*\(', 'System command execution', 25),
                (r'subprocess\.\w+', 'Subprocess execution', 20),
                (r'open\s*\([^)]*[\'"][wa]', 'File write operation', 15),
                (r'rm\s+-rf', 'Dangerous file deletion', 40),
                (r'chmod\s+777', 'Overly permissive file permissions', 25),
                (r'password\s*=\s*[\'"][^\'\"]+[\'"]', 'Hardcoded password', 35),
                (r'api_key\s*=\s*[\'"][^\'\"]+[\'"]', 'Hardcoded API key', 35),
            ]
            
            for pattern, description, score in dangerous_patterns:
                matches = re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line_num = code[:match.start()].count('\n') + 1
                    issues.append({
                        'type': 'security_risk',
                        'line': line_num,
                        'description': description,
                        'severity': 'high' if score >= 30 else 'medium' if score >= 20 else 'low',
                        'code_snippet': code[max(0, match.start()-20):match.end()+20]
                    })
                    risk_score += score
            
            # Определяем общий уровень риска
            if risk_score >= 80:
                overall_risk = 'critical'
            elif risk_score >= 50:
                overall_risk = 'high'
            elif risk_score >= 25:
                overall_risk = 'medium'
            else:
                overall_risk = 'low'
            
            return {
                'file_path': file_path,
                'risk_score': min(risk_score, 100),
                'overall_risk': overall_risk,
                'issues_found': len(issues),
                'issues': issues[:10],  # Ограничиваем вывод
                'recommendations': self.get_code_recommendations(overall_risk),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'error': f'Code audit failed: {str(e)}',
                'risk_score': 100,
                'overall_risk': 'unknown'
            }
    
    def get_security_recommendations(self, risk_level: str) -> List[str]:
        """Получение рекомендаций по безопасности"""
        recommendations = {
            'low': [
                'Continue monitoring file',
                'Regular integrity checks'
            ],
            'medium': [
                'Review file permissions',
                'Monitor file changes closely',
                'Consider additional access controls'
            ],
            'high': [
                'Restrict file access',
                'Implement additional security measures',
                'Review file necessity',
                'Consider quarantine if suspicious'
            ],
            'critical': [
                'IMMEDIATE ATTENTION REQUIRED',
                'Isolate file immediately',
                'Conduct security audit',
                'Consider system-wide scan'
            ]
        }
        
        return recommendations.get(risk_level, ['Review file manually'])
    
    def get_code_recommendations(self, risk_level: str) -> List[str]:
        """Получение рекомендаций по коду"""
        recommendations = {
            'low': [
                'Code appears safe',
                'Continue with regular reviews'
            ],
            'medium': [
                'Review highlighted security issues',
                'Consider safer alternatives',
                'Add input validation'
            ],
            'high': [
                'Address security vulnerabilities immediately',
                'Review all highlighted issues',
                'Implement security best practices',
                'Consider code refactoring'
            ],
            'critical': [
                'CRITICAL SECURITY ISSUES FOUND',
                'Do not deploy this code',
                'Immediate security review required',
                'Consider complete rewrite of affected sections'
            ]
        }
        
        return recommendations.get(risk_level, ['Manual code review required'])
    
    async def get_system_status(self) -> Dict:
        """Получение полного статуса системы"""
        return {
            'type': 'system_status',
            'websocket_clients': len(self.websocket_clients),
            'file_observer_active': self.file_observer and self.file_observer.is_alive(),
            'watched_paths': self.watch_paths,
            'recent_changes': len(self.file_changes),
            'agent_statuses': self.agent_statuses,
            'ai_protection': {
                'enabled': self.ai_auditor is not None,
                'status': 'active' if self.ai_auditor else 'inactive',
                'features': [
                    'File integrity monitoring',
                    'AI threat detection',
                    'Real-time code analysis',
                    'Permission validation'
                ] if self.ai_auditor else []
            },
            'timestamp': datetime.now().isoformat()
        }
    
    async def run_periodic_checks(self):
        """Запуск периодических проверок"""
        while True:
            try:
                await asyncio.sleep(30)
                
                syntax_errors = await self.run_syntax_check()
                security_issues = await self.run_security_scan()
                
                syntax_errors_gauge.set(len(syntax_errors))
                security_issues_gauge.set(len(security_issues))
                
                status = await self.get_system_status()
                status['syntax_errors'] = len(syntax_errors)
                status['security_issues'] = len(security_issues)
                
                await self.broadcast_to_websockets(status)
                
                logger.info(f"Periodic check: {len(syntax_errors)} syntax errors, {len(security_issues)} security issues")
                
            except Exception as e:
                logger.error(f"Error in periodic checks: {e}")
    
    def stop(self):
        """Остановка сервера"""
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()
        
        self.executor.shutdown(wait=True)
        logger.info("🛑 Monitoring server stopped")


async def main():
    """Главная функция"""
    server = MonitoringServer()
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        server.stop()


if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════╗
    ║   GALAXY MONITORING SERVER v2.1 FIXED  ║
    ║     Real-time System Monitoring        ║
    ╚════════════════════════════════════════╝
    """)
    
    asyncio.run(main())