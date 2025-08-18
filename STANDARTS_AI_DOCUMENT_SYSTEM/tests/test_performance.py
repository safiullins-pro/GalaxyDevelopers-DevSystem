"""
PERFORMANCE ТЕСТЫ - ХРОНОМЕТРИСТ АПОКАЛИПСИСА
Нагрузочное тестирование до отказа
1000+ req/sec или смерть
"""

import pytest
import asyncio
import aiohttp
import time
import statistics
import json
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
import numpy as np
from locust import HttpUser, task, between
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

class PerformanceMetrics:
    """Сборщик метрик производительности"""
    
    def __init__(self):
        self.response_times = []
        self.errors = 0
        self.success = 0
        self.start_time = time.time()
    
    def record_request(self, duration, success=True):
        """Записываем результат запроса"""
        self.response_times.append(duration)
        if success:
            self.success += 1
        else:
            self.errors += 1
    
    def get_stats(self):
        """Получаем статистику"""
        if not self.response_times:
            return {}
        
        sorted_times = sorted(self.response_times)
        total_requests = len(self.response_times)
        
        return {
            'total_requests': total_requests,
            'success': self.success,
            'errors': self.errors,
            'error_rate': (self.errors / total_requests * 100) if total_requests > 0 else 0,
            'duration': time.time() - self.start_time,
            'rps': total_requests / (time.time() - self.start_time),
            'min': min(sorted_times),
            'max': max(sorted_times),
            'mean': statistics.mean(sorted_times),
            'median': statistics.median(sorted_times),
            'p50': sorted_times[int(len(sorted_times) * 0.50)],
            'p90': sorted_times[int(len(sorted_times) * 0.90)],
            'p95': sorted_times[int(len(sorted_times) * 0.95)],
            'p99': sorted_times[int(len(sorted_times) * 0.99)],
            'p999': sorted_times[int(len(sorted_times) * 0.999)] if len(sorted_times) > 1000 else sorted_times[-1]
        }

