"""
ГЛАВНЫЙ КОНФИГУРАЦИОННЫЙ ФАЙЛ PYTEST
Верховный Инквизитор Тестирования
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import asyncio
import json
import time
from datetime import datetime

# Добавляем корневую директорию в PATH
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "AGENTS"))

# ФИКСТУРЫ ДЛЯ ВСЕХ ТЕСТОВ

@pytest.fixture(scope="session")
def event_loop():
    """Создаем event loop для async тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_kafka_producer():
    """Mock для Kafka Producer"""
    with patch('kafka.KafkaProducer') as mock:
        producer = MagicMock()
        producer.send.return_value.get.return_value = {'status': 'success'}
        mock.return_value = producer
        yield producer

@pytest.fixture
def mock_kafka_consumer():
    """Mock для Kafka Consumer"""
    with patch('kafka.KafkaConsumer') as mock:
        consumer = MagicMock()
        consumer.__iter__.return_value = []
        mock.return_value = consumer
        yield consumer

@pytest.fixture
def mock_postgres_connection():
    """Mock для PostgreSQL соединения"""
    with patch('psycopg2.connect') as mock:
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        cursor.fetchone.return_value = None
        conn.cursor.return_value = cursor
        mock.return_value = conn
        yield conn

@pytest.fixture
def mock_redis_client():
    """Mock для Redis клиента"""
    with patch('redis.Redis') as mock:
        client = MagicMock()
        client.get.return_value = None
        client.set.return_value = True
        mock.return_value = client
        yield client

@pytest.fixture
def mock_openai_client():
    """Mock для OpenAI API"""
    with patch('openai.OpenAI') as mock:
        client = MagicMock()
        response = MagicMock()
        response.choices = [MagicMock(message=MagicMock(content="Test response"))]
        client.chat.completions.create.return_value = response
        mock.return_value = client
        yield client

@pytest.fixture
def mock_gemini_client():
    """Mock для Gemini API"""
    with patch('google.generativeai.GenerativeModel') as mock:
        model = MagicMock()
        response = MagicMock()
        response.text = "Test Gemini response"
        model.generate_content.return_value = response
        mock.return_value = model
        yield model

@pytest.fixture
def sample_task():
    """Пример задачи для тестирования"""
    return {
        'id': 'test-task-001',
        'type': 'research',
        'title': 'Test Research Task',
        'description': 'Research ITIL 4 best practices',
        'priority': 'high',
        'metadata': {
            'created_at': datetime.now().isoformat(),
            'author': 'test_suite',
            'tags': ['test', 'research', 'itil']
        }
    }

@pytest.fixture
def sample_document():
    """Пример документа для тестирования"""
    return {
        'id': 'doc-001',
        'title': 'Test Document',
        'content': '# Test Document\n\nThis is a test document for validation.',
        'format': 'markdown',
        'metadata': {
            'created_at': datetime.now().isoformat(),
            'author': 'ComposerAgent',
            'version': '1.0.0',
            'standards': ['ISO_27001', 'ITIL_4']
        }
    }

@pytest.fixture
def compliance_standards():
    """Стандарты для проверки compliance"""
    return {
        'ISO_27001': [
            'A.5 Information security policies',
            'A.6 Organization of information security',
            'A.7 Human resource security',
            'A.8 Asset management',
            'A.9 Access control'
        ],
        'ITIL_4': [
            'Incident Management',
            'Problem Management',
            'Change Enablement',
            'Service Request Management',
            'Service Level Management'
        ],
        'COBIT': [
            'EDM - Evaluate, Direct and Monitor',
            'APO - Align, Plan and Organize',
            'BAI - Build, Acquire and Implement',
            'DSS - Deliver, Service and Support',
            'MEA - Monitor, Evaluate and Assess'
        ]
    }

@pytest.fixture
def performance_metrics():
    """Метрики производительности для проверки"""
    return {
        'response_time_p50': 100,  # ms
        'response_time_p99': 1000,  # ms
        'response_time_p99_9': 5000,  # ms
        'error_rate': 0.01,  # %
        'availability': 99.99,  # %
        'throughput': 1000  # req/sec
    }

@pytest.fixture
def security_vectors():
    """Векторы атак для security тестов"""
    return {
        'sql_injection': "'; DROP TABLE agents; --",
        'xss': "<script>alert('pwned')</script>",
        'path_traversal': "../../../../etc/passwd",
        'command_injection': "; rm -rf /",
        'xxe': '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
        'csrf_token': 'invalid_csrf_token_12345',
        'buffer_overflow': 'A' * 10000,
        'null_byte': 'file.txt\x00.jpg'
    }

# ХУКИ ДЛЯ ОТЧЕТОВ

def pytest_configure(config):
    """Конфигурация перед запуском тестов"""
    # Создаем директории для отчетов
    reports_dir = ROOT_DIR / "reports"
    reports_dir.mkdir(exist_ok=True)
    (reports_dir / "coverage").mkdir(exist_ok=True)
    (reports_dir / "performance").mkdir(exist_ok=True)
    (reports_dir / "security").mkdir(exist_ok=True)
    
    # Добавляем кастомные маркеры
    config.addinivalue_line(
        "markers", "critical: Критические тесты которые должны пройти"
    )

def pytest_sessionstart(session):
    """Действия перед началом тестовой сессии"""
    print("\n" + "="*80)
    print("🔥 ИНКВИЗИЦИЯ НАЧАЛАСЬ! ТЕСТИРОВАНИЕ DOCUMENTSSYSTEM 🔥")
    print("="*80 + "\n")

def pytest_sessionfinish(session, exitstatus):
    """Действия после завершения тестовой сессии"""
    print("\n" + "="*80)
    if exitstatus == 0:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! КОД ДОСТОИН ЖИЗНИ!")
    else:
        print("❌ ТЕСТЫ ПРОВАЛЕНЫ! КОД ДОЛЖЕН БЫТЬ УНИЧТОЖЕН!")
    print("="*80 + "\n")

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Создаем детальные отчеты о каждом тесте"""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call" and report.failed:
        # Логируем провалившиеся тесты
        with open(ROOT_DIR / "reports" / "failed_tests.log", "a") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"FAILED: {item.nodeid}\n")
            f.write(f"Time: {datetime.now().isoformat()}\n")
            f.write(f"Error: {report.longrepr}\n")

# МЕТРИКИ КАЧЕСТВА

class TestMetrics:
    """Сборщик метрик тестирования"""
    
    def __init__(self):
        self.start_time = time.time()
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.assertions = 0
        self.bugs_found = []
    
    def record_bug(self, bug_description):
        """Записываем найденный баг"""
        self.bugs_found.append({
            'id': f'BUG-{len(self.bugs_found)+1:03d}',
            'description': bug_description,
            'timestamp': datetime.now().isoformat()
        })
    
    def generate_report(self):
        """Генерируем отчет о тестировании"""
        duration = time.time() - self.start_time
        return {
            'duration_seconds': duration,
            'total_tests': self.tests_run,
            'passed': self.tests_passed,
            'failed': self.tests_failed,
            'pass_rate': (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0,
            'assertions_count': self.assertions,
            'bugs_found': len(self.bugs_found),
            'bugs': self.bugs_found
        }

@pytest.fixture(scope="session")
def test_metrics():
    """Глобальные метрики тестирования"""
    return TestMetrics()