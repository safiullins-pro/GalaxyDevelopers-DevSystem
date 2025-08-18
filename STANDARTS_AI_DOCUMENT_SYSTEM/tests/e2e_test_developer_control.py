import unittest
import subprocess
import time
import redis
import json

class TestDeveloperControlPhase(unittest.TestCase):

    def setUp(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True, password='galaxy_redis_secure_2024')

    def test_1_docker_isolation_build(self):
        """Тест: Сборка Docker-образа для изоляции"""
        try:
            subprocess.run(
                "docker build -t test_dev_env -f ../Dockerfile.dev_isolation .",
                shell=True, check=True, capture_output=True, text=True
            )
        except subprocess.CalledProcessError as e:
            self.fail(f"Сборка Docker-образа провалилась: {e.stderr}")

    def test_2_ai_agent_health_check(self):
        """Тест: Проверка здоровья AI агента через Redis"""
        # Предполагается, что агент запущен в отдельном процессе
        # python AGENTS/ai_code_auditor_agent.py
        
        # Отправляем ping
        ping_message = json.dumps({'agent_id': 'ai_code_auditor'})
        self.redis_client.publish('agent_ping', ping_message)
        
        # Ждем pong
        response_raw = self.redis_client.brpop('agent_pong', timeout=5)
        self.assertIsNotNone(response_raw, "Агент не ответил на ping в течение 5 секунд")
        
        response = json.loads(response_raw[1])
        self.assertEqual(response.get('agent_id'), 'ai_code_auditor')
        self.assertEqual(response.get('status'), 'alive')

    def test_3_file_monitoring_event(self):
        """Тест: Отправка и получение события изменения файла"""
        pubsub = self.redis_client.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe('analysis_results')
        
        # Отправляем тестовое событие
        test_event = {
            'file_path': 'test.py',
            'file_content': 'print("hello world")',
            'commit_id': 'test_commit_123'
        }
        self.redis_client.publish('file_changes', json.dumps(test_event))
        
        # Ждем результат анализа
        message = pubsub.get_message(timeout=5.0)
        self.assertIsNotNone(message, "Агент не прислал результат анализа")
        
        result = json.loads(message['data'])
        self.assertIn('tzComplianceScore', result)
        self.assertIn('qualityScore', result)
        
        pubsub.close()

if __name__ == '__main__':
    unittest.main()