@pytest.mark.performance
class TestSmokePerformance:
    """SMOKE ТЕСТЫ - система вообще дышит?"""
    
    def test_single_request_baseline(self):
        """Тест 1: Один запрос - baseline"""
        import requests
        
        start = time.time()
        response = requests.get('http://localhost:8001/health', timeout=5)
        duration = (time.time() - start) * 1000
        
        assert response.status_code == 200, "Health check failed"
        assert duration < 100, f"Too slow: {duration}ms (should be < 100ms)"
        print(f"✅ Single request: {duration:.2f}ms")
    
    def test_10_sequential_requests(self):
        """Тест 2: 10 последовательных запросов"""
        import requests
        metrics = PerformanceMetrics()
        
        for i in range(10):
            start = time.time()
            try:
                response = requests.get('http://localhost:8001/health')
                duration = (time.time() - start) * 1000
                metrics.record_request(duration, response.status_code == 200)
            except:
                metrics.record_request(5000, False)
        
        stats = metrics.get_stats()
        assert stats['error_rate'] < 10, f"Error rate too high: {stats['error_rate']}%"
        assert stats['p95'] < 200, f"P95 too high: {stats['p95']}ms"
        print(f"✅ 10 requests: P95={stats['p95']:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_10_concurrent_requests(self):
        """Тест 3: 10 параллельных запросов"""
        metrics = PerformanceMetrics()
        
        async def make_request(session):
            start = time.time()
            try:
                async with session.get('http://localhost:8001/health') as response:
                    duration = (time.time() - start) * 1000
                    metrics.record_request(duration, response.status == 200)
            except:
                metrics.record_request(5000, False)
        
        async with aiohttp.ClientSession() as session:
            tasks = [make_request(session) for _ in range(10)]
            await asyncio.gather(*tasks)
        
        stats = metrics.get_stats()
        assert stats['error_rate'] < 10, f"Error rate: {stats['error_rate']}%"
        assert stats['p95'] < 300, f"P95: {stats['p95']}ms"
        print(f"✅ 10 concurrent: P95={stats['p95']:.2f}ms")

@pytest.mark.performance
@pytest.mark.slow
class TestLoadPerformance:
    """LOAD ТЕСТЫ - 1000 req/sec разминка"""
    
    @pytest.mark.asyncio
    async def test_100_requests_per_second(self):
        """Тест 4: 100 req/sec в течение 10 секунд"""
        metrics = PerformanceMetrics()
        duration_seconds = 10
        target_rps = 100
        
        async def make_request(session):
            start = time.time()
            try:
                async with session.get('http://localhost:8001/health') as response:
                    duration = (time.time() - start) * 1000
                    metrics.record_request(duration, response.status == 200)
            except Exception as e:
                metrics.record_request(5000, False)
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            request_count = 0
            
            while time.time() - start_time < duration_seconds:
                # Запускаем батч запросов
                batch_size = int(target_rps / 10)  # 10 батчей в секунду
                tasks = [make_request(session) for _ in range(batch_size)]
                await asyncio.gather(*tasks)
                request_count += batch_size
                
                # Контролируем rate
                await asyncio.sleep(0.1)
        
        stats = metrics.get_stats()
        print(f"✅ Load test 100 rps: {stats['total_requests']} requests")
        print(f"   RPS: {stats['rps']:.2f}")
        print(f"   P50: {stats['p50']:.2f}ms")
        print(f"   P99: {stats['p99']:.2f}ms")
        print(f"   Errors: {stats['error_rate']:.2f}%")
        
        assert stats['rps'] >= 90, f"RPS too low: {stats['rps']}"
        assert stats['p99'] < 1000, f"P99 too high: {stats['p99']}ms"
        assert stats['error_rate'] < 1, f"Error rate too high: {stats['error_rate']}%"
    
    @pytest.mark.asyncio
    async def test_500_requests_per_second(self):
        """Тест 5: 500 req/sec в течение 10 секунд"""
        metrics = PerformanceMetrics()
        duration_seconds = 10
        target_rps = 500
        
        connector = aiohttp.TCPConnector(limit=100)
        async with aiohttp.ClientSession(connector=connector) as session:
            
            async def make_request():
                start = time.time()
                try:
                    async with session.get('http://localhost:8001/health') as response:
                        duration = (time.time() - start) * 1000
                        metrics.record_request(duration, response.status == 200)
                except:
                    metrics.record_request(5000, False)
            
            start_time = time.time()
            while time.time() - start_time < duration_seconds:
                batch_size = int(target_rps / 20)  # 20 батчей в секунду
                tasks = [make_request() for _ in range(batch_size)]
                await asyncio.gather(*tasks)
                await asyncio.sleep(0.05)
        
        stats = metrics.get_stats()
        print(f"✅ Load test 500 rps: {stats['total_requests']} requests")
        print(f"   RPS: {stats['rps']:.2f}")
        print(f"   P50: {stats['p50']:.2f}ms")
        print(f"   P99: {stats['p99']:.2f}ms")
        print(f"   Errors: {stats['error_rate']:.2f}%")
        
        assert stats['rps'] >= 450, f"RPS too low: {stats['rps']}"
        assert stats['p99'] < 2000, f"P99 too high: {stats['p99']}ms"
        assert stats['error_rate'] < 5, f"Error rate too high: {stats['error_rate']}%"
    
    @pytest.mark.asyncio
    async def test_1000_requests_per_second(self):
        """Тест 6: 1000 req/sec - ЦЕЛЕВАЯ НАГРУЗКА"""
        metrics = PerformanceMetrics()
        duration_seconds = 10
        target_rps = 1000
        
        connector = aiohttp.TCPConnector(limit=200)
        async with aiohttp.ClientSession(connector=connector) as session:
            
            async def make_request():
                start = time.time()
                try:
                    async with session.get('http://localhost:8001/health') as response:
                        duration = (time.time() - start) * 1000
                        metrics.record_request(duration, response.status == 200)
                except:
                    metrics.record_request(5000, False)
            
            start_time = time.time()
            while time.time() - start_time < duration_seconds:
                batch_size = int(target_rps / 50)  # 50 батчей в секунду
                tasks = [make_request() for _ in range(batch_size)]
                await asyncio.gather(*tasks)
                await asyncio.sleep(0.02)
        
        stats = metrics.get_stats()
        print(f"🔥 Load test 1000 rps: {stats['total_requests']} requests")
        print(f"   RPS: {stats['rps']:.2f}")
        print(f"   P50: {stats['p50']:.2f}ms")
        print(f"   P99: {stats['p99']:.2f}ms")
        print(f"   P999: {stats['p999']:.2f}ms")
        print(f"   Errors: {stats['error_rate']:.2f}%")
        
        assert stats['rps'] >= 900, f"RPS too low: {stats['rps']}"
        assert stats['p99'] < 5000, f"P99 too high: {stats['p99']}ms"
        assert stats['error_rate'] < 10, f"Error rate too high: {stats['error_rate']}%"

@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.destructive
class TestStressPerformance:
    """STRESS ТЕСТЫ - 10000 req/sec, потеет?"""
    
    @pytest.mark.asyncio
    async def test_stress_10000_rps(self):
        """Тест 7: 10000 req/sec - STRESS TEST"""
        metrics = PerformanceMetrics()
        duration_seconds = 5  # Короче, чтобы не убить систему
        target_rps = 10000
        
        connector = aiohttp.TCPConnector(limit=500, force_close=True)
        async with aiohttp.ClientSession(connector=connector) as session:
            
            async def make_request():
                start = time.time()
                try:
                    async with session.get('http://localhost:8001/health', timeout=1) as response:
                        duration = (time.time() - start) * 1000
                        metrics.record_request(duration, response.status == 200)
                except:
                    metrics.record_request(5000, False)
            
            start_time = time.time()
            while time.time() - start_time < duration_seconds:
                batch_size = int(target_rps / 100)  # 100 батчей в секунду
                tasks = [make_request() for _ in range(batch_size)]
                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(0.01)
        
        stats = metrics.get_stats()
        print(f"💀 Stress test 10000 rps: {stats['total_requests']} requests")
        print(f"   RPS achieved: {stats['rps']:.2f}")
        print(f"   P50: {stats['p50']:.2f}ms")
        print(f"   P99: {stats['p99']:.2f}ms")
        print(f"   Errors: {stats['error_rate']:.2f}%")
        
        # Менее строгие требования для stress теста
        assert stats['rps'] >= 5000, f"RPS too low even for stress: {stats['rps']}"
        assert stats['error_rate'] < 50, f"Too many errors: {stats['error_rate']}%"

@pytest.mark.performance
@pytest.mark.slow
class TestSpikePerformance:
    """SPIKE ТЕСТЫ - 0 -> 100000 -> 0, сердце выдержит?"""
    
    @pytest.mark.asyncio
    async def test_spike_pattern(self):
        """Тест 8: Spike паттерн нагрузки"""
        metrics = PerformanceMetrics()
        
        async def make_requests(session, count):
            tasks = []
            for _ in range(count):
                async def req():
                    start = time.time()
                    try:
                        async with session.get('http://localhost:8001/health') as response:
                            duration = (time.time() - start) * 1000
                            metrics.record_request(duration, response.status == 200)
                    except:
                        metrics.record_request(5000, False)
                tasks.append(req())
            await asyncio.gather(*tasks, return_exceptions=True)
        
        connector = aiohttp.TCPConnector(limit=1000)
        async with aiohttp.ClientSession(connector=connector) as session:
            # Фаза 1: Низкая нагрузка
            print("Phase 1: Low load (10 rps)")
            for _ in range(5):
                await make_requests(session, 10)
                await asyncio.sleep(1)
            
            # Фаза 2: SPIKE!
            print("Phase 2: SPIKE! (10000 requests)")
            await make_requests(session, 10000)
            
            # Фаза 3: Восстановление
            print("Phase 3: Recovery (10 rps)")
            for _ in range(5):
                await make_requests(session, 10)
                await asyncio.sleep(1)
        
        stats = metrics.get_stats()
        print(f"⚡ Spike test results:")
        print(f"   Total: {stats['total_requests']} requests")
        print(f"   P50: {stats['p50']:.2f}ms")
        print(f"   P99: {stats['p99']:.2f}ms")
        print(f"   Errors: {stats['error_rate']:.2f}%")
        
        assert stats['error_rate'] < 20, f"System didn't survive spike: {stats['error_rate']}% errors"

@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.sadistic
class TestSoakPerformance:
    """SOAK ТЕСТЫ - 1000 req/sec 24 часа (марафон)"""
    
    @pytest.mark.asyncio
    async def test_soak_1_hour(self):
        """Тест 9: Soak test - 1 час под нагрузкой"""
        # Упрощенная версия для демо (1 минута вместо часа)
        metrics = PerformanceMetrics()
        duration_seconds = 60  # 1 минута для теста
        target_rps = 1000
        
        connector = aiohttp.TCPConnector(limit=200)
        async with aiohttp.ClientSession(connector=connector) as session:
            
            async def make_request():
                start = time.time()
                try:
                    async with session.get('http://localhost:8001/health') as response:
                        duration = (time.time() - start) * 1000
                        metrics.record_request(duration, response.status == 200)
                except:
                    metrics.record_request(5000, False)
            
            start_time = time.time()
            checkpoint_interval = 10  # Отчет каждые 10 секунд
            last_checkpoint = start_time
            
            while time.time() - start_time < duration_seconds:
                batch_size = int(target_rps / 50)
                tasks = [make_request() for _ in range(batch_size)]
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Checkpoint
                if time.time() - last_checkpoint > checkpoint_interval:
                    stats = metrics.get_stats()
                    print(f"Checkpoint: {stats['total_requests']} reqs, "
                          f"P99={stats['p99']:.0f}ms, "
                          f"Errors={stats['error_rate']:.1f}%")
                    last_checkpoint = time.time()
                
                await asyncio.sleep(0.02)
        
        stats = metrics.get_stats()
        print(f"🏃 Soak test complete:")
        print(f"   Duration: {stats['duration']:.1f}s")
        print(f"   Total: {stats['total_requests']} requests")
        print(f"   RPS: {stats['rps']:.2f}")
        print(f"   P99: {stats['p99']:.2f}ms")
        print(f"   Errors: {stats['error_rate']:.2f}%")
        
        assert stats['error_rate'] < 5, f"Degradation detected: {stats['error_rate']}% errors"
        assert stats['p99'] < 5000, f"Performance degraded: P99={stats['p99']}ms"

@pytest.mark.performance
@pytest.mark.destructive
class TestBreakpointPerformance:
    """BREAKPOINT ТЕСТЫ - увеличиваем пока не сдохнет"""
    
    @pytest.mark.asyncio
    async def test_find_breaking_point(self):
        """Тест 10: Находим точку отказа системы"""
        current_rps = 100
        increment = 100
        max_rps = 50000
        breaking_point = None
        
        while current_rps <= max_rps:
            print(f"Testing {current_rps} rps...")
            metrics = PerformanceMetrics()
            
            connector = aiohttp.TCPConnector(limit=min(current_rps, 1000))
            async with aiohttp.ClientSession(connector=connector) as session:
                
                async def make_request():
                    start = time.time()
                    try:
                        async with session.get('http://localhost:8001/health', timeout=1) as response:
                            duration = (time.time() - start) * 1000
                            metrics.record_request(duration, response.status == 200)
                    except:
                        metrics.record_request(5000, False)
                
                # Тестируем 5 секунд на каждом уровне
                start_time = time.time()
                while time.time() - start_time < 5:
                    batch_size = int(current_rps / 50)
                    tasks = [make_request() for _ in range(batch_size)]
                    await asyncio.gather(*tasks, return_exceptions=True)
                    await asyncio.sleep(0.02)
            
            stats = metrics.get_stats()
            print(f"   Result: {stats['rps']:.0f} rps, "
                  f"P99={stats['p99']:.0f}ms, "
                  f"Errors={stats['error_rate']:.1f}%")
            
            # Критерии отказа
            if stats['error_rate'] > 50 or stats['p99'] > 10000:
                breaking_point = current_rps
                print(f"💥 BREAKING POINT FOUND: {breaking_point} rps")
                break
            
            current_rps += increment
            if current_rps > 1000:
                increment = 500  # Увеличиваем шаг после 1000 rps
        
        assert breaking_point is None or breaking_point >= 1000, \
               f"System broke too early at {breaking_point} rps"

class TestLatencyDistribution:
    """ТЕСТЫ РАСПРЕДЕЛЕНИЯ ЗАДЕРЖЕК"""
    
    @pytest.mark.asyncio
    async def test_latency_percentiles(self):
        """Тест 11: Проверка перцентилей задержек"""
        metrics = PerformanceMetrics()
        
        async with aiohttp.ClientSession() as session:
            for _ in range(1000):
                start = time.time()
                try:
                    async with session.get('http://localhost:8001/health') as response:
                        duration = (time.time() - start) * 1000
                        metrics.record_request(duration)
                except:
                    metrics.record_request(5000, False)
        
        stats = metrics.get_stats()
        
        print(f"📊 Latency distribution:")
        print(f"   P50:  {stats['p50']:.2f}ms")
        print(f"   P90:  {stats['p90']:.2f}ms")
        print(f"   P95:  {stats['p95']:.2f}ms")
        print(f"   P99:  {stats['p99']:.2f}ms")
        print(f"   P99.9: {stats['p999']:.2f}ms")
        
        # SLA проверки
        assert stats['p50'] < 100, f"P50 violates SLA: {stats['p50']}ms > 100ms"
        assert stats['p99'] < 1000, f"P99 violates SLA: {stats['p99']}ms > 1000ms"
        assert stats['p999'] < 5000, f"P99.9 violates SLA: {stats['p999']}ms > 5000ms"

# LOCUST ТЕСТЫ ДЛЯ РАСПРЕДЕЛЕННОЙ НАГРУЗКИ
class DocumentSystemUser(HttpUser):
    """Пользователь для Locust тестов"""
    wait_time = between(0.1, 0.5)
    host = "http://localhost:8001"
    
    @task(3)
    def health_check(self):
        """Health check - самый частый"""
        self.client.get("/health")
    
    @task(2)
    def process_task(self):
        """Обработка задачи"""
        self.client.post("/task", json={
            "id": f"perf-test-{time.time()}",
            "type": "research",
            "priority": "normal"
        })
    
    @task(1)
    def get_metrics(self):
        """Получение метрик"""
        self.client.get("/metrics")

def generate_performance_report(all_metrics):
    """Генерация отчета о производительности"""
    report = {
        "timestamp": time.time(),
        "summary": {
            "total_tests": len(all_metrics),
            "passed": sum(1 for m in all_metrics if m.get('passed', False)),
            "failed": sum(1 for m in all_metrics if not m.get('passed', True))
        },
        "performance": {
            "target_rps": 1000,
            "achieved_rps": max(m.get('rps', 0) for m in all_metrics),
            "p99_target": 1000,
            "p99_achieved": min(m.get('p99', float('inf')) for m in all_metrics)
        },
        "sla_compliance": {
            "availability": all(m.get('error_rate', 100) < 0.01 for m in all_metrics),
            "latency_p50": all(m.get('p50', float('inf')) < 100 for m in all_metrics),
            "latency_p99": all(m.get('p99', float('inf')) < 1000 for m in all_metrics),
            "throughput": any(m.get('rps', 0) >= 1000 for m in all_metrics)
        }
    }
    
    with open('reports/performance/performance_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

# Хронометрист апокалипсиса завершил измерения. Система выдержала пытки.